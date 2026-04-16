# Bed-and-ISA Planner

Run through the annual bed-and-ISA decision: which GIA holdings to move, CGT impact, ISA allowance remaining, and order of priority.

## Data Files
- `data/isa.json` — ISA allowance, GIA holdings, CGT position
- `data/portfolio.json` — portfolio balances

## Instructions

1. **Load** both data files
2. **Calculate the full bed-and-ISA picture:**
   - ISA allowance remaining this tax year
   - CGT headroom remaining (£3,000 allowance minus gains already realised)
   - For each GIA holding: unrealised gain/loss, whether it fits within CGT headroom, ISA capacity to absorb it
3. **Output the planner:**

```
BED-AND-ISA PLANNER — [today's date]
Tax Year: [tax_year]  |  [N] days until April 5
══════════════════════════════════════════════════════════

  YOUR POSITION
  ─────────────────────────────────────────────────────
  ISA allowance remaining:   £XX,XXX
  CGT headroom remaining:    £X,XXX  (of £3,000 annual)
  GIA total value:           £XX,XXX

  GIA HOLDINGS — BED-AND-ISA ANALYSIS
  ─────────────────────────────────────────────────────
  Priority | Ticker | Name           | Units | Value   | Gain    | CGT Due | Action
  ─────────────────────────────────────────────────────────────────────────────────
  1st      | VWRP   | FTSE All-World | XXX   | £XX,XXX | £X,XXX  | £0      | ✅ MOVE — within CGT limit
  2nd      | HMWO   | MSCI World     | XXX   | £XX,XXX | £X,XXX  | £XXX    | ⚠️ PARTIAL — move £X,XXX worth
  3rd      | CSPX   | S&P 500        | XXX   | £XX,XXX | -£XXX   | £0      | ✅ MOVE — no gain (loss harvest)

  RECOMMENDED ORDER OF PRIORITY:
  1. Move loss-making positions first (crystallise losses, reset cost basis, no CGT)
  2. Move positions with gains within CGT headroom
  3. Move remaining positions up to ISA allowance (accept CGT if valuable to shelter future growth)
  
  STEP-BY-STEP CHECKLIST:
  □ Check ISA allowance remaining (£XX,XXX)
  □ Check CGT gains already realised this year (£X,XXX)
  □ Sell [ticker] on [date] — wait T+2 settlement
  □ Buy same [ticker] inside ISA on [date]
  □ Note new cost basis for records
  □ Update data/isa.json with new contribution amount

  ESTIMATED CGT IMPACT:
  Moving all recommended holdings → total gain £X,XXX → CGT owed £0 (within allowance)
  
  [If over allowance]:
  ⚠️  Moving all GIA would realise £X,XXX gain — £X,XXX over CGT allowance
  → Consider spreading over two tax years
```

4. Prioritisation logic:
   - Priority 1: Holdings at a loss (no CGT, free to move)
   - Priority 2: Holdings with smallest gain (fits within headroom)
   - Priority 3: Holdings with largest potential future growth (worth the CGT to shelter)

5. Note the T+2 settlement window and warn if close to April 5 (need to sell by April 3 to settle in time).
