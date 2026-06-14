"""
Battle-testing harness for the AutoTrader strategy — pure analysis over
historical bars, no orders. Wraps tools.backtest.run_backtest to answer the
questions that matter before trusting a config with 90 days of live capital:

  - walk-forward / out-of-sample: does it hold up window after window, or was
    one lucky stretch carrying it?
  - regimes: how does it behave in a bear vs a bull slice?
  - parameter robustness: is the live config a broad plateau or a fragile peak
    (overfit)?

Everything applies ONE fixed config across the slices (the strategy has no
per-window fitting), so consistent out-of-sample results = a robust edge.
"""

from datetime import date, timedelta

from tools.backtest import run_backtest

LIVE_CONFIG = dict(
    budget=50000, cash_per_trade=5000, max_positions=10,
    short_window=20, long_window=50, enter_on_trend=True,
    trailing_stop_pct=8,
)


def slice_bars(bars_by_symbol: dict, start: str, end: str | None = None) -> dict:
    """Keep only bars whose date is within [start, end] (inclusive)."""
    return {
        s: [b for b in bars if b["t"][:10] >= start and (end is None or b["t"][:10] <= end)]
        for s, bars in bars_by_symbol.items()
    }


def _metrics_row(name: str, result: dict) -> dict:
    m = result["metrics"]
    return {
        "window": name,
        "return_pct": m["total_return_pct"],
        "buyhold_pct": m["buy_hold_return_pct"],
        "max_dd_pct": m["max_drawdown_pct"],
        "sharpe": m["sharpe"],
        "trades": m["num_trades"],
        "win_pct": m["win_rate_pct"],
    }


def walk_forward(bars_by_symbol: dict, test_days: int = 90, warmup_days: int = 120,
                 config: dict | None = None) -> list[dict]:
    """
    Consecutive out-of-sample windows of `test_days`, each with a `warmup_days`
    lead-in so the SMAs are primed before the measured window starts.
    """
    cfg = {**LIVE_CONFIG, **(config or {})}
    all_dates = sorted({b["t"][:10] for bars in bars_by_symbol.values() for b in bars})
    if not all_dates:
        return []
    first = date.fromisoformat(all_dates[0]) + timedelta(days=warmup_days)
    last = date.fromisoformat(all_dates[-1])
    rows, cursor, i = [], first, 1
    while cursor < last:
        win_end = min(cursor + timedelta(days=test_days), last)
        lead = (cursor - timedelta(days=warmup_days)).isoformat()
        sliced = slice_bars(bars_by_symbol, lead, win_end.isoformat())
        result = run_backtest(sliced, **cfg)
        row = _metrics_row(f"W{i} {cursor.isoformat()}→{win_end.isoformat()}", result)
        rows.append(row)
        cursor, i = win_end, i + 1
    return rows


def regime_test(bars_by_symbol: dict, regimes: dict, config: dict | None = None) -> list[dict]:
    """Run the config over each named (start, end) regime slice."""
    cfg = {**LIVE_CONFIG, **(config or {})}
    rows = []
    for name, (start, end) in regimes.items():
        sliced = slice_bars(bars_by_symbol, start, end)
        if not any(sliced.values()):
            continue
        rows.append(_metrics_row(f"{name} ({start}→{end})", run_backtest(sliced, **cfg)))
    return rows


def param_sweep(bars_by_symbol: dict, short_windows, long_windows, trails,
                base: dict | None = None) -> list[dict]:
    """
    Grid over (short_window, long_window, trailing_stop_pct). A broad cluster of
    similar results around the live config = robust; a lone spike = overfit.
    """
    cfg0 = {**LIVE_CONFIG, **(base or {})}
    rows = []
    for sw in short_windows:
        for lw in long_windows:
            if sw >= lw:
                continue
            for tr in trails:
                cfg = {**cfg0, "short_window": sw, "long_window": lw, "trailing_stop_pct": tr}
                m = run_backtest(bars_by_symbol, **cfg)["metrics"]
                rows.append({
                    "short": sw, "long": lw, "trail": tr,
                    "return_pct": m["total_return_pct"], "max_dd_pct": m["max_drawdown_pct"],
                    "sharpe": m["sharpe"], "trades": m["num_trades"],
                })
    rows.sort(key=lambda r: (r["sharpe"] or -9), reverse=True)
    return rows


def summarize(rows: list[dict], key: str = "return_pct") -> dict:
    """Aggregate a set of window rows (consistency check)."""
    vals = [r[key] for r in rows if r.get(key) is not None]
    if not vals:
        return {}
    return {
        "windows": len(vals),
        "avg": round(sum(vals) / len(vals), 2),
        "min": round(min(vals), 2),
        "max": round(max(vals), 2),
        "positive_windows": sum(1 for v in vals if v > 0),
    }
