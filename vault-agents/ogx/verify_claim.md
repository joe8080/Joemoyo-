# Sub-task: verify_claim

**Inputs:** `topic` (text), `claim` (text), optional `content_id` (uuid)

## Steps
1. Look up existing record:
   ```sql
   SELECT id, verified, source, source_type, confidence_level, verified_date
   FROM ogx_research_claims
   WHERE topic = :topic AND claim = :claim
   LIMIT 1;
   ```
2. If no row → status `UNVERIFIED`. Insert a stub row with
   `verified = false`. Return: `{"status":"unverified","claim_id":...}`.
3. If row exists with `verified = true` AND `source IS NOT NULL`:
   - If content is current-affairs / time-sensitive AND
     `verified_date < now() - interval '18 months'` → status `STALE`,
     surface for re-verification.
   - Otherwise return `{"status":"verified","source":...,"confidence":...}`.
4. If row exists with `verified = false` → return `{"status":"pending"}`
   with the existing notes.

## Writing back (execute mode)
- May UPDATE `verified`, `source`, `source_type`, `confidence_level`,
  `verified_date`, `notes` on a row the agent just researched.
- May INSERT new claims.
- Must NOT delete claims.

## Source taxonomy (`source_type` values)
- `academic` — peer-reviewed paper, university press
- `documentary` — broadcast / streaming long-form
- `primary` — original document, archive, government record
- `secondary` — reputable journalism, established history site

## Confidence
- `high` — multiple primary or academic sources agree
- `medium` — one primary or two secondary sources
- `low` — single secondary source, or single primary contested elsewhere

Anything below `medium` blocks publish (see `publish_checklist.md`).

## Decision log
On any insert/update: log
`{"agent":"ogx","intent":"verify_claim","claim_id":...,"result":<status>}`.
