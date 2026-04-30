# Sub-task: goal_progress

**Inputs:** none (sweeps active goals).
**Mode:** advise-only.

## Steps

### 1. Load active goals
```sql
SELECT id, name, category, target_value_gbp, current_value_gbp,
       progress_pct, status, updated_at
FROM goals
WHERE status = 'active'
ORDER BY category, name;
```

### 2. Recompute current_value for portfolio-linked goals
For any `category = 'portfolio'` goal: pull latest
`portfolio_summary.total_value_gbp` and propose new `current_value_gbp`.

For other categories (e.g. `cash_reserve`, `sinking_fund`): pull from
the relevant source table (`net_worth_snapshots`, `sinking_funds`).

### 3. Recompute security_ladder
```sql
SELECT id, level, name, status, criteria, completed_at
FROM security_ladder
ORDER BY level ASC;
```
For each `status='in_progress'` level whose criteria are now met,
propose moving to `status='completed'` with `completed_at = now()`.

### 4. Milestone detection
Check each goal's new `progress_pct` against milestone bands
(10/15/25/50/75/100). If a milestone has just been crossed, surface
in the advise envelope.

### 5. Advise envelope
```
GOALS DIFF
----------
<id>  <name>            <old_pct%> → <new_pct%>     [milestone? yes/no]
...

LADDER DIFF
-----------
Level <n> <name>: in_progress → completed   [criteria: ...]
...

To apply, reply: confirm
To cancel, reply: cancel
```

### 6. On confirm
- UPDATE matched `goals.current_value_gbp` and `progress_pct`.
- UPDATE matched `security_ladder` rows.
- One `decision_log` entry for the sweep.

## No-op rule
If no goals or ladder rows changed beyond rounding, do not write
`decision_log`. Surface "no change since <last sweep date>".
