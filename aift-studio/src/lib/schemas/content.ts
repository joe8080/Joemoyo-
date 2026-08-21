import { z } from 'zod';

/**
 * Every LLM step in this system is a typed function: structured JSON in,
 * schema-validated JSON out. A response that fails to parse is rejected and
 * retried; it is never coerced, patched, or partially accepted.
 */

// ---------------------------------------------------------------------------
// Shared primitives
// ---------------------------------------------------------------------------

export const isoDate = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/u, 'expected an ISO date (YYYY-MM-DD)');

export const sourceTier = z.enum([
  'primary_filing',       // 10-K/10-Q/20-F/8-K, prospectus, exchange notice
  'primary_company',      // IR page, press release, earnings deck, transcript
  'primary_regulator',    // SEC/FCA/central bank/statistics agency
  'specialist',           // professional research, standards bodies, academia
  'journalism',           // reputable financial press
  'unverified',           // discovery-only; may never back a material claim
]);
export type SourceTier = z.infer<typeof sourceTier>;

export const claimType = z.enum([
  'price_or_performance',
  'market_cap',
  'financial_statement',
  'forecast_or_guidance',
  'rating_or_recommendation',
  'insider_or_ownership',
  'valuation',
  'causal',
  'definitional',        // "a P/E ratio is..." — educational, no source needed
  'contextual',          // non-material colour
]);
export type ClaimType = z.infer<typeof claimType>;

/** Claim types that cannot enter a script without full evidence. */
export const MATERIAL_CLAIM_TYPES: ReadonlySet<string> = new Set<string>([
  'price_or_performance',
  'market_cap',
  'financial_statement',
  'forecast_or_guidance',
  'rating_or_recommendation',
  'insider_or_ownership',
  'valuation',
  'causal',
]);

export function isMaterial(t: ClaimType): boolean {
  return MATERIAL_CLAIM_TYPES.has(t);
}

// ---------------------------------------------------------------------------
// Stage 2 — research plan (AI produces a query plan only; it fetches nothing)
// ---------------------------------------------------------------------------

export const searchPlanSchema = z.object({
  reference_date: isoDate,
  rationale: z.string().min(20).max(1200),
  queries: z
    .array(
      z.object({
        query: z.string().min(3).max(200),
        intent: z.string().min(3).max(200),
        preferred_tiers: z.array(sourceTier).min(1),
      }),
    )
    .min(3)
    .max(12),
  required_primary_documents: z.array(z.string().min(3).max(200)).max(10),
  out_of_scope: z.array(z.string().min(3).max(200)).max(10),
});
export type SearchPlan = z.infer<typeof searchPlanSchema>;

// ---------------------------------------------------------------------------
// Stage 3 — evidence classification (relevance only; never invents a source)
// ---------------------------------------------------------------------------

export const sourceAssessmentSchema = z.object({
  assessments: z.array(
    z.object({
      canonical_url: z.string().url(),
      relevance: z.enum(['high', 'medium', 'low', 'irrelevant']),
      supports_topics: z.array(z.string().max(160)).max(8),
      caution_notes: z.string().max(600).default(''),
    }),
  ),
});
export type SourceAssessment = z.infer<typeof sourceAssessmentSchema>;

// ---------------------------------------------------------------------------
// Stage 4 — analyst brief + claim ledger
// ---------------------------------------------------------------------------

export const claimSchema = z.object({
  claim_id: z.string().regex(/^C-\d{3}$/u, 'claim ids look like C-001'),
  claim_text: z.string().min(10).max(600),
  claim_type: claimType,
  source_document_ids: z.array(z.string().min(1)).default([]),
  source_excerpt: z.string().max(1200).default(''),
  as_of_date: isoDate.nullable().default(null),
  confidence: z.number().min(0).max(1),
  uncertainty_note: z.string().max(400).default(''),
});
export type Claim = z.infer<typeof claimSchema>;

export const analystBriefSchema = z.object({
  reference_date: isoDate,
  headline: z.string().min(10).max(160),
  summary: z.string().min(100).max(3000),
  bull_case: z.array(z.string().min(10).max(500)).min(1).max(6),
  bear_case: z.array(z.string().min(10).max(500)).min(1).max(6),
  key_risks: z.array(z.string().min(10).max(500)).min(2).max(8),
  open_questions: z.array(z.string().min(5).max(300)).max(8),
  claims: z.array(claimSchema).min(1).max(60),
});
export type AnalystBrief = z.infer<typeof analystBriefSchema>;

// ---------------------------------------------------------------------------
// Stage 5 — editorial plan
// ---------------------------------------------------------------------------

export const editorialPlanSchema = z.object({
  angle: z.string().min(20).max(600),
  audience_promise: z.string().min(20).max(400),
  title_options: z
    .array(
      z.object({
        title: z.string().min(10).max(90),
        why_it_works: z.string().min(10).max(300),
        overpromise_risk: z.enum(['low', 'medium', 'high']),
      }),
    )
    .min(3)
    .max(6),
  hook: z.string().min(20).max(500),
  outline: z
    .array(
      z.object({
        chapter: z.string().min(3).max(80),
        purpose: z.string().min(10).max(300),
        claim_ids: z.array(z.string()).default([]),
        target_seconds: z.number().int().min(20).max(240),
      }),
    )
    .min(4)
    .max(12),
  call_to_action: z.string().min(10).max(300),
});
export type EditorialPlan = z.infer<typeof editorialPlanSchema>;

// ---------------------------------------------------------------------------
// Stage 6 — script
// ---------------------------------------------------------------------------

export const scriptBeatSchema = z.object({
  beat_id: z.string().min(1).max(24),
  chapter: z.string().min(1).max(80),
  narration: z.string().min(1).max(1200),
  on_screen_text: z.string().max(160).default(''),
  claim_ids: z.array(z.string()).default([]),
  /** Visual intent, resolved into a concrete composition by the visual planner. */
  visual_intent: z.enum([
    'title_card',
    'statement',
    'stat_reveal',
    'line_chart',
    'bar_chart',
    'comparison_table',
    'quote_card',
    'risk_card',
    'chapter_card',
    'broll',
    'disclosure',
    'outro',
  ]),
});
export type ScriptBeat = z.infer<typeof scriptBeatSchema>;

export const scriptSchema = z.object({
  working_title: z.string().min(10).max(100),
  reference_date: isoDate,
  beats: z.array(scriptBeatSchema).min(6).max(120),
  chapters: z
    .array(z.object({ title: z.string().min(2).max(80), start_beat: z.string().min(1) }))
    .min(2)
    .max(14),
  description_markdown: z.string().min(100).max(6000),
  tags: z.array(z.string().min(2).max(40)).min(5).max(25),
  disclosure_text: z.string().min(40).max(600),
});
export type Script = z.infer<typeof scriptSchema>;

// ---------------------------------------------------------------------------
// Stage 7 — visual plan
// ---------------------------------------------------------------------------

export const chartSeriesSchema = z.object({
  label: z.string().min(1).max(60),
  /** Points come from validated structured data, never from a language model. */
  points: z.array(z.object({ x: z.string().min(1).max(24), y: z.number() })).min(2).max(400),
  unit: z.string().max(16).default(''),
});

export const sceneSchema = z.object({
  scene_id: z.string().min(1).max(24),
  beat_ids: z.array(z.string()).min(1),
  start_ms: z.number().int().min(0),
  duration_ms: z.number().int().min(1200).max(30_000),
  composition: z.enum([
    'title_card',
    'statement',
    'stat_reveal',
    'line_chart',
    'bar_chart',
    'comparison_table',
    'quote_card',
    'risk_card',
    'chapter_card',
    'broll',
    'disclosure',
    'outro',
  ]),
  headline: z.string().max(160).default(''),
  subhead: z.string().max(240).default(''),
  /** Present only for data compositions. Sourced + dated or the visual gate fails. */
  data: z
    .object({
      series: z.array(chartSeriesSchema).min(1).max(4),
      y_label: z.string().max(40).default(''),
      x_label: z.string().max(40).default(''),
      source_label: z.string().min(3).max(120),
      as_of_date: isoDate,
      claim_ids: z.array(z.string()).min(1),
      highlight_index: z.number().int().nullable().default(null),
    })
    .nullable()
    .default(null),
  stat: z
    .object({
      value: z.string().min(1).max(24),
      caption: z.string().max(120),
      source_label: z.string().min(3).max(120),
      as_of_date: isoDate,
      claim_ids: z.array(z.string()).min(1),
    })
    .nullable()
    .default(null),
  rows: z
    .array(z.object({ label: z.string().max(60), values: z.array(z.string().max(40)).max(4) }))
    .max(8)
    .default([]),
  columns: z.array(z.string().max(40)).max(4).default([]),
  bullets: z.array(z.string().max(160)).max(5).default([]),
  /** Atmospheric only. The visual gate rejects any prompt implying numbers. */
  broll_prompt: z.string().max(600).default(''),
  transition: z.enum(['cut', 'fade', 'push_left', 'rise']).default('fade'),
  citation: z.string().max(160).default(''),
});
export type Scene = z.infer<typeof sceneSchema>;

export const scenePlanSchema = z.object({
  format: z.enum(['deep_dive', 'short']),
  width: z.number().int().positive(),
  height: z.number().int().positive(),
  fps: z.number().int().min(24).max(60),
  total_ms: z.number().int().positive(),
  scenes: z.array(sceneSchema).min(3).max(160),
});
export type ScenePlan = z.infer<typeof scenePlanSchema>;

// ---------------------------------------------------------------------------
// Stage 9 — independent reviewer critique (separate model / separate prompt)
// ---------------------------------------------------------------------------

export const reviewerCritiqueSchema = z.object({
  verdict: z.enum(['pass', 'rework', 'block']),
  findings: z
    .array(
      z.object({
        severity: z.enum(['blocking', 'warning', 'note']),
        area: z.enum(['evidence', 'compliance', 'clarity', 'balance', 'visual', 'brand']),
        detail: z.string().min(10).max(800),
        remediation: z.string().min(5).max(600),
        beat_id: z.string().max(24).default(''),
      }),
    )
    .max(40),
  strengths: z.array(z.string().max(400)).max(10),
});
export type ReviewerCritique = z.infer<typeof reviewerCritiqueSchema>;

// ---------------------------------------------------------------------------
// Thumbnail brief
// ---------------------------------------------------------------------------

export const thumbnailBriefSchema = z.object({
  concept: z.string().min(20).max(600),
  primary_text: z.string().min(1).max(28),
  secondary_text: z.string().max(36).default(''),
  visual_direction: z.string().min(20).max(600),
  palette: z.array(z.string().regex(/^#[0-9a-fA-F]{6}$/u)).min(2).max(5),
  forbidden: z.array(z.string().max(200)).max(10),
});
export type ThumbnailBrief = z.infer<typeof thumbnailBriefSchema>;
