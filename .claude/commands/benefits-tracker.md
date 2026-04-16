# Benefits Tracker

Monitor your full benefit payment schedule, flag missed or late payments, and calculate upcoming payment dates.

## Data File
Read from `data/benefits.json` in the project root.

## Instructions

1. **Load** `data/benefits.json`
2. **Calculate upcoming payments** for each benefit:
   - For 4-weekly benefits: calculate the next 3 payment dates from today
   - For monthly benefits: calculate the next payment date
   - For weekly benefits: calculate the next 4 payment dates
3. **Flag any alerts:**
   - Payments due within the next 3 days → mark as UPCOMING (amber)
   - Payments that were due in the last 3 days with no update → mark as OVERDUE CHECK (red)
   - Any benefit with amount showing as REPLACE_WITH → mark as NEEDS SETUP (grey)
4. **Output a formatted table:**

```
BENEFITS PAYMENT TRACKER — [today's date]
══════════════════════════════════════════

  Benefit         | Amount   | Frequency | Next Payment   | Status
  ─────────────────────────────────────────────────────────────────
  PIP             | £XXX.XX  | 4-weekly  | DD Mon YYYY    | ✅ On track
  UC              | £XXX.XX  | Monthly   | DD Mon YYYY    | ✅ On track
  DLA (Name)      | £XXX.XX  | 4-weekly  | DD Mon YYYY    | ⚠️  Due in 2 days
  Child Benefit   | £XXX.XX  | 4-weekly  | DD Mon YYYY    | ✅ On track
  CA              | £XXX.XX  | Weekly    | DD Mon YYYY    | ✅ On track
  ─────────────────────────────────────────────────────────────────
  TOTAL MONTHLY   | £X,XXX.XX (normalised to monthly equivalent)

UPCOMING 30 DAYS:
  [List each payment with date and amount]

ALERTS:
  [List any red/amber flags]
```

5. **Normalise to monthly** by converting:
   - 4-weekly payments: multiply by 13 then divide by 12
   - Weekly payments: multiply by 52 then divide by 12

6. If any data fields contain "REPLACE_WITH", output a **SETUP REQUIRED** section at the bottom listing which fields need filling in `data/benefits.json`.

## Updating Data
If the user provides updated amounts, dates, or confirms a payment was received, update `data/benefits.json` accordingly and confirm the change.
