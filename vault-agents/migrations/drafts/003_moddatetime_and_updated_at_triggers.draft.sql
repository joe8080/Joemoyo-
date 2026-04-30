-- ============================================================
-- DRAFT 3 / 3 — Install moddatetime + add updated_at triggers
--                + fix scip_outreach.led_by hardcoded default
-- ============================================================
-- Project:   qxwfrsoztfddwicqtuar  (finance-chief / The Vault)
-- Status:    DRAFT — review before applying
-- Priority:  LOW–MEDIUM (fixes spurious staleness flags + a
--                       data-hygiene issue around pending role)
-- Apply via: mcp__supabase-vault__apply_migration
-- Suggested migration name: enable_moddatetime_and_fix_defaults
-- ============================================================
--
-- WHY (three problems, one migration)
-- -----------------------------------
-- 1. `updated_at` columns on ogx_content_pipeline, scip_outreach,
--    scip_pipeline default to now() on INSERT but never refresh on
--    UPDATE — there are zero triggers in the public schema today
--    (verified via information_schema.triggers).
--    Effect: the agents' "stuck > 14 days" / "stale > 21 days" flags
--    will fire spuriously the moment they sweep an old row.
--
-- 2. moddatetime is the standard, supported PostgreSQL contrib module
--    Supabase exposes for exactly this purpose. Installing it is one
--    line; the alternative is hand-rolling a plpgsql function.
--
-- 3. scip_outreach.led_by has a schema-level DEFAULT 'Kelly'::text.
--    Per the SCIP CLAUDE.md spec, the public-facing-lead role is
--    "NOT YET CONFIRMED" — the schema currently bakes that assumption
--    into every direct INSERT (bypassing any agent-level "default to
--    NULL" intent). Drop the default; require explicit attribution.
--
-- COVERAGE NOTE — tables WITHOUT an updated_at column
-- ----------------------------------------------------
--   - ogx_research_claims  → has created_at + verified_date only
--   - scip_intelligence    → has created_at + entry_date only
-- These tables don't get triggers in this migration (no column to
-- update). The agent CLAUDE.md files use verified_date / entry_date
-- for staleness on these. Adding updated_at to them is a separate,
-- more invasive ALTER and not part of this fix. Flagged for review.
--
-- BLAST RADIUS
-- ------------
--   - moddatetime extension                        → install only, no row touched
--   - 3 BEFORE-UPDATE triggers                     → only fire on UPDATE; existing row reads are unaffected
--   - ALTER scip_outreach DROP DEFAULT             → existing rows unaffected; only future direct INSERTs change behaviour
--
-- Idempotent: CREATE EXTENSION IF NOT EXISTS, DROP TRIGGER IF EXISTS
-- before each CREATE TRIGGER, ALTER ... DROP DEFAULT (no-op if none).
--
-- Run inside a single transaction.

BEGIN;

-- ------------------------------------------------------------
-- 1. Install moddatetime extension
-- ------------------------------------------------------------
-- moddatetime is a PostgreSQL contrib module that ships a trigger
-- function `extensions.moddatetime(column_name)` to refresh a
-- timestamp column on UPDATE. Supabase recommends placing extensions
-- in the `extensions` schema (not `public`).
CREATE EXTENSION IF NOT EXISTS moddatetime SCHEMA extensions;


-- ------------------------------------------------------------
-- 2. Triggers on the 3 tables that have an updated_at column
-- ------------------------------------------------------------
-- Pattern: BEFORE UPDATE FOR EACH ROW EXECUTE FUNCTION moddatetime(updated_at)
-- The single argument names the column to refresh.

DROP TRIGGER IF EXISTS set_updated_at ON public.ogx_content_pipeline;
CREATE TRIGGER set_updated_at
  BEFORE UPDATE ON public.ogx_content_pipeline
  FOR EACH ROW
  EXECUTE FUNCTION extensions.moddatetime(updated_at);

DROP TRIGGER IF EXISTS set_updated_at ON public.scip_outreach;
CREATE TRIGGER set_updated_at
  BEFORE UPDATE ON public.scip_outreach
  FOR EACH ROW
  EXECUTE FUNCTION extensions.moddatetime(updated_at);

DROP TRIGGER IF EXISTS set_updated_at ON public.scip_pipeline;
CREATE TRIGGER set_updated_at
  BEFORE UPDATE ON public.scip_pipeline
  FOR EACH ROW
  EXECUTE FUNCTION extensions.moddatetime(updated_at);


-- ------------------------------------------------------------
-- 3. Drop the hardcoded 'Kelly'::text default on scip_outreach.led_by
-- ------------------------------------------------------------
-- The public-facing lead role is pending confirmation. Bake nothing
-- into the schema. The agent (or the operator) must attribute
-- explicitly on every INSERT.
ALTER TABLE public.scip_outreach
  ALTER COLUMN led_by DROP DEFAULT;

COMMIT;


-- ============================================================
-- VERIFICATION (run after apply)
-- ============================================================
-- 1. Extension installed:
-- SELECT name, installed_version, schema
-- FROM pg_available_extensions
-- WHERE name = 'moddatetime';
--
-- 2. Triggers in place:
-- SELECT event_object_table AS table_name, trigger_name, event_manipulation
-- FROM information_schema.triggers
-- WHERE event_object_schema = 'public'
--   AND trigger_name = 'set_updated_at'
-- ORDER BY event_object_table;
-- Expect 3 rows: ogx_content_pipeline, scip_outreach, scip_pipeline.
--
-- 3. led_by default cleared:
-- SELECT column_name, column_default
-- FROM information_schema.columns
-- WHERE table_schema = 'public'
--   AND table_name = 'scip_outreach'
--   AND column_name = 'led_by';
-- Expect column_default = NULL.
--
-- 4. Functional smoke test (run on a throwaway row):
-- INSERT INTO public.ogx_content_pipeline (title, content_type, topic)
--   VALUES ('test_trigger', 'test', 'test') RETURNING id, created_at, updated_at;
-- -- record the created_at and updated_at; they should be equal
-- -- now wait a second, then:
-- UPDATE public.ogx_content_pipeline SET notes = 'touched'
--   WHERE title = 'test_trigger'
--   RETURNING id, created_at, updated_at;
-- -- updated_at should now be > created_at
-- DELETE FROM public.ogx_content_pipeline WHERE title = 'test_trigger';


-- ============================================================
-- ROLLBACK
-- ============================================================
-- BEGIN;
-- DROP TRIGGER IF EXISTS set_updated_at ON public.ogx_content_pipeline;
-- DROP TRIGGER IF EXISTS set_updated_at ON public.scip_outreach;
-- DROP TRIGGER IF EXISTS set_updated_at ON public.scip_pipeline;
-- ALTER TABLE public.scip_outreach ALTER COLUMN led_by SET DEFAULT 'Kelly'::text;
-- DROP EXTENSION IF EXISTS moddatetime;  -- only if no other table uses it
-- COMMIT;


-- ============================================================
-- FOLLOW-UP ITEMS (NOT in this migration — flagged for your review)
-- ============================================================
-- A. ogx_research_claims and scip_intelligence have no updated_at
--    column. If you want auto-refresh on these too, that's a separate
--    ALTER + ADD COLUMN + trigger migration. Cost: changes the row
--    layout; trivial but worth a separate review window.
--
-- B. decision_log is meant to be append-only but currently has no
--    trigger or revoke preventing UPDATE / DELETE. Suggest a future
--    migration:
--        CREATE OR REPLACE FUNCTION public.deny_decision_log_mutation()
--        RETURNS trigger LANGUAGE plpgsql AS $$
--        BEGIN
--          RAISE EXCEPTION 'decision_log is append-only';
--        END $$;
--        CREATE TRIGGER deny_mutation
--          BEFORE UPDATE OR DELETE ON public.decision_log
--          FOR EACH ROW EXECUTE FUNCTION public.deny_decision_log_mutation();
--
-- C. Several tables have free-text columns that would benefit from
--    CHECK enums (scip_intelligence.category, scip_intelligence.source_type,
--    scip_intelligence.council, scip_outreach.outreach_type,
--    scip_outreach.status, scip_pipeline.stage). Currently the agent
--    CLAUDE.md files enforce these via validation. Belt-and-braces
--    approach: add CHECK constraints in DB. Out of scope here.
