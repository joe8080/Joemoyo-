# JISA Tracker

Monitor Andre and Ameera's JISA balances, track contribution gaps, and calculate equalisation amounts.

## Data File
Read from and write to `data/jisa.json` in the project root.

## Instructions

1. **Load** `data/jisa.json`
2. **Calculate for each child:**
   - Total JISA balance (sum across all accounts)
   - JISA allowance used this tax year
   - JISA allowance remaining (£9,000 − contributed_this_year)
   - Age and years until the JISA matures (at 18)
3. **Output the dashboard:**

```
JISA TRACKER — [today's date]
Tax Year: [tax_year]  |  JISA allowance per child: £9,000
══════════════════════════════════════════════════════════

  ANDRE
  ─────────────────────────────────────────────────────
  DOB: [dob]  |  Age: [X]  |  Matures: [Year]  |  [N] years to go
  
  Account                          | Provider    | Balance
  Stocks & Shares JISA             | [Provider]  | £XX,XXX
  ─────────────────────────────────────────────────────
  Total balance:                   | £XX,XXX
  Contributed this year:           | £X,XXX
  Allowance remaining:             | £X,XXX  ████████░░  XX%
  
  AMEERA
  ─────────────────────────────────────────────────────
  DOB: [dob]  |  Age: [X]  |  Matures: [Year]  |  [N] years to go
  
  Account                          | Provider    | Balance
  Stocks & Shares JISA             | [Provider]  | £XX,XXX
  ─────────────────────────────────────────────────────
  Total balance:                   | £XX,XXX
  Contributed this year:           | £X,XXX
  Allowance remaining:             | £X,XXX  ████████░░  XX%

  EQUALISATION
  ─────────────────────────────────────────────────────
  Andre total:   £XX,XXX
  Ameera total:  £XX,XXX
  Difference:    £XXX  ([Name] is ahead by [X]%)
  
  [If difference > 10%]:
  ⚠️  Gap is over 10% — to equalise, add £XXX to [Name]'s JISA
  [If within 10%]:
  ✅ Balances are within 10% — well equalised

  COMBINED TOTALS
  ─────────────────────────────────────────────────────
  Combined JISA balance:           £XX,XXX
  Combined allowance remaining:    £XX,XXX
  Combined allowance used:         £XX,XXX  of £18,000

  CONTRIBUTION ALERTS:
  [If significant allowance unused and we're within 60 days of April 5]:
  ⚠️  £X,XXX combined JISA allowance still unused — deadline: April 5
```

4. Equalisation target from `data/jisa.json` `equalisation_target` field.
5. If any data contains "REPLACE_WITH", flag setup required.

## Updating Data
- "Andre's JISA is now £X,XXX" → update balance
- "I contributed £X to Ameera's JISA" → update contributed_this_year and recalculate remaining
- Always update `last_updated` on save and recalculate allowance_remaining automatically.
