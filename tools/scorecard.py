"""
Pass/Fail scorecard for the strategy (see docs/STRATEGY.md).

`evaluate()` is pure and deterministic — it takes precomputed numbers and returns
the verdict (PASS / WATCH / FAIL / IN PROGRESS) with a per-criterion breakdown.
`build_inputs()` gathers those numbers live from Alpaca + the journal ledger so
the CLI and dashboard can show the same result.
"""

from datetime import date
from math import sqrt
from statistics import mean, pstdev

# Thresholds — keep in sync with docs/STRATEGY.md §3.
MIN_DAYS = 20
MIN_TRADES = 10
HARD_FAIL_DD = 25.0          # bot max drawdown % -> auto FAIL
HARD_FAIL_TRADE = -25.0      # any single closed trade % -> auto FAIL
TRAILING_WIDTH = 8.0         # swing trailing-stop width, for the C6 sanity bound


def max_drawdown_pct(equity: list[float]) -> float:
    peak, mdd = float("-inf"), 0.0
    for e in equity:
        peak = max(peak, e)
        if peak > 0:
            mdd = max(mdd, (peak - e) / peak)
    return round(mdd * 100, 2)


def annualized_sharpe(equity: list[float]) -> float | None:
    rets = [equity[i] / equity[i - 1] - 1 for i in range(1, len(equity)) if equity[i - 1] > 0]
    if len(rets) < 2:
        return None
    s = pstdev(rets)
    return round(mean(rets) / s * sqrt(252), 2) if s > 0 else None


def evaluate(*, budget, bot_return_pct, sharpe, bot_max_dd, spy_max_dd,
             profit_factor, num_trades, days_elapsed, worst_trade_pct,
             stop_exits) -> dict:
    """Return {verdict, day, criteria:[...], passed, evaluable, summary}."""
    # Gate 1: not enough data yet.
    if days_elapsed < MIN_DAYS or num_trades < MIN_TRADES:
        return {
            "verdict": "IN PROGRESS",
            "day": days_elapsed,
            "summary": (f"Day {days_elapsed} · {num_trades} closed trades — "
                        f"gathering data (need ≥{MIN_DAYS} days & ≥{MIN_TRADES} trades)."),
            "criteria": [], "passed": 0, "evaluable": 0,
        }

    # Gate 2: hard fails.
    hard = []
    if bot_max_dd is not None and bot_max_dd > HARD_FAIL_DD:
        hard.append(f"max drawdown {bot_max_dd}% > {HARD_FAIL_DD}%")
    if worst_trade_pct is not None and worst_trade_pct < HARD_FAIL_TRADE:
        hard.append(f"worst trade {worst_trade_pct}% < {HARD_FAIL_TRADE}%")

    crit = []

    def add(name, ok, target, actual):
        crit.append({"criterion": name, "pass": ok, "target": target, "actual": actual})

    add("C1 Profitable", bot_return_pct > 0, "> 0%", f"{bot_return_pct}%")
    if sharpe is not None:
        add("C2 Risk-adjusted (Sharpe)", sharpe >= 0.5, "≥ 0.5", str(sharpe))
    if bot_max_dd is not None:
        add("C3 Capital protection", bot_max_dd <= 15, "≤ 15%", f"{bot_max_dd}%")
        if spy_max_dd is not None:
            add("C4 Downside edge vs SPY", bot_max_dd <= spy_max_dd,
                "≤ SPY DD", f"{bot_max_dd}% vs {spy_max_dd}%")
    if num_trades >= 15 and profit_factor is not None:
        add("C5 Edge quality (profit factor)", profit_factor >= 1.2, "≥ 1.2", str(profit_factor))
    add("C6 Risk controls active",
        stop_exits > 0 and (worst_trade_pct is None or worst_trade_pct >= -2 * TRAILING_WIDTH),
        "stops fire, none < -16%",
        f"{stop_exits} stop/trail exits, worst {worst_trade_pct}%")

    evaluable = len(crit)
    passed = sum(1 for c in crit if c["pass"])
    ratio = passed / evaluable if evaluable else 0

    if hard:
        verdict = "FAIL"
        summary = "Hard-fail: " + "; ".join(hard)
    elif ratio >= 0.8:
        verdict = "PASS"
        summary = f"{passed}/{evaluable} criteria met — passing."
    elif ratio >= 0.5:
        verdict = "WATCH"
        summary = f"{passed}/{evaluable} criteria met — watch the misses."
    else:
        verdict = "FAIL"
        summary = f"only {passed}/{evaluable} criteria met."

    return {"verdict": verdict, "day": days_elapsed, "criteria": crit,
            "passed": passed, "evaluable": evaluable, "summary": summary}


def build_inputs(client, *, budget, symbols, start_date, mode_filter=None):
    """
    Gather scorecard inputs live. `client` is an AlpacaClient. Uses the journal
    ledger for realized trades, current positions for unrealized, bot equity
    snapshots (Supabase) for the equity curve, and SPY for the benchmark.
    """
    from tools.journal import build_ledger, ledger_stats
    from tools import supabase_store

    orders = client.simplify_orders(client.get_orders(status="all", limit=500))
    mine = set(symbols)
    trips = [t for t in build_ledger(orders) if t["symbol"] in mine]
    stats = ledger_stats(trips)

    positions = {p["symbol"]: p for p in client.simplify_positions(client.get_positions())
                 if p["symbol"] in mine}
    realized = sum(t["pnl"] for t in trips)
    unrealized = sum(p.get("unrealized_pl", 0.0) for p in positions.values())
    bot_return_pct = round((realized + unrealized) / budget * 100, 2) if budget else 0.0

    # Live bot equity curve from snapshots (bot_pnl); drawdown/Sharpe on it.
    snaps = supabase_store.get_equity_snapshots() if supabase_store.enabled() else []
    curve = [budget + float(s["bot_pnl"]) for s in snaps if s.get("bot_pnl") is not None]
    bot_max_dd = max_drawdown_pct(curve) if len(curve) >= 2 else None
    sharpe = annualized_sharpe(curve) if len(curve) >= 20 else None

    # SPY benchmark drawdown over the campaign window.
    spy_max_dd = None
    try:
        spy = client.fetch_bars("SPY", "1Day", start=start_date)
        closes = [float(b["close"]) for b in spy if b.get("close")]
        if len(closes) >= 2:
            spy_max_dd = max_drawdown_pct(closes)
    except Exception:
        pass

    days_elapsed = (date.today() - date.fromisoformat(start_date)).days
    worst = min((t["pnl_pct"] for t in trips), default=None)
    stop_exits = sum(1 for t in trips if t.get("exit_reason") in ("stop", "trailing"))

    return dict(
        budget=budget, bot_return_pct=bot_return_pct, sharpe=sharpe,
        bot_max_dd=bot_max_dd, spy_max_dd=spy_max_dd,
        profit_factor=stats.get("profit_factor"), num_trades=stats.get("num_trades", 0),
        days_elapsed=max(0, days_elapsed), worst_trade_pct=worst, stop_exits=stop_exits,
    )
