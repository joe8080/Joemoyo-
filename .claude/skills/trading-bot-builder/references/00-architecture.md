# Architecture

```
                    ┌─────────────────────────────────────────────┐
                    │                  main.py (CLI)               │
                    │  overview · autotrade · backtest · validate  │
                    │            · coach · scorecard               │
                    └───────────────┬─────────────────────────────┘
                                    │
   price bars        signals        │ orders / exits         durable memory
 ┌──────────────┐  ┌────────────┐   ▼   ┌──────────────┐   ┌────────────────┐
 │ alpaca_client│→ │ strategies │→ │auto │→ Alpaca API   │   │ supabase_store │
 │ (SIP/IEX,    │  │ (pure:     │  │trader│  (paper)      │←─→│ (public.bot_*) │
 │  paginated)  │  │  SMA,risk) │  │ loop │               │   └────────────────┘
 └──────┬───────┘  └─────┬──────┘  └──┬───┘                          ▲
        │                │            │ trades.csv / logs            │
        ▼                ▼            ▼                              │
 ┌──────────────┐  ┌────────────┐  ┌──────────────┐  ┌──────────────┴─┐
 │  backtest    │  │  validate  │  │   journal    │→ │     coach      │
 │ (same rules) │  │ (walk-fwd) │  │ (FIFO ledger)│  │ (Claude note + │
 └──────────────┘  └─────┬──────┘  └──────┬───────┘  │  tendencies)   │
                         │                │          └────────────────┘
                         ▼                ▼
                   ┌────────────┐   ┌──────────────────────────────┐
                   │ scorecard  │   │   dashboard/app.py (Streamlit)│
                   │ PASS/FAIL  │   │  live view + journal + coach  │
                   └────────────┘   └──────────────────────────────┘
```

## Principles
- **Pure strategy core** (`strategies.py`) → the backtester and live bot share
  the exact same signal/sizing/exit functions.
- **Deterministic by default** — no LLM per trade; the bot is auditable and free
  to run continuously. The LLM is used only to *review* (coach) and optionally to
  *veto* risky proposals, never to predict.
- **Best-effort side-channels** — Supabase logging and the coach never block
  trading; missing creds = clean no-op.
- **One account, multiple engines** — budget/positions/flatten scoped per engine
  with disjoint watchlists.
- **Paper-only guardrail** baked into the loop.

## Data flow per cycle
clock check → account/positions/orders → per symbol: bars → signal → risk-exit
→ proposal (budget/caps) → execute or dry-run → log (CSV + Supabase) → daily
equity snapshot. After the close: ledger → coach note + tendencies → scorecard.
