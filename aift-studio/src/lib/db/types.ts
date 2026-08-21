import type {
  BrandSettings, ClaimRecord, ContentAsset, ContentJob, JobRun,
  QualityCheck, ResearchJob, ReviewEvent, SourceDocument, Uuid,
} from '@/lib/domain';
import type { ContentState, TransitionActor } from '@/lib/workflow/states';

/**
 * Persistence port.
 *
 * The only state-changing method for a content job's status is `transition`,
 * and it takes an actor. There is no `setStatus`. That is what makes "cannot be
 * archived without an authenticated reviewer" a property of the data layer
 * rather than a convention the callers are trusted to follow.
 */
export interface Repository {
  readonly name: string;

  getBrandSettings(userId: Uuid): Promise<BrandSettings>;
  updateBrandSettings(userId: Uuid, patch: Partial<BrandSettings>): Promise<BrandSettings>;

  createResearchJob(job: ResearchJob): Promise<ResearchJob>;
  updateResearchJob(id: Uuid, patch: Partial<ResearchJob>): Promise<ResearchJob>;
  getResearchJob(id: Uuid): Promise<ResearchJob | null>;
  listResearchJobs(userId: Uuid): Promise<ResearchJob[]>;

  /** Upsert on (research_job_id, canonical_url) — re-running never duplicates. */
  upsertSourceDocument(doc: SourceDocument): Promise<SourceDocument>;
  listSourceDocuments(researchJobId: Uuid): Promise<SourceDocument[]>;

  /** Upsert on (research_job_id, claim_id). */
  upsertClaim(claim: ClaimRecord): Promise<ClaimRecord>;
  listClaims(researchJobId: Uuid): Promise<ClaimRecord[]>;

  createContentJob(job: ContentJob): Promise<ContentJob>;
  updateContentJob(id: Uuid, patch: Partial<Omit<ContentJob, 'status'>>): Promise<ContentJob>;
  getContentJob(id: Uuid): Promise<ContentJob | null>;
  listContentJobs(userId: Uuid): Promise<ContentJob[]>;

  /** The only path to a status change. Rejects illegal and actor-inappropriate moves. */
  transition(id: Uuid, to: ContentState, actor: TransitionActor, note: string): Promise<ContentJob>;

  /** Upsert on (content_job_id, asset_type, storage_key). */
  upsertAsset(asset: ContentAsset): Promise<ContentAsset>;
  listAssets(contentJobId: Uuid): Promise<ContentAsset[]>;

  replaceQualityChecks(contentJobId: Uuid, checks: QualityCheck[]): Promise<QualityCheck[]>;
  listQualityChecks(contentJobId: Uuid): Promise<QualityCheck[]>;

  recordReviewEvent(event: ReviewEvent): Promise<ReviewEvent>;
  listReviewEvents(contentJobId: Uuid): Promise<ReviewEvent[]>;

  /** Returns `deduplicated: true` when the idempotency key has already run. */
  beginRun(run: Omit<JobRun, 'trace' | 'provider_calls'>): Promise<{ run: JobRun; deduplicated: boolean }>;
  appendRunTrace(runId: Uuid, entry: JobRun['trace'][number]): Promise<void>;
  appendProviderCall(runId: Uuid, call: JobRun['provider_calls'][number]): Promise<void>;
  finishRun(runId: Uuid, status: JobRun['status'], errorSummary: string | null): Promise<JobRun>;
  listRuns(limit: number): Promise<JobRun[]>;
}

export class TransitionError extends Error {
  constructor(message: string) { super(message); this.name = 'TransitionError'; }
}
