# Sub-task: sync_pipeline

**Inputs:** none (full sweep) OR `content_id` (single item refresh)

## Steps
1. Fetch active pipeline items:
   ```sql
   SELECT id, title, content_type, topic, stage, platform, verified,
          publish_date, updated_at
   FROM ogx_content_pipeline
   WHERE stage NOT IN ('monetise', 'archived')
   ORDER BY updated_at DESC;
   ```
2. Compute flags per item:
   - `STUCK` — `updated_at < now() - interval '14 days'` AND `stage != 'publish'`
   - `READY_BUT_UNVERIFIED` — `stage = 'ready_to_publish'` AND `verified = false`
   - `MISSING_DATE` — `stage = 'publish'` AND `publish_date IS NULL`
3. For `READY_BUT_UNVERIFIED`:
   - Fetch `ogx_research_claims WHERE :content_id = ANY(content_ids)`
   - Count `verified = true` vs `verified = false`
   - Surface unverified count in the report
4. Return a summary: `items_in_progress`, `items_blocked`, `items_ready`,
   plus per-item flags.

## Writing back (execute mode)
- May `UPDATE updated_at` to mark a "touched" sweep — but **do not**
  modify `stage` automatically. Stage transitions require a human or
  a different sub-task.
- May INSERT new pipeline items if invoked with that intent
  (`intent='create_pipeline_item'`).

## Decision log
One entry per sweep:
`{"agent":"ogx","intent":"sync_pipeline","totals":{...},"flags":{...}}`.
