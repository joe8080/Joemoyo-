# Sub-task: sync_portfolio

**Inputs:** path to T212 CSV export (or in-memory CSV string).
**Mode:** advise-only. Computes a proposed diff; the operator approves
before any DB write.

## Steps

### 1. Parse CSV
- Standard T212 export columns expected. If column shape differs,
  surface the diff and refuse to proceed.

### 2. Compute proposed `holdings` rows
For `snapshot_date = CURRENT_DATE`, build one row per ticker held.
Compare against the latest existing snapshot:
```sql
WITH latest AS (
  SELECT MAX(snapshot_date) AS d FROM holdings
)
SELECT * FROM holdings WHERE snapshot_date = (SELECT d FROM latest);
```
Produce a per-ticker diff: `{ticker, old_qty, new_qty, old_value, new_value}`.

### 3. Recompute proposed `portfolio_summary` and `portfolio_buckets`
- Total `current_value_gbp = SUM(holdings.current_value_gbp)`.
- Bucket allocations as defined in `portfolio_buckets` (AI / Infra /
  Dividend / Cash etc.).

### 4. Apply pre-checks (see invest/CLAUDE.md "Hard rules")
Run all 8 hard-rule checks against the **proposed** end-state, not the
current state. Output an advise envelope.

### 5. Wait for `confirm`
Do not write to `holdings`, `portfolio_summary`, or `portfolio_buckets`
until the operator types `confirm`.

### 6. On confirm
- INSERT new `holdings` rows for `snapshot_date = today` (do not
  overwrite older snapshots — this table is append-only by design).
- UPSERT `portfolio_summary` for today.
- UPSERT `portfolio_buckets` for today.
- Trigger `uc_monitor.md` and `goal_progress.md` as follow-ups.
- Write a single `decision_log` entry covering the sync.

## On cancel / edit
- Do not write anything.
- Log a `decision_log` entry with `status='cancelled'` (no diff).
