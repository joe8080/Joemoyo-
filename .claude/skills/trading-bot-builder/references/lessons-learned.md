# Lessons learned (the expensive ones)

Real pitfalls hit while building this bot. This page is the most valuable part
of the skill — it's the stuff you only learn by shipping.

## Strategy & risk

- **Take-profit caps hurt a trend-follower.** On mega-caps, a fixed take-profit
  (e.g. 15%) capped winners and *cut total return* — the backtest dropped from
  ~75% to ~48%. Let winners run.
- **A fixed catastrophe stop also hurt.** A 12% hard stop ejected positions on
  violent dips that then recovered, missing the rebound (return fell to ~58%).
- **A trailing stop alone won:** best return *and* best Sharpe *and* lowest
  drawdown. The trailing stop is its own crash protection. **Backtest your own
  universe — don't copy these numbers.**
- **A freshly started crossover bot can sit idle for months** waiting for the
  next cross. "Regime mode" (enter when short SMA is already above long) lets it
  engage day one. Mirror the exact rule in the backtester.

## Data

- **IEX vs SIP feed:** the free IEX feed reports only ~4% of real volume (SPY
  showed 1.0M vs 26.6M on SIP). Any volume-based logic is meaningless on IEX —
  use the consolidated SIP feed if the plan allows, with an automatic IEX
  fallback.
- **Pagination:** the bars endpoint caps at 1000 rows per page. Without
  following `next_page_token` you silently get a truncated/old window — fatal for
  long or intraday backtests. Also keep the full intraday timestamp (don't
  truncate to date) or 5-min bars collide.

## Automation (GitHub Actions)

- **Scheduled workflows only run from the repo's DEFAULT branch.** A workflow on
  a feature branch will never fire on cron. This wasted a day — set the default
  branch (or merge) before expecting the schedule.
- **Cron is delayed and coarse** (observed 10–15 min late, and it warms up over
  hours). Fine for swing; for intraday treat it as minutes-to-hours, not
  scalping, and rely on an end-of-day flatten.
- **Don't poll the GitHub API anonymously in a loop** — you'll hit the
  unauthenticated rate limit. Use authenticated calls / back off.

## Secrets (this one bites)

- **Never paste a whole `KEY = "value"` block into a single secret.** A secrets
  blob pasted into `ALPACA_API_SECRET_KEY` got sent as an HTTP header — it failed
  AND echoed the key into a public Actions log. Two defenses, both in the
  templates: (1) `settings._alpaca_env()` extracts the real value if a blob is
  pasted; (2) keep one value per secret.
- **A public repo's Actions logs are public.** If a secret ever prints, rotate
  it and delete the run logs immediately.
- **Don't inline a key "fallback" in a workflow.** Use `${{ secrets.X }}` only.

## Persistence

- **Supabase custom schemas aren't exposed to the REST API by default.** A
  `paper_bot` schema 404s over PostgREST unless you toggle "exposed schemas."
  Shipping tables in `public` with a `bot_` prefix gives the same isolation and
  works immediately with the service-role key.
- **Streamlit Community Cloud has an ephemeral filesystem** — anything written
  at runtime (e.g. a manual journal) resets on restart. Persist to Supabase (or
  commit from a workflow) instead.
- **Logging must never break trading.** The Supabase client is best-effort: every
  call is wrapped and returns falsy on failure so a logging outage can't stop the
  bot from trading or exiting.

## Process

- **The backtester must call the same functions the live bot uses.** If they
  drift, you're validating a different system.
- **Don't chase the backtest peak.** A parameter sweep showed a faster SMA
  scoring marginally higher — but adopt a change only after *walk-forward*
  confirms it out-of-sample. One change at a time.
- **Judge a trend-follower on risk-adjusted return and downside protection vs the
  benchmark**, not raw return — it will lag buy-and-hold in a rip and that's fine.
