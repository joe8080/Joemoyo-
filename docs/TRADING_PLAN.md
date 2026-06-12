# JoeMoyo AutoTrader — One-Month Trading Plan ($50k paper)

Start: 2026-06-12 · Review: weekly · Final review: 2026-07-10
Account: Alpaca paper ($100k) · Bot allocation: **$50,000**

## The setup

| Parameter | Value |
|---|---|
| Watchlist | SPY, QQQ, AAPL, MSFT, NVDA, GOOGL, AMZN, META, TSLA, AMD |
| Strategy | SMA 20/50 trend following on daily bars, regime mode |
| Position size | $5,000 target per name, max 10 positions |
| Budget cap | $50,000 total — the bot cannot deploy more |
| Schedule | One cycle every 30 min during US market hours (GitHub Actions) |
| Entry gates | Liquidity/range participation check (avg vol ≥ 2M, ATR ≥ $1) |
| Exits | Bearish crossover or bearish regime — never blocked by any filter |

Rationale for what's ON and OFF (from the 2022–2026 backtest, 10 names,
$50k, regime mode): baseline returned **+70.4%** (Sharpe 0.94, max DD 20.1%).
Adding volume confirmation and/or a SPY market filter *reduced* return and
Sharpe in every combination, so both ship **off by default** (available as
`--confirm-volume` / `--market-filter` for experiments). Buy-and-hold beat
the strategy in this bull window (+122%) — trend following pays its way in
downtrends, which this window mostly lacked; that's a known trade-off, not a
bug.

## Week 1 (Jun 12–19) — Deploy and observe

- Bot trades the full $50k: tops up the five starter positions to ~$5k each
  and opens the five new names as their trends allow.
- Daily (2 min, phone): open the dashboard — equity curve, positions, last
  cycle's log. Confirm the Actions runs are green.
- No parameter changes this week, no matter how it performs. Day-to-day noise
  is not signal.

## Week 2 (Jun 19–26) — First data review

- Pull `outputs/reports/trades.csv` and ask Claude for the SMB-style
  "autopsy": win rate, P&L by symbol, did any exit fire, did the budget stay
  ≤ $50k.
- Compare bot equity vs. SPY over the same window (dashboard backtest tab
  gives the benchmark).
- Allowed change: drop a symbol that's chronically choppy. Nothing else.

## Week 3 (Jun 26–Jul 3) — One experiment, isolated

- Run backtests (not live changes) on one variation: e.g. SMA 10/30 vs 20/50,
  or `--market-filter` on, or a different 10-name watchlist.
- The live bot keeps running untouched. An experiment earns its way into the
  live config only by beating the baseline on return AND Sharpe over the
  4-year backtest.

## Week 4 (Jul 3–10) — Monthly review and decision

- Full review: realized + unrealized P&L vs. $50k, vs. SPY buy-and-hold,
  max drawdown, number of trades, win rate, any failed/rejected orders.
- Decide one of: keep as is / adopt the Week-3 winner / scale allocation.
- Write the next month's plan from what the data says — not from how the
  month felt.

## Standing rules

1. **Paper only.** The bot hard-refuses live trading in this version.
2. **Exits are never filtered.** Any gate we add applies to entries only.
3. **One change at a time**, and only after a backtest supports it.
4. **Drawdown brake:** if bot equity drops more than 10% of budget ($5k)
   from its peak, halve `--cash-per-trade` until the weekly review.
5. Every trade and every blocked trade is logged (`trades.csv` + daily
   markdown log) — the review process depends on this record.
