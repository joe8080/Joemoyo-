# Sub-task: publish_checklist

**Inputs:** `content_id` (uuid)

## Block-or-pass gate
Approve publish only if **all** of:
1. `ogx_content_pipeline.stage IN ('verify','ready_to_publish')`
2. `ogx_content_pipeline.verified = true`
3. Every claim referenced by this content has `verified = true`
   AND `confidence_level IN ('medium','high')`
4. For current-affairs topics: every claim's `verified_date >=
   now() - interval '18 months'`
5. `script_ref IS NOT NULL`
6. `seo_keywords` is non-empty
7. `publish_date` is set AND `>= CURRENT_DATE`

If any check fails: return `{"approved": false, "blocking": [...]}`.
If all pass: return `{"approved": true}`.

## On approval (execute mode)
- May UPDATE `stage = 'publish'`.
- Insert a `decision_log` entry:
  `{"agent":"ogx","intent":"publish_approved","content_id":...,"checks_passed":[...]}`.
- Do **not** trigger any external publish action from here. That's a
  separate side-effect step done by n8n / human.

## On block
- Insert `decision_log` with `status='blocked'` and the failing checks.
