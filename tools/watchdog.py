"""
Watchdog: keep the durable-memory database alive and scream if the bot goes
quiet. Run daily (weekdays) by .github/workflows/watchdog.yml.

Does two things:
  1. Writes a keep-alive heartbeat so the Supabase project never idles into an
     auto-pause (a pause is what silently blinded us for two weeks).
  2. Checks freshness: if no equity snapshot has landed in the last few days
     despite markets being open, exits non-zero so the workflow goes RED and
     GitHub emails the owner. Silence must never look like success.

If Supabase credentials aren't configured it exits 0 with a warning (a daily
red run for a known-unconfigured optional feature would just train you to
ignore alerts).
"""

import sys
from datetime import date, timedelta

from tools import supabase_store

MAX_STALE_DAYS = 4  # tolerates a weekend + one holiday before alarming


def main() -> int:
    if not supabase_store.enabled():
        print("WARN: SUPABASE_URL / SUPABASE_SERVICE_KEY not set — watchdog "
              "cannot check liveness. Add them as repo secrets.")
        return 0

    ok = supabase_store.heartbeat("keepalive-watchdog", mode="watchdog")
    print(f"keep-alive heartbeat: {'ok' if ok else 'FAILED'}")

    snaps = supabase_store.get_equity_snapshots()
    if not snaps:
        print("ALERT: no equity snapshots exist at all — the bot has never "
              "logged, or the database was wiped.")
        return 1

    last = max(s["snapshot_date"] for s in snaps if s.get("snapshot_date"))
    last_d = date.fromisoformat(last)
    stale = (date.today() - last_d).days
    print(f"latest equity snapshot: {last} ({stale} day(s) ago)")

    if stale > MAX_STALE_DAYS:
        print(f"ALERT: bot has not logged an equity snapshot in {stale} days "
              f"(threshold {MAX_STALE_DAYS}). The runner may be down or its "
              "Alpaca/Supabase credentials broken. Check Railway logs and "
              "GitHub workflow runs.")
        return 1

    if not ok:
        print("ALERT: keep-alive write failed — Supabase may be paused or the "
              "service key is wrong.")
        return 1

    print("watchdog: all good.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
