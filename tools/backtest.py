"""
Backtester for the AutoTrader's SMA-crossover strategy — pure logic, no I/O.

Replays the exact signal (tools.strategies.sma_crossover_signal) and sizing
rules (position_size + budget / max_positions caps) the live bot uses, bar by
bar over historical daily data, so results reflect what the bot would actually
have done. Fills happen at the signal bar's close; no slippage or commissions
are modeled (Alpaca is commission-free).
"""

from math import sqrt

from tools.strategies import (
    sma, sma_crossover_signal, position_size, volume_confirmed,
    opening_range, orb_signal,
)


def run_backtest(
    bars_by_symbol: dict[str, list[dict]],
    budget: float = 5000.0,
    cash_per_trade: float = 1000.0,
    max_positions: int = 5,
    short_window: int = 20,
    long_window: int = 50,
    enter_on_trend: bool = False,
    confirm_volume: bool = False,
    volume_mult: float = 1.5,
    regime_bars: list[dict] | None = None,
    stop_loss_pct: float = 0.0,
    take_profit_pct: float = 0.0,
    trailing_stop_pct: float = 0.0,
    flatten_eod: bool = False,
) -> dict:
    """
    Simulate the strategy over historical bars.

    bars_by_symbol maps symbol -> chronological daily bars as returned by
    AlpacaClient.get_bars (dicts with "t" and "close").

    Returns a dict with:
      equity_curve   — [{"date", "equity"}] one point per trading day
      trades         — closed round-trips with entry/exit/pnl
      open_positions — positions still held at the end (marked to last close)
      metrics        — summary stats incl. a buy-and-hold benchmark
    """
    by_date = {
        s: {b["t"]: b for b in bars if b.get("close") is not None}
        for s, bars in bars_by_symbol.items()
    }
    calendar = sorted({d for day_map in by_date.values() for d in day_map})
    history: dict[str, list[dict]] = {s: [] for s in by_date}
    # For the intraday engine: the last bar timestamp of each calendar date, so
    # we can flatten everything before the close (no overnight holds).
    last_ts_of_date: dict[str, str] = {}
    for d in calendar:
        last_ts_of_date[d[:10]] = d

    cash = budget
    positions: dict[str, dict] = {}
    trades: list[dict] = []
    equity_curve: list[dict] = []
    last_close: dict[str, float] = {}

    # Market regime by date (mirrors AutoTrader's market filter): new buys
    # are only allowed while the benchmark's short SMA is above its long SMA.
    market_ok_by_date: dict[str, bool] = {}
    if regime_bars:
        closes: list[float] = []
        for b in regime_bars:
            if b.get("close") is None:
                continue
            closes.append(float(b["close"]))
            s, l = sma(closes, short_window), sma(closes, long_window)
            market_ok_by_date[b["t"]] = s is not None and l is not None and s > l
    market_ok = True

    for day in calendar:
        if regime_bars:
            market_ok = market_ok_by_date.get(day, market_ok)
        for symbol, day_map in by_date.items():
            bar = day_map.get(day)
            if bar is None:
                continue
            history[symbol].append(bar)
            price = float(bar["close"])
            last_close[symbol] = price
            holding = symbol in positions

            # Risk-managed exits modeled intrabar against the bar's high/low,
            # taking priority over the signal. Stop is checked first (worst
            # case when a bar spans both stop and target).
            if holding and (stop_loss_pct or take_profit_pct or trailing_stop_pct):
                pos = positions[symbol]
                hi, lo = float(bar.get("high", price)), float(bar.get("low", price))
                pos["peak"] = max(pos.get("peak", pos["entry"]), hi)
                entry = pos["entry"]
                exit_px = exit_reason = None
                if stop_loss_pct and lo <= entry * (1 - stop_loss_pct / 100):
                    exit_px, exit_reason = min(entry * (1 - stop_loss_pct / 100), hi), "stop"
                elif take_profit_pct and hi >= entry * (1 + take_profit_pct / 100):
                    exit_px, exit_reason = max(entry * (1 + take_profit_pct / 100), lo), "take_profit"
                elif trailing_stop_pct and lo <= pos["peak"] * (1 - trailing_stop_pct / 100):
                    exit_px, exit_reason = pos["peak"] * (1 - trailing_stop_pct / 100), "trailing"
                if exit_reason:
                    positions.pop(symbol)
                    cash += pos["qty"] * exit_px
                    pnl = pos["qty"] * (exit_px - entry)
                    trades.append({
                        "symbol": symbol, "qty": pos["qty"],
                        "entry_date": pos["entry_date"], "entry": round(entry, 2),
                        "exit_date": day, "exit": round(exit_px, 2),
                        "pnl": round(pnl, 2),
                        "pnl_pct": round(pnl / (pos["qty"] * entry) * 100, 2),
                        "exit_reason": exit_reason,
                    })
                    continue

            signal = sma_crossover_signal(
                history[symbol], short_window=short_window, long_window=long_window
            )
            from_crossover = signal == "buy"

            # Regime mode (mirrors AutoTrader): trade the current trend, not
            # just the crossover bar.
            if enter_on_trend and signal == "hold":
                closes = [float(b["close"]) for b in history[symbol]]
                s, l = sma(closes, short_window), sma(closes, long_window)
                if s is not None and l is not None:
                    if not holding and s > l:
                        signal = "buy"
                    elif holding and s < l:
                        signal = "sell"

            # Entry gates (exits are never gated).
            if signal == "buy":
                if not market_ok:
                    signal = "hold"
                elif (confirm_volume and from_crossover
                      and not volume_confirmed(history[symbol], mult=volume_mult)):
                    signal = "hold"

            if signal == "buy" and not holding and len(positions) < max_positions:
                qty = position_size(cash, cash_per_trade, price)
                if qty > 0:
                    cash -= qty * price
                    positions[symbol] = {"qty": qty, "entry": price,
                                         "entry_date": day, "peak": price}
            elif signal == "sell" and holding:
                pos = positions.pop(symbol)
                proceeds = pos["qty"] * price
                cash += proceeds
                pnl = proceeds - pos["qty"] * pos["entry"]
                trades.append({
                    "symbol": symbol,
                    "qty": pos["qty"],
                    "entry_date": pos["entry_date"],
                    "entry": round(pos["entry"], 2),
                    "exit_date": day,
                    "exit": round(price, 2),
                    "pnl": round(pnl, 2),
                    "pnl_pct": round(pnl / (pos["qty"] * pos["entry"]) * 100, 2),
                    "exit_reason": "signal",
                })

        # End-of-day flatten (intraday engine): close everything on the last
        # bar of the trading day so nothing is held overnight.
        if flatten_eod and day == last_ts_of_date.get(day[:10]):
            for s, p in list(positions.items()):
                px = last_close.get(s, p["entry"])
                positions.pop(s)
                cash += p["qty"] * px
                pnl = p["qty"] * (px - p["entry"])
                trades.append({
                    "symbol": s, "qty": p["qty"],
                    "entry_date": p["entry_date"], "entry": round(p["entry"], 2),
                    "exit_date": day, "exit": round(px, 2),
                    "pnl": round(pnl, 2),
                    "pnl_pct": round(pnl / (p["qty"] * p["entry"]) * 100, 2),
                    "exit_reason": "eod_flatten",
                })

        equity = cash + sum(
            p["qty"] * last_close.get(s, p["entry"]) for s, p in positions.items()
        )
        equity_curve.append({"date": day, "equity": round(equity, 2)})

    open_positions = [
        {
            "symbol": s,
            "qty": p["qty"],
            "entry_date": p["entry_date"],
            "entry": round(p["entry"], 2),
            "last": round(last_close.get(s, p["entry"]), 2),
            "unrealized_pnl": round(p["qty"] * (last_close.get(s, p["entry"]) - p["entry"]), 2),
        }
        for s, p in positions.items()
    ]

    return {
        "equity_curve": equity_curve,
        "trades": trades,
        "open_positions": open_positions,
        "metrics": _metrics(equity_curve, trades, open_positions, by_date, budget),
    }


def _metrics(equity_curve, trades, open_positions, by_date, budget) -> dict:
    final_equity = equity_curve[-1]["equity"] if equity_curve else budget
    total_return_pct = (final_equity / budget - 1) * 100 if budget > 0 else 0.0

    # Max drawdown over the equity curve.
    peak, max_dd = float("-inf"), 0.0
    for pt in equity_curve:
        peak = max(peak, pt["equity"])
        if peak > 0:
            max_dd = max(max_dd, (peak - pt["equity"]) / peak)

    # Annualized Sharpe from daily equity returns (risk-free rate ~ 0).
    rets = [
        b["equity"] / a["equity"] - 1
        for a, b in zip(equity_curve, equity_curve[1:])
        if a["equity"] > 0
    ]
    sharpe = None
    if len(rets) > 1:
        mean = sum(rets) / len(rets)
        var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
        std = sqrt(var)
        if std > 0:
            sharpe = round(mean / std * sqrt(252), 2)

    wins = [t for t in trades if t["pnl"] > 0]
    realized_pnl = round(sum(t["pnl"] for t in trades), 2)
    unrealized_pnl = round(sum(p["unrealized_pnl"] for p in open_positions), 2)

    # Benchmark: split the budget equally and buy-and-hold every symbol from
    # its first bar to its last.
    bh_value = 0.0
    n = len(by_date) or 1
    for day_map in by_date.values():
        days = sorted(day_map)
        if not days:
            continue
        first = float(day_map[days[0]]["close"])
        last = float(day_map[days[-1]]["close"])
        bh_value += (budget / n) * (last / first if first > 0 else 1.0)
    buy_hold_return_pct = (bh_value / budget - 1) * 100 if budget > 0 else 0.0

    return {
        "starting_budget": budget,
        "final_equity": round(final_equity, 2),
        "total_return_pct": round(total_return_pct, 2),
        "buy_hold_return_pct": round(buy_hold_return_pct, 2),
        "max_drawdown_pct": round(max_dd * 100, 2),
        "sharpe": sharpe,
        "num_trades": len(trades),
        "win_rate_pct": round(len(wins) / len(trades) * 100, 1) if trades else None,
        "realized_pnl": realized_pnl,
        "unrealized_pnl": unrealized_pnl,
        "open_positions": len(open_positions),
        "trading_days": len(equity_curve),
    }


def run_orb_backtest(
    bars_by_symbol: dict[str, list[dict]],
    spy_bars: list[dict] | None = None,
    budget: float = 10000.0,
    cash_per_trade: float = 2000.0,
    max_positions: int = 5,
    or_bars: int = 6,
    vol_mult: float = 1.5,
    trail_pct: float = 3.0,
    market_filter: bool = True,
    slip_bps: float = 5.0,
) -> dict:
    """
    Opening-range-breakout intraday backtest, sharing the exact entry logic the
    live bot uses (tools.strategies.orb_signal / opening_range). Models: a
    breakout entry above the opening-range high on volume; an initial stop at the
    opening-range low; a trailing stop; an optional market-green filter (only
    enter when SPY is above its session open); one entry per symbol per day; a
    proper budget / max-position concurrency cap; and an end-of-day flatten.
    Bars must be regular-trading-hours, in order. slip_bps applies to fills.
    """
    spy_open: dict[str, float] = {}
    spy_px: dict[str, float] = {}
    if spy_bars:
        byd: dict[str, list[dict]] = {}
        for b in spy_bars:
            byd.setdefault(b["t"][:10], []).append(b)
        for d, day in byd.items():
            spy_open[d] = float(day[0]["open"])
            for b in day:
                spy_px[b["t"]] = float(b["close"])

    by_ts = {s: {b["t"]: b for b in bars} for s, bars in bars_by_symbol.items()}
    calendar = sorted({t for m in by_ts.values() for t in m})
    last_ts_of_date: dict[str, str] = {}
    for t in calendar:
        last_ts_of_date[t[:10]] = t

    cash = budget
    positions: dict[str, dict] = {}
    trades: list[dict] = []
    equity_curve: list[dict] = []
    last_close: dict[str, float] = {}
    today_bars: dict[str, list[dict]] = {s: [] for s in by_ts}
    traded_today: set = set()
    cur_date = None

    def _record(s, p, px, reason):
        pnl = p["qty"] * (px - p["entry"])
        trades.append({
            "symbol": s, "qty": p["qty"], "entry_date": p["entry_date"],
            "entry": round(p["entry"], 2), "exit_date": ts, "exit": round(px, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round((px - p["entry"]) / p["entry"] * 100, 2),
            "exit_reason": reason,
        })

    for ts in calendar:
        d = ts[:10]
        if d != cur_date:
            today_bars = {s: [] for s in by_ts}
            traded_today = set()
            cur_date = d
        for s, m in by_ts.items():
            bar = m.get(ts)
            if bar is None:
                continue
            today_bars[s].append(bar)
            price = float(bar["close"])
            last_close[s] = price
            if s in positions:
                pos = positions[s]
                hi, lo = float(bar["high"]), float(bar["low"])
                pos["peak"] = max(pos["peak"], hi)
                rng = opening_range(today_bars[s], or_bars)
                xp = reason = None
                if rng and lo <= rng["low"]:
                    xp, reason = rng["low"] * (1 - slip_bps / 1e4), "orb_stop"
                elif lo <= pos["peak"] * (1 - trail_pct / 100):
                    xp, reason = pos["peak"] * (1 - trail_pct / 100), "trailing"
                if reason:
                    positions.pop(s)
                    cash += pos["qty"] * xp
                    _record(s, pos, xp, reason)
                    continue
            else:
                if s in traded_today or len(positions) >= max_positions:
                    continue
                if orb_signal(today_bars[s], or_bars, vol_mult) == "buy":
                    rng = opening_range(today_bars[s], or_bars)
                    mkt_ok = (not market_filter) or (spy_px.get(ts, 0) > spy_open.get(d, 1e18))
                    if rng and mkt_ok:
                        entry = rng["high"] * (1 + slip_bps / 1e4)
                        qty = position_size(cash, cash_per_trade, entry)
                        if qty > 0:
                            cash -= qty * entry
                            positions[s] = {"qty": qty, "entry": entry,
                                            "entry_date": ts, "peak": float(bar["high"])}
                            traded_today.add(s)
        if ts == last_ts_of_date[d]:
            for s, p in list(positions.items()):
                px = last_close.get(s, p["entry"])
                positions.pop(s)
                cash += p["qty"] * px
                _record(s, p, px, "eod_flatten")
        equity = cash + sum(p["qty"] * last_close.get(s, p["entry"]) for s, p in positions.items())
        equity_curve.append({"date": ts, "equity": round(equity, 2)})

    open_positions = [
        {"symbol": s, "qty": p["qty"], "entry_date": p["entry_date"],
         "entry": round(p["entry"], 2), "last": round(last_close.get(s, p["entry"]), 2),
         "unrealized_pnl": round(p["qty"] * (last_close.get(s, p["entry"]) - p["entry"]), 2)}
        for s, p in positions.items()
    ]
    return {
        "equity_curve": equity_curve, "trades": trades, "open_positions": open_positions,
        "metrics": _metrics(equity_curve, trades, open_positions, by_ts, budget),
    }
