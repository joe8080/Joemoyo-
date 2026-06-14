# Phase 7 — Journal + AI coach

**Goal:** the system logs and reviews itself.

## Ledger (`tools/journal.py`)
`build_ledger(orders)` pairs filled buys/sells per symbol **FIFO** into closed
round trips (entry/exit/P&L/hold/exit-reason). `ledger_stats(trips)` rolls them
into win rate, profit factor, P&L by symbol and by exit reason, and a daily-P&L
calendar. Pure and unit-testable.

## Coach (`agents/coach.py`)
`generate_coach_report(orders, reports_dir)` builds the ledger, then asks Claude
to write a plain-English performance note + 2–5 recurring **tendencies**. It
feeds the *previous* tendencies back in so the analysis compounds. Falls back to
a deterministic stats-only note when no `ANTHROPIC_API_KEY` — the report always
generates. Reuses the same Anthropic call pattern as any LLM helper.

Important framing: the coach **analyses what happened**, it does not predict or
pick trades. That's the safe, useful use of an LLM here.

## Automate it
`.github/workflows/daily-close.yml` runs `python main.py coach` after the close
and commits the outputs so a hosted dashboard self-updates.

## Verify
```bash
python main.py coach
```
Before any round trips close it correctly says "no closed trips yet." After
exits, you get stats + (with a key) a written note.
