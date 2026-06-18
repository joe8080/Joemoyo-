# Weekly Ops Brief

One command. Full picture. Portfolio status, ladder progress, benefit flags, sinking fund health, ISA position, and key actions for the week.

## Data Files
- `data/benefits.json`
- `data/ladder.json`
- `data/portfolio.json`
- `data/isa.json`
- `data/sinking-funds.json`
- `data/jisa.json`

## Instructions

Load all data files and produce the master weekly brief.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  WEEKLY OPS BRIEF — [Day, DD Month YYYY]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  BENEFITS  ─────────────────────────────────────────
  [List each benefit with next payment date and amount]
  Next payment: [Benefit] — £XXX on [Date] ([N] days)
  [Any overdue or flagged payments in RED]
  Monthly total (normalised): £X,XXX

  FINANCIAL LADDER  ──────────────────────────────────
  Current level: [N] — [Level Name]
  Progress: ████████░░  XX% (£X,XXX of £X,XXX)
  At £XXX/month → complete in [N] months ([Month Year])
  Next level: [N+1] — [Name] — [ETA]

  PORTFOLIO  ─────────────────────────────────────────
  Total portfolio: £XX,XXX  ([+/-X.X% vs last update if known])
  ISA: £XX,XXX  |  GIA: £XX,XXX  |  JISAs: £XX,XXX
  Progress to £1M: ██░░░░░░░░  X.X%

  ISA / TAX  ─────────────────────────────────────────
  Tax year: [tax_year]  |  [N] days to April 5
  ISA allowance used: £X,XXX of £20,000 (£X,XXX remaining)
  CGT headroom: £X,XXX remaining
  [Any bed-and-ISA actions needed — flag if urgent]

  SINKING FUNDS  ──────────────────────────────────────
  [Pots on track]: ✅ Christmas, Car Maintenance
  [Pots needing attention]: ⚠️  School Uniforms (behind £XX/mo)
  Total across all pots: £X,XXX of £X,XXX targets

  JISA  ──────────────────────────────────────────────
  Andre: £XX,XXX  |  Ameera: £XX,XXX  |  Combined: £XX,XXX
  [Any equalisation gap or allowance alerts]

  ─────────────────────────────────────────────────────
  THIS WEEK'S ACTIONS
  ─────────────────────────────────────────────────────
  [Compile a prioritised list of 3–5 actions based on all the above]
  □ [Action 1 — e.g. "PIP payment due Thursday — check bank by EOD"]
  □ [Action 2 — e.g. "Top up School Uniform pot by £XX to stay on track"]
  □ [Action 3 — e.g. "X days until April 5 — £X,XXX ISA allowance unused"]
  □ [Action 4 — e.g. "Update portfolio balances after market close Friday"]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Logic for Actions List
Generate actions in this priority order:
1. 🔴 RED: Any benefit overdue or not received
2. 🔴 RED: ISA deadline within 14 days with unused allowance
3. ⚠️ AMBER: Any sinking fund behind target
4. ⚠️ AMBER: JISA equalisation gap > 10%
5. ℹ️ INFO: Upcoming benefit payment within 3 days
6. ℹ️ INFO: Monthly portfolio update reminder (if last_updated > 7 days ago)

## Notes
- If any data file is missing or has REPLACE_WITH values, skip that section and note it as "NEEDS SETUP"
- Keep the brief tight — no padding, just the numbers and actions
- Run this once a week, ideally Monday morning
