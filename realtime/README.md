# Real-time intraday runner

The day-trade (opening-range breakout) engine needs to react during the session.
GitHub Actions can't do this reliably — its scheduled triggers were delayed by
**hours** (e.g. a 14:00 UTC trigger fired at 18:25 UTC), so the engine missed
whole sessions. This runs the intraday engine as a **continuous always-on
process** instead: it loops every 5 minutes, trades only while the market is
open (it checks the Alpaca clock each cycle), and flattens before the close.

The **swing engine stays on GitHub Actions** (its 30-minute cadence is not
time-sensitive and has been reliable). Only the intraday engine moves here.

## What it runs

The container/worker runs the validated config:

```
python main.py autotrade --symbols NFLX,AVGO,COIN,IWM,SMH --interval 5 \
  --mode intraday --strategy orb --timeframe 5Min --or-bars 6 \
  --budget 10000 --cash-per-trade 2000 --max-positions 5 \
  --market-filter --trailing-stop-pct 3 --daily-loss-limit 500 --flatten-eod
```

## Environment variables to set on the host

| Variable | Required | Notes |
|---|---|---|
| `ALPACA_API_KEY_ID` | yes | paper key id |
| `ALPACA_API_SECRET_KEY` | yes | paper secret |
| `ALPACA_PAPER` | yes | `true` |
| `SUPABASE_URL` / `SUPABASE_SERVICE_KEY` | optional | durable logging |
| `AGENT_OS_URL` / `AGENT_OS_KEYS` | optional | live card on the Agent OS board; Pause is honoured (see docs/AGENT_OS.md) |

## Deploy options (pick one)

### A. Railway — easiest (~$5/mo)
1. railway.app → New Project → Deploy from GitHub repo → pick this repo.
2. Settings → set the Dockerfile path to `realtime/Dockerfile` (or copy it to the
   repo root).
3. Variables → add the env vars above.
4. Deploy. It runs 24/7; the loop self-gates on market hours.

### B. Fly.io — has a small free allowance
1. `fly launch --dockerfile realtime/Dockerfile --no-deploy`
2. `fly secrets set ALPACA_API_KEY_ID=... ALPACA_API_SECRET_KEY=... ALPACA_PAPER=true`
3. `fly deploy` and scale to one always-on machine.

### C. Free forever — Oracle Cloud / GCP free-tier VM (more setup)
1. Create an always-free micro VM (Oracle `VM.Standard.A1` or GCP `e2-micro`).
2. Install Docker, clone the repo, `docker build -f realtime/Dockerfile -t bot .`
3. `docker run -d --restart=always --env-file .env bot`

## Verifying it works
- Host logs should show a cycle every ~5 minutes: "Market is CLOSED" outside
  hours, and per-symbol ORB checks during the session.
- Trades appear on the dashboard / in Alpaca, tagged `mode=intraday`.
- It flattens all intraday positions ~5 minutes before the close.

Paper trading only — educational, not financial advice.
