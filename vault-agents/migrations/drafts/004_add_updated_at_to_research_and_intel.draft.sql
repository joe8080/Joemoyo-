-- ============================================================
-- DRAFT 4 / 4 — Add updated_at + trigger to research/intel tables
-- ============================================================
-- Project:   qxwfrsoztfddwicqtuar  (finance-chief / The Vault)
-- Status:    DRAFT — review before applying
-- Priority:  LOW (non-blocking; queued follow-up to Draft 3)
-- Apply via: mcp__supabase-vault__apply_migration
-- Suggested migration name: add_updated_at_to_research_and_intel
-- ============================================================
--
-- WHY
-- ---
-- Draft 3 added `set_updated_at` triggers to the 3 new tables that
-- already had an `updated_at` column. Two new tables don't:
--   - public.ogx_research_claims    → only created_at + verified_date
--   - public.scip_intelligence      → only created_at + entry_date
--
-- Without `updated_at`, the agents currently fall back to
-- domain-specific dates (verified_date / entry_date) for staleness.
-- That works for the originally-conceived flow but breaks if you
-- want a uniform "last-touched" signal across all OGX/SCIP tables.
-- This migration adds that uniform signal.
--
-- DECISION
-- --------
-- ADD COLUMN with NOT NULL DEFAULT now() (pre-fills existing rows
-- to creation time, which is correct for a "last-touched" semantic
-- since they haven't been touched since insert). The two affected
-- tables currently have 0 rows, so the backfill is no-op anyway.
--
-- Then attach the same `set_updated_at` BEFORE UPDATE trigger
-- pattern from Draft 3.
--
-- TABLES AFFECTED
-- ---------------
--   public.ogx_research_claims    ALTER TABLE ... ADD COLUMN updated_at
--                                 + CREATE TRIGGER set_updated_at
--   public.scip_intelligence      ALTER TABLE ... ADD COLUMN updated_at
--                                 + CREATE TRIGGER set_updated_at
--
-- BLAST RADIUS
-- ------------
--   - Existing rows: pre-filled with now() at the moment of ALTER
--   - SELECTs: previously returned N columns, now return N+1.
--     Any agent using `SELECT *` will see the new column; agents
--     using explicit column lists are unaffected. The CLAUDE.md
--     guidance says prefer explicit column lists — adhere.
--   - INSERTs without explicit updated_at: default to now() — fine.
--   - UPDATEs: now refresh updated_at automatically via trigger.
--
-- DEPENDENCIES
-- ------------
-- Requires the moddatetime extension installed by Draft 3
-- (extensions.moddatetime). Will fail with a clear error if Draft 3
-- has not been applied first.
--
-- Idempotent: ADD COLUMN IF NOT EXISTS, DROP TRIGGER IF EXISTS
-- before each CREATE TRIGGER.
--
-- Run inside a single transaction.

BEGIN;

-- ------------------------------------------------------------
-- Pre-flight: confirm moddatetime is installed
-- ------------------------------------------------------------
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_extension
    WHERE extname = 'moddatetime'
  ) THEN
    RAISE EXCEPTION
      'moddatetime extension not installed. Apply Draft 3 first.';
  END IF;
END $$;


-- ------------------------------------------------------------
-- 1. ogx_research_claims  — add column + trigger
-- ------------------------------------------------------------
ALTER TABLE public.ogx_research_claims
  ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

DROP TRIGGER IF EXISTS set_updated_at ON public.ogx_research_claims;
CREATE TRIGGER set_updated_at
  BEFORE UPDATE ON public.ogx_research_claims
  FOR EACH ROW
  EXECUTE FUNCTION extensions.moddatetime(updated_at);


-- ------------------------------------------------------------
-- 2. scip_intelligence  — add column + trigger
-- ------------------------------------------------------------
ALTER TABLE public.scip_intelligence
  ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

DROP TRIGGER IF EXISTS set_updated_at ON public.scip_intelligence;
CREATE TRIGGER set_updated_at
  BEFORE UPDATE ON public.scip_intelligence
  FOR EACH ROW
  EXECUTE FUNCTION extensions.moddatetime(updated_at);

COMMIT;


-- ============================================================
-- VERIFICATION (run after apply)
-- ============================================================
-- 1. Both columns exist:
-- SELECT table_name, column_name, data_type, is_nullable, column_default
-- FROM information_schema.columns
-- WHERE table_schema = 'public'
--   AND table_name IN ('ogx_research_claims','scip_intelligence')
--   AND column_name = 'updated_at'
-- ORDER BY table_name;
--
-- 2. Both triggers in place:
-- SELECT event_object_table AS table_name, trigger_name, event_manipulation, action_timing
-- FROM information_schema.triggers
-- WHERE event_object_schema = 'public'
--   AND trigger_name = 'set_updated_at'
-- ORDER BY event_object_table;
-- After all 3+4 are applied, expect 5 rows: ogx_content_pipeline,
-- ogx_research_claims, scip_intelligence, scip_outreach, scip_pipeline.
--
-- 3. Functional smoke test (throwaway row):
-- INSERT INTO public.ogx_research_claims (topic, claim, verified)
--   VALUES ('test_trigger','test_claim',false)
--   RETURNING id, created_at, updated_at;
-- -- created_at and updated_at should equal at insert.
-- UPDATE public.ogx_research_claims SET notes = 'touched'
--   WHERE topic = 'test_trigger';
-- -- updated_at should now be > created_at.
-- DELETE FROM public.ogx_research_claims WHERE topic = 'test_trigger';


-- ============================================================
-- ROLLBACK
-- ============================================================
-- BEGIN;
-- DROP TRIGGER IF EXISTS set_updated_at ON public.ogx_research_claims;
-- DROP TRIGGER IF EXISTS set_updated_at ON public.scip_intelligence;
-- ALTER TABLE public.ogx_research_claims  DROP COLUMN IF EXISTS updated_at;
-- ALTER TABLE public.scip_intelligence    DROP COLUMN IF EXISTS updated_at;
-- COMMIT;


-- ============================================================
-- AGENT IMPACT (informational — no code change required here)
-- ============================================================
-- After applying, the SCIP CLAUDE.md staleness predicate for
-- scip_intelligence can use either updated_at OR entry_date —
-- updated_at gives "last-touched"; entry_date gives "first-recorded".
-- Same for ogx_research_claims (updated_at vs verified_date).
-- The existing CLAUDE.md files use the domain-specific dates.
-- A follow-up commit to vault-agents/{ogx,scip}/CLAUDE.md can switch
-- the predicates to updated_at if you prefer uniform semantics.
