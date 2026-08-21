import { join } from 'node:path';
import type { Repository } from '@/lib/db/types';
import type { Providers } from '@/lib/providers/types';
import type {
  BrandSettings, ClaimRecord, ContentAsset, ContentJob, ResearchJob, SourceDocument, Uuid,
} from '@/lib/domain';
import {
  analystBriefSchema, editorialPlanSchema, reviewerCritiqueSchema, scriptSchema,
  searchPlanSchema, sourceAssessmentSchema, thumbnailBriefSchema,
  type AnalystBrief, type EditorialPlan, type ReviewerCritique, type ScenePlan, type Script, type ThumbnailBrief,
} from '@/lib/schemas/content';
import type { EvidenceItem } from './payloads';
import { PROMPT_VERSION, systemPrompt, userPrompt } from './prompts';
import { evaluateClaim } from '@/lib/qa/claim-safety';
import { planScenes } from './visual-planner';
import type { DataRegistry } from './data-registry';
import { FIXTURE_SOURCES } from '@/lib/fixtures/northwind';
import { sha256, stableId } from '@/lib/util/hash';
import { estimateNarrationSeconds } from '@/lib/providers/voice/wav';
import { buildCaptionTimeline, toChaptersJson, toSrt, youtubeStamp } from '@/lib/video/captions';
import { buildDocument, type PreparedScene } from '@/lib/video/compose';
import { assembleNarration, peakDbfs, type Placement } from '@/lib/video/audio';
import { renderStill, renderVideo } from '@/lib/video/render';
import { runAllGates, isBlocked, type GateContext } from '@/lib/qa/gates';
import { SvgChartRenderer } from '@/lib/providers/chart/svg';
import { PermanentJobError } from '@/lib/providers/jobs/inline';
import type { ContentState } from '@/lib/workflow/states';

/**
 * The workflow engine.
 *
 * Every stage is a plain method with an explicit input and an explicit output,
 * and every state change goes through `repo.transition`. There is no method on
 * this class that approves, archives or publishes anything: approval belongs to
 * the reviewer routes, and publishing does not exist.
 */

export type EngineLogger = (level: 'info' | 'warn' | 'error', stage: string, message: string) => void;

export type EngineDeps = {
  repo: Repository;
  providers: Providers;
  registry: DataRegistry;
  log?: EngineLogger;
  now?: () => Date;
  /** Where rendered media is written before being stored. */
  workDir?: string;
};

export class WorkflowEngine {
  private readonly repo: Repository;
  private readonly p: Providers;
  private readonly registry: DataRegistry;
  private readonly log: EngineLogger;
  private readonly now: () => Date;
  private readonly workDir: string;
  private readonly charts = new SvgChartRenderer();

  constructor(deps: EngineDeps) {
    this.repo = deps.repo;
    this.p = deps.providers;
    this.registry = deps.registry;
    this.log = deps.log ?? (() => undefined);
    this.now = deps.now ?? (() => new Date());
    this.workDir = deps.workDir ?? join(process.cwd(), '.artifacts', 'render');
  }

  private iso(): string { return this.now().toISOString(); }

  // -------------------------------------------------------------------------
  // Stage 1 — intake
  // -------------------------------------------------------------------------

  async intake(input: {
    userId: Uuid; topic: string; ticker: string | null;
    jobType: ResearchJob['job_type']; referenceDate: string;
  }): Promise<ResearchJob> {
    if (!input.topic.trim()) throw new Error('intake requires a topic');
    if (!/^\d{4}-\d{2}-\d{2}$/u.test(input.referenceDate)) throw new Error('reference date must be YYYY-MM-DD');

    const id = stableId('aift_research_job', `${input.userId}:${input.topic}:${input.referenceDate}:${input.jobType}`);
    const existing = await this.repo.getResearchJob(id);
    if (existing) {
      this.log('info', 'intake', `research job already exists for this topic and reference date (${id})`);
      return existing;
    }

    return this.repo.createResearchJob({
      id, user_id: input.userId, topic: input.topic, ticker: input.ticker,
      job_type: input.jobType, source_policy_version: PROMPT_VERSION,
      status: 'queued', reference_date: input.referenceDate,
      created_at: this.iso(), completed_at: null, failure_reason: null,
      search_plan: null, brief: null,
    });
  }

  // -------------------------------------------------------------------------
  // Stages 2–4 — research plan, evidence, analyst brief
  // -------------------------------------------------------------------------

  async runResearch(researchJobId: Uuid, brand: BrandSettings): Promise<{
    job: ResearchJob; sources: SourceDocument[]; claims: ClaimRecord[];
  }> {
    const job = await this.repo.getResearchJob(researchJobId);
    if (!job) throw new Error(`research job ${researchJobId} not found`);

    await this.repo.updateResearchJob(job.id, { status: 'researching' });
    const context = await this.p.context.load(job.reference_date);
    this.log('info', 'research_plan', `private context loaded via ${this.p.context.name}: ${context.research_topics.length} topic(s), ${context.agent_rules.length} rule(s)`);

    const plan = await this.call('search_plan', 'fast', searchPlanSchema, {
      kind: 'search_plan', topic: job.topic, ticker: job.ticker,
      reference_date: job.reference_date,
      approved_source_domains: brand.approved_source_domains,
      private_context: context,
    });
    await this.repo.updateResearchJob(job.id, { search_plan: plan });
    this.log('info', 'research_plan', `${plan.queries.length} queries planned`);

    // --- evidence collection ------------------------------------------------
    const discovered = new Map<string, { url: string; title: string; snippet: string; publisher: string }>();
    for (const q of plan.queries) {
      for (const r of await this.p.research.discover(q.query, 6)) {
        if (!discovered.has(r.url)) discovered.set(r.url, r);
      }
    }
    this.log('info', 'evidence', `${discovered.size} unique candidate URL(s) discovered`);

    const assessment = await this.call('source_assessment', 'fast', sourceAssessmentSchema, {
      kind: 'source_assessment', topic: job.topic, discovered: [...discovered.values()],
    });
    const keep = new Set(assessment.assessments.filter((a) => a.relevance !== 'irrelevant').map((a) => a.canonical_url));

    const sources: SourceDocument[] = [];
    for (const url of keep) {
      const fetched = await this.p.research.fetchSource(url);
      const stored = await this.repo.upsertSourceDocument({
        id: stableId('aift_source_document', `${job.id}:${url}`),
        research_job_id: job.id,
        canonical_url: fetched.canonicalUrl,
        publisher: fetched.publisher,
        published_at: fetched.publishedAt,
        accessed_at: fetched.accessedAt,
        source_tier: tierFor(url),
        title: fetched.title,
        excerpt: fetched.excerpt,
        content_hash: fetched.contentHash,
        licence_notes: fetched.licenceNotes,
        retrieval_status: fetched.status,
      });
      sources.push(stored);
    }
    this.log('info', 'evidence', `${sources.filter((s) => s.retrieval_status === 'fetched').length}/${sources.length} source(s) fetched and stored`);

    // --- analyst brief ------------------------------------------------------
    const evidence: EvidenceItem[] = sources
      .filter((s) => s.retrieval_status === 'fetched')
      .map((s) => ({
        source_document_id: s.id,
        canonical_url: s.canonical_url,
        title: s.title,
        publisher: s.publisher,
        published_at: s.published_at,
        source_tier: s.source_tier,
        excerpt: s.excerpt,
        candidate_facts: (FIXTURE_SOURCES.find((f) => f.url === s.canonical_url)?.facts ?? []).map((f) => ({
          id: f.id, text: f.text, type: f.type, excerpt: f.excerpt,
          as_of: f.asOf, confidence: f.confidence, direction: f.direction, uncertainty: f.uncertainty,
        })),
      }));

    const brief = await this.call('analyst_brief', 'fast', analystBriefSchema, {
      kind: 'analyst_brief', topic: job.topic, ticker: job.ticker,
      reference_date: job.reference_date, evidence,
    });

    const claims: ClaimRecord[] = [];
    for (const c of brief.claims) {
      const verdict = evaluateClaim(c, sources);
      claims.push(await this.repo.upsertClaim({
        ...c,
        id: stableId('aift_claim', `${job.id}:${c.claim_id}`),
        research_job_id: job.id,
        review_status: 'unreviewed',
        is_public_safe: verdict.isPublicSafe,
        public_safe_reason: verdict.reason,
      }));
    }

    const safe = claims.filter((c) => c.is_public_safe).length;
    this.log('info', 'analyst_brief', `${claims.length} claim(s) extracted, ${safe} cleared as public-safe`);

    const updated = await this.repo.updateResearchJob(job.id, {
      status: 'evidence_ready', brief, completed_at: this.iso(),
    });
    return { job: updated, sources, claims };
  }

  // -------------------------------------------------------------------------
  // Content job creation
  // -------------------------------------------------------------------------

  async createContentJob(input: {
    userId: Uuid; researchJobId: Uuid; format: 'deep_dive' | 'short'; workingTitle: string;
  }): Promise<ContentJob> {
    const id = stableId('aift_content_job', `${input.researchJobId}:${input.format}`);
    const existing = await this.repo.getContentJob(id);
    if (existing) return existing;
    return this.repo.createContentJob({
      id, user_id: input.userId, research_job_id: input.researchJobId,
      format: input.format, working_title: input.workingTitle,
      status: 'queued', review_stage: 'created', script_version: 0,
      asset_manifest_url: null, created_at: this.iso(), approved_at: null,
      editorial_plan: null, script: null, scene_plan: null, thumbnail_brief: null,
    });
  }

  // -------------------------------------------------------------------------
  // Stages 5–9 — editorial, script, visual plan, render, QA
  // -------------------------------------------------------------------------

  async produce(contentJobId: Uuid, brand: BrandSettings, opts?: { renderVideo?: boolean; fps?: number }): Promise<{
    job: ContentJob; assets: ContentAsset[]; blocked: boolean;
  }> {
    const job0 = await this.repo.getContentJob(contentJobId);
    if (!job0) throw new Error(`content job ${contentJobId} not found`);
    const research = await this.repo.getResearchJob(job0.research_job_id);
    if (!research?.brief) throw new Error('content job has no completed research brief');

    const sources = await this.repo.listSourceDocuments(research.id);
    const claims = await this.repo.listClaims(research.id);
    const approved = claims.filter((c) => c.is_public_safe);

    // queued → researching → evidence_ready is owned by the research job; the
    // content job walks its own path from queued.
    await this.advance(contentJobId, 'drafting', `${approved.length}/${claims.length} claims cleared`);

    const editorial = await this.call('editorial_plan', 'fast', editorialPlanSchema, {
      kind: 'editorial_plan', topic: research.topic, ticker: research.ticker,
      brief: research.brief, channel_name: brand.channel_name, voice_guide: brand.voice_guide,
      audience_profile: brand.audience_profile, banned_phrases: brand.banned_phrases,
      target_minutes: job0.format === 'short' ? 1 : brand.default_video_length_minutes,
      format: job0.format,
    });

    const script = await this.call('script', 'fast', scriptSchema, {
      kind: 'script', format: job0.format, brief: research.brief, editorial,
      approved_claims: approved.map(toPlainClaim),
      disclosure_text: brand.disclosure_text, channel_name: brand.channel_name,
      reference_date: research.reference_date, banned_phrases: brand.banned_phrases,
    });

    await this.repo.updateContentJob(contentJobId, {
      editorial_plan: editorial, script, script_version: job0.script_version + 1,
      working_title: script.working_title,
    });
    this.log('info', 'script', `${script.beats.length} beats, ${countWords(script)} words`);

    // --- narration ----------------------------------------------------------
    await this.advance(contentJobId, 'visual_planning', 'narration + scene plan');
    const narrationSeconds = new Map<string, number>();
    const clips: Array<{ beatId: string; wav: Uint8Array }> = [];
    for (const beat of script.beats) {
      const clip = await this.p.voice.speak({
        text: beat.narration, voice: 'en-gb',
        targetSeconds: this.p.voice.isLive ? undefined : estimateNarrationSeconds(beat.narration),
      });
      narrationSeconds.set(beat.beat_id, clip.durationSeconds);
      clips.push({ beatId: beat.beat_id, wav: clip.wav });
    }

    const plan: ScenePlan = planScenes({
      script, claims: approved.map(toPlainClaim), brand,
      registry: this.registry, format: job0.format, narrationSeconds,
      bullCase: research.brief.bull_case, bearCase: research.brief.bear_case,
      sourceLabels: new Map(approved.map((c) => [
        c.claim_id,
        sources.find((s) => c.source_document_ids.includes(s.id))?.publisher ?? 'Stored source register',
      ])),
    });
    const thumbnail = buildThumbnailBrief(script, editorial, brand);
    await this.repo.updateContentJob(contentJobId, { scene_plan: plan, thumbnail_brief: thumbnail });
    this.log('info', 'visual_plan', `${plan.scenes.length} scenes, ${(plan.total_ms / 1000).toFixed(1)}s`);

    // --- render -------------------------------------------------------------
    await this.advance(contentJobId, 'rendering', 'assembling pack');
    const prefix = `${job0.user_id}/${contentJobId}/${job0.format}`;
    const assets: ContentAsset[] = [];
    const store = async (
      type: ContentAsset['asset_type'], name: string, data: Uint8Array | string, contentType: string,
      extra?: Partial<ContentAsset>,
    ) => {
      const stored = await this.p.storage.put(`${prefix}/${name}`, data, contentType);
      const asset = await this.repo.upsertAsset({
        id: stableId('aift_content_asset', `${contentJobId}:${type}:${stored.key}`),
        content_job_id: contentJobId, asset_type: type, storage_key: stored.key,
        sha256: stored.sha256, generator: `${this.p.llm.name}+${this.charts.name}`,
        prompt_version: PROMPT_VERSION, source_claim_ids: [], status: 'draft',
        duration_seconds: null, aspect_ratio: null, bytes: stored.bytes,
        created_at: this.iso(), ...extra,
      });
      assets.push(asset);
      return asset;
    };

    const captions = buildCaptionTimeline(script, plan, narrationSeconds);
    const srt = toSrt(captions);
    const aspect = job0.format === 'short' ? '9:16' : '16:9';

    // Charts are pre-rendered here, in Node, by the same renderer whose
    // `visibleValues()` the visual gate checks. The frames the encoder receives
    // are therefore produced by audited code, not by anything in the page.
    const renderedChartValues = new Map<string, string[]>();
    const prepared: PreparedScene[] = [];
    const chartStepMs = 1000 / (opts?.fps ?? plan.fps);

    for (const scene of plan.scenes) {
      if ((scene.composition === 'line_chart' || scene.composition === 'bar_chart') && scene.data) {
        const drawMs = Math.min(1800, scene.duration_ms * 0.55);
        const steps = Math.max(2, Math.ceil(drawMs / chartStepMs));
        const palette = {
          ink: brand.visual_style.ink, inkDim: brand.visual_style.ink_dim,
          accent: brand.visual_style.accent, accent2: brand.visual_style.accent_2,
          grid: 'rgba(140,151,168,0.16)', surface: brand.visual_style.surface,
        };
        const size = job0.format === 'short'
          ? { width: 940, height: 820 }
          : { width: 1560, height: 700 };
        const frames: string[] = [];
        for (let i = 0; i <= steps; i += 1) {
          frames.push(this.charts.renderSvg({
            kind: scene.composition === 'bar_chart' ? 'bar' : 'line',
            ...size,
            series: scene.data.series,
            yLabel: scene.data.y_label, xLabel: scene.data.x_label,
            sourceLabel: scene.data.source_label, asOfDate: scene.data.as_of_date,
            highlightIndex: scene.data.highlight_index,
            progress: i / steps, palette,
          }));
        }
        renderedChartValues.set(scene.scene_id, this.charts.visibleValues({
          kind: 'line', ...size, series: scene.data.series, yLabel: '', xLabel: '',
          sourceLabel: scene.data.source_label, asOfDate: scene.data.as_of_date,
          highlightIndex: null, progress: 1,
          palette: { ink: '', inkDim: '', accent: '', accent2: '', grid: '', surface: '' },
        }));
        prepared.push({ scene, chartFrames: frames, chartStepMs });
      } else if (scene.composition === 'broll' && scene.broll_prompt) {
        const media = await this.p.media.generate({
          prompt: scene.broll_prompt, aspect, seed: plan.scenes.indexOf(scene), kind: 'image',
        });
        const b64 = Buffer.from(media.bytes).toString('base64');
        prepared.push({ scene, brollDataUri: `data:${media.mimeType};base64,${b64}` });
        await store('broll_prompt', `broll/${scene.scene_id}.txt`, scene.broll_prompt, 'text/plain', {
          generator: media.generator,
        });
      } else {
        prepared.push({ scene });
      }
    }

    const html = buildDocument({
      plan, script, brand, prepared, captions,
      formatLabel: job0.format === 'short' ? 'Short' : 'Deep dive',
    });

    const audioWav = assembleNarration(
      clips.map((c): Placement => {
        const scene = plan.scenes.find((s) => s.beat_ids.includes(c.beatId));
        return { wav: c.wav, startMs: (scene?.start_ms ?? 0) + 260 };
      }),
      plan.total_ms,
    );
    const audioPeak = peakDbfs(audioWav);

    // Text assets
    await store('script_markdown', 'script.md', scriptMarkdown(script, plan, brand), 'text/markdown');
    await store('script_json', 'script.json', JSON.stringify(script, null, 2), 'application/json');
    await store('scene_plan', 'scene_plan.json', JSON.stringify(plan, null, 2), 'application/json');
    await store('narration_text', 'narration.txt', script.beats.map((b) => b.narration).join('\n\n'), 'text/plain');
    await store('captions_srt', 'captions.srt', srt, 'application/x-subrip');
    await store('chapters_json', 'chapters.json', toChaptersJson(script, plan), 'application/json');
    await store('description_markdown', 'description.md', descriptionWithChapters(script, plan, brand), 'text/markdown');
    await store('title_options', 'title_options.json', JSON.stringify(editorial.title_options, null, 2), 'application/json');
    await store('thumbnail_brief', 'thumbnail_brief.json', JSON.stringify(thumbnail, null, 2), 'application/json');
    await store('source_manifest', 'source_manifest.json', sourceManifest(sources, claims, research.reference_date), 'application/json');
    await store('audio_wav', 'narration.wav', audioWav, 'audio/wav', { duration_seconds: plan.total_ms / 1000 });
    // The editable motion-graphics source, stored alongside the render so a
    // human can open it, change a card and re-render without the pipeline.
    await store('composition_html', 'composition.html', html, 'text/html');

    // Media
    let videoBytes = 0;
    if (opts?.renderVideo !== false) {
      const { mkdir } = await import('node:fs/promises');
      await mkdir(this.workDir, { recursive: true });
      const mp4Path = join(this.workDir, `${contentJobId}-${job0.format}.mp4`);
      const posterPath = join(this.workDir, `${contentJobId}-${job0.format}-poster.png`);

      const result = await renderVideo({
        html, width: plan.width, height: plan.height, fps: opts?.fps ?? plan.fps,
        totalMs: plan.total_ms, audioWav, outPath: mp4Path,
        onProgress: (f, n) => {
          if (f % 300 === 0 || f === n) this.log('info', 'render', `frame ${f}/${n} (${((f / n) * 100).toFixed(0)}%)`);
        },
      });
      videoBytes = result.bytes;

      const { readFile } = await import('node:fs/promises');
      await store('video_mp4', job0.format === 'short' ? 'short.mp4' : 'video.mp4', new Uint8Array(await readFile(mp4Path)), 'video/mp4', {
        duration_seconds: result.durationSeconds, aspect_ratio: aspect, generator: result.encoder,
      });

      await renderStill({ html, width: plan.width, height: plan.height, atMs: 900, outPath: posterPath });
      await store('thumbnail_png', 'poster.png', new Uint8Array(await readFile(posterPath)), 'image/png', {
        aspect_ratio: aspect, generator: 'composition-still@1',
      });
    } else {
      this.log('warn', 'render', 'video rendering skipped by caller; pack is text-only');
    }

    // --- QA -----------------------------------------------------------------
    await this.advance(contentJobId, 'qa_running', 'quality gates');

    const critique = await this.call('reviewer_critique', 'review', reviewerCritiqueSchema, {
      kind: 'reviewer_critique', script,
      approved_claim_ids: approved.map((c) => c.claim_id),
      disclosure_text: brand.disclosure_text, banned_phrases: brand.banned_phrases,
    }).catch((err: unknown): ReviewerCritique | null => {
      this.log('warn', 'qa', `independent reviewer unavailable: ${err instanceof Error ? err.message : String(err)}`);
      return null;
    });

    const gateCtx: GateContext = {
      contentJobId, format: job0.format, brand, script, plan, claims, sources,
      assets, critique, renderedChartValues,
      audioPeakDbfs: audioPeak, videoBytes,
      videoAspect: aspect,
      narrationSeconds: [...narrationSeconds.values()].reduce((a, b) => a + b, 0),
      runAt: this.iso(),
    };
    const checks = runAllGates(gateCtx);
    await this.repo.replaceQualityChecks(contentJobId, checks);

    const report = qualityReport(checks, plan, script);
    await store('quality_report', 'quality_report.md', report, 'text/markdown');
    await store('package_manifest', 'manifest.json', JSON.stringify({
      content_job_id: contentJobId, format: job0.format, aspect_ratio: aspect,
      duration_seconds: plan.total_ms / 1000, reference_date: research.reference_date,
      prompt_version: PROMPT_VERSION,
      providers: {
        llm: this.p.llm.name, research: this.p.research.name, voice: this.p.voice.name,
        media: this.p.media.name, chart: this.charts.name, storage: this.p.storage.name,
      },
      assets: assets.map((a) => ({ type: a.asset_type, key: a.storage_key, sha256: a.sha256, bytes: a.bytes })),
      publishing: 'This package is for manual upload by the owner. The system has no upload capability.',
    }, null, 2), 'application/json');

    const blocked = isBlocked(checks);
    if (blocked) {
      await this.repo.transition(contentJobId, 'blocked', 'workflow',
        `${checks.filter((c) => c.result === 'fail' && c.severity === 'blocking').length} blocking check(s)`);
      this.log('warn', 'qa', 'job blocked by quality gates');
    } else {
      await this.advance(contentJobId, 'needs_review', 'awaiting owner review');
      this.log('info', 'qa', 'all blocking checks passed; job is in needs_review');
    }

    const finalJob = (await this.repo.getContentJob(contentJobId))!;
    return { job: finalJob, assets, blocked };
  }

  // -------------------------------------------------------------------------

  /**
   * The canonical forward path. `advance` walks it rather than jumping, so a job
   * that resumes mid-way — after a rework, or after a blocked run was cleared —
   * still passes through every state and every state change is still a legal,
   * recorded FSM edge.
   */
  private static readonly ORDER: ContentState[] = [
    'queued', 'researching', 'evidence_ready', 'drafting',
    'visual_planning', 'rendering', 'qa_running', 'needs_review',
  ];

  private async advance(id: Uuid, to: ContentState, note: string): Promise<void> {
    let job = await this.repo.getContentJob(id);
    if (!job) throw new Error(`content job ${id} not found`);

    if (job.status === 'rework_required') {
      job = await this.repo.transition(id, 'drafting', 'workflow', 'rework accepted');
    }
    if (job.status === 'blocked') {
      throw new PermanentJobError(
        'job is blocked; a reviewer must clear the blocking failures before production can resume',
      );
    }
    if (['needs_review', 'approved_for_archive', 'archived'].includes(job.status) && to !== 'needs_review') {
      throw new PermanentJobError(
        `job is in "${job.status}"; send it back for rework before producing again`,
      );
    }

    const target = WorkflowEngine.ORDER.indexOf(to);
    let i = WorkflowEngine.ORDER.indexOf(job.status);
    if (i < 0 || target < 0) return;
    while (i < target) {
      job = await this.repo.transition(id, WorkflowEngine.ORDER[i + 1]!, 'workflow', note);
      i += 1;
    }
  }

  private async call<T>(
    kind: Parameters<typeof systemPrompt>[0],
    role: 'fast' | 'review',
    schema: import('zod').ZodType<T, import('zod').ZodTypeDef, unknown>,
    payload: import('./payloads').StagePayload,
  ): Promise<T> {
    const res = await this.p.llm.complete({
      role, promptVersion: PROMPT_VERSION,
      system: systemPrompt(kind), user: userPrompt(payload),
      schema, schemaName: kind, payload,
    });
    this.log('info', kind, `${res.usage.provider}/${res.usage.model} returned valid ${kind} in ${res.attempts} attempt(s)`);
    return res.value;
  }
}

// ---------------------------------------------------------------------------

function toPlainClaim(c: ClaimRecord) {
  return {
    claim_id: c.claim_id, claim_text: c.claim_text, claim_type: c.claim_type,
    source_document_ids: c.source_document_ids, source_excerpt: c.source_excerpt,
    as_of_date: c.as_of_date, confidence: c.confidence, uncertainty_note: c.uncertainty_note,
  };
}

function tierFor(url: string): string {
  const f = FIXTURE_SOURCES.find((s) => s.url === url);
  if (f) return f.tier;
  if (/sec\.gov|investor\./iu.test(url)) return 'primary_filing';
  if (/\.gov|europa\.eu|bankofengland/iu.test(url)) return 'primary_regulator';
  return 'journalism';
}

function countWords(script: Script): number {
  return script.beats.reduce((n, b) => n + b.narration.trim().split(/\s+/u).filter(Boolean).length, 0);
}

function buildThumbnailBrief(script: Script, editorial: EditorialPlan, brand: BrandSettings): ThumbnailBrief {
  const primary = editorial.title_options[0]!.title.split(/[:—]/u)[0]!.trim().slice(0, 26).toUpperCase();
  return thumbnailBriefSchema.parse({
    concept:
      `Single dominant figure from the filing, set left, with the counter-case named in small type beneath. ` +
      `No face, no arrow, no red circle. The promise is "the filing, read properly", so the thumbnail should ` +
      `look like a document rather than a reaction.`,
    primary_text: primary || 'THE FILING',
    secondary_text: script.reference_date,
    visual_direction:
      `Dark editorial ground with a single accent light from upper left. One code-rendered chart fragment at ` +
      `12% opacity behind the type. Type is the subject; imagery is texture. Legible at 320px wide.`,
    palette: [brand.visual_style.background, brand.visual_style.accent, brand.visual_style.ink],
    forbidden: [
      'Any performance figure not present in the claim ledger',
      'Fabricated screenshots or fake broker interfaces',
      'Company logos or trademarks',
      'Text smaller than 48px at 1280×720',
      'Arrows, shock faces, or red circles implying a prediction',
    ],
  });
}

function scriptMarkdown(script: Script, plan: ScenePlan, brand: BrandSettings): string {
  const lines: string[] = [
    `# ${script.working_title}`, '',
    `**Channel:** ${brand.channel_name}  `,
    `**Reference date:** ${script.reference_date}  `,
    `**Runtime:** ${(plan.total_ms / 1000 / 60).toFixed(1)} minutes  `,
    `**Beats:** ${script.beats.length} · **Scenes:** ${plan.scenes.length}`, '',
    '---', '',
  ];
  let current = '';
  for (const [i, beat] of script.beats.entries()) {
    if (beat.chapter !== current) {
      current = beat.chapter;
      const scene = plan.scenes[i];
      lines.push('', `## ${beat.chapter} — ${youtubeStamp(scene?.start_ms ?? 0)}`, '');
    }
    const scene = plan.scenes[i];
    lines.push(`### ${beat.beat_id} · ${beat.visual_intent}${beat.claim_ids.length ? ` · claims: ${beat.claim_ids.join(', ')}` : ''}`);
    lines.push('');
    lines.push(`> ${beat.narration}`);
    if (beat.on_screen_text) lines.push('', `**On screen:** ${beat.on_screen_text}`);
    if (scene) lines.push('', `_${(scene.duration_ms / 1000).toFixed(1)}s · ${scene.composition}_`);
    lines.push('');
  }
  lines.push('---', '', '## Disclosure', '', script.disclosure_text, '');
  return lines.join('\n');
}

function descriptionWithChapters(script: Script, plan: ScenePlan, brand: BrandSettings): string {
  const chapterLines = script.chapters.map((c) => {
    const i = script.beats.findIndex((b) => b.beat_id === c.start_beat);
    return `${youtubeStamp(plan.scenes[Math.max(0, i)]?.start_ms ?? 0)} ${c.title}`;
  }).join('\n');

  return [
    script.description_markdown.replace(/^- —.*$/gmu, '').replace(/### Chapters\n\n?/u, `### Chapters\n${chapterLines}\n`),
    '', '---', '',
    `${brand.channel_name} · ${script.reference_date}`,
    '', script.disclosure_text, '',
    `Tags: ${script.tags.join(', ')}`,
  ].join('\n');
}

function sourceManifest(sources: SourceDocument[], claims: ClaimRecord[], referenceDate: string): string {
  return JSON.stringify({
    reference_date: referenceDate,
    generated_at: new Date(0).toISOString().slice(0, 10),
    sources: sources.map((s) => ({
      id: s.id, url: s.canonical_url, title: s.title, publisher: s.publisher,
      published_at: s.published_at, accessed_at: s.accessed_at, tier: s.source_tier,
      content_sha256: s.content_hash, licence_notes: s.licence_notes, retrieval_status: s.retrieval_status,
    })),
    claims: claims.map((c) => ({
      claim_id: c.claim_id, text: c.claim_text, type: c.claim_type,
      source_document_ids: c.source_document_ids, excerpt: c.source_excerpt,
      as_of_date: c.as_of_date, confidence: c.confidence,
      is_public_safe: c.is_public_safe, reason: c.public_safe_reason,
    })),
  }, null, 2);
}

function qualityReport(checks: ReturnType<typeof runAllGates>, plan: ScenePlan, script: Script): string {
  const blocking = checks.filter((c) => c.result === 'fail' && c.severity === 'blocking');
  const warnings = checks.filter((c) => c.result === 'fail' && c.severity === 'warning');
  const passed = checks.filter((c) => c.result === 'pass');

  const lines = [
    `# Quality report — ${script.working_title}`, '',
    `**Verdict:** ${blocking.length === 0 ? 'PASS — ready for owner review' : `BLOCKED — ${blocking.length} blocking failure(s)`}  `,
    `**Checks:** ${passed.length} passed · ${warnings.length} warning(s) · ${blocking.length} blocking  `,
    `**Runtime:** ${(plan.total_ms / 1000 / 60).toFixed(2)} min · ${plan.scenes.length} scenes · ${plan.width}×${plan.height} @ ${plan.fps}fps`,
    '',
  ];

  if (blocking.length > 0) {
    lines.push('## Blocking failures', '');
    for (const c of blocking) {
      lines.push(`### ✗ ${c.gate} / ${c.check_name}`, '', c.details.message, '');
      if (c.details.offenders.length) lines.push(...c.details.offenders.map((o) => `- \`${o}\``), '');
      lines.push(`**Fix:** ${c.details.remediation}`, '');
    }
  }
  if (warnings.length > 0) {
    lines.push('## Warnings', '');
    for (const c of warnings) lines.push(`- **${c.gate}/${c.check_name}** — ${c.details.message}`);
    lines.push('');
  }
  lines.push('## Passed', '');
  for (const c of passed) lines.push(`- ✓ **${c.gate}/${c.check_name}** — ${c.details.message}`);
  lines.push('', '---', '',
    '_No step in this system uploads, schedules or publishes anything. This package exists for the owner to review and, if they choose, upload by hand._');
  return lines.join('\n');
}
