"""
Tests for the copy-trade sleeve. No network: Alpaca and the Supabase inbox are
replaced with in-memory fakes, so every gate can be exercised deterministically.

    python -m unittest discover -s tests -v
"""

import os
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone

os.environ.setdefault("ANTHROPIC_API_KEY", "test-placeholder")
os.environ["OUTPUT_DIR"] = tempfile.mkdtemp(prefix="copytest_")

from agents.copy_trader import CopyTrader, entry_date_from_orders  # noqa: E402

TODAY = date.today()


def days_ago(n: int) -> str:
    return (TODAY - timedelta(days=n)).isoformat()


def make_bars(price: float = 100.0, volume: float = 5_000_000, n: int = 40,
              highs: list[float] | None = None) -> list[dict]:
    bars = []
    for i in range(n):
        d = (TODAY - timedelta(days=n - i)).isoformat()
        high = highs[i] if highs else price * 1.01
        bars.append({"t": d, "open": price, "high": high, "low": price * 0.99,
                     "close": price, "volume": volume})
    return bars


class FakeAlpaca:
    paper = True

    def __init__(self):
        self.is_open = True
        self.clock_error = None
        self.account = {"equity": 100_000.0, "cash": 100_000.0, "buying_power": 100_000.0,
                        "todays_pl": 0.0, "trading_blocked": False, "account_blocked": False}
        self.positions: list[dict] = []
        self.orders: list[dict] = []        # all orders (filled history)
        self.open_orders: list[dict] = []
        self.assets: dict[str, dict] = {}
        self.bars: dict[str, list[dict]] = {}
        self.submitted: list[dict] = []
        self.closed: list[str] = []
        self.refuse_orders = False

    def add_stock(self, symbol, price=100.0, volume=5_000_000, **asset):
        self.assets[symbol] = {"tradable": True, "status": "active",
                               "class": "us_equity", **asset}
        self.bars[symbol] = make_bars(price, volume)

    def hold(self, symbol, qty=10, entry=100.0, current=100.0, entered_days_ago=5):
        self.positions.append({
            "symbol": symbol, "qty": str(qty), "side": "long",
            "avg_entry_price": entry, "current_price": current,
            "market_value": qty * current, "unrealized_pl": qty * (current - entry),
            "unrealized_plpc": (current - entry) / entry})
        self.orders.append({"symbol": symbol, "side": "buy", "filled_qty": str(qty),
                            "filled_avg_price": str(entry),
                            "submitted_at": f"{days_ago(entered_days_ago)}T14:00:00Z"})

    # --- API surface used by CopyTrader -------------------------------- #
    def get_clock(self):
        if self.clock_error:
            raise RuntimeError(self.clock_error)
        return {"is_open": self.is_open, "next_open": "tomorrow"}

    def account_summary(self):
        return dict(self.account)

    def get_positions(self):
        return list(self.positions)

    def simplify_positions(self, positions):
        return [{k: (float(p[k]) if k not in ("symbol", "qty", "side") else p[k])
                 for k in ("symbol", "qty", "side", "avg_entry_price", "current_price",
                           "market_value", "unrealized_pl")} for p in positions]

    def get_orders(self, status="all", limit=50):
        return list(self.open_orders) if status == "open" else list(self.orders)

    def simplify_orders(self, orders):
        return [{k: o.get(k) for k in ("symbol", "side", "filled_qty",
                                       "filled_avg_price", "submitted_at")} for o in orders]

    def get_asset(self, symbol):
        if symbol not in self.assets:
            raise RuntimeError("Alpaca API error 404: {'message': 'asset not found'}")
        return self.assets[symbol]

    def get_bars(self, symbol, timeframe="1Day", days_back=30):
        return self.bars.get(symbol, [])

    def submit_order(self, symbol, side, qty=None, **kw):
        if self.refuse_orders:
            raise RuntimeError("Alpaca API error 403: insufficient buying power")
        order = {"id": f"ord-{len(self.submitted) + 1}", "symbol": symbol,
                 "side": side, "qty": qty, "status": "accepted"}
        self.submitted.append(order)
        self.open_orders.append(order)
        return order

    def close_position(self, symbol):
        self.closed.append(symbol)
        self.positions = [p for p in self.positions if p["symbol"] != symbol]
        return {}


class FakeStore:
    def __init__(self):
        self.signals: list[dict] = []
        self.trades: list[dict] = []
        self.snapshots: list[dict] = []
        self.inbox_down = False
        self.claims_fail = False
        self.count_fails = False
        self._next = 1

    def add(self, symbol, side="buy", conviction=4, actor="Rep Example",
            disclosed_days_ago=1, traded_days_ago=20, status="new", **extra):
        sig = {"id": self._next, "created_at": f"{days_ago(0)}T12:00:{self._next:02d}Z",
               "source": "quiver_congress", "actor": actor, "symbol": symbol, "side": side,
               "conviction": conviction, "disclosed_on": days_ago(disclosed_days_ago),
               "traded_on": days_ago(traded_days_ago), "status": status,
               "status_reason": None, "processed_at": None, **extra}
        self._next += 1
        self.signals.append(sig)
        return sig

    def by_symbol(self, symbol):
        return [s for s in self.signals if s["symbol"] == symbol]

    # --- interface used by CopyTrader ---------------------------------- #
    def enabled(self):
        return True

    def get_new_signals(self, limit=50):
        if self.inbox_down:
            return None
        return [dict(s) for s in self.signals if s["status"] == "new"][:limit]

    def get_stuck_signals(self, older_than_iso):
        return [dict(s) for s in self.signals if s["status"] == "executing"
                and (s["processed_at"] or "") < older_than_iso]

    def _row(self, signal_id):
        return next(s for s in self.signals if s["id"] == signal_id)

    def claim_signal(self, signal_id, now_iso):
        row = self._row(signal_id)
        if self.claims_fail or row["status"] != "new":
            return False
        row.update(status="executing", processed_at=now_iso)
        return True

    def finish_signal(self, signal_id, status, reason, now_iso, **extra):
        self._row(signal_id).update(status=status, status_reason=reason,
                                    processed_at=now_iso, **extra)
        return True

    def count_copy_buys_since(self, since_iso):
        if self.count_fails:
            return None
        return sum(1 for s in self.signals if s["side"] == "buy"
                   and s["status"] in ("executing", "executed")
                   and (s["processed_at"] or "") >= since_iso[:19])

    def last_copied_buy(self, symbol):
        rows = [s for s in self.signals if s["symbol"] == symbol
                and s["side"] == "buy" and s["status"] == "executed"]
        return rows[-1] if rows else None

    def log_copy_trade(self, row):
        self.trades.append(row)
        return True

    def snapshot_copy(self, row):
        self.snapshots.append(row)
        return True


class CopyTraderTest(unittest.TestCase):
    def setUp(self):
        self.alpaca = FakeAlpaca()
        self.store = FakeStore()

    def trader(self, **kw):
        return CopyTrader(alpaca=self.alpaca, store=self.store, **kw)

    # ---- the happy path ------------------------------------------------ #

    def test_fresh_idea_becomes_a_capped_paper_buy(self):
        self.alpaca.add_stock("ABC", price=40.0)
        sig = self.store.add("ABC")
        out = self.trader().run_once()

        self.assertEqual(len(self.alpaca.submitted), 1)
        order = self.alpaca.submitted[0]
        self.assertEqual((order["symbol"], order["side"], order["qty"]), ("ABC", "buy", 25))
        row = self.store.by_symbol("ABC")[0]
        self.assertEqual(row["status"], "executed")
        self.assertEqual(row["order_id"], "ord-1")
        self.assertEqual(row["qty"], 25)
        self.assertEqual(self.store.trades[0]["signal_id"], sig["id"])
        self.assertEqual(len(out["bought"]), 1)
        self.assertEqual(len(self.store.snapshots), 1)

    def test_market_closed_leaves_ideas_waiting(self):
        self.alpaca.add_stock("ABC")
        self.store.add("ABC")
        self.alpaca.is_open = False
        out = self.trader().run_once()
        self.assertTrue(out["skipped"])
        self.assertEqual(self.alpaca.submitted, [])
        self.assertEqual(self.store.signals[0]["status"], "new")

    # ---- ideas that must be turned down -------------------------------- #

    def assert_no_buy(self, symbol, status, reason_part):
        self.assertEqual(self.alpaca.submitted, [])
        row = self.store.by_symbol(symbol)[0]
        self.assertEqual(row["status"], status)
        self.assertIn(reason_part, row["status_reason"])

    def test_low_conviction_is_rejected(self):
        self.alpaca.add_stock("ABC")
        self.store.add("ABC", conviction=2)
        self.trader().run_once()
        self.assert_no_buy("ABC", "rejected", "conviction")

    def test_stale_disclosure_expires(self):
        self.alpaca.add_stock("ABC")
        self.store.add("ABC", disclosed_days_ago=11)
        self.trader().run_once()
        self.assert_no_buy("ABC", "expired", "made public")

    def test_old_original_trade_expires(self):
        self.alpaca.add_stock("ABC")
        self.store.add("ABC", disclosed_days_ago=1, traded_days_ago=61)
        self.trader().run_once()
        self.assert_no_buy("ABC", "expired", "original trade")

    def test_already_held_is_rejected(self):
        self.alpaca.add_stock("ABC")
        self.alpaca.hold("ABC")
        self.store.add("ABC")
        self.trader().run_once()
        self.assert_no_buy("ABC", "rejected", "already holds")

    def test_unknown_ticker_is_rejected(self):
        self.store.add("ZZZZ")
        self.trader().run_once()
        self.assert_no_buy("ZZZZ", "rejected", "Alpaca can trade")

    def test_inactive_or_non_equity_asset_is_rejected(self):
        self.alpaca.add_stock("OLD", status="inactive")
        self.alpaca.add_stock("COIN", **{"class": "crypto"})
        self.store.add("OLD")
        self.store.add("COIN")
        self.trader().run_once()
        self.assertEqual(self.alpaca.submitted, [])
        self.assertEqual({s["status"] for s in self.store.signals}, {"rejected"})

    def test_penny_stock_is_rejected(self):
        self.alpaca.add_stock("PNY", price=2.0)
        self.store.add("PNY")
        self.trader().run_once()
        self.assert_no_buy("PNY", "rejected", "below the")

    def test_thinly_traded_stock_is_rejected(self):
        self.alpaca.add_stock("THN", volume=50_000)
        self.store.add("THN")
        self.trader().run_once()
        self.assert_no_buy("THN", "rejected", "thinly traded")

    def test_share_dearer_than_per_trade_cap_is_rejected(self):
        self.alpaca.add_stock("BIG", price=1500.0)
        self.store.add("BIG")
        self.trader().run_once()
        self.assert_no_buy("BIG", "rejected", "per-trade cap")

    def test_malformed_ticker_never_reaches_alpaca(self):
        self.store.add("ABC&status=eq.new")
        self.store.add("abc; drop", side="sell")
        self.alpaca.get_asset = lambda s: self.fail("looked up a malformed ticker")
        self.trader().run_once()
        self.assertEqual(self.alpaca.submitted, [])
        self.assertEqual({s["status"] for s in self.store.signals}, {"rejected"})

    def test_alpaca_refusal_marks_idea_rejected(self):
        self.alpaca.add_stock("ABC")
        self.store.add("ABC")
        self.alpaca.refuse_orders = True
        out = self.trader().run_once()
        row = self.store.by_symbol("ABC")[0]
        self.assertEqual(row["status"], "rejected")
        self.assertIn("refused", row["status_reason"])
        self.assertEqual(out["bought"], [])

    # ---- caps ----------------------------------------------------------- #

    def test_daily_limit_buys_best_conviction_first_and_defers_the_rest(self):
        for sym, conv in (("AAA", 3), ("BBB", 5), ("CCC", 4), ("DDD", 3), ("EEE", 5)):
            self.alpaca.add_stock(sym)
            self.store.add(sym, conviction=conv)
        out = self.trader(max_new_per_day=3).run_once()

        bought = [o["symbol"] for o in self.alpaca.submitted]
        self.assertEqual(bought, ["BBB", "EEE", "CCC"])
        self.assertEqual(out["deferred"], 2)
        waiting = sorted(s["symbol"] for s in self.store.signals if s["status"] == "new")
        self.assertEqual(waiting, ["AAA", "DDD"])

    def test_daily_limit_counts_buys_from_earlier_cycles(self):
        for sym in ("AAA", "BBB", "CCC", "DDD"):
            self.alpaca.add_stock(sym)
            self.store.add(sym)
        t = self.trader(max_new_per_day=3)
        t.run_once()
        self.alpaca.open_orders.clear()
        t.run_once()
        self.assertEqual(len(self.alpaca.submitted), 3)

    def test_budget_is_never_exceeded(self):
        for sym in ("AAA", "BBB", "CCC", "DDD"):
            self.alpaca.add_stock(sym, price=100.0)
            self.store.add(sym)
        self.trader(budget=2500, cash_per_trade=1000, max_new_per_day=10).run_once()
        spent = sum(o["qty"] * 100.0 for o in self.alpaca.submitted)
        self.assertEqual([o["qty"] for o in self.alpaca.submitted], [10, 10, 5])
        self.assertLessEqual(spent, 2500)
        self.assertEqual(self.store.by_symbol("DDD")[0]["status"], "new")

    def test_existing_holdings_count_against_budget(self):
        self.alpaca.hold("HELD", qty=90, entry=100.0, current=100.0)  # $9,000 deployed
        self.alpaca.bars["HELD"] = make_bars(100.0)
        self.alpaca.add_stock("NEW", price=100.0)
        self.alpaca.add_stock("NEW2", price=100.0)
        self.store.add("NEW")
        self.store.add("NEW2")
        self.trader(budget=10_000).run_once()
        self.assertEqual([(o["symbol"], o["qty"]) for o in self.alpaca.submitted],
                         [("NEW", 10)])

    def test_full_sleeve_defers_new_ideas(self):
        self.alpaca.hold("H1")
        self.alpaca.hold("H2")
        self.alpaca.add_stock("ABC")
        self.store.add("ABC")
        out = self.trader(max_positions=2, trailing_stop_pct=0).run_once()
        self.assertEqual(self.alpaca.submitted, [])
        self.assertEqual(out["deferred"], 1)
        self.assertEqual(self.store.signals[0]["status"], "new")

    def test_daily_loss_limit_pauses_buys_but_not_exits(self):
        self.alpaca.account["todays_pl"] = -350.0
        self.alpaca.hold("DROP", entry=100.0, current=85.0)
        self.alpaca.bars["DROP"] = make_bars(85.0, highs=[101.0] * 40)
        self.alpaca.add_stock("ABC")
        self.store.add("ABC")
        out = self.trader(daily_loss_limit=300).run_once()
        self.assertEqual(self.alpaca.submitted, [])
        self.assertEqual(self.store.signals[0]["status"], "new")
        self.assertEqual(self.alpaca.closed, ["DROP"])
        self.assertEqual(len(out["closed"]), 1)

    def test_two_ideas_for_one_stock_buy_once(self):
        self.alpaca.add_stock("ABC")
        self.store.add("ABC", actor="Rep One")
        self.store.add("ABC", actor="Rep Two")
        self.trader().run_once()
        self.assertEqual(len(self.alpaca.submitted), 1)
        self.assertEqual(sorted(s["status"] for s in self.store.signals),
                         ["executed", "rejected"])

    # ---- failure handling ---------------------------------------------- #

    def test_unclaimable_idea_is_never_traded(self):
        self.alpaca.add_stock("ABC")
        self.store.add("ABC")
        self.store.claims_fail = True
        out = self.trader().run_once()
        self.assertEqual(self.alpaca.submitted, [])
        self.assertEqual(out["deferred"], 1)

    def test_unreachable_inbox_buys_nothing_but_still_runs_exits(self):
        self.store.inbox_down = True
        self.alpaca.hold("DROP", entry=100.0, current=85.0)
        self.alpaca.bars["DROP"] = make_bars(85.0, highs=[101.0] * 40)
        out = self.trader().run_once()
        self.assertTrue(out.get("inbox_error"))
        self.assertEqual(self.alpaca.submitted, [])
        self.assertEqual(self.alpaca.closed, ["DROP"])

    def test_uncountable_daily_buys_pause_new_buys(self):
        self.alpaca.add_stock("ABC")
        self.store.add("ABC")
        self.store.count_fails = True
        self.trader().run_once()
        self.assertEqual(self.alpaca.submitted, [])
        self.assertEqual(self.store.signals[0]["status"], "new")

    def test_rejected_keys_fail_loudly(self):
        self.alpaca.clock_error = "Alpaca API error 401: unauthorized"
        with self.assertRaises(EnvironmentError):
            self.trader().run_once()

    def test_interrupted_buy_is_recovered_as_executed_when_position_exists(self):
        old = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat(timespec="seconds")
        self.alpaca.hold("ABC")
        self.alpaca.bars["ABC"] = make_bars(100.0)
        self.store.add("ABC", status="executing", processed_at=old)
        self.store.add("GONE", status="executing", processed_at=old)
        self.trader().run_once()
        self.assertEqual(self.store.by_symbol("ABC")[0]["status"], "executed")
        self.assertEqual(self.store.by_symbol("GONE")[0]["status"], "rejected")
        self.assertEqual(self.alpaca.submitted, [])

    def test_dry_run_changes_nothing(self):
        self.alpaca.add_stock("ABC")
        self.alpaca.hold("DROP", entry=100.0, current=85.0)
        self.alpaca.bars["DROP"] = make_bars(85.0, highs=[101.0] * 40)
        self.store.add("ABC")
        self.store.add("DROP", side="sell")
        out = self.trader(dry_run=True).run_once()
        self.assertEqual(self.alpaca.submitted, [])
        self.assertEqual(self.alpaca.closed, [])
        self.assertEqual({s["status"] for s in self.store.signals}, {"new"})
        self.assertEqual((self.store.trades, self.store.snapshots), ([], []))
        self.assertEqual(len(out["bought"]), 1)

    # ---- exits ---------------------------------------------------------- #

    def test_trailing_stop_closes_a_fallen_position(self):
        self.alpaca.hold("DROP", entry=100.0, current=91.0, entered_days_ago=10)
        self.alpaca.bars["DROP"] = make_bars(91.0, highs=[100.0] * 40)
        self.trader(trailing_stop_pct=8).run_once()
        self.assertEqual(self.alpaca.closed, ["DROP"])
        self.assertEqual(self.store.trades[0]["exit_reason"], "trailing")

    def test_trailing_stop_ignores_highs_from_before_entry(self):
        highs = [200.0] * 30 + [100.0] * 10   # the 200s predate our entry
        self.alpaca.hold("HOLD", entry=100.0, current=97.0, entered_days_ago=5)
        self.alpaca.bars["HOLD"] = make_bars(97.0, highs=highs)
        self.trader(trailing_stop_pct=8).run_once()
        self.assertEqual(self.alpaca.closed, [])

    def test_healthy_position_is_kept(self):
        self.alpaca.hold("GOOD", entry=100.0, current=104.0)
        self.alpaca.bars["GOOD"] = make_bars(104.0, highs=[105.0] * 40)
        self.trader().run_once()
        self.assertEqual(self.alpaca.closed, [])

    def test_sell_by_the_copied_trader_closes_the_position(self):
        self.alpaca.hold("ABC")
        self.alpaca.bars["ABC"] = make_bars(100.0)
        self.store.add("ABC", actor="Rep Example", status="executed")
        sell = self.store.add("ABC", side="sell", actor="rep example")
        self.trader().run_once()
        self.assertEqual(self.alpaca.closed, ["ABC"])
        self.assertEqual(self.store._row(sell["id"])["status"], "executed")
        self.assertEqual(self.store.trades[-1]["exit_reason"], "copied_sell")

    def test_sell_by_someone_else_is_ignored(self):
        self.alpaca.hold("ABC")
        self.alpaca.bars["ABC"] = make_bars(100.0)
        self.store.add("ABC", actor="Rep Example", status="executed")
        sell = self.store.add("ABC", side="sell", actor="Senator Other")
        self.trader().run_once()
        self.assertEqual(self.alpaca.closed, [])
        self.assertEqual(self.store._row(sell["id"])["status"], "rejected")

    def test_sell_for_a_stock_not_held_is_rejected(self):
        sell = self.store.add("ABC", side="sell")
        self.trader().run_once()
        self.assertEqual(self.alpaca.closed, [])
        self.assertEqual(self.store._row(sell["id"])["status"], "rejected")


class GuardTest(unittest.TestCase):
    def test_needs_the_inbox(self):
        store = FakeStore()
        store.enabled = lambda: False
        with self.assertRaises(EnvironmentError):
            CopyTrader(alpaca=FakeAlpaca(), store=store)

    def test_refuses_a_live_account(self):
        alpaca = FakeAlpaca()
        alpaca.paper = False
        with self.assertRaises(EnvironmentError):
            CopyTrader(alpaca=alpaca, store=FakeStore())

    def test_needs_its_own_keys(self):
        for var in ("ALPACA_COPY_API_KEY_ID", "ALPACA_COPY_API_SECRET_KEY"):
            os.environ.pop(var, None)
        with self.assertRaises(EnvironmentError):
            CopyTrader(store=FakeStore())

    def test_refuses_the_main_accounts_keys(self):
        from config.settings import settings
        original = settings.alpaca_api_key_id
        settings.alpaca_api_key_id = "PKMAINACCOUNT"
        os.environ["ALPACA_COPY_API_KEY_ID"] = "PKMAINACCOUNT"
        os.environ["ALPACA_COPY_API_SECRET_KEY"] = "secret"
        try:
            with self.assertRaises(EnvironmentError) as ctx:
                CopyTrader(store=FakeStore())
            self.assertIn("separate paper account", str(ctx.exception))
        finally:
            settings.alpaca_api_key_id = original
            for var in ("ALPACA_COPY_API_KEY_ID", "ALPACA_COPY_API_SECRET_KEY"):
                os.environ.pop(var, None)

    def test_dedicated_client_is_forced_to_the_paper_endpoint(self):
        os.environ["ALPACA_COPY_API_KEY_ID"] = "PKCOPYSLEEVE"
        os.environ["ALPACA_COPY_API_SECRET_KEY"] = "secret"
        os.environ["ALPACA_PAPER"] = "false"
        try:
            t = CopyTrader(store=FakeStore())
            self.assertTrue(t.alpaca.paper)
            self.assertIn("paper-api", t.alpaca.base_url)
            self.assertEqual(t.alpaca.headers["APCA-API-KEY-ID"], "PKCOPYSLEEVE")
        finally:
            for var in ("ALPACA_COPY_API_KEY_ID", "ALPACA_COPY_API_SECRET_KEY", "ALPACA_PAPER"):
                os.environ.pop(var, None)


class EntryDateTest(unittest.TestCase):
    def test_finds_the_start_of_the_current_position(self):
        orders = [
            {"symbol": "ABC", "side": "buy", "filled_qty": "10", "submitted_at": "2026-01-05T14:00:00Z"},
            {"symbol": "ABC", "side": "sell", "filled_qty": "10", "submitted_at": "2026-02-01T14:00:00Z"},
            {"symbol": "ABC", "side": "buy", "filled_qty": "5", "submitted_at": "2026-03-10T14:00:00Z"},
            {"symbol": "XYZ", "side": "buy", "filled_qty": "1", "submitted_at": "2026-04-01T14:00:00Z"},
        ]
        self.assertEqual(entry_date_from_orders(orders, "ABC"), "2026-03-10")
        self.assertIsNone(entry_date_from_orders(orders, "NOPE"))


if __name__ == "__main__":
    unittest.main()
