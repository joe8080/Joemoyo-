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
CMD ["python", "main.py", "autotrade", \
     "--symbols", "NFLX,AVGO,COIN,IWM,SMH", \
     "--interval", "5", "--mode", "intraday", "--strategy", "orb", \
     "--timeframe", "5Min", "--or-bars", "6", \
     "--budget", "10000", "--cash-per-trade", "2000", "--max-positions", "5", \
     "--market-filter", "--trailing-stop-pct", "3", \
     "--daily-loss-limit", "500", "--flatten-eod"]
