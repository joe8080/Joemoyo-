# Phase 9 — Validate, then grade

**Goal:** prove the edge is robust (not overfit) and define what "passing" means.

## Validation (`tools/validate.py` → `python main.py validate`)
- **Walk-forward:** consecutive out-of-sample 90-day windows with a warm-up
  lead-in. Consistency across windows (e.g. "11/17 positive") matters more than
  any single number.
- **Regime slices:** run the config over a bear slice and a bull slice
  separately. A trend-follower should lose far less than buy-and-hold in the bear
  and lag it in the bull — that's the thesis working.
- **Parameter sweep:** a grid over SMA windows and trailing %. You want a broad
  plateau of similar Sharpes around your config (robust), not a lone spike
  (overfit). Adopt a change only if walk-forward confirms it out-of-sample.

## Scorecard (`tools/scorecard.py` → `python main.py scorecard`)
Turns `docs/STRATEGY.md` into a machine verdict: **PASS / WATCH / FAIL / IN
PROGRESS**. Six criteria — profitable, Sharpe ≥ 0.5, drawdown ≤ 15%, drawdown ≤
the benchmark's, profit factor ≥ 1.2, risk controls firing — with hard-fail
bounds (drawdown > 25% or any trade < −25%) and a data gate (≥ 20 days & ≥ 10
trades before it judges).

**Measure on the bot's P&L vs its budget, not the whole account** — otherwise
idle cash dilutes the numbers and drawdown looks fake-good. The downside-edge
criterion (vs the benchmark) is how you confirm the "lose less in downturns"
thesis is actually holding.

## The discipline
The scorecard is the referee; `validate` is how you earn a rule change. One
change at a time, always confirmed out-of-sample before it goes live.
