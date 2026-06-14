# Phase 5 — Risk-managed exits

**Goal:** stop relying on the slow signal to exit. Most beginner bots only sell
when the averages cross back — by then a position can be down 20–30%.

## The function
`risk_exit(entry, last, peak, stop_pct, take_profit_pct, trail_pct)` in
`tools/strategies.py` returns `"stop" | "take_profit" | "trailing" | None`.
Stop is checked first (capital protection beats profit-taking). It's evaluated in
`auto_trader._gather_proposals` **before** the SMA logic, so a risk exit fires
regardless of trend — and a position can open and close the same day.

## Stateless peak for the trailing stop
The trailing stop needs the high since entry. Derive it without a state file:
find when the current net-long streak began from filled-order history, then take
the max bar-high since that date. (`_peak_since_entry` in `auto_trader.py`.)

## What the backtest taught us (validate on YOUR universe)
On mega-caps: trailing-stop-only beat baseline on return, Sharpe, and drawdown.
Fixed take-profits capped winners; a fixed catastrophe stop ejected from dips
that recovered. The live swing config is `--trailing-stop-pct 8`, no take-profit,
no fixed stop. Always model the exits intrabar in the backtester and re-pick.

## Verify
```bash
python main.py backtest --symbols ... --trailing-stop-pct 8     # vs 0 to compare
python main.py autotrade --symbols ... --once --dry-run --trailing-stop-pct 8
```
The dry-run logs which exit would fire and the % vs entry.
