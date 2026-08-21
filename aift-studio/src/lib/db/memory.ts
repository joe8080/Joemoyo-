import type {
  BrandSettings, ClaimRecord, ContentAsset, ContentJob, JobRun,
  QualityCheck, ResearchJob, ReviewEvent, SourceDocument, Uuid,
} from '@/lib/domain';
import { canTransition, type ContentState, type TransitionActor } from '@/lib/workflow/states';
import { type Repository, TransitionError } from './types';
import { DEFAULT_BRAND_SETTINGS } from './defaults';

/**
 * In-memory repository.
 *
 * Used for the demo pack, for local runs without a database and for the whole
 * test suite. It enforces the same invariants as the Postgres implementation —
 * the FSM, the uniqueness constraints and the idempotency ledger — so a test
 * that passes here is testing the real rules, not a permissive stub.
 */
export class MemoryRepository implements Repository {
  readonly name = 'memory@1';

  private brand = new Map<Uuid, BrandSettings>();
  private researchJobs = new Map<Uuid, ResearchJob>();
  private sources = new Map<string, SourceDocument>();
  private claims = new Map<string, ClaimRecord>();
  private contentJobs = new Map<Uuid, ContentJob>();
  private assets = new Map<string, ContentAsset>();
  private checks = new Map<Uuid, QualityCheck[]>();
  private reviews: ReviewEvent[] = [];
  private runs = new Map<Uuid, JobRun>();
  private idempotency = new Map<string, Uuid>();

  async getBrandSettings(userId: Uuid): Promise<BrandSettings> {
    const existing = this.brand.get(userId);
    if (existing) return existing;
    const created = { ...DEFAULT_BRAND_SETTINGS, user_id: userId };
    this.brand.set(userId, created);
    return created;
  }

  async updateBrandSettings(userId: Uuid, patch: Partial<BrandSettings>): Promise<BrandSettings> {
    const current = await this.getBrandSettings(userId);
    const next = { ...current, ...patch, user_id: userId };
    this.brand.set(userId, next);
    return next;
  }

  async createResearchJob(job: ResearchJob): Promise<ResearchJob> {
    this.researchJobs.set(job.id, job);
    return job;
  }

  async updateResearchJob(id: Uuid, patch: Partial<ResearchJob>): Promise<ResearchJob> {
    const cur = this.researchJobs.get(id);
    if (!cur) throw new Error(`research job ${id} not found`);
    const next = { ...cur, ...patch, id };
    this.researchJobs.set(id, next);
    return next;
  }

  async getResearchJob(id: Uuid): Promise<ResearchJob | null> { return this.researchJobs.get(id) ?? null; }
  async listResearchJobs(userId: Uuid): Promise<ResearchJob[]> {
    return [...this.researchJobs.values()].filter((j) => j.user_id === userId)
      .sort((a, b) => b.created_at.localeCompare(a.created_at));
  }

  async upsertSourceDocument(doc: SourceDocument): Promise<SourceDocument> {
    const key = `${doc.research_job_id}|${doc.canonical_url}`;
    const existing = this.sources.get(key);
    const merged = existing ? { ...doc, id: existing.id } : doc;
    this.sources.set(key, merged);
    return merged;
  }

  async listSourceDocuments(researchJobId: Uuid): Promise<SourceDocument[]> {
    return [...this.sources.values()].filter((s) => s.research_job_id === researchJobId)
      .sort((a, b) => a.canonical_url.localeCompare(b.canonical_url));
  }

  async upsertClaim(claim: ClaimRecord): Promise<ClaimRecord> {
    const key = `${claim.research_job_id}|${claim.claim_id}`;
    const existing = this.claims.get(key);
    const merged = existing ? { ...claim, id: existing.id } : claim;
    this.claims.set(key, merged);
    return merged;
  }

  async listClaims(researchJobId: Uuid): Promise<ClaimRecord[]> {
    return [...this.claims.values()].filter((c) => c.research_job_id === researchJobId)
      .sort((a, b) => a.claim_id.localeCompare(b.claim_id));
  }

  async createContentJob(job: ContentJob): Promise<ContentJob> {
    this.contentJobs.set(job.id, job);
    return job;
  }

  async updateContentJob(id: Uuid, patch: Partial<Omit<ContentJob, 'status'>>): Promise<ContentJob> {
    const cur = this.contentJobs.get(id);
    if (!cur) throw new Error(`content job ${id} not found`);
    // `status` is deliberately unreachable here; see `transition`.
    const { status: _ignored, ...safe } = patch as Partial<ContentJob>;
    const next = { ...cur, ...safe, id };
    this.contentJobs.set(id, next);
    return next;
  }

  async getContentJob(id: Uuid): Promise<ContentJob | null> { return this.contentJobs.get(id) ?? null; }
  async listContentJobs(userId: Uuid): Promise<ContentJob[]> {
    return [...this.contentJobs.values()].filter((j) => j.user_id === userId)
      .sort((a, b) => b.created_at.localeCompare(a.created_at));
  }

  async transition(id: Uuid, to: ContentState, actor: TransitionActor, note: string): Promise<ContentJob> {
    const cur = this.contentJobs.get(id);
    if (!cur) throw new TransitionError(`content job ${id} not found`);
    const verdict = canTransition(cur.status, to, actor);
    if (!verdict.ok) throw new TransitionError(`${cur.status} → ${to} rejected: ${verdict.reason}`);
    const next: ContentJob = {
      ...cur,
      status: to,
      review_stage: note,
      approved_at: to === 'approved_for_archive' ? new Date().toISOString() : cur.approved_at,
    };
    this.contentJobs.set(id, next);
    return next;
  }

  async upsertAsset(asset: ContentAsset): Promise<ContentAsset> {
    const key = `${asset.content_job_id}|${asset.asset_type}|${asset.storage_key}`;
    const existing = this.assets.get(key);
    const merged = existing ? { ...asset, id: existing.id } : asset;
    this.assets.set(key, merged);
    return merged;
  }

  async listAssets(contentJobId: Uuid): Promise<ContentAsset[]> {
    return [...this.assets.values()].filter((a) => a.content_job_id === contentJobId)
      .sort((a, b) => a.asset_type.localeCompare(b.asset_type) || a.storage_key.localeCompare(b.storage_key));
  }

  async replaceQualityChecks(contentJobId: Uuid, list: QualityCheck[]): Promise<QualityCheck[]> {
    this.checks.set(contentJobId, list);
    return list;
  }

  async listQualityChecks(contentJobId: Uuid): Promise<QualityCheck[]> { return this.checks.get(contentJobId) ?? []; }

  async recordReviewEvent(event: ReviewEvent): Promise<ReviewEvent> { this.reviews.push(event); return event; }
  async listReviewEvents(contentJobId: Uuid): Promise<ReviewEvent[]> {
    return this.reviews.filter((r) => r.content_job_id === contentJobId);
  }

  async beginRun(run: Omit<JobRun, 'trace' | 'provider_calls'>): Promise<{ run: JobRun; deduplicated: boolean }> {
    const seen = this.idempotency.get(run.idempotency_key);
    if (seen) {
      const prior = this.runs.get(seen)!;
      return { run: prior, deduplicated: true };
    }
    const created: JobRun = { ...run, trace: [], provider_calls: [] };
    this.runs.set(created.id, created);
    this.idempotency.set(created.idempotency_key, created.id);
    return { run: created, deduplicated: false };
  }

  async appendRunTrace(runId: Uuid, entry: JobRun['trace'][number]): Promise<void> {
    this.runs.get(runId)?.trace.push(entry);
  }

  async appendProviderCall(runId: Uuid, call: JobRun['provider_calls'][number]): Promise<void> {
    this.runs.get(runId)?.provider_calls.push(call);
  }

  async finishRun(runId: Uuid, status: JobRun['status'], errorSummary: string | null): Promise<JobRun> {
    const run = this.runs.get(runId);
    if (!run) throw new Error(`run ${runId} not found`);
    const next: JobRun = { ...run, status, error_summary: errorSummary, finished_at: new Date().toISOString() };
    this.runs.set(runId, next);
    return next;
  }

  async listRuns(limit: number): Promise<JobRun[]> {
    return [...this.runs.values()].sort((a, b) => b.started_at.localeCompare(a.started_at)).slice(0, limit);
  }
}
