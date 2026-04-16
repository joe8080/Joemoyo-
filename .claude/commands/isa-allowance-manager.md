# ISA Allowance Manager

Track annual ISA allowance usage, GIA holdings pending bed-and-ISA, CGT headroom, and countdown to April 5.

## Data File
Read from and write to `data/isa.json` in the project root.

## Instructions

1. **Load** `data/isa.json`
2. **Calculate key figures:**
   - ISA allowance remaining = 20,000 − contributed_this_year
   - CGT headroom remaining = annual_allowance − used_this_year
   - Days to April 5 tax year end (use today's date)
3. **Output the dashboard:**

```
ISA ALLOWANCE MANAGER — [today's date]
Tax Year: [tax_year]  |  Days to April 5: [N days]
══════════════════════════════════════════════════

  ISA ALLOWANCE
  ─────────────────────────────────────────────
  Annual allowance:          £20,000
  Contributed this year:     £X,XXX
  Remaining allowance:       £XX,XXX  ████░░░░░░ XX%
  
  Accounts:
  [Provider] ([type]) ......... £X,XXX balance | £X,XXX contributed

  CGT HEADROOM
  ─────────────────────────────────────────────
  Annual CGT allowance:      £3,000
  Gains realised this year:  £X,XXX
  Headroom remaining:        £X,XXX

  GIA HOLDINGS (bed-and-ISA candidates)
  ─────────────────────────────────────────────
  Ticker | Name              | Units | Gain/Loss | Within CGT limit?
  VWRP   | FTSE All-World    | XXX   | £X,XXX    | ✅ Yes / ⚠️ Partial
  ...

  RECOMMENDED ACTION:
  [If allowance remaining > 0 and we're within 60 days of April 5]:
  ⚠️  £X,XXX ISA allowance remaining — use it before [April 5 date]!
  
  [If GIA holdings can be moved within CGT limit]:
  → Recommend moving [ticker] to ISA (£X,XXX gain — within £X,XXX headroom)

  BED-AND-ISA QUEUE:
  [List any items in bed_and_isa_queue]
```

4. **Urgency levels:**
   - Green: >90 days to April 5 or full allowance used
   - Amber: 30-90 days remaining with unused allowance
   - Red: <30 days remaining with significant unused allowance

5. If any data contains "REPLACE_WITH", flag setup required.

## Updating Data
User can say "I contributed £X to ISA" → update contributed_this_year.
User can say "add [ticker] to bed-and-ISA queue" → add to bed_and_isa_queue array.
Always update `last_updated` on save.
