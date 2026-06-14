# Phase 4 — Automation (GitHub Actions)

**Goal:** run the bot on a schedule, no laptop open.

`.github/workflows/autotrade.yml` installs deps and runs one `--once` cycle on a
market-hours cron. Credentials come from repo secrets.

## Setup
1. Repo → **Settings → Secrets and variables → Actions** → add
   `ALPACA_API_KEY_ID`, `ALPACA_API_SECRET_KEY` (and optional `SUPABASE_*`,
   `ANTHROPIC_API_KEY`).
2. **Set the repo's default branch to the branch holding the workflow** — cron
   only runs from the default branch.
3. Actions tab → enable workflows → optionally "Run workflow" to test now.

## Gotchas (see lessons-learned)
- Scheduled runs fire **only from the default branch**.
- Cron is **delayed/coarse** — don't expect exact timing.
- Never inline a key fallback in the YAML; `${{ secrets.X }}` only.
- One value per secret — never paste a whole `KEY=value` block.

## Verify
Trigger the workflow manually; open the run log. Outside market hours it should
log "market closed" and exit cleanly (that's success). During market hours it
should place paper orders that appear on the dashboard.
