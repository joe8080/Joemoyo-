# JoeMoyo AutoTrader — Strategy Specification & Pass/Fail Scorecard

This is the bot's contract: what it does, why, and the **measurable criteria
that decide whether it's passing**. The criteria here are evaluated in code
(`tools/scorecard.py`), printed by `python main.py coach`, and shown on the
dashboard, so the bot knows its own verdict — PASS / WATCH / FAIL.

---

## 1. Thesis

Trend-following on liquid US mega-caps. The edge is **not** out-gaining the
market in a rip — it's **losing less when the market falls** while still
capturing most uptrends, producing better *risk-adjusted* returns than buy-and-
hold. Validation (2022–2026) bears this out: in the 2022 bear the strategy lost
~23% while buy-and-hold lost ~57%; in bull years it trails raw buy-and-hold.
Judge it on drawdown control and risk-adjusted return, not raw return vs SPY.

## 2. Rules

**Swing engine** (daily bars): enter when the 20-SMA is above the 50-SMA
(regime mode), size $5,000/position, max 10 positions, $50,000 total budget.
Exit on an **8% trailing stop** or a bearish SMA crossover — whichever first.

**Intraday engine** (5-min bars, **opening-range breakout**): buy when price
breaks above the first 30 minutes' high on volume ≥ 1.5× the opening-range
average, **only while the market (SPY) is green on the day**; initial stop at the
opening-range low, then a 3% trailing stop, **flatten before the close**, one
entry per name per day, $2,000/position, max 5, $10,000 budget, $500 daily-loss
breaker. Disjoint watchlist so it never collides with the swing book.

Why ORB and not an intraday SMA crossover: validated on a year of 5-min data,
the SMA crossover had **no intraday edge** (profit factor ~1.0); opening-range
breakout with the market filter was **positive in all four quarters** even at
doubled slippage. It is now in a **paper trial** before going to a real-time
runner — see TRADING_PLAN.md.

**Always:** paper only; budget/positions scoped per engine; exits are never
filtered by entry gates; every action logged (Supabase + CSV).

## 3. Pass/Fail Scorecard

Evaluated on the **bot's own P&L against its budget** (not the whole $100k
account, which would dilute the result). Two states gate everything:

- **IN PROGRESS** — until ≥ 20 trading days elapsed AND ≥ 10 closed round trips.
  Not enough data to judge; the readout shows progress only.
- **Hard-fail (auto FAIL)** — if either: bot max drawdown > **25%**, or any
  single closed trade lost more than **25%** (a risk control failed).

Otherwise the verdict is the share of these six core criteria met:
**PASS ≥ 80% · WATCH ≥ 50% · FAIL < 50%.**

| # | Criterion | Target | Why |
|---|-----------|--------|-----|
| C1 | Profitable | bot return on budget **> 0%** | basic |
| C2 | Risk-adjusted | annualized Sharpe **≥ 0.5** | rewards smooth gains |
| C3 | Capital protection | bot max drawdown **≤ 15%** | the core promise |
| C4 | Downside edge | bot max drawdown **≤ SPY's** over the window | the whole thesis |
| C5 | Edge quality | profit factor **≥ 1.2** (≥ 15 trades) | winners > losers |
| C6 | Risk controls active | trailing/stop exits fired, none worse than ~2× the stop width | the safety net works |

Criteria that can't yet be measured (e.g. C5 before 15 trades) are marked
"gathering" and excluded from the ratio rather than counted as failures.

## 4. What to do with the verdict

- **PASS** at day 90 → keep the config; consider a measured scale-up.
- **WATCH** → keep running; the weekly coach review targets the failing criteria
  (e.g. if C4 fails, the trailing stop may be too loose for the regime).
- **FAIL / hard-fail** → stop adding capital, diagnose, and only resume after a
  fix is validated by `python main.py validate` (walk-forward) — never by a
  single backtest.

One change at a time, always validated out-of-sample before it goes live. The
scorecard is the referee; the validator is how we earn a rule change.
