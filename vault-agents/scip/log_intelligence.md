# Sub-task: log_intelligence

**Inputs:** `title`, `summary`, `source`, `source_type`, `council`,
optional `category`, optional `actionable` (default false).

**Mode:** advise-only.

## Steps
1. Validate inputs:
   - `source_type` ∈ {`council_doc`, `meeting`, `public_data`, `media`}
   - `category` ∈ {`housing`, `transport`, `planning`, `social_care`, `other`}
   - `council` ∈ {`Worthing`, `Adur`, `West Sussex`, `Other`}
2. Duplicate detection:
   ```sql
   SELECT id FROM scip_intelligence
   WHERE title = :title AND source = :source
   LIMIT 1;
   ```
   If a row exists, surface `DUP(existing_id)` and refuse to insert.
3. If `actionable = true`:
   - Build a proposed `scip_pipeline` insert (linked via
     `scip_intelligence.pipeline_id` after both rows are created).
   - Show both rows in the advise envelope.
4. Output advise envelope with both proposed inserts (if applicable).

## On confirm
- INSERT into `scip_intelligence`.
- If actionable: INSERT into `scip_pipeline`, then UPDATE
  `scip_intelligence.pipeline_id`.
- One `decision_log` entry covering both inserts.
