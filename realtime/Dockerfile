# Always-on real-time runner for the intraday opening-range-breakout engine.
# GitHub Actions cron proved too unreliable for day trading (scheduled triggers
# delayed by hours), so the intraday engine runs as a continuous process here:
# it loops every 5 minutes, trades only while the market is open (the loop gates
# on the Alpaca clock), and flattens before the close. Deploy on any always-on
# host (Railway, Fly.io, Render, or a small VM).
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV ALPACA_PAPER=true PYTHONUNBUFFERED=1
# Intraday ORB engine, validated config. Credentials come from host env vars:
# ALPACA_API_KEY_ID, ALPACA_API_SECRET_KEY, and optionally SUPABASE_URL/_KEY.
# The supervisor runs every job in this one container: the intraday ORB
# loop, swing cycles every 30 min in market hours, and the daily coach.
# (The swing engine moved here from GitHub Actions after its copy of the
# rotated Alpaca keys went stale — one host, one set of credentials.)
CMD ["python", "realtime/supervisor.py"]
