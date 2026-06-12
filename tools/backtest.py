"""
Backtester for the AutoTrader's SMA-crossover strategy — pure logic, no I/O.

Replays the exact signal (tools.strategies.sma_crossover_signal) and sizing
rules (position_size + budget / max_positions caps) the live bot uses, bar by
bar over historical daily data, so results reflect what the bot would actually
have done. Fills happen at the signal bar's close; no slippage or commissions
are modeled (Alpaca is commission-free).
"""

from math import sqrt

from tools.strategies import sma, sma_crossover_signal, position_size, volume_confirmed


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

            signal = sma_crossover_signal(
                history[symbol], short_window=short_window, long_window=long_window
            )
            holding = symbol in positions
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
                    positions[symbol] = {"qty": qty, "entry": price, "entry_date": day}
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
