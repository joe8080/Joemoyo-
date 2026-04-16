# Sinking Fund Manager

Track all sinking fund pots, calculate monthly contributions needed to hit each target, and flag underfunded pots.

## Data File
Read from and write to `data/sinking-funds.json` in the project root.

## Instructions

1. **Load** `data/sinking-funds.json`
2. **For each pot**, calculate:
   - Amount remaining to target (target − current_balance)
   - Months remaining until deadline (from today's date)
   - Required monthly contribution to hit target on time
   - Whether current monthly_contribution is sufficient
3. **Output the dashboard:**

```
SINKING FUND MANAGER — [today's date]
══════════════════════════════════════════════════════════

  Pot               | Target  | Balance | Monthly Needed | Contributing | Status      | Deadline
  ────────────────────────────────────────────────────────────────────────────────────────────────
  Christmas         | £800    | £XXX    | £XXX           | £XXX         | ✅ On track  | 1 Dec 2026
  Birthdays         | £500    | £XXX    | £XXX           | £XXX         | ⚠️  Low      | Rolling
  School Uniforms   | £300    | £XXX    | £XXX           | £XXX         | 🔴 Behind    | 1 Aug 2026
  School Trips      | £400    | £XXX    | £XXX           | £XXX         | ✅ On track  | Rolling
  Car Maintenance   | £600    | £XXX    | £XXX           | £XXX         | ✅ On track  | Rolling
  Holiday           | £1,500  | £XXX    | £XXX           | £XXX         | ⚠️  Low      | [Date]
  ────────────────────────────────────────────────────────────────────────────────────────────────
  TOTAL             | £X,XXX  | £X,XXX  | £XXX/mo needed | £XXX/mo set  |

ALERTS:
  🔴 [Pot name] is behind — needs £XXX/month but only £XXX set. Shortfall: £XXX.
  ⚠️  [Pot name] contribution is low — increase by £XX/month to stay on track.

FULLY FUNDED:
  ✅ [Pot name] — on track to hit £XXX by [deadline]
```

4. **Status thresholds:**
   - GREEN ✅: Contributing enough to hit target on time (within 5%)
   - AMBER ⚠️: Contributing but 5–20% short of what's needed
   - RED 🔴: Contributing less than 80% of what's needed, or not contributing at all

5. **Rolling pots** (no fixed deadline): show current balance vs target and % funded.

## Updating Data
- "Update [pot] balance to £X" → update current_balance
- "Add a new pot called [name] with target £X by [date]" → add new pot entry
- "Change [pot] monthly contribution to £X" → update monthly_contribution
Always update `last_updated` on save.
