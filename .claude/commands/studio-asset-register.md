# Studio Asset Register

Manage the full studio equipment inventory with insurance values, condition grades, and market values.

## Data File
Read from and write to `data/assets.json` in the project root.

## Commands

The user can say things like:
- `/studio-asset-register` — show full register
- `/studio-asset-register add` — add a new item (ask for details)
- `/studio-asset-register update [item]` — update an existing item
- `/studio-asset-register summary` — show summary totals by category
- `/studio-asset-register insurance` — output insurance-ready formatted list

## Instructions

### Default view — full register:

1. Load `data/assets.json`
2. Output a formatted register:

```
STUDIO ASSET REGISTER — [today's date]
Studio: [studio_name]
Insurer: [insurer] | Policy: [policy_number]
══════════════════════════════════════════════════════════════════

  ID        | Category    | Make & Model              | S/N         | Cond. | Purchase | Mkt Value | Insured
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  ASSET-001 | Console     | SSL 4000 G Series         | XXXXXXX     | Exc.  | £XX,XXX  | £XX,XXX   | £XX,XXX
  ...

  ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  TOTALS:   [N items]                                                        £XX,XXX    £XX,XXX    £XX,XXX
```

3. After the table show a **Category Breakdown:**
```
  Category Breakdown:
  Console .............. £XX,XXX  (X items)
  Microphone ........... £XX,XXX  (X items)
  ...
```

### Add item:
Ask the user for: Category, Make, Model, Serial Number (or "unknown"), Condition, Purchase date, Purchase price, Current market value, Insured value, Notes.
Assign the next ASSET-XXX ID automatically.
Add to `data/assets.json` and confirm.

### Insurance output:
Format as a clean list suitable for emailing to an insurer:

```
STUDIO EQUIPMENT SCHEDULE — [date]
[Studio Name]

Item | Description | Serial | Value
1    | SSL 4000 G Series Console | SN: XXXXXX | £XX,XXX
...

TOTAL DECLARED VALUE: £XX,XXX
```

## Notes
- Condition grades: Mint / Excellent / Good / Fair / Poor
- Market value = realistic current resale (not purchase price)
- Insured value should be replacement cost (typically higher than market)
- Update `last_updated` date whenever the register is modified
