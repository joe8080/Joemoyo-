---
name: trading-bot-builder
description: Build a complete automated stock paper-trading bot on Alpaca — an SMA trend strategy with trailing-stop risk exits, backtesting and walk-forward validation, an intraday engine, a Streamlit dashboard, GitHub Actions automation, a self-logging journal with an AI coach, Supabase durable memory, and a pass/fail scorecard. Use when the user wants to build, scaffold, or learn how to build an algorithmic trading bot, paper-trading system, or trading dashboard from scratch.
---

# Trading Bot Builder

This skill builds a production-shaped **paper-trading** bot end to end, the way
the JoeMoyo AutoTrader was built. It is both a **guided builder** (genericized
code templates in `assets/templates/` you can drop in and wire up) and a
**methodology playbook** (the ordered phases below + deep dives in
`references/`).

> ⚠️ **Paper trading only. Educational, not financial advice.** Every template
> hard-refuses live trading. Past/backtested performance does not predict future
> results. Keep it on a paper account.

## How to use this skill

1. Read this file top to bottom — it's the build order and the decisions that
   matter.
2. Work the phases **in order**. Each phase says: the goal, the key decision,
   which template(s) to copy from `assets/templates/`, and the lesson learned.
3. For depth on any phase, open the matching file in `references/`.
4. Before anything ships or is shared, do the **Genericize & secrets** pass.

Default stack: Python 3.12, Alpaca (paper), Streamlit, GitHub Actions, optional
Supabase + Anthropic. Templates use `click` for the CLI and plain `requests` for
APIs (no heavy SDKs).

## Architecture in one paragraph

A deterministic strategy (`tools/strategies.py`) produces signals from price
bars fetched via a thin Alpaca client (`tools/alpaca_client.py`). An unattended
loop (`agents/auto_trader.py`) turns signals into orders under explicit risk
caps and exits. A backtester (`tools/backtest.py`) replays the *exact* same
rules over history; a validator (`tools/validate.py`) proves it out-of-sample. A
Streamlit dashboard (`dashboard/app.py`) shows it live. GitHub Actions runs it
on a schedule. A journal (`tools/journal.py`) + AI coach (`agents/coach.py`)
review the results; Supabase (`tools/supabase_store.py`) makes the history
durable; a scorecard (`tools/scorecard.py`) grades it PASS/WATCH/FAIL. Everything
is driven from one CLI (`main.py`).

## The build, in order

Build the **minimum viable bot** first (Phases 1–4), get it trading on paper,
then layer the rest. Don't build all of it before the first trade.

### Phase 1 — Paper-trading core
- **Goal:** account access + one strategy + a loop that can place paper orders.
- **Decision:** start with one transparent, deterministic signal — an SMA
  crossover — not an ML black box. Keep strategy logic *pure* (no I/O) so it's
  unit-testable and reusable by the backtester.
- **Templates:** `config/settings.py`, `tools/alpaca_client.py`,
  `tools/strategies.py`, `agents/auto_trader.py`, `main.py`, `requirements.txt`,
  `.env.example`.
- **Guardrail:** the loop hard-refuses non-paper accounts. Keep that.
- Detail: `references/01-paper-trading-core.md`.

### Phase 2 — Backtest before you trust it
- **Goal:** replay the strategy over historical bars; report return vs
  buy-and-hold, max drawdown, Sharpe, win rate.
- **Decision:** the backtester must call the **same** signal/sizing functions
  the live bot uses — otherwise you're testing a different bot.
- **Template:** `tools/backtest.py` (+ `backtest` command in `main.py`).
- Detail: `references/02-backtesting.md`.

### Phase 3 — Dashboard
- **Goal:** see the account, positions, orders, equity curve, and per-symbol
  signal charts in a browser/phone.
- **Template:** `dashboard/app.py` (Streamlit). Deploys free on Streamlit
  Community Cloud; reads secrets from `st.secrets` or `.env`.
- Detail: `references/03-dashboard.md`.

### Phase 4 — Automate in the cloud
- **Goal:** run the bot on a schedule with no laptop open.
- **Template:** `.github/workflows/autotrade.yml` (cron during market hours,
  one `--once` cycle per run).
- **Lesson (important):** GitHub only runs *scheduled* workflows from the repo's
  **default branch**, and cron is delayed/coarse. See lessons-learned.
- Detail: `references/04-automation-github-actions.md`.

### Phase 5 — Risk-managed exits (the part most bots skip)
- **Goal:** stop relying on the slow signal to exit; add stop-loss / take-profit
  / trailing-stop.
- **Decision (backtest-driven):** for a mega-cap trend follower, a **trailing
  stop alone won** — fixed take-profits cap winners and fixed stops eject you
  from dips that recover. Don't assume; backtest your own universe.
- **Template:** `risk_exit()` in `tools/strategies.py`, wired into
  `auto_trader.py` ahead of the signal; modeled intrabar in `backtest.py`.
- Detail: `references/05-risk-exits.md`.

### Phase 6 — Intraday engine (optional day-trading)
- **Goal:** a faster engine on minute bars with an end-of-day flatten.
- **Decision:** run it as a **separate engine** with its own budget and a
  watchlist **disjoint** from the swing book; scope budget/positions/flatten per
  engine so two bots can share one account safely.
- **Template:** `.github/workflows/intraday.yml` + the `--timeframe/--flatten-eod
  /--daily-loss-limit/--mode` flags already in `auto_trader.py`/`main.py`.
- Detail: `references/06-intraday-engine.md`.

### Phase 7 — Journal + AI coach
- **Goal:** the system logs and reviews itself. Pair fills into round trips;
  have Claude narrate performance + recurring "tendencies."
- **Templates:** `tools/journal.py` (FIFO ledger + stats), `agents/coach.py`,
  the `coach` command, `.github/workflows/daily-close.yml`.
- Detail: `references/07-journal-and-coach.md`.

### Phase 8 — Durable memory (Supabase)
- **Goal:** history that survives restarts; the coach builds on the past.
- **Template:** `tools/supabase_store.py` (best-effort REST; no-ops without
  creds so trading never breaks) + `supabase/migrations/0001_bot_tables.sql`.
- **Lesson:** custom Postgres schemas aren't exposed by Supabase's REST API by
  default — ship tables in `public` with a `bot_` prefix instead.
- Detail: `references/08-supabase-memory.md`.

### Phase 9 — Validate, then grade
- **Goal:** prove the edge is robust (not overfit) and define what "passing"
  means.
- **Templates:** `tools/validate.py` (walk-forward / regime / parameter sweep),
  `tools/scorecard.py` (PASS/WATCH/FAIL), `docs/STRATEGY.md` (the contract).
- **Decision:** judge a trend-follower on **risk-adjusted** terms and **downside
  protection vs the benchmark**, not raw return — and adopt a parameter change
  only after walk-forward confirms it out-of-sample.
- Detail: `references/09-validation-and-scorecard.md`.

## Genericize & secrets (do this before sharing/selling)

- Templates contain **no credentials**. All keys come from env/secrets:
  `ALPACA_API_KEY_ID`, `ALPACA_API_SECRET_KEY`, `ALPACA_PAPER=true`, optional
  `ANTHROPIC_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`.
- Set them as GitHub Actions repo secrets and Streamlit Cloud secrets.
- Watchlists, budgets, and SMA/stop parameters in the templates are **examples** —
  tune to the user's risk profile and re-run `validate`.
- Never paste a whole `KEY = value` block into a single secret (it leaks into
  logs and breaks parsing — see lessons-learned).

## Packaging to share or sell

Run `scripts/package_skill.sh` to produce a standalone zip in `dist/` containing
this skill (SKILL.md + references + templates), a top-level README, and
`LICENSE`/`NOTICE`. To use the skill locally, copy this folder into
`~/.claude/skills/`.

See `references/lessons-learned.md` for the real pitfalls hit while building this
— it's the most valuable page for a buyer.
