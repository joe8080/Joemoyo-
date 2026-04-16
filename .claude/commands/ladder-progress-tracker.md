# Ladder Progress Tracker

Full Financial Security Ladder status update with estimated months to each next level based on current cash flow.

## Data File
Read from `data/ladder.json` in the project root.

## Instructions

1. **Load** `data/ladder.json`
2. **Identify current level** from `current_level` field
3. **For each level**, calculate:
   - Amount remaining to complete it (target minus current)
   - Months to complete at current `monthly_surplus`
   - Estimated completion date
4. **Output a formatted progress report:**

```
FINANCIAL SECURITY LADDER — [today's date]
══════════════════════════════════════════
Monthly surplus available: £XXX

  Lvl | Name                        | Progress          | Status      | ETA
  ────────────────────────────────────────────────────────────────────────────
  1   | Zero Debt                   | ████████████ 100% | ✅ COMPLETE  | Apr 2025
  2   | Emergency Fund — 1 Month    | ████████░░░░  67% | 🔄 CURRENT   | 2 months
  3   | Emergency Fund — 3 Months   | ░░░░░░░░░░░░   0% | ⏳ PENDING   | 8 months
  4   | Emergency Fund — 6 Months   | ░░░░░░░░░░░░   0% | ⏳ PENDING   | 18 months
  5   | First ISA Year              | ░░░░░░░░░░░░   0% | ⏳ PENDING   | 24 months
  ...

CURRENT FOCUS:
  Level X — [Name]
  Target: £X,XXX | Current: £X,XXX | Remaining: £XXX
  At £XXX/month → complete in X months (Month YYYY)

NEXT MILESTONE:
  Level X+1 — [Name] — estimated [Month YYYY]

PATH TO £1M:
  At current surplus → [X years Y months] total journey
  Estimated financial independence: [Year]
```

5. Draw progress bars using █ and░ characters (12 chars wide, scaled to %).
6. If `monthly_surplus` is set to REPLACE_WITH, note that surplus needs setting and show targets without ETAs.
7. Celebrate any recently completed levels (completed_date within last 30 days).

## Updating Data
If the user provides updated balances or marks a level complete, update `data/ladder.json` and confirm.
To update monthly surplus: update the `monthly_surplus` field.
