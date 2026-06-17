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

import csv
import json
import os
import re
import time
from datetime import datetime, timezone

from rich.console import Console

from config.settings import settings
from tools.strategies import (
    sma, sma_crossover_signal, position_size,
    volume_confirmed, participation_ok, risk_exit,
    session_bars, opening_range, orb_signal,
)
from tools import supabase_store

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
        enter_on_trend: bool = False,
        # Backtests (2022-2026, 10 mega-caps, daily bars) showed these two
        # filters reduce both return and Sharpe for this strategy, so they
        # default OFF and are opt-in for experimentation.
        confirm_volume: bool = False,
        volume_mult: float = 1.5,
        market_filter: bool = False,
        regime_symbol: str = "SPY",
        min_avg_volume: float = 2_000_000,
        min_atr: float = 1.0,
        # Risk-managed exits (percentages; 0 disables each). These exit a
        # position regardless of the SMA signal, so a trade can open and close
        # the same day when a stop or target is hit intraday.
        stop_loss_pct: float = 0.0,
        take_profit_pct: float = 0.0,
        trailing_stop_pct: float = 0.0,
        flatten_eod: bool = False,
        daily_loss_limit: float = 0.0,
        mode: str = "swing",
        # strategy: "sma" (daily trend) or "orb" (intraday opening-range
        # breakout). ORB uses or_bars (count of opening-range bars), volume_mult
        # (breakout volume vs OR average), market_filter (only enter when the
        # market is green on the day), and trailing_stop_pct for the trail.
        strategy: str = "sma",
        or_bars: int = 6,
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
        # How many calendar days of history to pull. Daily bars need a long
        # window; intraday bars (5Min etc.) pack ~78 bars/day, so a short span
        # keeps Alpaca's 1000-bar page on RECENT data instead of truncating to
        # stale bars from the start date.
        self.bars_days_back = (long_window * 3 + 10) if timeframe == "1Day" else 7
        self.cash_buffer = cash_buffer
        # Regime mode: also enter when already in an uptrend (short SMA above
        # long) and exit when in a downtrend, instead of trading only on the
        # exact crossover bar. Without it, a freshly started bot can wait
        # months for the next cross before its first trade.
        self.enter_on_trend = enter_on_trend
        # Participation filters ("only trade stocks in play"): a buy signal
        # must fire on above-average volume, the broad market must be in an
        # uptrend, and the symbol must have enough liquidity and range.
        # Exits are never gated — risk reduction always goes through.
        self.confirm_volume = confirm_volume
        self.volume_mult = volume_mult
        self.market_filter = market_filter
        self.regime_symbol = regime_symbol
        self.min_avg_volume = min_avg_volume
        self.min_atr = min_atr
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.trailing_stop_pct = trailing_stop_pct
        self.flatten_eod = flatten_eod
        self.daily_loss_limit = daily_loss_limit
        self.mode = mode
        self.strategy = strategy
        self.or_bars = or_bars
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

    def _log_trade(self, p: dict, status: str) -> None:
        """Append one executed/attempted trade to a CSV ready for analysis."""
        path = os.path.join(settings.output_dir, "reports", "trades.csv")
        fields = ["timestamp", "symbol", "action", "qty", "price", "est_cost",
                  "entry_price", "pnl_pct", "exit_reason", "mode", "reason", "status"]
        new_file = not os.path.exists(path)
        with open(path, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            if new_file:
                w.writeheader()
            w.writerow({
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "symbol": p["symbol"],
                "action": p["action"],
                "qty": p["qty"],
                "price": p.get("last_price"),
                "est_cost": p.get("est_cost"),
                "entry_price": p.get("entry_price"),
                "pnl_pct": p.get("pnl_pct"),
                "exit_reason": p.get("exit_reason", ""),
                "mode": self.mode,
                "reason": p.get("reason", ""),
                "status": status,
            })
        # Mirror to Supabase for durable history (best-effort; never blocks).
        supabase_store.log_trade({**p, "mode": self.mode, "status": status,
                                  "price": p.get("last_price")})

    # ------------------------------------------------------------------ #
    #  Exit helpers                                                       #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _minutes_to_close(clock: dict) -> float:
        """Minutes until the market closes, from the Alpaca clock. inf if unknown."""
        nxt = clock.get("next_close")
        if not nxt:
            return float("inf")
        try:
            close = datetime.fromisoformat(nxt.replace("Z", "+00:00"))
            return (close - datetime.now(timezone.utc)).total_seconds() / 60.0
        except (ValueError, AttributeError):
            return float("inf")

    def _peak_since_entry(self, symbol: str, bars: list[dict], fallback: float) -> float:
        """
        Highest price reached since the current position was opened, used for
        the trailing stop. Derived statelessly: find when the current net-long
        streak began from filled order history, then take the high of the bars
        on/after that date. Falls back to the recent bar high (or `fallback`)
        if order history is unavailable.
        """
        recent_high = max((float(b["high"]) for b in bars if b.get("high")), default=fallback)
        try:
            orders = self.alpaca.get_orders(status="all", limit=200)
        except RuntimeError:
            return recent_high
        fills = sorted(
            (o for o in orders
             if o.get("symbol") == symbol and o.get("filled_qty")
             and float(o.get("filled_qty", 0)) > 0 and o.get("submitted_at")),
            key=lambda o: o["submitted_at"],
        )
        # Walk forward; record the date the position last crossed from flat to long.
        net = 0.0
        entry_date = None
        for o in fills:
            q = float(o["filled_qty"]) * (1 if o.get("side") == "buy" else -1)
            if net <= 0 and net + q > 0:
                entry_date = o["submitted_at"][:10]
            net += q
        if entry_date is None:
            return recent_high
        highs = [float(b["high"]) for b in bars
                 if b.get("high") and b.get("t", "")[:10] >= entry_date]
        return max(highs) if highs else recent_high

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

        all_positions = {p["symbol"]: p for p in self.alpaca.simplify_positions(self.alpaca.get_positions())}
        # Scope to THIS bot's symbols only, so a second bot (e.g. intraday)
        # sharing the account never sees, sizes against, or flattens the other
        # bot's positions. Watchlists must be disjoint between bots.
        positions = {s: p for s, p in all_positions.items() if s in set(self.symbols)}
        open_orders = self.alpaca.get_orders(status="open")
        symbols_with_open_orders = {o.get("symbol") for o in open_orders}
        buying_power = account.get("buying_power", 0.0)
        open_position_count = len(positions)

        # Budget cap: capital already deployed in THIS bot's symbols counts
        # against the budget, so new buys can only spend what's left of it.
        deployed = sum(p.get("market_value", 0.0) for p in positions.values())
        if self.budget > 0:
            remaining_budget = max(0.0, self.budget - deployed)
            budget_note = f", budget ${remaining_budget:,.0f} of ${self.budget:,.0f} left"
        else:
            remaining_budget = float("inf")
            budget_note = ""

        todays_pl = account.get("todays_pl", 0.0)
        self._log(
            f"Equity ${account.get('equity')}, buying power ${buying_power}, "
            f"{open_position_count} position(s), today P&L ${todays_pl}"
            f"{budget_note}"
        )
        # Durable daily equity snapshot (upsert by date; best-effort). Records
        # the BOT's own P&L vs its budget — realized round-trips (this mode's
        # symbols) plus unrealized on current positions — so the scorecard can
        # measure drawdown/return on the bot, not the diluted account.
        bot_pnl = None
        if supabase_store.enabled():
            try:
                from tools.journal import build_ledger
                orders = self.alpaca.simplify_orders(self.alpaca.get_orders(status="all", limit=500))
                mine = set(self.symbols)
                realized = sum(t["pnl"] for t in build_ledger(orders) if t["symbol"] in mine)
                unrealized = sum(p.get("unrealized_pl", 0.0) for p in positions.values())
                bot_pnl = round(realized + unrealized, 2)
            except Exception:
                bot_pnl = None
        supabase_store.snapshot_equity({
            "snapshot_date": datetime.now().strftime("%Y-%m-%d"),
            "equity": account.get("equity"), "cash": account.get("cash"),
            "buying_power": buying_power, "positions": open_position_count,
            "todays_pl": todays_pl, "budget": self.budget, "bot_pnl": bot_pnl,
            "bot_return_pct": round(bot_pnl / self.budget * 100, 2)
            if (bot_pnl is not None and self.budget) else None,
        })

        # End-of-day flatten: within the final minutes of the session, close
        # this bot's open positions so nothing is held overnight (intraday mode).
        if self.flatten_eod and self._minutes_to_close(clock) <= 5 and positions:
            self._log("Flatten-EOD: closing this bot's positions before the bell.")
            proposals = [{
                "symbol": s, "action": "close", "qty": p["qty"],
                "last_price": p.get("current_price"),
                "signal": "sell", "exit_reason": "eod_flatten",
                "reason": "end-of-day flatten",
            } for s, p in positions.items()]
            executed = self._execute_proposals(proposals)
            self._log(f"**Cycle end** — flattened {len(executed)} position(s).")
            return {"skipped": False, "proposals": proposals, "executed": executed, "account": account}

        # Daily-loss circuit breaker: once the day's loss hits the limit, stop
        # opening/adding (set budget to 0) but still allow risk exits to fire.
        if self.daily_loss_limit > 0 and todays_pl <= -abs(self.daily_loss_limit):
            self._log(
                f"Daily-loss limit hit (today P&L ${todays_pl} ≤ -${self.daily_loss_limit}). "
                "No new buys this cycle; exits still active."
            )
            remaining_budget = 0.0

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
        if self.strategy == "orb":
            return self._gather_orb_proposals(
                positions, symbols_with_open_orders, buying_power,
                open_position_count, remaining_budget,
            )

        proposals: list[dict] = []
        remaining_bp = buying_power

        # Market regime gate: only open new longs when the broad market's own
        # short SMA is above its long SMA. Exits are never blocked by this.
        market_ok = True
        if self.market_filter:
            try:
                mkt_bars = self.alpaca.get_bars(
                    self.regime_symbol, timeframe=self.timeframe,
                    days_back=self.bars_days_back,
                )
                mkt_closes = [float(b["close"]) for b in mkt_bars if b.get("close") is not None]
                ms, ml = sma(mkt_closes, self.short_window), sma(mkt_closes, self.long_window)
                market_ok = ms is not None and ml is not None and ms > ml
                if not market_ok:
                    self._log(
                        f"Market filter: {self.regime_symbol} SMA{self.short_window} below "
                        f"SMA{self.long_window} — no NEW buys this cycle (exits still active)."
                    )
            except RuntimeError as e:
                self._log(f"Market filter: could not fetch {self.regime_symbol} bars ({e}) — "
                          "blocking new buys this cycle (fail-safe).")
                market_ok = False

        for symbol in self.symbols:
            if symbol in symbols_with_open_orders:
                self._log(f"{symbol}: open order already pending — skip.")
                continue

            try:
                bars = self.alpaca.get_bars(
                    symbol, timeframe=self.timeframe, days_back=self.bars_days_back
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

            # Risk-managed exits take priority over the SMA signal: a stop,
            # take-profit, or trailing stop closes the position regardless of
            # trend, and can fire the same day the position was opened.
            if holding and last_close > 0 and (
                self.stop_loss_pct or self.take_profit_pct or self.trailing_stop_pct
            ):
                entry = float(positions[symbol].get("avg_entry_price") or 0.0)
                peak = self._peak_since_entry(symbol, bars, last_close)
                rexit = risk_exit(
                    entry, last_close, peak,
                    stop_pct=self.stop_loss_pct,
                    take_profit_pct=self.take_profit_pct,
                    trail_pct=self.trailing_stop_pct,
                )
                if rexit:
                    pnl_pct = (last_close - entry) / entry * 100 if entry else 0.0
                    label = {"stop": "stop-loss", "take_profit": "take-profit",
                             "trailing": "trailing stop"}[rexit]
                    self._log(f"{symbol}: EXIT — {label} ({pnl_pct:+.1f}% vs entry ${entry:.2f}).")
                    proposals.append({
                        "symbol": symbol, "action": "close",
                        "qty": positions[symbol]["qty"],
                        "last_price": round(last_close, 2),
                        "entry_price": round(entry, 2),
                        "pnl_pct": round(pnl_pct, 2),
                        "signal": "sell", "exit_reason": rexit,
                        "reason": f"{label} ({pnl_pct:+.1f}% vs entry)",
                    })
                    continue

            # Regime mode: trade the current trend, not just the cross bar.
            reason = {"buy": "bullish SMA crossover", "sell": "bearish SMA crossover"}.get(signal, "")
            if self.enter_on_trend and signal == "hold" and short_sma and long_sma:
                if not holding and short_sma > long_sma:
                    signal, reason = "buy", "bullish regime (short SMA above long)"
                elif holding and short_sma < long_sma:
                    signal, reason = "sell", "bearish regime (short SMA below long)"

            if signal == "buy" and not holding:
                if not market_ok:
                    self._log(f"{symbol}: BUY blocked — market regime filter ({self.regime_symbol} downtrend).")
                    continue
                if not participation_ok(bars, self.min_avg_volume, self.min_atr):
                    self._log(
                        f"{symbol}: BUY blocked — not enough participation "
                        f"(needs avg vol ≥ {self.min_avg_volume:,.0f} and ATR ≥ ${self.min_atr})."
                    )
                    continue
                if (self.confirm_volume and "crossover" in reason
                        and not volume_confirmed(bars, mult=self.volume_mult)):
                    self._log(
                        f"{symbol}: BUY blocked — crossover fired on weak volume "
                        f"(needs ≥ {self.volume_mult}x the 20-day average)."
                    )
                    continue
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
                    "reason": reason,
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
                    "reason": reason,
                })
            elif (holding and self.enter_on_trend and market_ok
                  and short_sma and long_sma and short_sma > long_sma
                  and positions[symbol].get("market_value", 0.0) < self.cash_per_trade * 0.6):
                # Top up an under-sized position toward cash_per_trade so a
                # raised budget actually gets deployed into existing trends.
                gap = self.cash_per_trade - positions[symbol].get("market_value", 0.0)
                spendable = min(remaining_bp, remaining_budget)
                qty = position_size(spendable, gap, last_close, self.cash_buffer)
                if qty > 0:
                    est_cost = round(qty * last_close, 2)
                    remaining_bp -= est_cost
                    remaining_budget -= est_cost
                    proposals.append({
                        "symbol": symbol,
                        "action": "buy",
                        "qty": qty,
                        "est_cost": est_cost,
                        "last_price": round(last_close, 2),
                        "signal": "buy",
                        "short_sma": round(short_sma, 2),
                        "long_sma": round(long_sma, 2),
                        "reason": "top-up to target position size",
                    })
                else:
                    self._log(f"{symbol}: under-sized but no budget left to top up.")
            else:
                state = "holding" if holding else "flat"
                self._log(f"{symbol}: signal={signal}, {state} — no action.")

        return proposals

    # ------------------------------------------------------------------ #
    #  Opening-range-breakout proposals (intraday)                        #
    # ------------------------------------------------------------------ #

    def _gather_orb_proposals(
        self, positions: dict, symbols_with_open_orders: set, buying_power: float,
        open_position_count: int, remaining_budget: float = float("inf"),
    ) -> list[dict]:
        """
        Intraday opening-range breakout (validated edge): enter above the first
        30 minutes' high on volume while the market is green; exit on the
        opening-range low, a trailing stop, or the end-of-day flatten. Long-only,
        one entry per symbol per day. Shares tools.strategies.orb_signal with the
        backtester so live and tested behaviour match.
        """
        proposals: list[dict] = []
        remaining_bp = buying_power

        # Market-green filter: SPY above its session open.
        market_ok = True
        session_date = None
        try:
            mkt = self.alpaca.get_bars(self.regime_symbol, timeframe=self.timeframe,
                                       days_back=self.bars_days_back)
            if mkt:
                session_date = mkt[-1]["t"][:10]
                mday = session_bars(mkt, session_date)
                if mday and self.market_filter:
                    market_ok = float(mday[-1]["close"]) > float(mday[0]["open"])
                    if not market_ok:
                        self._log(f"ORB: {self.regime_symbol} below its session open — "
                                  "no new breakouts this cycle (exits still active).")
        except RuntimeError as e:
            if self.market_filter:
                self._log(f"ORB: market data fetch failed ({e}) — blocking new entries.")
                market_ok = False

        # One breakout entry per symbol per day.
        traded_today: set = set()
        if session_date:
            try:
                for o in self.alpaca.get_orders(status="all", limit=200):
                    if (o.get("side") == "buy" and float(o.get("filled_qty") or 0) > 0
                            and (o.get("submitted_at") or "")[:10] == session_date):
                        traded_today.add(o.get("symbol"))
            except RuntimeError:
                pass

        for symbol in self.symbols:
            try:
                bars = self.alpaca.get_bars(symbol, timeframe=self.timeframe,
                                            days_back=self.bars_days_back)
            except RuntimeError as e:
                self._log(f"{symbol}: bar fetch failed: {e}")
                continue
            sdate = session_date or (bars[-1]["t"][:10] if bars else None)
            day = session_bars(bars, sdate) if sdate else []
            if not day:
                continue
            last_close = float(day[-1]["close"])
            rng = opening_range(day, self.or_bars)

            if symbol in positions:
                # Exit: opening-range-low stop first, then trailing stop.
                entry = float(positions[symbol].get("avg_entry_price") or 0.0)
                peak = max((float(b["high"]) for b in day), default=last_close)
                reason = None
                if rng and last_close <= rng["low"]:
                    reason = "orb_stop"
                elif (self.trailing_stop_pct and peak > 0
                      and (last_close - peak) / peak * 100 <= -self.trailing_stop_pct):
                    reason = "trailing"
                if reason:
                    pnl_pct = (last_close - entry) / entry * 100 if entry else 0.0
                    self._log(f"{symbol}: ORB EXIT — {reason} ({pnl_pct:+.1f}% vs entry).")
                    proposals.append({
                        "symbol": symbol, "action": "close", "qty": positions[symbol]["qty"],
                        "last_price": round(last_close, 2), "entry_price": round(entry, 2),
                        "pnl_pct": round(pnl_pct, 2), "signal": "sell",
                        "exit_reason": reason, "reason": f"ORB {reason}",
                    })
                continue

            # Entry gates: not already traded today, no pending order, market
            # green, a fresh breakout, and room under the caps/budget.
            if symbol in symbols_with_open_orders or symbol in traded_today:
                continue
            if not market_ok:
                continue
            if orb_signal(day, self.or_bars, self.volume_mult) != "buy":
                continue
            if open_position_count >= self.max_positions:
                self._log(f"{symbol}: ORB breakout but max_positions ({self.max_positions}) reached — skip.")
                continue
            spendable = min(remaining_bp, remaining_budget)
            qty = position_size(spendable, self.cash_per_trade, last_close, self.cash_buffer)
            if qty <= 0:
                self._log(f"{symbol}: ORB breakout but insufficient budget/buying power — skip.")
                continue
            est_cost = round(qty * last_close, 2)
            remaining_bp -= est_cost
            remaining_budget -= est_cost
            open_position_count += 1
            orh = rng["high"] if rng else last_close
            self._log(f"{symbol}: ORB BREAKOUT — buy {qty} @ ~${last_close:.2f} (OR high ${orh:.2f}).")
            proposals.append({
                "symbol": symbol, "action": "buy", "qty": qty, "est_cost": est_cost,
                "last_price": round(last_close, 2), "signal": "buy",
                "reason": "opening-range breakout",
            })
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
                    self._log_trade(p, "submitted")
                    executed.append(p)
                except (RuntimeError, ValueError) as e:
                    self._log(f"{symbol}: BUY rejected: {e}")
                    self._log_trade(p, f"rejected: {e}")
            elif action == "close":
                if self.dry_run:
                    self._log(f"{symbol}: [DRY-RUN] would CLOSE position of {qty} shares")
                    executed.append(p)
                    continue
                try:
                    self.alpaca.close_position(symbol)
                    self._log(f"{symbol}: position CLOSED ({p.get('reason', 'bearish signal')})")
                    self._log_trade(p, "submitted")
                    executed.append(p)
                except RuntimeError as e:
                    self._log(f"{symbol}: close failed: {e}")
                    self._log_trade(p, f"failed: {e}")
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
        # Liveness ping so we can confirm the always-on runner booted and its
        # Supabase connection works without waiting for the market to open.
        supabase_store.heartbeat(
            f"runner up: {self.strategy}/{self.mode} {','.join(self.symbols)}",
            mode=self.mode)
        try:
            while True:
                result = {}
                try:
                    result = self.run_once() or {}
                except Exception as e:  # keep the loop alive across transient errors
                    self._log(f"Cycle error (continuing): {e}")
                # When the market is closed, idle in longer naps so an always-on
                # host isn't doing 5-minute no-ops (and spamming logs) overnight.
                closed = result.get("skipped") and result.get("reason") == "market_closed"
                nap = 15 if closed else self.interval_minutes
                console.print(f"[dim]Sleeping {nap} min...[/dim]")
                time.sleep(nap * 60)
        except KeyboardInterrupt:
            self._log("AutoTrader stopped by user (KeyboardInterrupt).")
            console.print("\n[bold yellow]AutoTrader stopped.[/bold yellow]")
