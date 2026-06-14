# JoeMoyo AutoTrader — 90-Day Battle-Test Plan ($50k paper)

Start: 2026-06-15 · Reviews: weekly · Final review: ~2026-09-13
Account: Alpaca paper ($100k) · Swing budget: **$50,000** · Intraday budget: **$10,000**

## The two engines

| | Swing engine | Intraday engine |
|---|---|---|
| Workflow | `autotrade.yml` (every ~30 min) | `intraday.yml` (every ~5 min, market hours) |
| Watchlist | SPY QQQ AAPL MSFT NVDA GOOGL AMZN META TSLA AMD | NFLX AVGO COIN IWM SMH (disjoint) |
| Bars / SMAs | daily, 20/50, regime mode | 5-min, 9/20, regime mode |
| Exit | **trailing stop 8%** + SMA signal | trailing 2% + **EOD flatten** + $500 daily-loss limit |
| Sizing | $5k/position, max 10 | $2k/position, max 5 |

Both share one Alpaca account safely (budget/positions/flatten scoped per bot).

## Why this config (battle-testing done up front)

`python main.py validate` ran walk-forward, regime, and parameter tests on
2022–2026 SIP data. Findings:
- **Walk-forward:** 11/17 out-of-sample 90-day windows positive (avg +6.8%).
- **Regimes:** 2022 bear −23% vs buy-and-hold −57% (trailing stop cutting
  losses); lags raw buy-and-hold in rips, as trend-following does.
- **Robustness:** a broad plateau of similar Sharpes around the live config —
  not an overfit spike. (A faster 10/40–10/50 scored marginally higher Sharpe;
  it's the **Week-4 walk-forward candidate**, not adopted blindly.)

## Durable memory (Supabase)

Every trade, daily equity snapshot, round-trip, coach note, tendency, pattern
stat, and manual journal entry is written to `public.bot_*` tables in the
Investment Supabase project (isolated from real holdings/ISA data). The coach
feeds prior tendencies back in, so analysis compounds over the 90 days. Requires
`SUPABASE_URL` + `SUPABASE_SERVICE_KEY` secrets; the bot no-ops cleanly without
them (still logs to CSV).

## The 90 days

**Weeks 1–2 — Deploy & observe.** Both engines live. Daily: glance at the
dashboard (equity, positions, Journal & Coach tabs). No parameter changes.
Confirm Supabase rows accumulate and the daily-close coach note appears.

**Weeks 3–4 — First real read.** Enough closed round-trips to judge. Weekly
coach review: win rate, profit factor, P&L by symbol and by exit reason, swing
vs intraday. Allowed change: drop a chronically choppy symbol. End of Week 4:
walk-forward the 10/40 candidate; adopt only if it beats the live config on
return AND Sharpe out-of-sample.

**Weeks 5–8 — Stress & refine.** One isolated experiment at a time, each
backtested first. Watch behavior through any market drawdown — this is where the
trailing stop earns its keep. Track max drawdown vs the $50k.

**Weeks 9–12 — Verdict.** Full review from Supabase history: realized +
unrealized P&L vs $50k, vs SPY buy-and-hold, max drawdown, win rate, profit
factor, swing vs intraday contribution. Decide: keep / adopt the best validated
variant / rescale / retire an engine. Write the go-forward plan from the data.

## Standing rules
1. **Paper only** — the bot hard-refuses live trading in this version.
2. **Exits are never filtered**; risk reduction always goes through.
3. **One change at a time**, only after a backtest/walk-forward supports it.
4. **Drawdown brake:** if swing equity falls >10% of budget ($5k) from peak,
   halve `--cash-per-trade` until the next weekly review.
5. Everything is logged (Supabase + CSV + daily markdown). The review process
   depends on that record — never trade blind.
