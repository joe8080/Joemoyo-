# Live Portfolio Tracker

`Portfolio_Tracker.xlsx` — a live-updating Excel tracker for the Trading 212 ISA,
one tab per holding. v1 covers the Never Sell sleeve: **AMZN, MSFT, UBER**.

## Tabs

| Tab | What it does |
|---|---|
| `Dashboard` | Portfolio totals, all holdings side by side, weights, and every sell signal in one view. |
| `README` | Colour legend, tab guide, how to make prices live, and the full assumptions list. |
| `Prices` | The price engine. Update the live price cells here and the whole workbook moves. |
| `AMZN` / `MSFT` / `UBER` | Per holding: position, valuation & EPS, sell discipline, dividends, trade history, thesis. |
| `Transactions` | Master trade log. Shares and average cost are **calculated** from it, never typed. |
| `Dividends` | Dividend log, feeding the income block on each holding tab. |
| `Sell_Rules` | Default take-profit / trim / stop / trailing-stop levels, inherited by every holding tab. |

## How the numbers flow

```
Transactions ──SUMIFS──> holding tab (shares, invested, avg cost, realised P/L)
Prices ───────ref──────> holding tab (live price, FX, EPS, 52w range)
Dividends ────SUMIFS──> holding tab (income received)
Sell_Rules ───ref──────> holding tab (trigger levels, overridable per holding)
holding tabs ─ref──────> Dashboard (totals, weights, signals)
```

Nothing is double-entered. Add a trade in `Transactions` and every dependent
figure — average cost, P/L, weight, sell signal — moves on its own.

Average-cost accounting: a SELL is booked against the average cost of the shares
held before it, and the difference lands in `Realised P/L`.

## Making prices live

A generated `.xlsx` cannot ship already wired to a market feed — Excel only
trusts a connection the user enables. Three options, documented on the `README`
tab:

1. **Stocks data type** (Microsoft 365) — select the tickers, `Data > Stocks`, then `=A7.Price`.
2. **STOCKHISTORY** (Microsoft 365) — recalculates on open.
3. **Manual paste** — works in every Excel including web and Mac.

## Regenerating

```bash
python3 build_portfolio_tracker.py     # writes Portfolio_Tracker.xlsx
python3 verify_portfolio_tracker.py    # checks references + recomputes the arithmetic
```

`verify_portfolio_tracker.py` resolves every cross-sheet reference, rejects
spilling/post-2007 functions that break outside Microsoft 365, confirms each
formula targets the row its label claims, and independently recomputes shares,
invested, market value and P/L from the transaction log — reconciling to the
source export to the penny.

## Data sources and assumptions

| Item | Source |
|---|---|
| Shares, invested, current value | Trading 212 Never Sell pie export, `Never-sell-2026-08-04T11-15-05.211Z.csv` |
| Opening prices (USD) | Derived: GBP value per share × GBP/USD 1.34499 — not a feed print |
| GBP/USD 1.34499 | FMP forex quote `GBPUSD`, 4 August 2026 |
| EPS, forward EPS, analyst target, 52-week range | **Left blank deliberately.** Company financials are not invented — fill from the latest 10-Q or broker research. |
| Sell rule defaults | Placeholders (50% take-profit, 25%/40% trims, 20% stop, 25% trailing). Not advice. |
| Fees | Zero on the opening rows. Trading 212 charges 0.15% FX on USD trades. |

Not financial advice. The figures are only as good as the inputs kept current.

## Still to add

The remaining sleeves, once a full holdings CSV is available: Income (VHYL,
LGEN, BA, ABBV, O, BMO, ADP, V, MAIN), Energy & Nuclear (SHEL, HAL, MPC, XOM,
OXY, BWXT, ENB, CVX, OKLO, CCJ), and 100% Returns (Ondas, Nebius, Zeta,
Klaviyo, Iren).
