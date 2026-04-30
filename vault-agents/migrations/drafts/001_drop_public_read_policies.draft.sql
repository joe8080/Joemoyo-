-- ============================================================
-- DRAFT 1 / 3 — Drop anon/public SELECT policies (PRIVACY FIX)
-- ============================================================
-- Project:   qxwfrsoztfddwicqtuar  (finance-chief / The Vault)
-- Status:    DRAFT — review before applying
-- Priority:  HIGHEST  (live privacy leak)
-- Apply via: mcp__supabase-vault__apply_migration
-- Suggested migration name: drop_anon_read_on_personal_tables
-- ============================================================
--
-- WHY
-- ---
-- Migration `add_public_read_policies` (2026-04-19) granted SELECT
-- to the `anon` (or `public`) Postgres role on 15 tables that hold
-- household financial, personal-identity, and decision-history data.
-- Anyone in possession of the project's anon/publishable key can
-- currently read these tables.
--
-- Service-role (which our agents and MCP server use) bypasses RLS,
-- so dropping the anon policies costs us NOTHING operationally.
--
-- DECISION
-- --------
-- Option chosen: DROP the anon/public SELECT policies. Result:
--   - With RLS enabled and no policy, anon and authenticated roles
--     are denied SELECT by default. Service-role still has full
--     access (it bypasses RLS).
-- Alternative considered: restrict to `authenticated`. Rejected
-- because there is no current authenticated-user surface that needs
-- read access; YAGNI. Easy to add later if needed.
--
-- TABLES AFFECTED  (15 policies)
-- -------------------------------
--   agent_rules            policy: public_read_agent_rules            (anon)
--   asset_register         policy: public_read_asset_register         (anon)
--   benefits_status        policy: public_read_benefits_status        (anon)
--   care_assessments       policy: public_read_care                   (public)
--   creative_works         policy: public_read_creative               (public)
--   decision_log           policy: public_read_decision_log           (anon)
--   ecosystem_map          policy: public_read_ecosystem_map          (anon)
--   identity_core          policy: public_read_identity_core          (anon)
--   income_summary         policy: public_read_income_summary         (anon)
--   net_worth_snapshots    policy: public_read_net_worth_snapshots    (anon)
--   portfolio_buckets      policy: public_read_portfolio_buckets      (anon)
--   portfolio_summary      policy: public_read_portfolio_summary      (anon)
--   price_snapshots        policy: public_read_prices                 (public)
--   security_ladder        policy: public_read_security_ladder        (anon)
--   ventures               policy: public_read_ventures               (anon)
--
-- BLAST RADIUS
-- ------------
--   - Service-role connections (agents, MCP)        → unaffected
--   - Anon-key SELECTs against these tables         → will start returning 0 rows
--   - INSERT/UPDATE/DELETE policies                 → unchanged (this migration touches SELECT only)
--
-- Run inside a single transaction so partial application is impossible.

BEGIN;

DROP POLICY IF EXISTS public_read_agent_rules         ON public.agent_rules;
DROP POLICY IF EXISTS public_read_asset_register      ON public.asset_register;
DROP POLICY IF EXISTS public_read_benefits_status     ON public.benefits_status;
DROP POLICY IF EXISTS public_read_care                ON public.care_assessments;
DROP POLICY IF EXISTS public_read_creative            ON public.creative_works;
DROP POLICY IF EXISTS public_read_decision_log        ON public.decision_log;
DROP POLICY IF EXISTS public_read_ecosystem_map       ON public.ecosystem_map;
DROP POLICY IF EXISTS public_read_identity_core       ON public.identity_core;
DROP POLICY IF EXISTS public_read_income_summary      ON public.income_summary;
DROP POLICY IF EXISTS public_read_net_worth_snapshots ON public.net_worth_snapshots;
DROP POLICY IF EXISTS public_read_portfolio_buckets   ON public.portfolio_buckets;
DROP POLICY IF EXISTS public_read_portfolio_summary   ON public.portfolio_summary;
DROP POLICY IF EXISTS public_read_prices              ON public.price_snapshots;
DROP POLICY IF EXISTS public_read_security_ladder     ON public.security_ladder;
DROP POLICY IF EXISTS public_read_ventures            ON public.ventures;

COMMIT;


-- ============================================================
-- VERIFICATION (run after apply, expect zero rows)
-- ============================================================
-- SELECT schemaname, tablename, policyname, cmd, roles::text
-- FROM pg_policies
-- WHERE schemaname = 'public'
--   AND (roles::text LIKE '%anon%' OR roles::text LIKE '%public%');


-- ============================================================
-- ROLLBACK (re-create the original policies — keep handy but DO
-- NOT run unless you specifically need anon reads back)
-- ============================================================
-- BEGIN;
-- CREATE POLICY public_read_agent_rules         ON public.agent_rules         FOR SELECT TO anon USING (true);
-- CREATE POLICY public_read_asset_register      ON public.asset_register      FOR SELECT TO anon USING (true);
-- CREATE POLICY public_read_benefits_status     ON public.benefits_status     FOR SELECT TO anon USING (true);
-- CREATE POLICY public_read_care                ON public.care_assessments    FOR SELECT TO public USING (true);
-- CREATE POLICY public_read_creative            ON public.creative_works      FOR SELECT TO public USING (true);
-- CREATE POLICY public_read_decision_log        ON public.decision_log        FOR SELECT TO anon USING (true);
-- CREATE POLICY public_read_ecosystem_map       ON public.ecosystem_map       FOR SELECT TO anon USING (true);
-- CREATE POLICY public_read_identity_core       ON public.identity_core       FOR SELECT TO anon USING (true);
-- CREATE POLICY public_read_income_summary      ON public.income_summary      FOR SELECT TO anon USING (true);
-- CREATE POLICY public_read_net_worth_snapshots ON public.net_worth_snapshots FOR SELECT TO anon USING (true);
-- CREATE POLICY public_read_portfolio_buckets   ON public.portfolio_buckets   FOR SELECT TO anon USING (true);
-- CREATE POLICY public_read_portfolio_summary   ON public.portfolio_summary   FOR SELECT TO anon USING (true);
-- CREATE POLICY public_read_prices              ON public.price_snapshots     FOR SELECT TO public USING (true);
-- CREATE POLICY public_read_security_ladder     ON public.security_ladder     FOR SELECT TO anon USING (true);
-- CREATE POLICY public_read_ventures            ON public.ventures            FOR SELECT TO anon USING (true);
-- COMMIT;


-- ============================================================
-- RELATED INFO  (advisor flagged but NOT blocking, NOT changed here)
-- ============================================================
-- The following 13 tables have RLS enabled but no policies. That's
-- the correct lockdown posture (only service-role can read), but
-- Supabase's linter raises an INFO that explicit policies make intent
-- clearer. Optional follow-up — not part of this migration:
--   contacts, goals, health_timeline, holdings, sinking_funds, trades,
--   watchlist, ogx_content_pipeline, ogx_research_claims,
--   scip_intelligence, scip_outreach, scip_pipeline
-- See: https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy
