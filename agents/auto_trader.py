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

import os
import time
from datetime import datetime

from rich.console import Console

from config.settings import settings
from tools.strategies import sma_crossover_signal, position_size

console = Console()


class AutoTrader:
    def __init__(
        self,
        symbols: list[str],
        interval_minutes: int = 15,
        cash_per_trade: float = 5000.0,
        max_positions: int = 5,
        short_window: int = 20,
        long_window: int = 50,
        timeframe: str = "1Day",
        cash_buffer: float = 0.0,
        dry_run: bool = False,
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
        self.short_window = short_window
        self.long_window = long_window
        self.timeframe = timeframe
        self.cash_buffer = cash_buffer
        self.dry_run = dry_run

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
        self._log(f"**Cycle start** ({mode}) watching {', '.join(self.symbols)}")

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

        self._log(
            f"Equity ${account.get('equity')}, buying power ${buying_power}, "
            f"{open_position_count} position(s), today P&L ${account.get('todays_pl')}"
        )

        actions = []

        # 3. Evaluate each symbol.
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

            if signal == "buy" and not holding:
                if open_position_count >= self.max_positions:
                    self._log(f"{symbol}: BUY signal but max_positions ({self.max_positions}) reached — skip.")
                    continue
                last_close = float(bars[-1]["close"])
                qty = position_size(buying_power, self.cash_per_trade, last_close, self.cash_buffer)
                if qty <= 0:
                    self._log(f"{symbol}: BUY signal but insufficient buying power to size a trade — skip.")
                    continue
                est_cost = round(qty * last_close, 2)
                actions.append({"symbol": symbol, "side": "buy", "qty": qty, "est_cost": est_cost})
                if self.dry_run:
                    self._log(f"{symbol}: [DRY-RUN] would BUY {qty} @ ~${last_close} (~${est_cost})")
                else:
                    try:
                        order = self.alpaca.submit_order(symbol=symbol, side="buy", qty=qty)
                        self._log(f"{symbol}: BUY {qty} submitted (order {order.get('id')}, status {order.get('status')})")
                        buying_power -= est_cost
                        open_position_count += 1
                    except (RuntimeError, ValueError) as e:
                        self._log(f"{symbol}: BUY rejected: {e}")

            elif signal == "sell" and holding:
                qty = positions[symbol]["qty"]
                actions.append({"symbol": symbol, "side": "sell", "qty": qty})
                if self.dry_run:
                    self._log(f"{symbol}: [DRY-RUN] would CLOSE position of {qty} shares")
                else:
                    try:
                        self.alpaca.close_position(symbol)
                        self._log(f"{symbol}: position CLOSED (bearish crossover)")
                        open_position_count = max(0, open_position_count - 1)
                    except RuntimeError as e:
                        self._log(f"{symbol}: close failed: {e}")
            else:
                state = "holding" if holding else "flat"
                self._log(f"{symbol}: signal={signal}, {state} — no action.")

        self._log(f"**Cycle end** — {len(actions)} action(s).")
        return {"skipped": False, "actions": actions, "account": account}

    # ------------------------------------------------------------------ #
    #  Continuous loop                                                    #
    # ------------------------------------------------------------------ #

    def run_forever(self) -> None:
        """Run run_once() every interval_minutes until interrupted (Ctrl-C)."""
        self._log(
            f"AutoTrader starting: interval={self.interval_minutes}m, "
            f"cash_per_trade=${self.cash_per_trade}, max_positions={self.max_positions}, "
            f"SMA {self.short_window}/{self.long_window} on {self.timeframe}. "
            f"Log: {self.log_path}"
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
