# Phase 8 — Durable memory (Supabase)

**Goal:** history that survives restarts; the coach builds on the past; the
manual journal persists.

## Schema
Apply `supabase/migrations/0001_bot_tables.sql`: `bot_trades`,
`bot_round_trips`, `bot_equity_snapshots` (incl. `bot_pnl`/`bot_return_pct`),
`bot_coach_notes`, `bot_tendencies`, `bot_pattern_performance`,
`bot_manual_journal`. RLS on; a service-role policy grants the server-side bot
full access while anon clients get nothing.

## Why `public.bot_*` and not a `paper_bot` schema
Supabase's REST API only exposes the `public` schema by default; a custom schema
404s unless you toggle "exposed schemas." A `bot_` prefix in `public` gives the
same isolation from your other tables and works immediately. (If you prefer a
real schema, expose it in the dashboard or connect via direct Postgres.)

## Client (`tools/supabase_store.py`)
Thin PostgREST client using `requests` + the **service-role** key
(`SUPABASE_URL`, `SUPABASE_SERVICE_KEY`). Inserts/upserts trades, equity
snapshots, round trips, coach notes, tendencies, patterns, journal entries; reads
them back for the dashboard. **Best-effort:** every call is wrapped and returns
falsy on failure, and `enabled()` is False without creds — so trading never
breaks and local runs still work (CSV only).

## Wire-in
- `auto_trader`: `log_trade` per trade + a daily `snapshot_equity` carrying the
  bot's own realized+unrealized P&L vs budget (so drawdown/Sharpe are real, not
  diluted by the idle account).
- `coach`: saves notes/tendencies/patterns/round-trips and reads prior
  tendencies.
- dashboard: reads durable history; manual journal persists.

## Verify
Set the secrets, run one cycle, then check rows landed (`select count(*) from
public.bot_trades;`). Confirm your other tables are untouched.
