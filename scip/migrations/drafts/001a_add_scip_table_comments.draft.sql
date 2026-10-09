-- ============================================================
-- DRAFT 1a / 3 — Track A: Add COMMENT ON TABLE to every scip_*
-- ============================================================
-- Project:   ympbtirltohryxrcqhlm  (worthing database / SCIP)
-- Status:    DRAFT — review wording before applying
-- Priority:  MEDIUM (unblocks every downstream track —
--            dashboard, briefings, FOI ingest all need
--            documented table semantics)
-- Apply via: mcp__Supabase__apply_migration
-- Suggested migration name: scip_add_table_comments
-- ============================================================
--
-- WHY
-- ---
-- 23 scip_* tables in the public schema currently carry zero
-- COMMENTs. For a resident-facing product with FOI/attribution
-- expectations, that's a documentation gap:
--   - no future reader (operator, buyer, Claude agent) can tell
--     which table is canonical vs. deprecated,
--   - briefing generation + semantic search need table-level
--     intent to disambiguate rows,
--   - open-data posture means we WILL publish the schema.
--
-- These comments describe each table's intent, source, grain,
-- and public-data status. Values are DRAFT — edit the wording
-- before applying if any description is wrong.
--
-- SCOPE
-- -----
-- Adds COMMENT ON TABLE for 23 tables. Does NOT modify data,
-- schema, policies, or anything else. Fully reversible by
-- re-applying with the previous (empty) comments.
--
-- Idempotent: COMMENT ON overwrites existing comments.
--
-- Run inside a transaction.

BEGIN;

-- ------------------------------------------------------------
-- CORE / CONTROL PLANE
-- ------------------------------------------------------------

COMMENT ON TABLE public.scip_unified_data IS
  'SCIP core star fact table — unified intelligence rows across every data domain (housing, transport, planning, health, air quality, benefits, etc.). ~98k rows. One row per observation. Open council data; attribute by source_type / source. Downstream: vector-embedded for semantic search.';

COMMENT ON TABLE public.scip_indices IS
  'SCIP indices — small registry mapping index names/keys to their underlying data source and semantics. Reference table used to interpret rows across scip_* domain tables.';

COMMENT ON TABLE public.scip_data_register IS
  'SCIP data source register — one row per external data source (council feed, public dataset, FOI release). Tracks source URL, publisher, licence, refresh cadence. Attribution root for every scip_* row.';

COMMENT ON TABLE public.scip_metadata IS
  'SCIP metadata — per-dataset schema, provenance, and processing notes. Used by ingest pipelines and the public dashboard to render source credits.';

COMMENT ON TABLE public.scip_automation_log IS
  'SCIP automation audit log — one row per automated ingest / briefing / FOI-extract run. Tracks run id, duration, status, errors. Append-only by convention.';

COMMENT ON TABLE public.scip_reports_log IS
  'SCIP report generation log — one row per generated report (weekly briefing, FOI response, monthly dashboard snapshot). Tracks who/what consumed the data.';

COMMENT ON TABLE public.scip_intelligence IS
  'SCIP working intelligence capture — curated / editor-produced intelligence entries (not raw feed data). Classified by category, source_type, council. Links to scip_pipeline for actionable items.';

COMMENT ON TABLE public.scip_geo_lookup IS
  'SCIP postcode → geocode lookup for the Worthing / Adur area (~907 rows). WARNING: may duplicate the top-level public.postcodes_master table (same row count). See draft 001c for the dedup audit.';

-- ------------------------------------------------------------
-- HOUSING / PROPERTY / PLANNING DOMAIN
-- ------------------------------------------------------------

COMMENT ON TABLE public.scip_house_price_index IS
  'UK HM Land Registry House Price Index for Worthing / Adur / West Sussex. Monthly series: average_price, monthly_change_pct, annual_change_pct, plus detached/semi/terraced/flat breakdown. Open government licence. Source: gov.uk/government/statistical-data-sets/uk-house-price-index.';

COMMENT ON TABLE public.scip_rental_market IS
  'Local rental market stats (medians, listing counts, time-on-market) — source TBD (ONS Private Rental or VOA). Currently empty; populate before use.';

COMMENT ON TABLE public.scip_planning_applications IS
  'Planning applications filed with Adur & Worthing Councils. One row per application. Includes reference, decision, address, received/decided dates. Published by council. See also top-level planning_applications table (status: investigate overlap).';

COMMENT ON TABLE public.scip_building_control IS
  'Building Control applications — notifications of works needing regulations approval, filed with Adur & Worthing. Open council data.';

COMMENT ON TABLE public.scip_business_rates_new IS
  'Non-domestic (business) rates roll for Worthing / Adur. One row per hereditament. VOA rateable value + council billing data. "_new" suffix indicates a replacement for an older business_rates / business_rates_full table — audit before deciding canonical. See draft 001b.';

COMMENT ON TABLE public.scip_council_tax_bands IS
  'Council Tax banding by property / postcode area. Reference data from the Valuation Office Agency (VOA). Used for affordability analysis + resident lookup.';

-- ------------------------------------------------------------
-- TRANSPORT / INFRASTRUCTURE
-- ------------------------------------------------------------

COMMENT ON TABLE public.scip_traffic_counts IS
  'DfT road traffic count points covering Worthing / Adur. Vehicle-type and time-period counts at each monitoring site. Open government licence. Source: roadtraffic.dft.gov.uk.';

COMMENT ON TABLE public.scip_parking_restrictions IS
  'On-street parking restrictions (Traffic Regulation Orders) across Adur & Worthing. Open council data; derived from TRO publications.';

COMMENT ON TABLE public.scip_broadband_speeds IS
  'Ofcom broadband availability + speed data by postcode / UPRN across the Worthing / Adur area. Source: Ofcom Connected Nations open dataset.';

-- ------------------------------------------------------------
-- HEALTH / ENVIRONMENT
-- ------------------------------------------------------------

COMMENT ON TABLE public.scip_gp_practices IS
  'GP practices operating in the Worthing / Adur NHS catchment area, with ODS codes, address, patient list sizes. Source: NHS Digital ODS + Fingertips. Open NHS data.';

COMMENT ON TABLE public.scip_air_quality IS
  'Local air quality readings (NO₂, PM2.5, PM10) from Adur & Worthing Councils + Defra monitoring sites. Open government licence.';

COMMENT ON TABLE public.scip_flood_risk IS
  'Environment Agency flood-risk zones + historical flood events overlaid onto Worthing / Adur geography. Open government licence. ("flood_risk" is the canonical table; scip_flood_risk_new is the staged replacement — see 001b.)';

COMMENT ON TABLE public.scip_flood_risk_new IS
  'Replacement feed for scip_flood_risk — pending audit (draft 001b) to decide which becomes canonical.';

-- ------------------------------------------------------------
-- SOCIO-ECONOMIC
-- ------------------------------------------------------------

COMMENT ON TABLE public.scip_benefits_aggregated IS
  'DWP StatXplore aggregated benefits caseload data for the Worthing / Adur / West Sussex geographies. No individual-level data (aggregated only). Open government licence.';

COMMENT ON TABLE public.scip_employment_new IS
  'ONS Claimant Count + employment indicators for Worthing / Adur geographies. "_new" suffix indicates replacement for an earlier employment_data / employment_statistics table — audit before deciding canonical.';

COMMENT ON TABLE public.scip_school_performance_new IS
  'DfE school performance tables (KS2 / KS4 / 16-18) for schools in Worthing & Adur, joined to Ofsted ratings. "_new" suffix indicates replacement for an earlier school_performance table — audit before deciding canonical.';

COMMIT;


-- ============================================================
-- VERIFICATION (run after apply, expect 23 rows w/ non-null comment)
-- ============================================================
-- SELECT c.relname AS table_name,
--        obj_description(c.oid, 'pg_class') AS comment
-- FROM pg_class c
-- JOIN pg_namespace n ON n.oid = c.relnamespace
-- WHERE n.nspname = 'public' AND c.relkind = 'r' AND c.relname LIKE 'scip_%'
-- ORDER BY c.relname;


-- ============================================================
-- ROLLBACK  (clears every comment back to NULL)
-- ============================================================
-- BEGIN;
-- COMMENT ON TABLE public.scip_unified_data           IS NULL;
-- COMMENT ON TABLE public.scip_indices                IS NULL;
-- COMMENT ON TABLE public.scip_data_register          IS NULL;
-- COMMENT ON TABLE public.scip_metadata               IS NULL;
-- COMMENT ON TABLE public.scip_automation_log         IS NULL;
-- COMMENT ON TABLE public.scip_reports_log            IS NULL;
-- COMMENT ON TABLE public.scip_intelligence           IS NULL;
-- COMMENT ON TABLE public.scip_geo_lookup             IS NULL;
-- COMMENT ON TABLE public.scip_house_price_index      IS NULL;
-- COMMENT ON TABLE public.scip_rental_market          IS NULL;
-- COMMENT ON TABLE public.scip_planning_applications  IS NULL;
-- COMMENT ON TABLE public.scip_building_control       IS NULL;
-- COMMENT ON TABLE public.scip_business_rates_new     IS NULL;
-- COMMENT ON TABLE public.scip_council_tax_bands      IS NULL;
-- COMMENT ON TABLE public.scip_traffic_counts         IS NULL;
-- COMMENT ON TABLE public.scip_parking_restrictions   IS NULL;
-- COMMENT ON TABLE public.scip_broadband_speeds       IS NULL;
-- COMMENT ON TABLE public.scip_gp_practices           IS NULL;
-- COMMENT ON TABLE public.scip_air_quality            IS NULL;
-- COMMENT ON TABLE public.scip_flood_risk             IS NULL;
-- COMMENT ON TABLE public.scip_flood_risk_new         IS NULL;
-- COMMENT ON TABLE public.scip_benefits_aggregated    IS NULL;
-- COMMENT ON TABLE public.scip_employment_new         IS NULL;
-- COMMENT ON TABLE public.scip_school_performance_new IS NULL;
-- COMMIT;


-- ============================================================
-- PRE-APPLY CHECKLIST
-- ============================================================
--   [ ] Database project awake (restore_project if INACTIVE)
--   [ ] Confirm scip_flood_risk exists (I inferred from the pattern,
--       but my earlier table list showed only scip_flood_risk_new).
--       If scip_flood_risk doesn't exist, remove its COMMENT ON line
--       and keep only scip_flood_risk_new.
--   [ ] Edit any wording that misdescribes the actual table contents.
--   [ ] Confirm 23 is still the right count (data has been actively
--       ingested — may be more scip_* tables now than when I listed).
