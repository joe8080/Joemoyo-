"""
CopyTrader: the copy-trade paper sleeve.

A scout (Grok Bot) drops trade IDEAS into the Supabase signal inbox. This
engine decides whether each idea becomes a paper trade. The scout never places
an order and never holds an Alpaca key — every trade goes through the caps
below, on a SEPARATE Alpaca paper account, so nothing here can touch the
swing/intraday battle test or its scorecard.

Flow per cycle (run_once):
  1. Skip if the market is closed (ideas wait in the inbox).
  2. Tidy up any idea left half-processed by a crash.
  3. Risk exits on what the sleeve holds (trailing stop / stop-loss).
  4. Sell ideas: close a holding when the person we copied sells.
  5. Buy ideas, best conviction first, each through every gate:
       fresh enough -> tradable -> liquid -> room under the caps -> buy.
  6. Journal every decision and snapshot the sleeve.

Every idea ends in exactly one state: executed, rejected (with the reason),
expired (too old), or left as new (deferred to a later cycle because a daily
or budget cap is full).

Requires ALPACA_COPY_API_KEY_ID / ALPACA_COPY_API_SECRET_KEY (a dedicated paper
account) plus SUPABASE_URL / SUPABASE_SERVICE_KEY.
"""

import os
import re
from datetime import date, datetime, timedelta, timezone

from rich.console import Console

from config.settings import settings
from tools import supabase_store
from tools.strategies import participation_ok, position_size, risk_exit

console = Console()

# The inbox function already enforces this; the engine checks again so a row
# written any other way can never reach an order or a query.
TICKER = re.compile(r"[A-Z]{1,5}(\.[A-Z])?")


def entry_date_from_orders(orders: list[dict], symbol: str) -> str | None:
    """Date the current long position in `symbol` was opened (flat -> long)."""
    fills = sorted(
        (o for o in orders
         if o.get("symbol") == symbol and float(o.get("filled_qty") or 0) > 0
         and o.get("submitted_at")),
        key=lambda o: o["submitted_at"],
    )
    net, entry = 0.0, None
    for o in fills:
        q = float(o["filled_qty"]) * (1 if o.get("side") == "buy" else -1)
        if net <= 0 and net + q > 0:
            entry = o["submitted_at"][:10]
        net += q
    return entry


class CopyTrader:
    def __init__(
        self,
        budget: float = 10_000.0,
        cash_per_trade: float = 1_000.0,
        max_positions: int = 10,
        max_new_per_day: int = 3,
        # An idea is stale once its public disclosure is this old...
        max_signal_age_days: int = 10,
        # ...or the original trade itself happened this long ago.
        max_trade_lag_days: int = 60,
        min_conviction: int = 3,
        trailing_stop_pct: float = 8.0,
        stop_loss_pct: float = 0.0,
        daily_loss_limit: float = 300.0,
        min_price: float = 5.0,
        min_avg_volume: float = 1_000_000,
        dry_run: bool = False,
        alpaca=None,
        store=None,
    ):
        self.store = store or supabase_store
        if not self.store.enabled():
            raise EnvironmentError(
                "The copy sleeve needs the Supabase signal inbox. Set "
                "SUPABASE_URL and SUPABASE_SERVICE_KEY where this runs."
            )
        self.alpaca = alpaca or self._dedicated_client()
        if not getattr(self.alpaca, "paper", False):
            raise EnvironmentError("The copy sleeve is paper-only.")

        self.budget = budget
        self.cash_per_trade = cash_per_trade
        self.max_positions = max_positions
        self.max_new_per_day = max_new_per_day
        self.max_signal_age_days = max_signal_age_days
        self.max_trade_lag_days = max_trade_lag_days
        self.min_conviction = min_conviction
        self.trailing_stop_pct = trailing_stop_pct
        self.stop_loss_pct = stop_loss_pct
        self.daily_loss_limit = daily_loss_limit
        self.min_price = min_price
        self.min_avg_volume = min_avg_volume
        self.dry_run = dry_run

        os.makedirs(os.path.join(settings.output_dir, "reports"), exist_ok=True)
        self.log_path = os.path.join(
            settings.output_dir, "reports",
            f"copytrade_log_{datetime.now().strftime('%Y%m%d')}.md",
        )

    @staticmethod
    def _dedicated_client():
        """Alpaca client for the sleeve's OWN paper account — never the main one."""
        from tools.alpaca_client import AlpacaClient

        key = os.environ.get("ALPACA_COPY_API_KEY_ID", "").strip().strip('"\'')
        secret = os.environ.get("ALPACA_COPY_API_SECRET_KEY", "").strip().strip('"\'')
        if not key or not secret:
            raise EnvironmentError(
                "The copy sleeve trades its own Alpaca paper account. Create one "
                "(Alpaca dashboard > account menu > Open New Paper Account), "
                "generate its API keys, and set ALPACA_COPY_API_KEY_ID and "
                "ALPACA_COPY_API_SECRET_KEY where this runs."
            )
        if key == settings.alpaca_api_key_id:
            raise EnvironmentError(
                "ALPACA_COPY_API_KEY_ID is the same as the main account's key. "
                "The copy sleeve must use a separate paper account so it cannot "
                "disturb the swing/intraday test."
            )
        # paper=True is forced: live keys simply fail against the paper endpoint.
        return AlpacaClient(paper=True, key_id=key, secret_key=secret)

    # ------------------------------------------------------------------ #
    #  Logging                                                            #
    # ------------------------------------------------------------------ #

    def _log(self, message: str) -> None:
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        console.print(f"{stamp} {message}", markup=False, highlight=False)
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(f"- `{stamp}` {message}\n")

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def _finish(self, sig: dict, status: str, reason: str, **extra) -> None:
        self._log(f"{sig['symbol']} (idea #{sig['id']}): {status.upper()} — {reason}")
        if not self.dry_run:
            self.store.finish_signal(sig["id"], status, reason, self._now(), **extra)

    # ------------------------------------------------------------------ #
    #  One cycle                                                          #
    # ------------------------------------------------------------------ #

    def run_once(self) -> dict:
        tag = "DRY-RUN" if self.dry_run else "PAPER"
        self._log(f"**Copy cycle start** ({tag})")
        out = {"skipped": False, "bought": [], "closed": [], "rejected": 0,
               "expired": 0, "deferred": 0}

        try:
            clock = self.alpaca.get_clock()
        except RuntimeError as e:
            if "401" in str(e) or "403" in str(e):
                self._log(f"ALPACA AUTH FAILED (copy account): {e}")
                raise EnvironmentError(
                    "Alpaca rejected the copy-sleeve keys (401/403). Update "
                    "ALPACA_COPY_API_KEY_ID / ALPACA_COPY_API_SECRET_KEY."
                ) from e
            self._log(f"Could not fetch market clock: {e}. Skipping cycle.")
            return {"skipped": True, "reason": "clock_error"}
        if not clock.get("is_open", False):
            self._log(f"Market is CLOSED. Next open: {clock.get('next_open', '?')}. "
                      "Ideas wait in the inbox.")
            return {"skipped": True, "reason": "market_closed"}

        account = self.alpaca.account_summary()
        if account.get("trading_blocked") or account.get("account_blocked"):
            self._log("Copy account is blocked from trading. Aborting cycle.")
            return {"skipped": True, "reason": "account_blocked"}

        signals = self.store.get_new_signals()
        if signals is None:
            # Unreachable inbox must not look like a quiet "nothing to do".
            self._log("SIGNAL INBOX UNREACHABLE — no new buys this cycle; "
                      "risk exits still run.")
            signals = []
            out["inbox_error"] = True

        positions = {p["symbol"]: p for p in
                     self.alpaca.simplify_positions(self.alpaca.get_positions())}
        raw_orders = self.alpaca.get_orders(status="all", limit=500)
        pending = {o.get("symbol") for o in self.alpaca.get_orders(status="open")}
        self._reconcile_stuck(positions, pending)

        # 3. Risk exits first — risk reduction is never gated.
        for symbol in list(positions):
            if symbol in pending:
                continue
            closed = self._risk_exit(symbol, positions[symbol], raw_orders)
            if closed:
                out["closed"].append(closed)
                positions.pop(symbol)

        # 4. Sell ideas.
        for sig in [s for s in signals if s.get("side") == "sell"]:
            result = self._handle_sell(sig, positions, pending)
            if isinstance(result, dict):
                out["closed"].append(result)
                positions.pop(sig["symbol"], None)
            else:
                out[result] += 1

        # 5. Buy ideas — strongest conviction first, then oldest.
        deployed = sum(p.get("market_value", 0.0) for p in positions.values())
        state = {
            "remaining_budget": max(0.0, self.budget - deployed),
            "buying_power": account.get("buying_power", 0.0),
            "open_count": len(positions),
            "new_today": 0,
            "halted": None,
        }
        todays_pl = account.get("todays_pl", 0.0)
        if self.daily_loss_limit > 0 and todays_pl <= -abs(self.daily_loss_limit):
            state["halted"] = (f"daily-loss limit hit (today ${todays_pl:,.2f}); "
                               "no new buys today")
        else:
            midnight = datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00Z")
            counted = self.store.count_copy_buys_since(midnight)
            if counted is None:
                state["halted"] = "could not count today's buys; no new buys this cycle"
            else:
                state["new_today"] = counted
        if state["halted"]:
            self._log(f"New buys paused: {state['halted']}.")

        buys = sorted((s for s in signals if s.get("side") == "buy"),
                      key=lambda s: (-(s.get("conviction") or 0), s.get("created_at") or ""))
        for sig in buys:
            result = self._handle_buy(sig, positions, pending, state)
            if result == "deferred":
                out["deferred"] += 1
            elif result in ("rejected", "expired"):
                out[result] += 1
            else:
                out["bought"].append(result)

        self._snapshot(account, positions, raw_orders)
        self._log(
            f"**Copy cycle end** — bought {len(out['bought'])}, closed "
            f"{len(out['closed'])}, rejected {out['rejected']}, expired "
            f"{out['expired']}, waiting {out['deferred']}."
        )
        return out

    # ------------------------------------------------------------------ #
    #  Crash recovery                                                     #
    # ------------------------------------------------------------------ #

    def _reconcile_stuck(self, positions: dict, pending: set) -> None:
        """An idea stuck in 'executing' means a cycle died between claiming it
        and recording the order. Settle it from what the account actually shows."""
        if self.dry_run:
            return
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat(timespec="seconds")
        for sig in self.store.get_stuck_signals(cutoff):
            sym = sig["symbol"]
            if sig["side"] == "buy" and (sym in positions or sym in pending):
                self._finish(sig, "executed", "recovered after an interrupted cycle")
            elif sig["side"] == "sell" and sym not in positions:
                self._finish(sig, "executed", "recovered after an interrupted cycle")
            else:
                self._finish(sig, "rejected", "cycle was interrupted before the order went in")

    # ------------------------------------------------------------------ #
    #  Exits                                                              #
    # ------------------------------------------------------------------ #

    def _close(self, symbol: str, pos: dict, reason: str, exit_reason: str,
               signal_id: int | None = None) -> dict | None:
        entry = float(pos.get("avg_entry_price") or 0.0)
        last = float(pos.get("current_price") or 0.0)
        pnl_pct = round((last - entry) / entry * 100, 2) if entry else None
        trade = {"signal_id": signal_id, "symbol": symbol, "action": "close",
                 "qty": pos.get("qty"), "price": last, "entry_price": entry,
                 "pnl_pct": pnl_pct, "exit_reason": exit_reason, "reason": reason}
        if self.dry_run:
            self._log(f"{symbol}: [DRY-RUN] would CLOSE {pos.get('qty')} shares — {reason}")
            return trade
        try:
            self.alpaca.close_position(symbol)
        except RuntimeError as e:
            self._log(f"{symbol}: close failed: {e}")
            self.store.log_copy_trade({**trade, "status": f"failed: {e}"[:200]})
            return None
        self._log(f"{symbol}: position CLOSED — {reason}")
        self.store.log_copy_trade({**trade, "status": "submitted"})
        return trade

    def _risk_exit(self, symbol: str, pos: dict, raw_orders: list[dict]) -> dict | None:
        if not (self.trailing_stop_pct or self.stop_loss_pct):
            return None
        entry = float(pos.get("avg_entry_price") or 0.0)
        last = float(pos.get("current_price") or 0.0)
        peak = last
        try:
            bars = self.alpaca.get_bars(symbol, timeframe="1Day", days_back=400)
            since = entry_date_from_orders(raw_orders, symbol)
            highs = [float(b["high"]) for b in bars if b.get("high")
                     and (since is None or b.get("t", "")[:10] >= since)]
            peak = max(highs + [last])
        except RuntimeError as e:
            self._log(f"{symbol}: bar fetch failed ({e}) — checking stops on last price only.")
        why = risk_exit(entry, last, peak, stop_pct=self.stop_loss_pct,
                        trail_pct=self.trailing_stop_pct)
        if not why:
            return None
        label = {"stop": "stop-loss", "trailing": "trailing stop"}[why]
        change = (last - entry) / entry * 100 if entry else 0.0
        return self._close(symbol, pos, f"{label} ({change:+.1f}% vs entry)", why)

    def _handle_sell(self, sig: dict, positions: dict, pending: set):
        """Returns the trade dict when closed, else 'rejected' | 'deferred'."""
        symbol = sig["symbol"]
        if not TICKER.fullmatch(symbol or ""):
            self._finish(sig, "rejected", "not a plain US ticker")
            return "rejected"
        if symbol not in positions:
            self._finish(sig, "rejected", "sell idea, but the sleeve does not hold it")
            return "rejected"
        if symbol in pending:
            self._finish(sig, "rejected", "an order is already pending for this stock")
            return "rejected"
        copied = self.store.last_copied_buy(symbol) or {}
        ours = (copied.get("actor") or "").strip().lower()
        theirs = (sig.get("actor") or "").strip().lower()
        if ours and theirs and ours != theirs:
            self._finish(sig, "rejected",
                         f"sell is from {sig.get('actor')}, but we copied {copied.get('actor')}")
            return "rejected"
        if not self.dry_run and not self.store.claim_signal(sig["id"], self._now()):
            self._log(f"{symbol} (idea #{sig['id']}): could not claim — left for next cycle.")
            return "deferred"
        who = sig.get("actor") or "the copied trader"
        trade = self._close(symbol, positions[symbol], f"{who} sold", "copied_sell", sig["id"])
        if trade is None:
            self._finish(sig, "rejected", "close order failed")
            return "rejected"
        self._finish(sig, "executed", f"closed because {who} sold", qty=trade.get("qty"),
                     est_price=trade.get("price"))
        return trade

    # ------------------------------------------------------------------ #
    #  Entries                                                            #
    # ------------------------------------------------------------------ #

    def _handle_buy(self, sig: dict, positions: dict, pending: set, state: dict):
        """Returns the trade dict when bought, else 'rejected' | 'expired' | 'deferred'."""
        symbol = sig["symbol"]
        today = date.today()
        if not TICKER.fullmatch(symbol or ""):
            self._finish(sig, "rejected", "not a plain US ticker")
            return "rejected"

        conviction = sig.get("conviction") or 0
        if conviction < self.min_conviction:
            self._finish(sig, "rejected",
                         f"conviction {conviction} is below the minimum {self.min_conviction}")
            return "rejected"

        disclosed = self._as_date(sig.get("disclosed_on")) or self._as_date(sig.get("created_at"))
        if disclosed and (today - disclosed).days > self.max_signal_age_days:
            self._finish(sig, "expired",
                         f"made public {(today - disclosed).days} days ago "
                         f"(limit {self.max_signal_age_days})")
            return "expired"
        traded = self._as_date(sig.get("traded_on"))
        if traded and (today - traded).days > self.max_trade_lag_days:
            self._finish(sig, "expired",
                         f"original trade was {(today - traded).days} days ago "
                         f"(limit {self.max_trade_lag_days})")
            return "expired"

        if symbol in positions:
            self._finish(sig, "rejected", "the sleeve already holds this stock")
            return "rejected"
        if symbol in pending:
            self._finish(sig, "rejected", "an order is already pending for this stock")
            return "rejected"

        # Caps that reset or free up later: leave the idea in the inbox.
        if state["halted"]:
            return "deferred"
        if state["new_today"] >= self.max_new_per_day:
            self._log(f"{symbol} (idea #{sig['id']}): waiting — daily limit of "
                      f"{self.max_new_per_day} new positions reached.")
            return "deferred"
        if state["open_count"] >= self.max_positions:
            self._log(f"{symbol} (idea #{sig['id']}): waiting — sleeve is full "
                      f"({self.max_positions} positions).")
            return "deferred"

        try:
            asset = self.alpaca.get_asset(symbol)
        except RuntimeError as e:
            if "404" in str(e):
                self._finish(sig, "rejected", "not a stock Alpaca can trade")
                return "rejected"
            self._log(f"{symbol} (idea #{sig['id']}): asset lookup failed ({e}) — will retry.")
            return "deferred"
        if (not asset.get("tradable") or asset.get("status") != "active"
                or asset.get("class") != "us_equity"):
            self._finish(sig, "rejected", "not an active, tradable US stock")
            return "rejected"

        try:
            bars = self.alpaca.get_bars(symbol, timeframe="1Day", days_back=60)
        except RuntimeError as e:
            self._log(f"{symbol} (idea #{sig['id']}): price fetch failed ({e}) — will retry.")
            return "deferred"
        closes = [float(b["close"]) for b in bars if b.get("close") is not None]
        price = closes[-1] if closes else 0.0
        if price < self.min_price:
            self._finish(sig, "rejected",
                         f"price ${price:.2f} is below the ${self.min_price:.2f} minimum")
            return "rejected"
        if not participation_ok(bars, self.min_avg_volume, min_atr=0.0):
            self._finish(sig, "rejected",
                         f"too thinly traded or too newly listed "
                         f"(needs {self.min_avg_volume:,.0f} shares a day)")
            return "rejected"
        if price > self.cash_per_trade:
            self._finish(sig, "rejected",
                         f"one share (${price:,.2f}) costs more than the "
                         f"${self.cash_per_trade:,.0f} per-trade cap")
            return "rejected"

        spendable = min(state["buying_power"], state["remaining_budget"])
        qty = position_size(spendable, self.cash_per_trade, price)
        if qty <= 0:
            self._log(f"{symbol} (idea #{sig['id']}): waiting — only ${spendable:,.0f} "
                      "of the sleeve budget is free.")
            return "deferred"

        est_cost = round(qty * price, 2)
        who = sig.get("actor") or sig.get("source") or "signal"
        trade = {"signal_id": sig["id"], "symbol": symbol, "action": "buy", "qty": qty,
                 "price": round(price, 2), "est_cost": est_cost,
                 "reason": f"copy {who} (conviction {conviction})"}

        if self.dry_run:
            self._log(f"{symbol} (idea #{sig['id']}): [DRY-RUN] would BUY {qty} @ "
                      f"~${price:.2f} (~${est_cost:,.2f}) — {trade['reason']}")
        else:
            # Claim BEFORE ordering: an idea we cannot mark is an idea we do not
            # trade, so a database hiccup can never cause a repeat buy.
            if not self.store.claim_signal(sig["id"], self._now()):
                self._log(f"{symbol} (idea #{sig['id']}): could not claim — left for next cycle.")
                return "deferred"
            try:
                order = self.alpaca.submit_order(symbol=symbol, side="buy", qty=qty)
            except (RuntimeError, ValueError) as e:
                self.store.log_copy_trade({**trade, "status": f"rejected: {e}"[:200]})
                self._finish(sig, "rejected", f"Alpaca refused the order: {e}")
                return "rejected"
            self.store.log_copy_trade({**trade, "status": "submitted"})
            self._finish(sig, "executed", f"bought {qty} @ ~${price:.2f}",
                         order_id=order.get("id"), qty=qty, est_price=round(price, 2))

        state["remaining_budget"] -= est_cost
        state["buying_power"] -= est_cost
        state["open_count"] += 1
        state["new_today"] += 1
        pending.add(symbol)
        return trade

    @staticmethod
    def _as_date(value) -> date | None:
        if not value:
            return None
        try:
            return date.fromisoformat(str(value)[:10])
        except ValueError:
            return None

    # ------------------------------------------------------------------ #
    #  Snapshot                                                           #
    # ------------------------------------------------------------------ #

    def _snapshot(self, account: dict, positions: dict, raw_orders: list[dict]) -> None:
        if self.dry_run:
            return
        try:
            from tools.journal import build_ledger
            realized = sum(t["pnl"] for t in
                           build_ledger(self.alpaca.simplify_orders(raw_orders)))
        except Exception:  # noqa: BLE001 — a snapshot must never break trading
            realized = 0.0
        unrealized = sum(p.get("unrealized_pl", 0.0) for p in positions.values())
        pnl = round(realized + unrealized, 2)
        self.store.snapshot_copy({
            "snapshot_date": datetime.now().strftime("%Y-%m-%d"),
            "equity": account.get("equity"), "cash": account.get("cash"),
            "deployed": round(sum(p.get("market_value", 0.0) for p in positions.values()), 2),
            "positions": len(positions),
            "holdings": [{k: p.get(k) for k in ("symbol", "qty", "avg_entry_price",
                                                "current_price", "unrealized_pl")}
                         for p in positions.values()],
            "budget": self.budget, "sleeve_pnl": pnl,
            "sleeve_return_pct": round(pnl / self.budget * 100, 2) if self.budget else None,
        })
