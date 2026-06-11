"""
AutoTrader: Unattended, rule-based paper-trading loop.

Runs a deterministic SMA-crossover momentum strategy over a watchlist against
the Alpaca PAPER account. No LLM call per tick — it's fully auditable, free to
run continuously, and bounded by explicit risk caps.

Flow per cycle (run_once):
  1. Skip if the market is closed.
  2. Refresh account + current positions + open orders.
  3. For each watchlist symbol:
       - pull recent bars, compute the crossover signal
       - BUY on a fresh bullish crossover (if not already holding and caps allow)
       - close the position on a fresh bearish crossover (if holding)
  4. Log every decision.

Requires ALPACA_API_KEY_ID and ALPACA_API_SECRET_KEY in .env.
"""

import json
import os
import re
import time
from datetime import datetime

from rich.console import Console

from config.settings import settings
from tools.strategies import sma, sma_crossover_signal, position_size

console = Console()


class AutoTrader:
    def __init__(
        self,
        symbols: list[str],
        interval_minutes: int = 15,
        cash_per_trade: float = 1000.0,
        max_positions: int = 5,
        budget: float = 5000.0,
        short_window: int = 20,
        long_window: int = 50,
        timeframe: str = "1Day",
        cash_buffer: float = 0.0,
        dry_run: bool = False,
        llm_review: bool = False,
        paper: bool | None = None,
    ):
        # Lazy import so missing credentials only error when the trader is used.
        from tools.alpaca_client import AlpacaClient

        if not symbols:
            raise ValueError("AutoTrader needs at least one symbol to watch.")

        self.alpaca = AlpacaClient(paper=paper)
        if not self.alpaca.paper:
            # Hard guard: v1 is paper-only. Refuse to auto-trade real money.
            raise EnvironmentError(
                "AutoTrader is paper-only in this version. "
                "Set ALPACA_PAPER=true in your .env before running."
            )

        self.symbols = [s.strip().upper() for s in symbols if s.strip()]
        self.interval_minutes = interval_minutes
        self.cash_per_trade = cash_per_trade
        self.max_positions = max_positions
        # Total capital the bot may deploy across all positions. The rest of
        # the account stays untouched. <= 0 means no cap.
        self.budget = budget
        self.short_window = short_window
        self.long_window = long_window
        self.timeframe = timeframe
        self.cash_buffer = cash_buffer
        self.dry_run = dry_run
        self.llm_review = llm_review
        self._llm_client = None  # lazy Anthropic client for the review layer

        os.makedirs(os.path.join(settings.output_dir, "reports"), exist_ok=True)
        self.log_path = os.path.join(
            settings.output_dir,
            "reports",
            f"autotrade_log_{datetime.now().strftime('%Y%m%d')}.md",
        )

    # ------------------------------------------------------------------ #
    #  Logging                                                            #
    # ------------------------------------------------------------------ #

    def _log(self, message: str) -> None:
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"- `{stamp}` {message}"
        console.print(f"[dim]{stamp}[/dim] {message}")
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    # ------------------------------------------------------------------ #
    #  One cycle                                                          #
    # ------------------------------------------------------------------ #

    def run_once(self) -> dict:
        """Run a single decision cycle. Returns a summary dict."""
        mode = "DRY-RUN" if self.dry_run else "LIVE-PAPER"
        review = " +LLM-review" if self.llm_review else ""
        self._log(f"**Cycle start** ({mode}{review}) watching {', '.join(self.symbols)}")

        # 1. Market hours gate.
        try:
            clock = self.alpaca.get_clock()
        except RuntimeError as e:
            self._log(f"Could not fetch market clock: {e}. Skipping cycle.")
            return {"skipped": True, "reason": "clock_error"}

        if not clock.get("is_open", False):
            nxt = clock.get("next_open", "?")
            self._log(f"Market is CLOSED. Next open: {nxt}. No trades.")
            return {"skipped": True, "reason": "market_closed"}

        # 2. Account + positions + open orders.
        account = self.alpaca.account_summary()
        if account.get("trading_blocked") or account.get("account_blocked"):
            self._log("Account is blocked from trading. Aborting cycle.")
            return {"skipped": True, "reason": "account_blocked"}

        positions = {p["symbol"]: p for p in self.alpaca.simplify_positions(self.alpaca.get_positions())}
        open_orders = self.alpaca.get_orders(status="open")
        symbols_with_open_orders = {o.get("symbol") for o in open_orders}
        buying_power = account.get("buying_power", 0.0)
        open_position_count = len(positions)

        # Budget cap: capital already deployed counts against the budget, so
        # new buys can only spend what's left of it.
        deployed = sum(p.get("market_value", 0.0) for p in positions.values())
        if self.budget > 0:
            remaining_budget = max(0.0, self.budget - deployed)
            budget_note = f", budget ${remaining_budget:,.0f} of ${self.budget:,.0f} left"
        else:
            remaining_budget = float("inf")
            budget_note = ""

        self._log(
            f"Equity ${account.get('equity')}, buying power ${buying_power}, "
            f"{open_position_count} position(s), today P&L ${account.get('todays_pl')}"
            f"{budget_note}"
        )

        # 3. Gather proposals from the deterministic strategy (no orders yet).
        proposals = self._gather_proposals(
            positions, symbols_with_open_orders, buying_power, open_position_count,
            remaining_budget,
        )

        # 4. Optional LLM risk review — may veto proposals before execution.
        if self.llm_review and proposals:
            proposals = self._apply_llm_review(proposals, account, positions)

        # 5. Execute the surviving proposals (or log them under --dry-run).
        executed = self._execute_proposals(proposals)

        self._log(f"**Cycle end** — {len(executed)} action(s) of {len(proposals)} proposed.")
        return {"skipped": False, "proposals": proposals, "executed": executed, "account": account}

    # ------------------------------------------------------------------ #
    #  Proposal gathering (deterministic)                                 #
    # ------------------------------------------------------------------ #

    def _gather_proposals(
        self, positions: dict, symbols_with_open_orders: set, buying_power: float,
        open_position_count: int, remaining_budget: float = float("inf"),
    ) -> list[dict]:
        """Compute the strategy's proposed trades without placing any orders."""
        proposals: list[dict] = []
        remaining_bp = buying_power

        for symbol in self.symbols:
            if symbol in symbols_with_open_orders:
                self._log(f"{symbol}: open order already pending — skip.")
                continue

            try:
                bars = self.alpaca.get_bars(
                    symbol, timeframe=self.timeframe, days_back=self.long_window * 3 + 10
                )
            except RuntimeError as e:
                self._log(f"{symbol}: bar fetch failed: {e}")
                continue

            signal = sma_crossover_signal(
                bars, short_window=self.short_window, long_window=self.long_window
            )
            holding = symbol in positions
            closes = [float(b["close"]) for b in bars if b.get("close") is not None]
            last_close = closes[-1] if closes else 0.0
            short_sma = sma(closes, self.short_window)
            long_sma = sma(closes, self.long_window)

            if signal == "buy" and not holding:
                if open_position_count >= self.max_positions:
                    self._log(f"{symbol}: BUY signal but max_positions ({self.max_positions}) reached — skip.")
                    continue
                spendable = min(remaining_bp, remaining_budget)
                qty = position_size(spendable, self.cash_per_trade, last_close, self.cash_buffer)
                if qty <= 0:
                    self._log(
                        f"{symbol}: BUY signal but insufficient budget/buying power "
                        f"(${spendable:,.0f} spendable) — skip."
                    )
                    continue
                est_cost = round(qty * last_close, 2)
                remaining_bp -= est_cost
                remaining_budget -= est_cost
                open_position_count += 1
                proposals.append({
                    "symbol": symbol,
                    "action": "buy",
                    "qty": qty,
                    "est_cost": est_cost,
                    "last_price": round(last_close, 2),
                    "signal": signal,
                    "short_sma": round(short_sma, 2) if short_sma else None,
                    "long_sma": round(long_sma, 2) if long_sma else None,
                    "reason": "bullish SMA crossover",
                })

            elif signal == "sell" and holding:
                proposals.append({
                    "symbol": symbol,
                    "action": "close",
                    "qty": positions[symbol]["qty"],
                    "last_price": round(last_close, 2),
                    "signal": signal,
                    "short_sma": round(short_sma, 2) if short_sma else None,
                    "long_sma": round(long_sma, 2) if long_sma else None,
                    "reason": "bearish SMA crossover",
                })
            else:
                state = "holding" if holding else "flat"
                self._log(f"{symbol}: signal={signal}, {state} — no action.")

        return proposals

    # ------------------------------------------------------------------ #
    #  Execution                                                          #
    # ------------------------------------------------------------------ #

    def _execute_proposals(self, proposals: list[dict]) -> list[dict]:
        """Place orders for approved proposals (or log them under dry_run)."""
        executed: list[dict] = []
        for p in proposals:
            symbol, action, qty = p["symbol"], p["action"], p["qty"]
            if action == "buy":
                if self.dry_run:
                    self._log(f"{symbol}: [DRY-RUN] would BUY {qty} @ ~${p['last_price']} (~${p['est_cost']})")
                    executed.append(p)
                    continue
                try:
                    order = self.alpaca.submit_order(symbol=symbol, side="buy", qty=qty)
                    self._log(f"{symbol}: BUY {qty} submitted (order {order.get('id')}, status {order.get('status')})")
                    executed.append(p)
                except (RuntimeError, ValueError) as e:
                    self._log(f"{symbol}: BUY rejected: {e}")
            elif action == "close":
                if self.dry_run:
                    self._log(f"{symbol}: [DRY-RUN] would CLOSE position of {qty} shares")
                    executed.append(p)
                    continue
                try:
                    self.alpaca.close_position(symbol)
                    self._log(f"{symbol}: position CLOSED (bearish crossover)")
                    executed.append(p)
                except RuntimeError as e:
                    self._log(f"{symbol}: close failed: {e}")
        return executed

    # ------------------------------------------------------------------ #
    #  LLM risk review (optional)                                         #
    # ------------------------------------------------------------------ #

    def _apply_llm_review(self, proposals: list[dict], account: dict, positions: dict) -> list[dict]:
        """
        Ask Claude to sanity-check the proposed trades as a conservative risk
        reviewer. Returns only the proposals Claude approves. Fail-safe: if the
        review errors or can't be parsed, the trades are VETOED (we don't trade
        on an unreviewed signal when review was explicitly requested).
        """
        import anthropic

        if self._llm_client is None:
            self._llm_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        payload = {
            "account": {
                "equity": account.get("equity"),
                "buying_power": account.get("buying_power"),
                "todays_pl": account.get("todays_pl"),
                "open_positions": len(positions),
                "max_positions": self.max_positions,
            },
            "proposed_trades": proposals,
        }
        system = (
            "You are a conservative risk reviewer for an automated PAPER trading bot "
            "that uses an SMA-crossover momentum strategy. You are given the account "
            "state and a list of proposed trades. Approve trades that are reasonable "
            "and well-sized; veto trades that look risky, oversized relative to equity, "
            "or where the crossover looks weak/noisy. This is paper money, so bias "
            "toward letting sound momentum trades through, but block anything reckless. "
            "Respond with ONLY a JSON object of the form: "
            '{"verdicts": [{"symbol": "AAPL", "approved": true, "reason": "..."}]}. '
            "Include one verdict per proposed trade. No prose outside the JSON."
        )
        try:
            resp = self._llm_client.messages.create(
                model=settings.model,
                max_tokens=1024,
                system=system,
                messages=[{"role": "user", "content": json.dumps(payload, indent=2)}],
            )
            text = "".join(b.text for b in resp.content if hasattr(b, "text"))
            verdicts = self._parse_verdicts(text)
        except Exception as e:
            self._log(f"LLM review failed ({e}) — vetoing all proposals this cycle (fail-safe).")
            return []

        approved: list[dict] = []
        for p in proposals:
            v = verdicts.get(p["symbol"])
            if v is None:
                self._log(f"{p['symbol']}: no LLM verdict returned — vetoed (fail-safe).")
                continue
            if v.get("approved"):
                self._log(f"{p['symbol']}: LLM APPROVED — {v.get('reason', '')}")
                approved.append(p)
            else:
                self._log(f"{p['symbol']}: LLM VETOED — {v.get('reason', '')}")
        return approved

    @staticmethod
    def _parse_verdicts(text: str) -> dict:
        """Extract {symbol: verdict} from the model's JSON reply, tolerating fences."""
        cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
        # Fall back to grabbing the outermost JSON object if there's stray text.
        if not cleaned.startswith("{"):
            match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
            cleaned = match.group(0) if match else cleaned
        data = json.loads(cleaned)
        return {v["symbol"].upper(): v for v in data.get("verdicts", []) if "symbol" in v}

    # ------------------------------------------------------------------ #
    #  Continuous loop                                                    #
    # ------------------------------------------------------------------ #

    def run_forever(self) -> None:
        """Run run_once() every interval_minutes until interrupted (Ctrl-C)."""
        self._log(
            f"AutoTrader starting: interval={self.interval_minutes}m, "
            f"budget=${self.budget}, cash_per_trade=${self.cash_per_trade}, "
            f"max_positions={self.max_positions}, "
            f"SMA {self.short_window}/{self.long_window} on {self.timeframe}, "
            f"llm_review={self.llm_review}. Log: {self.log_path}"
        )
        try:
            while True:
                try:
                    self.run_once()
                except Exception as e:  # keep the loop alive across transient errors
                    self._log(f"Cycle error (continuing): {e}")
                console.print(f"[dim]Sleeping {self.interval_minutes} min...[/dim]")
                time.sleep(self.interval_minutes * 60)
        except KeyboardInterrupt:
            self._log("AutoTrader stopped by user (KeyboardInterrupt).")
            console.print("\n[bold yellow]AutoTrader stopped.[/bold yellow]")
