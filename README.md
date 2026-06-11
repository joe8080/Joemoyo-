# JoeMoyo Business Agent System

AI-powered agents for your multi-brand business — built with Python and Claude AI.

## Your Businesses

| Business | Agent |
|---|---|
| YouTube Historical Channel | ContentResearchAgent + ScriptWriterAgent |
| YouTube Finance Channel | FinancialContentAgent + ScriptWriterAgent |
| Music Studio | LeadGeneratorAgent |
| Shopify Store | ShopifyReportingAgent |
| Paper Trading (Alpaca) | TradingAgent |

All brands → **MarketingAgent**

---

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
leave running unattended on the paper account. No LLM call per cycle, so it's
free to run continuously and every decision is logged to
`outputs/reports/autotrade_log_<date>.md`.

```bash
# Watch a list and trade every 15 min (runs until you press Ctrl-C)
python main.py autotrade --symbols AAPL,MSFT,SPY,NVDA --interval 15 \
    --cash-per-trade 5000 --max-positions 5

# Single decision cycle, watch what it would do without placing orders
python main.py autotrade --symbols AAPL,MSFT --once --dry-run

# Single real cycle
python main.py autotrade --symbols AAPL,MSFT --once
```

How it works: for each symbol it pulls recent daily bars and computes a short vs
long SMA crossover — **buys** on a fresh bullish cross (sized by `--cash-per-trade`,
capped at `--max-positions`) and **closes** the position on a bearish cross. It
only trades when the market is open and never spends past your buying power.
Tune the rule with `--short-window` / `--long-window`.

**Setup:** add your Alpaca paper keys to `.env`:

```
ALPACA_API_KEY_ID=PK...          # Key ID from app.alpaca.markets (Paper Trading)
ALPACA_API_SECRET_KEY=...        # Secret — shown only once at creation
ALPACA_PAPER=true                # keep "true" for simulated trading
```

> Get free paper keys at [app.alpaca.markets](https://app.alpaca.markets) →
> Home → Paper Trading → API Keys → Generate New Key.
> Educational paper trading only — not financial advice.

---

## Output Files

All generated content is saved to `outputs/`:

```
outputs/
├── scripts/      # YouTube research outlines and scripts
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
