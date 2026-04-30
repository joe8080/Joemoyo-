-- ============================================================
-- DRAFT 2 / 3 — Add 5 missing agent_rules rows
-- ============================================================
-- Project:   qxwfrsoztfddwicqtuar  (finance-chief / The Vault)
-- Status:    DRAFT — review and fill in personal values before applying
-- Priority:  MEDIUM  (unblocks INVEST advise-only agent)
-- Apply via: mcp__supabase-vault__apply_migration
-- Suggested migration name: add_missing_agent_rules_invest_tax
-- ============================================================
--
-- WHY
-- ---
-- The INVEST agent's CLAUDE.md refuses to compute investable capital,
-- CGT, HICBC bands, or band-proximity flags unless the relevant rules
-- exist in `agent_rules`. Adding these 5 rows unblocks the agent
-- without hardcoding any threshold in the markdown / git history.
--
-- FORMAT NOTE
-- -----------
-- I have NOT read any existing `agent_rules.rule_text` values (to
-- avoid leaking them into the conversation). The proposed format
-- below is structured JSON in `rule_text`. **If your existing 20
-- rules use a different format**, edit the `rule_text` strings to
-- match before applying.
--
-- PERSONAL VALUES MARKED <<FILL IN>>  — must be replaced with real
-- numbers before apply. Public UK 2025/26 tax-year values are
-- pre-filled where well-known.
--
-- TABLES AFFECTED
-- ---------------
--   agent_rules  (5 INSERTs)
--
-- BLAST RADIUS
-- ------------
-- New rows only. Idempotent via ON CONFLICT (rule_name) DO NOTHING.
-- Safe to re-run.
--
-- Run inside a transaction.

BEGIN;

-- ------------------------------------------------------------
-- 1. ukvi_reserve
--    Marks the UKVI cash reserve as ringfenced — excluded from
--    "investable capital" and frozen from in/out movements
--    until ukvi_resolved = true.
-- ------------------------------------------------------------
INSERT INTO public.agent_rules (rule_name, domain, rule_text, priority, active)
VALUES (
  'ukvi_reserve',
  'portfolio',
  $${
    "purpose": "Ringfence cash earmarked for UKVI application evidence.",
    "amount_gbp": "<<FILL IN — current pot size, e.g. 5000>>",
    "account_ref": "<<FILL IN — e.g. T212_cash>>",
    "ukvi_route": "<<FILL IN — spouse|skilled_worker|ilr|other>>",
    "min_hold_days": 180,
    "rule": "Exclude from investable capital. Block any deposit/withdrawal that resets the 6-month UKVI clock until ukvi_resolved = true."
  }$$,
  1,
  true
)
ON CONFLICT (rule_name) DO NOTHING;

-- ------------------------------------------------------------
-- 2. metro_bank_pi_trust
--    Marks the Personal Injury Trust funds as permanently
--    disregarded from UC capital (formal trust confirmed).
-- ------------------------------------------------------------
INSERT INTO public.agent_rules (rule_name, domain, rule_text, priority, active)
VALUES (
  'metro_bank_pi_trust',
  'benefits',
  $${
    "purpose": "Personal Injury Trust funds — permanently disregarded for UC capital.",
    "amount_gbp": "<<FILL IN — current trust balance>>",
    "account_ref": "<<FILL IN — e.g. metro_bank_savings_PI>>",
    "trust_type": "personal_injury_trust",
    "trust_status": "formal",
    "legal_basis": "Disregard under SS-CS&P Regs 2008 reg. 75 (UC) where held in a formal PI trust.",
    "rule": "Exclude from assessable capital permanently. Refuse any proposal that mixes these funds with non-trust assets — co-mingling can break the disregard."
  }$$,
  1,
  true
)
ON CONFLICT (rule_name) DO NOTHING;

-- ------------------------------------------------------------
-- 3. dividend_allowance
--    Per-year HMRC dividend allowance + rates.
--    UK 2025/26: £500 allowance. Basic 8.75%, higher 33.75%,
--    additional 39.35%.
-- ------------------------------------------------------------
INSERT INTO public.agent_rules (rule_name, domain, rule_text, priority, active)
VALUES (
  'dividend_allowance',
  'tax',
  $${
    "tax_year": "2025/26",
    "allowance_gbp": 500,
    "rates": {"basic": 0.0875, "higher": 0.3375, "additional": 0.3935},
    "review_due": "2026-04-06",
    "rule": "When proposing any GIA position with dividend yield, surface projected dividend income, allowance used YTD, and tax due at the household's marginal rate."
  }$$,
  2,
  true
)
ON CONFLICT (rule_name) DO NOTHING;

-- ------------------------------------------------------------
-- 4. hicbc_threshold
--    High Income Child Benefit Charge thresholds.
--    UK 2025/26: starts £60,000, full clawback at £80,000.
--    Adjusted Net Income basis. 1% of CB withdrawn per £200 over.
-- ------------------------------------------------------------
INSERT INTO public.agent_rules (rule_name, domain, rule_text, priority, active)
VALUES (
  'hicbc_threshold',
  'tax',
  $${
    "tax_year": "2025/26",
    "income_basis": "adjusted_net_income",
    "start_gbp": 60000,
    "full_clawback_gbp": 80000,
    "withdrawal_step_gbp": 200,
    "withdrawal_pct_per_step": 1.0,
    "applies_to": "<<FILL IN — household member id from contacts table; whoever claims Child Benefit OR has higher income>>",
    "rule": "On any income event that pushes adjusted net income past £60k: surface projected HICBC liability, plus pension salary-sacrifice / charity-donation deltas needed to stay under £60k."
  }$$,
  2,
  true
)
ON CONFLICT (rule_name) DO NOTHING;

-- ------------------------------------------------------------
-- 5. band_proximity
--    "Within £X of a tax band" warning.
--    Bands: basic→higher £50,270, HICBC start £60k,
--    PA taper start £100k, additional rate £125,140.
-- ------------------------------------------------------------
INSERT INTO public.agent_rules (rule_name, domain, rule_text, priority, active)
VALUES (
  'band_proximity',
  'tax',
  $${
    "tax_year": "2025/26",
    "warn_within_gbp": 500,
    "bands": [
      {"name": "basic_to_higher",        "threshold_gbp": 50270},
      {"name": "hicbc_start",            "threshold_gbp": 60000},
      {"name": "personal_allowance_taper","threshold_gbp": 100000},
      {"name": "additional_rate",        "threshold_gbp": 125140}
    ],
    "rule": "After every income import (income_summary refresh): emit a band_proximity flag if any household member's projected adjusted net income lands within warn_within_gbp of a band threshold."
  }$$,
  2,
  true
)
ON CONFLICT (rule_name) DO NOTHING;

COMMIT;


-- ============================================================
-- VERIFICATION  (expect 5 rows back — names only, no values)
-- ============================================================
-- SELECT rule_name, domain, priority, active
-- FROM public.agent_rules
-- WHERE rule_name IN (
--   'ukvi_reserve','metro_bank_pi_trust','dividend_allowance',
--   'hicbc_threshold','band_proximity'
-- )
-- ORDER BY domain, priority;


-- ============================================================
-- ROLLBACK  (delete the 5 newly inserted rules)
-- ============================================================
-- BEGIN;
-- DELETE FROM public.agent_rules
--  WHERE rule_name IN (
--    'ukvi_reserve','metro_bank_pi_trust','dividend_allowance',
--    'hicbc_threshold','band_proximity'
--  );
-- COMMIT;


-- ============================================================
-- PRE-APPLY CHECKLIST  (do these BEFORE you apply)
-- ============================================================
--   [ ] Replace every <<FILL IN>> placeholder above with the real value
--   [ ] Confirm rule_text JSON format matches your existing 20 rules.
--       If they're plain text instead of JSON, rewrite rule_text to
--       a single string before apply.
--   [ ] Confirm domain assignments (esp. metro_bank_pi_trust → 'benefits'
--       — we put it in benefits because the disregard is a UC concept;
--       move to 'portfolio' if you prefer).
--   [ ] Confirm the priority ordering against your existing rules.
--   [ ] Re-check 2025/26 figures haven't moved in the latest budget.
