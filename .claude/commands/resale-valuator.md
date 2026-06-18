# Resale Valuator

Get a realistic resale price for studio equipment by searching current eBay sold listings.

## Data File
Optionally reads `data/assets.json` to pull item details by asset ID.

## Instructions

The user will either:
- Name a specific piece of kit: `/resale-valuator SSL 4000 G Series`
- Provide an asset ID: `/resale-valuator ASSET-001`
- Ask generally: `/resale-valuator`

### Step 1 — Identify the item
If an asset ID is given, load `data/assets.json` and find that item.
If a name is given, use it directly.
If nothing given, ask: "Which piece of kit do you want to value?"

### Step 2 — Research current market
Search the web for:
- `site:ebay.co.uk "[make] [model]" sold`
- `"[make] [model]" used price UK`
- Recent forum discussions or dealer prices

Look for:
- eBay UK completed/sold listings (most reliable)
- Reverb.com sold prices
- Gear4Music, Thomann, or dealers for new price (as reference ceiling)

### Step 3 — Output the valuation

```
RESALE VALUATION — [today's date]
Item: [Make] [Model]
══════════════════════════════════════════════════

  MARKET DATA
  ─────────────────────────────────────────────
  Source               | Price Range     | Notes
  eBay UK (sold)       | £X,XXX–£X,XXX   | Last 90 days, [N] sales
  Reverb.com           | £X,XXX–£X,XXX   | [N] sold listings
  Dealer (used)        | £X,XXX          | [Source name]
  New (retail)         | £X,XXX          | [Source name]

  REALISTIC RESALE ESTIMATE
  ─────────────────────────────────────────────
  Private sale (eBay / Gumtree):  £X,XXX  ← use this for insurance replacement
  Part-exchange (dealer):         £X,XXX  (typically 40–60% of retail)
  Quick sale (fast, low price):   £X,XXX

  CONDITION ADJUSTMENT (if known):
  Your unit is: [Condition from assets.json]
  Mint: +15% | Excellent: +0% | Good: -10% | Fair: -25% | Poor: -40%
  Adjusted estimate: £X,XXX

  RECOMMENDATION:
  → For insurance purposes, declare at: £X,XXX (private sale value or replacement cost)
  → Update data/assets.json? [Yes/No — ask user]
```

### Step 4 — Offer to update asset register
Ask: "Do you want me to update the market value for this item in the asset register?"
If yes, update `data/assets.json` with the new current_market_value and today's date.
