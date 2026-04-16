# Portfolio Snapshot

Full portfolio analysis with ISA vs GIA split, concentration risk flags, and progress toward £1M.

## Data Files
- `data/portfolio.json` — holdings and balances
- `data/ladder.json` — for overall progress context

## Instructions

1. **Load** `data/portfolio.json` and `data/ladder.json`
2. **Calculate totals:**
   - ISA total (all ISA accounts)
   - GIA total (all GIA accounts)
   - JISA total (all JISA accounts)
   - Grand total
   - Progress % toward £1M target
3. **Output the snapshot:**

```
PORTFOLIO SNAPSHOT — [today's date]
══════════════════════════════════════════════════════════

  ACCOUNT SUMMARY
  ──────────────────────────────────────────────
  Account                    | Provider      | Value
  Stocks & Shares ISA        | [Provider]    | £XX,XXX
  GIA                        | [Provider]    | £XX,XXX
  JISA — Andre               | [Provider]    | £XX,XXX
  JISA — Ameera              | [Provider]    | £XX,XXX
  ──────────────────────────────────────────────
  TOTAL PORTFOLIO            |               | £XX,XXX

  WRAPPER SPLIT
  ──────────────────────────────────────────────
  ISA  ████████████░░░░  XX%  £XX,XXX  (tax-free)
  GIA  ████░░░░░░░░░░░░  XX%  £XX,XXX  (taxable)
  JISA ██░░░░░░░░░░░░░░  XX%  £XX,XXX  (children)

  PROGRESS TO £1,000,000
  ──────────────────────────────────────────────
  £XX,XXX of £1,000,000
  ████░░░░░░░░░░░░░░░░  X.X%
  Remaining: £XXX,XXX

  HOLDINGS BREAKDOWN (ISA + GIA combined)
  ──────────────────────────────────────────────
  Ticker | Name              | Value    | Alloc%  | Flag
  VWRP   | FTSE All-World    | £XX,XXX  | XX%     | ✅
  ...

  CONCENTRATION RISK FLAGS
  ──────────────────────────────────────────────
  [If any single holding > 25% of portfolio → ⚠️  CONCENTRATION: [ticker] at XX%]
  [If all within limits → ✅ No concentration risk detected]

  REBALANCING NOTES:
  [If GIA has holdings that could be sheltered in ISA → flag them]
  [Any suggested actions based on allocation]
```

4. Flag any data fields containing "REPLACE_WITH" as needing setup.

## Updating Data
User can say "update [account] balance to £X,XXX" → update `data/portfolio.json` and confirm.
Always update `last_updated` on save.
