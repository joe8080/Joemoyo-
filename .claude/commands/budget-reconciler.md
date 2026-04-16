# Budget Reconciler

Reconcile a bank statement CSV against monthly budget targets by category. Outputs a red/amber/green table.

## Data File
Budget targets: `data/budget.json`

## Instructions

The user will either:
- Paste CSV transaction data directly into the chat, OR
- Provide a file path to a CSV export (Monzo or Starling format)

### Step 1 — Get the data
If no CSV is provided, ask: "Please paste your bank statement CSV or provide the file path."

### Step 2 — Parse transactions
Handle these common CSV formats:

**Monzo:**
`Date, Time, Type, Name, Emoji, Category, Amount, Currency, Local amount, Local currency, Notes and #tags, Address, Receipt, Description, Category split, Money Out, Money In`

**Starling:**
`Date, Counter Party, Reference, Type, Amount (GBP), Balance (GBP), Spending Category`

Map each transaction to a budget category from `data/budget.json`. Use smart matching:
- Housing: rent, mortgage, landlord
- Food & Groceries: supermarket names, Tesco, Asda, Sainsburys, Lidl, Aldi, Just Eat, Deliveroo
- Transport: Uber, TfL, petrol, parking, RAC, AA
- Subscriptions: Netflix, Spotify, Amazon Prime, Disney+, etc.
- Children: school, uniform, childcare

### Step 3 — Output reconciliation table

```
BUDGET RECONCILER — [Month Year]
══════════════════════════════════════════════════════════

  Category                | Budget   | Actual   | Variance  | Status
  ─────────────────────────────────────────────────────────────────────
  Housing                 | £XXX     | £XXX     | £0        | ✅ GREEN
  Council Tax             | £XXX     | £XXX     | +£XX      | ✅ GREEN
  Gas & Electric          | £XXX     | £XXX     | +£XX      | ✅ GREEN
  Food & Groceries        | £XXX     | £XXX     | -£XX      | ⚠️  AMBER (over by X%)
  Transport               | £XXX     | £XXX     | -£XX      | 🔴 RED (over by X%)
  Children                | £XXX     | £XXX     | £0        | ✅ GREEN
  Subscriptions           | £XXX     | £XXX     | +£XX      | ✅ GREEN
  Investing               | £XXX     | £XXX     | £0        | ✅ GREEN
  Sinking Funds           | £XXX     | £XXX     | £0        | ✅ GREEN
  Personal / Discretionary| £XXX     | £XXX     | -£XX      | 🔴 RED (over by X%)
  ─────────────────────────────────────────────────────────────────────
  TOTAL SPENDING          | £X,XXX   | £X,XXX   | -£XXX     | ⚠️  AMBER
  
  UNCATEGORISED (review manually):
  [List any transactions that couldn't be mapped with their amounts]

SUMMARY:
  Total income this month:   £X,XXX
  Total spending:            £X,XXX
  Surplus / Deficit:         £XXX

GREEN categories (on/under budget): X
AMBER categories (up to 20% over):  X
RED categories (20%+ over):         X
```

### Status thresholds (from budget.json variance_thresholds):
- GREEN: within budget or under
- AMBER: 1–20% over budget
- RED: 20%+ over budget

### Step 4 — Insights
After the table, add 3 bullet point observations:
- Biggest overspend category
- Biggest saving category
- One actionable suggestion to improve next month
