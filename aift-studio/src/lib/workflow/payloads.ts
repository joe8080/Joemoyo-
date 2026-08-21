import type { AnalystBrief, EditorialPlan, Script } from '@/lib/schemas/content';
import type { ContentContext } from '@/lib/domain';

/**
 * The typed inputs to each LLM stage. These are serialised verbatim into the
 * `user` message for live providers and consumed directly by the mock composer,
 * so both paths see exactly the same stage input.
 */

export type EvidenceItem = {
  source_document_id: string;
  canonical_url: string;
  title: string;
  publisher: string;
  published_at: string | null;
  source_tier: string;
  excerpt: string;
  candidate_facts: Array<{
    id: string;
    text: string;
    type: string;
    excerpt: string;
    as_of: string;
    confidence: number;
    direction: 'bull' | 'bear' | 'neutral';
    uncertainty: string;
  }>;
};

export type SearchPlanPayload = {
  kind: 'search_plan';
  topic: string;
  ticker: string | null;
  reference_date: string;
  approved_source_domains: string[];
  private_context: ContentContext;
};

export type SourceAssessmentPayload = {
  kind: 'source_assessment';
  topic: string;
  discovered: Array<{ url: string; title: string; snippet: string; publisher: string }>;
};

export type AnalystBriefPayload = {
  kind: 'analyst_brief';
  topic: string;
  ticker: string | null;
  reference_date: string;
  evidence: EvidenceItem[];
};

export type EditorialPayload = {
  kind: 'editorial_plan';
  topic: string;
  ticker: string | null;
  brief: AnalystBrief;
  channel_name: string;
  voice_guide: string;
  audience_profile: string;
  banned_phrases: string[];
  target_minutes: number;
  format: 'deep_dive' | 'short';
};

export type ScriptPayload = {
  kind: 'script';
  format: 'deep_dive' | 'short';
  brief: AnalystBrief;
  editorial: EditorialPlan;
  /** Only claims that passed the public-safety check reach the writer. */
  approved_claims: AnalystBrief['claims'];
  disclosure_text: string;
  channel_name: string;
  reference_date: string;
  banned_phrases: string[];
};

export type CritiquePayload = {
  kind: 'reviewer_critique';
  script: Script;
  approved_claim_ids: string[];
  disclosure_text: string;
  banned_phrases: string[];
};

export type StagePayload =
  | SearchPlanPayload | SourceAssessmentPayload | AnalystBriefPayload
  | EditorialPayload | ScriptPayload | CritiquePayload;
