# Phase 1 — Paper-trading core

**Goal:** account access + one deterministic strategy + a loop that places paper
orders under explicit caps.

## Pieces
- `config/settings.py` — loads creds from env; paper is default; tolerates
  pasted secret blobs via `_alpaca_env()`.
- `tools/alpaca_client.py` — thin REST wrapper: `account_summary`,
  `get_positions`/`simplify_positions`, `get_orders`/`simplify_orders`,
  `submit_order`, `close_position`, `get_bars`/`fetch_bars`, `get_clock`. SIP
  feed with IEX fallback.
- `tools/strategies.py` — **pure** functions (no I/O): `sma`,
  `sma_crossover_signal`, `position_size`, plus `risk_exit` and participation
  helpers. Purity makes them unit-testable and reusable by the backtester.
- `agents/auto_trader.py` — the loop. `run_once()` per cycle:
  1. skip if market closed (`get_clock`);
  2. refresh account + positions + open orders;
  3. per symbol: pull bars → signal → risk-exit check → buy/close proposal under
     budget / max-positions caps;
  4. execute (or log under `--dry-run`); log every decision.

## Design rules that matter
- **Paper-only hard guard:** the loop raises if the account isn't paper. Keep it.
- **Budget cap** separate from buying power: the bot deploys at most `--budget`
  across positions; the rest of the account is untouched.
- **Scope to the bot's own symbols** (see Phase 6) so multiple engines can share
  one account.
- Log every cycle to a dated markdown file and `trades.csv` — you'll need it for
  the journal/coach.

## Verify
```bash
python main.py overview
python main.py autotrade --symbols SPY,QQQ --once --dry-run
```
Dry-run prints decisions and places no orders. Then drop `--dry-run` during
market hours for a real paper cycle.
