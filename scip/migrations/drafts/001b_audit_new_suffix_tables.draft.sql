-- ============================================================
-- DRAFT 1b / 3 — Track A: Audit "_new" suffix vs canonical tables
-- ============================================================
-- Project:   ympbtirltohryxrcqhlm  (worthing database / SCIP)
-- Status:    DRAFT — READ-ONLY AUDIT (no DDL, no row changes)
-- Priority:  MEDIUM
-- Apply via: mcp__Supabase__execute_sql  (NOT apply_migration —
--            this is a diagnostic query bundle, not a migration)
-- ============================================================
--
-- WHY
-- ---
-- The worthing DB has an ambiguous naming pattern — "_new" suffixed
-- tables sitting alongside tables that look like their predecessors:
--
--   scip_business_rates_new   ↔ business_rates / business_rates_full
--   scip_employment_new       ↔ employment_data / employment_statistics
--   scip_flood_risk_new       ↔ flood_risk
--   scip_school_performance_new ↔ school_performance
--   scip_rental_market        ↔ (no obvious predecessor — may be a
--                                 pending new feed)
--
-- Before any resident-facing dashboard goes live, we need to KNOW
-- which is the canonical, up-to-date source. Picking the wrong one
-- publishes stale data to the public.
--
-- This file is NOT a migration — it's a set of audit queries. Run
-- each, record the answers, then decide winners in draft 001d
-- (which will DROP or RENAME the losers).
--
-- ============================================================
-- AUDIT 1: Row counts side-by-side
-- ============================================================
-- Does the "_new" table have more or fewer rows than its ancestor?
-- A clearly bigger "_new" suggests it IS the replacement.
-- A clearly empty "_new" suggests it's a stub, not a replacement.

SELECT
  'business_rates'       AS pair,
  (SELECT COUNT(*) FROM public.business_rates)          AS canonical_rows,
  (SELECT COUNT(*) FROM public.business_rates_full)     AS canonical_full_rows,
  (SELECT COUNT(*) FROM public.scip_business_rates_new) AS new_rows
UNION ALL
SELECT
  'employment',
  (SELECT COUNT(*) FROM public.employment_data),
  (SELECT COUNT(*) FROM public.employment_statistics),
  (SELECT COUNT(*) FROM public.scip_employment_new)
UNION ALL
SELECT
  'flood_risk',
  (SELECT COUNT(*) FROM public.flood_risk),
  NULL,
  (SELECT COUNT(*) FROM public.scip_flood_risk_new)
UNION ALL
SELECT
  'school_performance',
  (SELECT COUNT(*) FROM public.school_performance),
  NULL,
  (SELECT COUNT(*) FROM public.scip_school_performance_new);


-- ============================================================
-- AUDIT 2: Last-modified / freshness check
-- ============================================================
-- Which table has fresher data? Looks for max(created_at) /
-- max(updated_at) depending on which exists per table.
-- NOTE: run these one at a time if any column doesn't exist —
-- otherwise the query errors on the missing column.

-- 2a: business_rates
SELECT 'business_rates'          AS tbl, MAX(created_at) AS last_write FROM public.business_rates
UNION ALL
SELECT 'business_rates_full',          MAX(created_at)                FROM public.business_rates_full
UNION ALL
SELECT 'scip_business_rates_new',      MAX(created_at)                FROM public.scip_business_rates_new;

-- 2b: employment
SELECT 'employment_data'         AS tbl, MAX(created_at) AS last_write FROM public.employment_data
UNION ALL
SELECT 'employment_statistics',        MAX(created_at)                FROM public.employment_statistics
UNION ALL
SELECT 'scip_employment_new',          MAX(created_at)                FROM public.scip_employment_new;

-- 2c: flood_risk
SELECT 'flood_risk'              AS tbl, MAX(created_at) AS last_write FROM public.flood_risk
UNION ALL
SELECT 'scip_flood_risk_new',          MAX(created_at)                FROM public.scip_flood_risk_new;

-- 2d: school_performance
SELECT 'school_performance'      AS tbl, MAX(created_at) AS last_write FROM public.school_performance
UNION ALL
SELECT 'scip_school_performance_new',  MAX(created_at)                FROM public.scip_school_performance_new;


-- ============================================================
-- AUDIT 3: Column-shape divergence
-- ============================================================
-- Do the "_new" tables carry the same columns, or a different
-- (possibly richer / standardised) schema? Big divergence
-- usually means the "_new" table is a real redesign, not a copy.

SELECT
  table_name,
  column_name,
  data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN (
    'business_rates','business_rates_full','scip_business_rates_new',
    'employment_data','employment_statistics','scip_employment_new',
    'flood_risk','scip_flood_risk_new',
    'school_performance','scip_school_performance_new'
  )
ORDER BY table_name, ordinal_position;


-- ============================================================
-- AUDIT 4: Dependency check — is anything still using the "old"?
-- ============================================================
-- Views, foreign keys, policies, functions that reference the
-- older tables. If something depends on them, we can't just drop.

SELECT DISTINCT
  dependent_ns.nspname  AS dependent_schema,
  dependent_view.relname AS dependent_object,
  source_ns.nspname     AS source_schema,
  source_table.relname  AS source_table
FROM pg_depend
JOIN pg_rewrite        ON pg_depend.objid     = pg_rewrite.oid
JOIN pg_class dependent_view ON pg_rewrite.ev_class = dependent_view.oid
JOIN pg_class source_table   ON pg_depend.refobjid    = source_table.oid
JOIN pg_namespace dependent_ns ON dependent_ns.oid = dependent_view.relnamespace
JOIN pg_namespace source_ns    ON source_ns.oid    = source_table.relnamespace
WHERE source_ns.nspname = 'public'
  AND source_table.relname IN (
    'business_rates','business_rates_full','employment_data',
    'employment_statistics','flood_risk','school_performance'
  )
  AND dependent_view.relname != source_table.relname;


-- ============================================================
-- DECISION MATRIX (fill in after running audits)
-- ============================================================
-- For each pair, pick ONE winner and record the reasoning:
--
--   business_rates / business_rates_full / scip_business_rates_new
--      winner:  ___________
--      losers:  ___________
--      reason:  ___________
--
--   employment_data / employment_statistics / scip_employment_new
--      winner:  ___________
--      losers:  ___________
--      reason:  ___________
--
--   flood_risk / scip_flood_risk_new
--      winner:  ___________
--      losers:  ___________
--      reason:  ___________
--
--   school_performance / scip_school_performance_new
--      winner:  ___________
--      losers:  ___________
--      reason:  ___________
--
-- Then: 001d_resolve_new_suffix.draft.sql will:
--   - RENAME winners to canonical name (drop the "_new" suffix)
--   - DROP or _archive losers (operator picks)
--   - UPDATE scip_data_register entries to point at the kept table
--
-- NO drops happen without an explicit second sign-off on 001d.
