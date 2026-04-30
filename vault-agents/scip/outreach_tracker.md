# Sub-task: outreach_tracker

**Inputs:** none (full sweep) OR `outreach_id` (single refresh).
**Mode:** advise-only.

## Steps

### 1. Sweep open outreach
```sql
SELECT id, contact_name, organisation, council, role, outreach_type,
       status, outreach_date, last_update, next_action, next_action_date,
       led_by
FROM scip_outreach
WHERE status NOT IN ('closed')
ORDER BY next_action_date NULLS LAST;
```

### 2. Compute flags per row
- `STALE`        — `last_update < now() - interval '21 days'`
- `OVERDUE`      — `next_action_date IS NOT NULL AND
                   next_action_date < CURRENT_DATE`
- `FOI_AT_RISK`  — `outreach_type = 'foi_request' AND
                   next_action_date <= CURRENT_DATE + 3`
- `PENDING_LEAD` — `led_by IN (SELECT id FROM contacts
                   WHERE status = 'pending')`

### 3. Pipeline review (when invoked with `intent='full_sweep'`)
```sql
SELECT id, opportunity_name, stage, council, estimated_value_gbp,
       probability_pct, expected_close_date, last_update
FROM scip_pipeline
WHERE stage NOT IN ('closed_won', 'closed_lost');
```
Per-row flag: `STAGNANT` if `last_update < now() - interval '14 days'`.

### 4. Output
```
OUTREACH SUMMARY  (date: <today>)
- open_count:       <n>
- stale (>21d):     <n>
- overdue:          <n>
- foi_at_risk:      <n>
- pending_lead:     <n>

PIPELINE SUMMARY
- active_count:     <n>
- stagnant (>14d):  <n>
- weighted_value:   £<sum(value*probability)>

PER-ITEM FLAGS
<list>
```

### 5. No write by default
This is a read-only summariser. To act on a flagged item, invoke
`log_intelligence.md` (for new intel) or use the orchestrator with
`intent='update_outreach'` which routes back here in proposal mode.

### 6. Decision log
One entry per sweep iff any flag is non-zero. No log on a clean sweep.
