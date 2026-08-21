import type { ContentState } from '@/lib/workflow/states';
import type {
  AnalystBrief, Claim, EditorialPlan, Script, ScenePlan, SearchPlan, ThumbnailBrief,
} from '@/lib/schemas/content';

export type Uuid = string;

export type BrandSettings = {
  user_id: Uuid;
  channel_name: string;
  voice_guide: string;
  audience_profile: string;
  visual_style: {
    background: string;
    surface: string;
    ink: string;
    ink_dim: string;
    accent: string;
    accent_2: string;
    positive: string;
    negative: string;
    display_font: string;
    body_font: string;
    mono_font: string;
    grain: number;
  };
  approved_source_domains: string[];
  banned_phrases: string[];
  disclosure_text: string;
  default_video_length_minutes: number;
  shorts_enabled: boolean;
  /**
   * Private-context allow-list. Every flag defaults to false. A flag that could
   * reveal personal finances stays false until the owner turns it on and the
   * privacy test suite still passes.
   */
  private_context_allowlist: {
    research_topics: boolean;
    agent_rules: boolean;
    intelligence_flags: boolean;
    market_snapshots: boolean;
    macro_indicators: boolean;
    portfolio_themes: boolean;   // aggregate themes only, never values
    portfolio_values: boolean;   // must remain false; guarded by test
  };
};

export type ResearchJob = {
  id: Uuid;
  user_id: Uuid;
  topic: string;
  ticker: string | null;
  job_type: 'deep_dive' | 'radar' | 'short';
  source_policy_version: string;
  status: 'queued' | 'researching' | 'evidence_ready' | 'blocked';
  reference_date: string;
  created_at: string;
  completed_at: string | null;
  failure_reason: string | null;
  search_plan: SearchPlan | null;
  brief: AnalystBrief | null;
};

export type SourceDocument = {
  id: Uuid;
  research_job_id: Uuid;
  canonical_url: string;
  publisher: string;
  published_at: string | null;
  accessed_at: string;
  source_tier: string;
  title: string;
  excerpt: string;
  content_hash: string;
  licence_notes: string;
  retrieval_status: 'fetched' | 'failed' | 'blocked_by_policy';
};

export type ClaimRecord = Claim & {
  id: Uuid;
  research_job_id: Uuid;
  review_status: 'unreviewed' | 'accepted' | 'rejected';
  is_public_safe: boolean;
  public_safe_reason: string;
};

export type ContentJob = {
  id: Uuid;
  user_id: Uuid;
  research_job_id: Uuid;
  format: 'deep_dive' | 'short';
  working_title: string;
  status: ContentState;
  review_stage: string;
  script_version: number;
  asset_manifest_url: string | null;
  created_at: string;
  approved_at: string | null;
  editorial_plan: EditorialPlan | null;
  script: Script | null;
  scene_plan: ScenePlan | null;
  thumbnail_brief: ThumbnailBrief | null;
};

export type ContentAsset = {
  id: Uuid;
  content_job_id: Uuid;
  asset_type:
    | 'script_markdown' | 'script_json' | 'scene_plan' | 'narration_text'
    | 'captions_srt' | 'chapters_json' | 'description_markdown' | 'title_options'
    | 'thumbnail_brief' | 'thumbnail_png' | 'chart_svg' | 'broll_prompt'
    | 'audio_wav' | 'video_mp4' | 'source_manifest' | 'quality_report' | 'package_manifest';
  storage_key: string;
  sha256: string;
  generator: string;
  prompt_version: string;
  source_claim_ids: string[];
  status: 'draft' | 'final' | 'superseded';
  duration_seconds: number | null;
  aspect_ratio: string | null;
  bytes: number;
  created_at: string;
};

export type QualityCheck = {
  id: Uuid;
  content_job_id: Uuid;
  check_name: string;
  gate: string;
  severity: 'blocking' | 'warning' | 'note';
  result: 'pass' | 'fail' | 'skipped';
  details: { message: string; offenders: string[]; remediation: string };
  run_at: string;
  resolved_at: string | null;
};

export type ReviewEvent = {
  id: Uuid;
  content_job_id: Uuid;
  reviewer_id: Uuid;
  decision: 'approved_for_archive' | 'rework_required' | 'archived' | 'unblocked';
  reason_codes: string[];
  freeform_feedback: string;
  created_at: string;
};

export type JobRun = {
  id: Uuid;
  job_type: string;
  idempotency_key: string;
  status: 'running' | 'succeeded' | 'failed' | 'skipped_duplicate';
  started_at: string;
  finished_at: string | null;
  attempt_count: number;
  error_summary: string | null;
  trace: Array<{ at: string; stage: string; message: string; level: 'info' | 'warn' | 'error' }>;
  provider_calls: Array<{
    provider: string; model: string; prompt_version: string;
    input_tokens: number | null; output_tokens: number | null; cost_usd: number | null;
  }>;
};

/** Redacted research context — the ONLY shape that may reach an LLM. */
export type ContentContext = {
  reference_date: string;
  research_topics: Array<{ topic: string; ticker: string | null; priority: number; requested_fields: string[] }>;
  agent_rules: Array<{ rule_name: string; rule_text: string; scope: string }>;
  intelligence_flags: Array<{ label: string; strength: 'low' | 'medium' | 'high' }>;
  market_snapshots: Array<{ symbol: string; metric: string; value: number; unit: string; as_of: string; source: string }>;
  macro_indicators: Array<{ indicator: string; value: number; unit: string; as_of: string; source: string }>;
  portfolio_themes: string[];
  redaction_notice: string;
};
