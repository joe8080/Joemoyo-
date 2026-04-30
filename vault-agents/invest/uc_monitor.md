# Sub-task: uc_monitor

**Inputs:** none (uses latest snapshots).
**Mode:** advise-only — surfaces banding and risk; does not write
unless approved.

## Steps

### 1. Resolve threshold + ringfencing rules
```sql
SELECT rule_name, rule_text
FROM agent_rules
WHERE active = true
  AND rule_name IN ('uc_check', 'isa_first', 'no_portfolio_withdrawal');
```
If `uc_check` is not present → refuse and ask the operator to add it.
Do **not** fall back to hardcoded thresholds.

### 2. Compute assessable capital
- `holdings_value_total = SUM(latest holdings.current_value_gbp)`.
- `cash_savings = latest net_worth_snapshots.cash_savings_gbp`
  (or whichever column the snapshot uses — confirm at first run).
- `assessable = holdings_value_total + cash_savings - SUM(ringfenced amounts from agent_rules)`.

### 3. Banding (against thresholds resolved from `uc_check.rule_text`)
- `safe`        — below the lower disregard threshold
- `tariff_zone` — between lower and upper threshold (every band step
  costs UC at the rate stated in the rule)
- `at_risk`    — within the operator-defined warning margin of upper
- `over_cliff` — at or above the upper threshold

For the `tariff_zone` band, compute the projected monthly UC reduction
using the increment value from the rule (do not hardcode any £/step
figure in this file).

### 4. Output (advise envelope)
```
UC POSITION SNAPSHOT  (date: <today>)
- assessable_capital:       £<x>
- band:                     <safe|tariff_zone|at_risk|over_cliff>
- monthly_uc_impact:        £<x>/month (zero if safe)
- distance_to_next_band:    £<x>
- ringfenced excluded:      <list of rule_names>

RISK FLAGS
- <flag if any>
```

### 5. No DB write
This sub-task does not write to holdings or benefits_status.
It may write **one** `decision_log` row summarising the snapshot.

## When to escalate
- Any move from `safe` → `tariff_zone` or higher → flag with
  Citizens Advice prompt.
- Any state of `over_cliff` → CRITICAL — block all subsequent invest
  proposals until resolved.
