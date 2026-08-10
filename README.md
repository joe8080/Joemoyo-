# JoeMoyo Business Agent System

AI-powered agents for your multi-brand business — built with Python and Claude AI.

## Your Businesses

| Business | Agent |
|---|---|
| OrigineX Human Archives (OGX) | OGXResearchAgent + OGXScriptWriterAgent + OGXVideoBuildAgent + OGXPackagingAgent |
| YouTube Historical Channel | ContentResearchAgent + ScriptWriterAgent |
| YouTube Finance Channel | FinancialContentAgent + ScriptWriterAgent |
| Music Studio | LeadGeneratorAgent |
| Shopify Store | ShopifyReportingAgent |
| Paper Trading (Alpaca) | TradingAgent |

All brands → **MarketingAgent**

---

## Two ways to run — with or without an API key

Agents reach Claude through one of two backends, chosen with `AGENT_BACKEND`:

| Backend | Auth | Notes |
|---|---|---|
| `sdk` (default) | `ANTHROPIC_API_KEY` | Calls the Anthropic API directly. Full Python tool-use loop. |
| `claude_cli` | your Claude Code session | Shells out to `claude -p`. **No API key, no separate bill.** |

```bash
# No API key needed — reuses the Claude Code session you're already signed into
AGENT_BACKEND=claude_cli AGENT_MODEL=claude-opus-5 \
  CLAUDE_MCP_CONFIG=~/.claude/mcp.json \
  python main.py ogx --topic "Mansa Musa I"
```

On the CLI backend an agent's tools come from Claude Code rather than from
Python: `WebSearch`/`WebFetch` stand in for the Brave search tool, and the
Supabase MCP stands in for the OGX database client. Same prompts, same evidence
rules, same output — a different way in. See `tools/claude_backend.py`.

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up your API keys

```bash
cp .env.example .env
```

Open `.env` and add your keys:

```
ANTHROPIC_API_KEY=sk-ant-...       # Required — get from console.anthropic.com
BRAVE_SEARCH_API_KEY=BSA...        # For web search — get from api.search.brave.com
SHOPIFY_SHOP_NAME=yourstore.myshopify.com   # For Shopify reports
SHOPIFY_ACCESS_TOKEN=shpat_...     # From Shopify Admin > Apps > Develop apps
```

### 3. Run your first agent

```bash
python main.py history --topic "The Fall of the Roman Empire"
```

---

## Commands

### History YouTube Channel

```bash
# Full pipeline: research + script + social media bundle
python main.py history --topic "The Fall of Constantinople"

# Write script only (no web research)
python main.py history --topic "Ancient Egypt" --script-only
```

### OrigineX (OGX) — evidence-gated history pipeline

The OGX channel runs on a stricter pipeline than the others: every factual claim
is checked against the OrigineX research database before it reaches a script,
a card, a title, or a description. The pipeline **refuses to start** without
that database. See [docs/OGX_PIPELINE.md](docs/OGX_PIPELINE.md) for the full
workflow, the house styles, and the schema contract.

```bash
# Full pipeline: research → script → video build sheet → posting pack
python main.py ogx --topic "Queen Nzinga"

# The declassified-receipts format (long-form statecraft documentaries)
python main.py ogx --topic "Operation Condor" --style declassified

# One stage at a time — iterate the script without paying for the rest
python main.py ogx --topic "Mansa Musa" --stage research
python main.py ogx --topic "Mansa Musa" --stage build \
    --from-file outputs/ogx/OGX_Mansa_Musa_script_archives_20260810_120000.md

# Run without the research database (everything is marked unverified)
python main.py ogx --topic "Sundiata Keita" --allow-unverified
```

### Finance YouTube Channel

```bash
# Full pipeline: analysis + script + social media bundle
python main.py finance --topic "Bitcoin ETF Impact on Retail Investors"

# Generate video ideas
python main.py finance --topic "stock market investing" --ideas-only --count 15
```

### Shopify Reporting

```bash
# Weekly report
python main.py shopify --report weekly

# Monthly report
python main.py shopify --report monthly
```

### Lead Generation

```bash
# Music studio client outreach
python main.py leads --type studio --name "The Jazz Quartet" --genre "Jazz" --followers "5k Instagram"

# YouTube sponsorship pitch
python main.py leads --type sponsor --name "Squarespace" --industry "website builder" --channel history_channel
```

### Marketing Content

```bash
# Social media bundle for any brand
python main.py market --brand history_channel --topic "New video: Fall of Rome"
python main.py market --brand music_studio --topic "Studio summer special offer"
python main.py market --brand shopify_store --topic "New product launch"

# Email newsletter
python main.py market --brand finance_channel --topic "This week's market recap" --type email

# Ad copy
python main.py market --brand music_studio --topic "Recording studio services" --type ads
```

### Content Calendar

```bash
# Generate 4-week content ideas for both YouTube channels
python main.py ideas --weeks 4
```

### Alpaca Paper Trading

Practice auto-trading with **simulated money and real market data** before
risking a cent. Defaults to Alpaca's paper environment
(`https://paper-api.alpaca.markets`).

```bash
# Account snapshot: equity, buying power, positions, open orders, market status
python main.py trade --action overview

# Research a ticker and get a proposed paper trade (does NOT place an order)
python main.py trade --action analyze --symbol AAPL

# Execute a trade described in plain English
python main.py trade --action execute --instruction "Buy $500 of AAPL at market"
python main.py trade --action execute --instruction "Sell half my TSLA position"
```

**Automated loop** — a deterministic SMA-crossover momentum strategy you can
leave running unattended on the paper account. No LLM call per cycle by default,
so it's free to run continuously and every decision is logged to
`outputs/reports/autotrade_log_<date>.md`. (Add `--llm-review` to layer in a
Claude risk check — see below.)

```bash
# Watch a list and trade every 15 min (runs until you press Ctrl-C).
# The bot may deploy at most $5,000 total, $1,000 per position, 5 positions.
python main.py autotrade --symbols AAPL,MSFT,SPY,NVDA --interval 15 \
    --budget 5000 --cash-per-trade 1000 --max-positions 5

# Single decision cycle, watch what it would do without placing orders
python main.py autotrade --symbols AAPL,MSFT --once --dry-run

# Single real cycle
python main.py autotrade --symbols AAPL,MSFT --once

# Add a Claude risk-review layer: it vetoes risky trades before they fire
python main.py autotrade --symbols AAPL,MSFT,SPY --interval 15 --llm-review
```

How it works: for each symbol it pulls recent daily bars and computes a short vs
long SMA crossover — **buys** on a fresh bullish cross (sized by `--cash-per-trade`,
capped at `--max-positions`) and **closes** the position on a bearish cross. It
only trades when the market is open and never spends past your buying power.
`--budget` caps the *total* capital the bot may deploy across all its positions
(default $5,000) — the rest of the account stays untouched. Tune the rule with
`--short-window` / `--long-window`.

**Risk-managed exits** — the bot no longer waits for the slow SMA to cross back
before selling. Add any of these (percentages; 0 = off):

```bash
python main.py autotrade --symbols ... --trailing-stop-pct 8   # exit 8% below peak
                                       --stop-loss-pct 5        # hard stop below entry
                                       --take-profit-pct 15     # profit target
```

The live swing bot runs `--trailing-stop-pct 8`. Backtesting (2022–2026, 10
mega-caps) picked it because it beat the SMA-only bot on return (74.9% vs 70.6%),
Sharpe (1.19 vs 0.97), and max drawdown (14.2% vs 16.2%); fixed take-profits and
stops both *hurt* (they cut winners / eject from dips that recover). A trailing
stop also produces same-day exits when a spike reverses.

**Intraday / day-trading mode** — 5-minute bars, fast SMAs, and an end-of-day
flatten so nothing is held overnight:

```bash
python main.py autotrade --symbols NFLX,AVGO,COIN,IWM,SMH --mode intraday \
    --timeframe 5Min --short-window 9 --long-window 20 \
    --trailing-stop-pct 2 --flatten-eod --daily-loss-limit 500
```

This runs as its own scheduled workflow with a separate sub-budget and a
watchlist kept *disjoint* from the swing book, so the two bots share one Alpaca
account without interfering. (GitHub Actions timing is approximate, so this is
minutes-to-hours intraday, not true scalping.)

**Backtesting** — replay the exact same signal and sizing rules over history
before trusting the bot with capital:

```bash
python main.py backtest --symbols SPY,QQQ,AAPL,MSFT,NVDA --days 365 \
    --budget 5000 --cash-per-trade 1000
```

Reports strategy return vs buy-and-hold, max drawdown, Sharpe, win rate, and
every closed trade. The same backtester is built into the dashboard
("Strategy backtest" section), so you can run it from any browser or phone.

**Journal & AI coach** — the system logs and reviews itself. It pairs filled
orders into round trips (entry/exit/P&L/hold/exit-reason), and a Claude "coach"
writes a plain-English performance note plus recurring *tendencies* to watch:

```bash
python main.py coach   # writes outputs/reports/{coach_<date>.md, tendencies.json, ledger.json}
```

A scheduled **daily-close ritual** (`.github/workflows/daily-close.yml`) runs
this after the bell and commits the results, so the dashboard's **Journal &
Coach** tabs (Performance · Round-trip trades · Coach & Tendencies · My journal)
update themselves. The "My journal" tab also lets you log your own discretionary
notes and grades. (Add an `ANTHROPIC_API_KEY` repo secret for the written coach
note; without it you still get the full deterministic stats.)

**Battle-testing** — validate a config out-of-sample before trusting it:

```bash
python main.py validate --start 2022-01-01
```

Runs walk-forward (rolling 90-day out-of-sample windows), market-regime slices,
and a parameter-robustness sweep so you can see whether an edge is consistent
and broad (robust) or a single lucky peak (overfit). Powered by paginated SIP
history (`AlpacaClient.fetch_bars`), which also enables intraday backtests.

**Strategy spec & pass/fail scorecard** — `docs/STRATEGY.md` is the bot's
contract: the rules plus measurable PASS/WATCH/FAIL criteria (profitability,
Sharpe, drawdown, downside edge vs SPY, profit factor, working risk controls).
The scorecard is evaluated in code so the bot knows its own verdict:

```bash
python main.py scorecard
```

It reports `PASS / WATCH / FAIL / IN PROGRESS` (measured on the bot's P&L vs its
budget, not the diluted account) and shows on the dashboard's Performance tab.

**Durable memory (Supabase)** — point the bot at a Supabase project and every
trade, daily equity snapshot, round-trip, coach note, tendency, and journal
entry is persisted to isolated `public.bot_*` tables, so history survives
restarts and the coach builds on past learning. Set `SUPABASE_URL` and
`SUPABASE_SERVICE_KEY` (service-role key) as repo + Streamlit secrets; without
them the bot logs to CSV only and never breaks. See `docs/TRADING_PLAN.md` for
the 90-day battle-test schedule.

**Run the bot in the cloud (no computer needed)** — the repo ships a GitHub
Actions workflow (`.github/workflows/autotrade.yml`) that runs one trading
cycle every 30 minutes during US market hours. To enable it:

1. On GitHub: repo → **Settings → Secrets and variables → Actions** →
   **New repository secret**. Add `ALPACA_API_KEY_ID` and
   `ALPACA_API_SECRET_KEY` (same values as the dashboard secrets).
2. Repo → **Actions** tab → enable workflows if prompted.
3. Optional: trigger a run immediately via **Actions → AutoTrader (paper) →
   Run workflow** to confirm everything is wired up.

Each run is a single `--once` cycle with the default $5k budget; edit the
watchlist or caps at the bottom of the workflow file.

With `--llm-review`, each cycle's proposed trades are handed to Claude acting as
a conservative risk reviewer before any order is placed — it approves sound
momentum trades and vetoes anything reckless or oversized. This is the one place
the loop spends tokens (one short call per cycle, only when there's something to
trade) and it's **fail-safe**: if the review errors or can't be parsed, it vetoes
rather than trades.

**Setup:** add your Alpaca paper keys to `.env`:

```
ALPACA_API_KEY_ID=PK...          # Key ID from app.alpaca.markets (Paper Trading)
ALPACA_API_SECRET_KEY=...        # Secret — shown only once at creation
ALPACA_PAPER=true                # keep "true" for simulated trading
```

> Get free paper keys at [app.alpaca.markets](https://app.alpaca.markets) →
> Home → Paper Trading → API Keys → Generate New Key.
> Educational paper trading only — not financial advice.

### Live Trading Dashboard

A Streamlit dashboard for watching the account and the AutoTrader in real time:
equity / cash / buying power, a 1-month equity curve, open positions with
unrealized P&L, open and filled orders, candlestick charts with the SMA 20/50
crossover signal for each watchlist symbol, and a live tail of the auto-trader
log. Auto-refreshes on an interval you pick in the sidebar.

```bash
streamlit run dashboard/app.py
```

Then open http://localhost:8501. Edit the watchlist in the sidebar to match the
symbols you run `autotrade` with. Set `DASHBOARD_REFRESH_SECS` to change the
default refresh interval (0 disables auto-refresh).

#### Free hosting on Streamlit Community Cloud

To get a permanent URL you can check from any device (no computer required):

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. Click **Create app** → pick this repo, your branch, and `dashboard/app.py`
   as the main file.
3. In **Advanced settings → Secrets**, paste your keys (see
   `.streamlit/secrets.toml.example`):

   ```toml
   ALPACA_API_KEY_ID = "your-paper-key-id"
   ALPACA_API_SECRET_KEY = "your-paper-secret-key"
   ALPACA_PAPER = "true"
   ```

4. Deploy. The app redeploys automatically on every push to the branch.

The hosted dashboard shows account, positions, orders, and signal charts; the
auto-trader log panel stays empty there since the bot writes logs on whatever
machine runs `autotrade`.

---

## Output Files

All generated content is saved to `outputs/`:

```
outputs/
├── scripts/      # YouTube research outlines and scripts
├── ogx/          # OGX dossiers, scripts, build sheets, posting packs
├── marketing/    # Social posts, emails, ad copy
├── leads/        # Outreach sequences and sponsorship pitches
└── reports/      # Shopify performance reports
```

---

## Customize Your Brands

Edit `config/brand_profiles.py` to update your channel names, tone, audience, and CTAs.

---

## Architecture

```
main.py (CLI)
    └── orchestrator/orchestrator.py (workflow routing)
            ├── agents/ogx_research.py      → tools/ogx_db.py + tools/web_search.py
            ├── agents/ogx_script.py        → tools/ogx_db.py
            ├── agents/ogx_video_build.py   → tools/ogx_db.py
            ├── agents/ogx_packaging.py     → tools/ogx_db.py
            ├── agents/content_research.py  → tools/web_search.py
            ├── agents/script_writer.py
            ├── agents/financial_content.py → tools/web_search.py
            ├── agents/marketing.py
            ├── agents/shopify_reporting.py → tools/shopify_client.py
            ├── agents/lead_generator.py   → tools/web_search.py
            ├── agents/trading_agent.py    → tools/alpaca_client.py
            └── agents/auto_trader.py      → tools/alpaca_client.py + tools/strategies.py
```

All agents inherit from `agents/base_agent.py` which handles the Claude tool-use loop automatically.
The four OGX agents inherit from `agents/ogx_base.py` instead, which adds the shared
research-database toolkit so no stage of that pipeline can skip the evidence gate.

Run the OGX schema-contract tests (stdlib only, no network, no API calls):

```bash
python tests/test_ogx.py
```
