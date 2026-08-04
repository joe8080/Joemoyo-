# Live Portfolio Tracker

`Portfolio_Tracker.xlsx` — a live Excel tracker for the Trading 212 ISA, one tab
per holding, with consensus EPS written through and a 3-year target model.
v2 covers the Never Sell sleeve: **AMZN, MSFT, UBER**.

## Tabs

| Tab | What it does |
|---|---|
| `Dashboard` | Portfolio totals, all holdings side by side, weights, sell signals, target status, % of the £1m goal. |
| `Targets` | The 3-year plan: projected value each year, required return, and the £1m goal maths. |
| `README` | Colour legend, tab guide, how the targets work, how to make prices live, assumptions. |
| `Prices` | Price engine, plus a reconciliation block against the Trading 212 pie export. |
| `Estimates` | Consensus EPS by fiscal year (FY2025–FY2030) and analyst price targets. Refresh quarterly. |
| `AMZN` / `MSFT` / `UBER` | Seven sections each: position, valuation & EPS, your 3-year targets, sell discipline, dividends, trade history, thesis. |
| `Transactions` | Master trade log, average-cost accounting. Shares and average cost are **calculated**, never typed. |
| `Dividends` | Dividend log, feeding the income block on each holding tab. |
| `Sell_Rules` | Default trigger levels, inherited by every holding tab. |

## How the numbers flow

```
Transactions ──SUMIFS──> holding tab (shares, invested, avg cost, realised P/L)
Prices ───────ref──────> holding tab (live price, FX, 52w range)
Estimates ────ref──────> holding tab (EPS by year, analyst target, implied P/E)
Dividends ────SUMIFS──> holding tab (income received)
Sell_Rules ───ref──────> holding tab (trigger levels, overridable per holding)
holding tabs ─ref──────> Dashboard + Targets (totals, weights, signals, projections)
```

Nothing is double-entered. Log a trade and every dependent figure moves on its own.

## The 3-year target model

1. **EPS** — `Estimates` carries consensus EPS for FY2027/28/29. Each holding tab
   copies those into three yellow cells you can overwrite with your own view.
2. **Your multiple** — target P/E starts at `consensus price target ÷ Year 1 EPS`,
   so Year 1 begins level with the street, then diverges as you set your own view.
3. **Target price** — `your target P/E × your EPS`, per year, in USD and GBP.
4. **On pace?** — `TARGET STATUS` compares today's price against your own path;
   `Targets` rolls all three holdings into one portfolio projection and solves the
   monthly contribution needed to close the gap to £1m.

## Making prices live

A generated `.xlsx` cannot ship already wired to a market feed — Excel only trusts
a connection the user enables. Three options, documented on the `README` tab:
Stocks data type, `STOCKHISTORY`, or manual paste.

## Regenerating

```bash
python3 build_portfolio_tracker.py       # writes Portfolio_Tracker.xlsx
pip install formulas                     # one-time, for the evaluator
python3 evaluate_portfolio_tracker.py    # evaluates every formula, reports error cells
```

`evaluate_portfolio_tracker.py` screens for spilling/post-2007 functions that break
outside Microsoft 365, builds the dependency graph, evaluates every cell, and
reports any `#NAME?` / `#REF!` / `#DIV/0!` / `#VALUE!` result. It then re-derives
the position block, checks the cost basis still ties to the pie export, checks
weights sum to 100%, checks each Year 1 target lands on the analyst consensus by
construction, and prints the signals. Rows are located by label, so the checks
cannot drift as the layout changes.

This replaces the usual LibreOffice recalc step, which hangs in the build sandbox
even on a two-cell workbook.

Last run: **2,220 cells evaluated, 0 formula errors**, weights summing to exactly
100%, cost basis tying to the export to the penny.

## Data sources and assumptions

| Item | Source |
|---|---|
| Shares, cost basis | Trading 212 Never Sell pie export, `Never-sell-2026-08-04T11-15-05.211Z.csv` |
| Prices, 52-week range | FMP end-of-day close, 3 Aug 2026 (last close before the export). 52w range on a closing basis, not intraday. |
| GBP/USD 1.34499 | FMP forex quote `GBPUSD`, 4 Aug 2026 |
| EPS FY2025–FY2030 | FMP analyst consensus (`epsAvg`) by fiscal year, 4 Aug 2026. AMZN/UBER to December, MSFT to June. |
| Analyst price targets | FMP price-target consensus, 4 Aug 2026 |
| Your target P/E | Seeded at consensus target ÷ Year 1 EPS. A starting point, not a recommendation. |
| Sell rule defaults | 50% take-profit, 25%/40% trims, 20% stop, 25% trailing. Placeholders, not advice. |
| Selling costs | 0.15% of market value — Trading 212's FX fee on a USD sale. |

### Why this differs from the pie export

The export's prices lag the 3 August US close. AMZN and MSFT both jumped on
30–31 July results, so the export understates them by ~2%; UBER matches to 0.11%,
which is what identifies the cause as stale prices rather than a bad FX rate. Cost
basis is unaffected. The `Prices` tab carries a live reconciliation block.

Two data quirks worth knowing: AMZN's FY2026E EPS sits *above* FY2027E because the
2026 consensus carries a large one-off gain, and UBER's FY2025 EPS is flattered by
a one-off tax benefit. Both are flagged on the `Estimates` tab.

Not financial advice. Projections are arithmetic on your own assumptions, not forecasts.

## Still to add

The remaining sleeves, once a full holdings CSV is available: Income (VHYL, LGEN,
BA, ABBV, O, BMO, ADP, V, MAIN), Energy & Nuclear (SHEL, HAL, MPC, XOM, OXY, BWXT,
ENB, CVX, OKLO, CCJ), and 100% Returns (Ondas, Nebius, Zeta, Klaviyo, Iren).
