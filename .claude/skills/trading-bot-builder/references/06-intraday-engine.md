# Phase 6 — Intraday engine (optional day-trading)

**Goal:** a faster engine on minute bars that never holds overnight.

Same `AutoTrader`, different settings via `intraday.yml`: `--timeframe 5Min`,
`--short-window 9 --long-window 20`, a tight `--trailing-stop-pct 2`,
`--daily-loss-limit 500`, and `--flatten-eod` (closes everything ~5 min before
the bell using the market clock). Tag it `--mode intraday` so the journal can
separate it from swing.

## Two engines, one account — the safety rule
Run intraday as a **separate engine with a disjoint watchlist** and its own
budget. Critically, the bot scopes **budget, position count, and EOD-flatten to
its own symbols** — otherwise the intraday bot would size against (or flatten!)
the swing book. With disjoint symbols + per-engine scoping, both share one Alpaca
account safely.

## Honest limits
GitHub Actions cron (~5 min, often late) is not true scalping — treat it as
minutes-to-hours intraday. The EOD flatten is the backstop that guarantees no
overnight risk regardless of timing. PDT rule: a >$25k account trades unlimited
day trades; below that you're capped at 3 per 5 days.

## History window
For intraday, fetch a short span (e.g. 7 days) so Alpaca's 1000-bar page stays on
recent data (`bars_days_back` switches automatically for non-daily timeframes).
