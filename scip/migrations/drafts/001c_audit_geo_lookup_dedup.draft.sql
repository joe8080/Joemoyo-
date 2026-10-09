-- ============================================================
-- DRAFT 1c / 3 — Track A: Audit scip_geo_lookup vs postcodes_master
-- ============================================================
-- Project:   ympbtirltohryxrcqhlm  (worthing database / SCIP)
-- Status:    DRAFT — READ-ONLY AUDIT
-- Priority:  LOW–MEDIUM
-- Apply via: mcp__Supabase__execute_sql
-- ============================================================
--
-- WHY
-- ---
-- Both tables carry exactly 907 rows. That's suspicious.
-- Either:
--   (a) They're literally the same data in two places
--       → one is redundant; pick a canonical, make the other a view
--   (b) They cover the same universe (907 Worthing/Adur postcodes)
--       but with different columns
--       → they complement each other; standardise column names,
--         consider a merged view
--   (c) Coincidence (same row count by accident)
--       → leave both; just document the distinction
--
-- Hopefully (a) or (b). The audit tells us which.
--
-- ============================================================
-- AUDIT 1: Column shape comparison
-- ============================================================

SELECT
  table_name,
  column_name,
  data_type,
  is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN ('scip_geo_lookup', 'postcodes_master')
ORDER BY table_name, ordinal_position;


-- ============================================================
-- AUDIT 2: Overlap on postcodes
-- ============================================================
-- Do the same 907 postcodes appear in both? If so, scenario (a) or (b).

WITH
  scip_pcs AS (SELECT DISTINCT UPPER(TRIM(postcode)) AS pc FROM public.scip_geo_lookup WHERE postcode IS NOT NULL),
  pm_pcs   AS (SELECT DISTINCT UPPER(TRIM(postcode)) AS pc FROM public.postcodes_master WHERE postcode IS NOT NULL)
SELECT
  (SELECT COUNT(*) FROM scip_pcs)                                                     AS scip_distinct_pcs,
  (SELECT COUNT(*) FROM pm_pcs)                                                       AS pm_distinct_pcs,
  (SELECT COUNT(*) FROM scip_pcs s JOIN pm_pcs p ON p.pc = s.pc)                      AS overlap_pcs,
  (SELECT COUNT(*) FROM scip_pcs s LEFT JOIN pm_pcs p ON p.pc = s.pc WHERE p.pc IS NULL) AS in_scip_only,
  (SELECT COUNT(*) FROM pm_pcs   p LEFT JOIN scip_pcs s ON s.pc = p.pc WHERE s.pc IS NULL) AS in_pm_only;


-- ============================================================
-- AUDIT 3: Sample rows side-by-side for 5 shared postcodes
-- ============================================================
-- Visually inspect for identical vs complementary data.

WITH shared AS (
  SELECT DISTINCT UPPER(TRIM(s.postcode)) AS pc
  FROM public.scip_geo_lookup s
  JOIN public.postcodes_master p
    ON UPPER(TRIM(p.postcode)) = UPPER(TRIM(s.postcode))
  LIMIT 5
)
SELECT 'scip_geo_lookup' AS source, s.*
FROM public.scip_geo_lookup s
JOIN shared ON UPPER(TRIM(s.postcode)) = shared.pc;

WITH shared AS (
  SELECT DISTINCT UPPER(TRIM(s.postcode)) AS pc
  FROM public.scip_geo_lookup s
  JOIN public.postcodes_master p
    ON UPPER(TRIM(p.postcode)) = UPPER(TRIM(s.postcode))
  LIMIT 5
)
SELECT 'postcodes_master' AS source, p.*
FROM public.postcodes_master p
JOIN shared ON UPPER(TRIM(p.postcode)) = shared.pc;


-- ============================================================
-- AUDIT 4: Where are they referenced?
-- ============================================================
-- Which other scip_* tables / views join against these?

SELECT DISTINCT
  dependent_ns.nspname  AS dependent_schema,
  dependent_view.relname AS dependent_object,
  source_table.relname  AS source_table
FROM pg_depend
JOIN pg_rewrite       ON pg_depend.objid     = pg_rewrite.oid
JOIN pg_class dependent_view ON pg_rewrite.ev_class = dependent_view.oid
JOIN pg_class source_table   ON pg_depend.refobjid    = source_table.oid
JOIN pg_namespace dependent_ns ON dependent_ns.oid = dependent_view.relnamespace
JOIN pg_namespace source_ns    ON source_ns.oid    = source_table.relnamespace
WHERE source_ns.nspname = 'public'
  AND source_table.relname IN ('scip_geo_lookup','postcodes_master')
  AND dependent_view.relname NOT IN ('scip_geo_lookup','postcodes_master');


-- ============================================================
-- DECISION MATRIX (fill in after running audits)
-- ============================================================
-- Scenario detected:  (a) duplicates / (b) complementary / (c) coincidence
--
-- If (a) duplicates:
--   winner:  ______________
--   loser:   ______________
--   plan:    Rename loser to _deprecated, add view aliasing to winner,
--            drop deprecated after N weeks.
--
-- If (b) complementary:
--   plan:    Create materialized view scip_postcode_full that joins
--            both; standardize column names; migrate dependents.
--
-- If (c) coincidence (very unlikely):
--   plan:    Add COMMENTs clarifying the distinction, leave as-is.
--
-- 001e_resolve_geo_lookup.draft.sql will carry whichever plan you
-- pick. No drops without a second sign-off.
