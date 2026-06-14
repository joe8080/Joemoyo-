# Phase 2 — Backtesting

**Goal:** replay the strategy over history and report return vs buy-and-hold,
max drawdown, Sharpe, win rate, and every trade.

## The one rule
`tools/backtest.py` must call the **same** `sma_crossover_signal` / `risk_exit` /
`position_size` functions the live bot uses. If the backtest reimplements the
logic, you're testing a different bot and the results lie.

## What it models
- Bar-by-bar over daily (or intraday) bars; fills at the signal bar's close.
- Risk exits modeled **intrabar** against each bar's high/low (stop checked
  first as the worst case when a bar spans both stop and target).
- A buy-and-hold benchmark over the same window, plus max drawdown and an
  annualized Sharpe from daily equity returns.
- No slippage/commission (Alpaca is commission-free) — note this assumption.

## Verify
```bash
python main.py backtest --symbols SPY,QQQ,AAPL,MSFT,NVDA --days 365 --trailing-stop-pct 8
```
Sanity checks: does final equity ≈ budget + realized + unrealized? Do trades fire
both directions? Compare a trailing-stop run vs `--trailing-stop-pct 0` to see the
exit's effect before trusting it. Backtesting tells you *if*; Phase 9 (validate)
tells you whether it's *robust*.
