"""
Railway supervisor: runs ALL bot jobs in the one place that has working keys.

Post-mortem context: the swing engine used to run on GitHub Actions, but the
Alpaca keys were rotated and only Railway got the new ones — GitHub's copies
went stale and the swing engine silently 401'd for weeks. Rather than keep
credentials in sync across two platforms, this supervisor consolidates
everything onto the always-on Railway container:

  1. Intraday ORB engine  — child process, the exact old Dockerfile CMD,
                            restarted with backoff if it ever dies.
  2. Swing engine         — one --once cycle every 30 min during US market
                            hours (same cadence the GitHub cron used; the
                            engine itself no-ops when the market is closed).
  3. Daily coach          — once per weekday after the close.

Credentials come from the host env (ALPACA_API_KEY_ID / ALPACA_API_SECRET_KEY,
SUPABASE_URL / SUPABASE_SERVICE_KEY) exactly as before.
"""

import os
import subprocess
import sys
import time
from datetime import date, datetime, timezone

# The deterministic strategies never call Anthropic; a placeholder just
# satisfies the settings module's startup check (the coach degrades to its
# stats-only note). A real key in the host env always wins.
os.environ.setdefault("ANTHROPIC_API_KEY", "unused-deterministic")

PY = sys.executable

INTRADAY_CMD = [
    PY, "main.py", "autotrade",
    "--symbols", "NFLX,AVGO,COIN,IWM,SMH",
    "--interval", "5", "--mode", "intraday", "--strategy", "orb",
    "--timeframe", "5Min", "--or-bars", "6",
    "--budget", "10000", "--cash-per-trade", "2000", "--max-positions", "5",
    "--market-filter", "--trailing-stop-pct", "3",
    "--daily-loss-limit", "500", "--flatten-eod",
]

SWING_CMD = [
    PY, "main.py", "autotrade",
    "--symbols", "SPY,QQQ,AAPL,MSFT,NVDA,GOOGL,AMZN,META,TSLA,AMD",
    "--once",
    "--budget", "50000", "--cash-per-trade", "5000", "--max-positions", "10",
    "--enter-on-trend", "--trailing-stop-pct", "8",
]

COACH_CMD = [PY, "main.py", "coach"]

SWING_INTERVAL_S = 30 * 60
SWING_UTC_HOURS = range(13, 21)   # 13:00–20:59 UTC ≈ US market hours; the
                                  # engine additionally gates on the real clock
COACH_UTC_HOUR = 21               # shortly after the US close


def log(msg: str) -> None:
    print(f"[supervisor] {datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S} {msg}",
          flush=True)


def run_job(name: str, cmd: list[str]) -> None:
    """Run a one-shot job; log the outcome, never let it kill the supervisor."""
    log(f"{name}: starting")
    try:
        rc = subprocess.run(cmd, timeout=15 * 60).returncode
        log(f"{name}: exited {rc}" + (" (FAILED — check keys/logs)" if rc else ""))
    except Exception as e:  # noqa: BLE001 — supervisor must survive everything
        log(f"{name}: error {e}")


def main() -> None:
    log("booting: intraday(loop) + swing(30m, market hours) + coach(daily)")
    intraday = None
    intraday_backoff = 30
    last_swing = 0.0
    last_coach_day = None

    while True:
        # Keep the intraday engine alive.
        if intraday is None or intraday.poll() is not None:
            if intraday is not None:
                log(f"intraday: died rc={intraday.returncode}; "
                    f"restarting in {intraday_backoff}s")
                time.sleep(intraday_backoff)
                intraday_backoff = min(intraday_backoff * 2, 900)
            intraday = subprocess.Popen(INTRADAY_CMD)
            log(f"intraday: running pid={intraday.pid}")
        else:
            intraday_backoff = 30

        now = datetime.now(timezone.utc)
        weekday = now.weekday() < 5

        if (weekday and now.hour in SWING_UTC_HOURS
                and time.time() - last_swing >= SWING_INTERVAL_S):
            last_swing = time.time()
            run_job("swing", SWING_CMD)

        if weekday and now.hour >= COACH_UTC_HOUR and last_coach_day != date.today():
            last_coach_day = date.today()
            run_job("coach", COACH_CMD)

        time.sleep(60)


if __name__ == "__main__":
    main()
