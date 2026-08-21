import { beforeAll, describe, expect, it } from 'vitest';
import type { BrandSettings, ClaimRecord, ContentAsset, ContentJob, QualityCheck } from '@/lib/domain';
import { MemoryRepository } from '@/lib/db/memory';
import { DEFAULT_BRAND_SETTINGS } from '@/lib/db/defaults';
import { WorkflowEngine } from '@/lib/workflow/engine';
import { MockLLMProvider } from '@/lib/providers/llm/mock';
import { MockResearchProvider } from '@/lib/providers/research/mock';
import { SvgChartRenderer } from '@/lib/providers/chart/svg';
import { MockMediaProvider } from '@/lib/providers/media/mock';
import { MockVoiceProvider } from '@/lib/providers/voice/mock';
import { ProceduralMusicProvider } from '@/lib/providers/music/procedural';
import { LocalStorageProvider } from '@/lib/providers/storage/local';
import { InlineJobRunner } from '@/lib/providers/jobs/inline';
import { MockContextProvider } from '@/lib/providers/context';
import { FixtureDataRegistry } from '@/lib/workflow/data-registry';
import { FIXTURE_TOPIC } from '@/lib/fixtures/northwind';
import { TransitionError } from '@/lib/db/types';
import { stableId } from '@/lib/util/hash';
import { join } from 'node:path';
import { mkdtemp } from 'node:fs/promises';
import { tmpdir } from 'node:os';

const USER = stableId('aift_user', 'test-owner');
const REVIEWER = USER;

async function makeEngine(brand: BrandSettings) {
  const repo = new MemoryRepository();
  const root = await mkdtemp(join(tmpdir(), 'aift-test-'));
  const engine = new WorkflowEngine({
    repo,
    registry: new FixtureDataRegistry(),
    providers: {
      llm: new MockLLMProvider(),
      research: new MockResearchProvider(),
      chart: new SvgChartRenderer(),
      media: new MockMediaProvider(),
      voice: new MockVoiceProvider(),
      music: new ProceduralMusicProvider(),
      storage: new LocalStorageProvider(root),
      jobs: new InlineJobRunner(repo),
      context: new MockContextProvider(brand.private_context_allowlist),
    },
  });
  await repo.updateBrandSettings(USER, brand);
  return { repo, engine };
}

type Produced = {
  repo: MemoryRepository; engine: WorkflowEngine; job: ContentJob;
  assets: ContentAsset[]; checks: QualityCheck[]; claims: ClaimRecord[];
};

async function produceDeepDive(brandOverride: Partial<BrandSettings> = {}): Promise<Produced> {
  const brand: BrandSettings = { ...DEFAULT_BRAND_SETTINGS, user_id: USER, ...brandOverride };
  const { repo, engine } = await makeEngine(brand);
  const research = await engine.intake({
    userId: USER, topic: FIXTURE_TOPIC.topic, ticker: FIXTURE_TOPIC.ticker,
    jobType: 'deep_dive', referenceDate: FIXTURE_TOPIC.referenceDate,
  });
  const { claims } = await engine.runResearch(research.id, brand);
  const created = await engine.createContentJob({
    userId: USER, researchJobId: research.id, format: 'deep_dive', workingTitle: FIXTURE_TOPIC.topic,
  });
  // Video rendering is exercised separately; these tests are about the rules.
  const { job, assets } = await engine.produce(created.id, brand, { renderVideo: false });
  return { repo, engine, job, assets, checks: await repo.listQualityChecks(created.id), claims };
}

describe('a complete content pack', () => {
  let out: Produced;
  beforeAll(async () => { out = await produceDeepDive(); }, 120_000);

  it('produces every artefact the hand-off requires', () => {
    const types = new Set(out.assets.map((a) => a.asset_type));
    for (const t of ['script_markdown', 'script_json', 'scene_plan', 'narration_text',
      'captions_srt', 'chapters_json', 'description_markdown', 'title_options',
      'thumbnail_brief', 'source_manifest', 'quality_report', 'package_manifest'] as const) {
      expect(types, `${t} missing from the pack`).toContain(t);
    }
  });

  it('records a content hash and a generator for every asset', () => {
    for (const a of out.assets) {
      expect(a.sha256, a.storage_key).toMatch(/^[0-9a-f]{64}$/u);
      expect(a.generator.length).toBeGreaterThan(0);
      expect(a.prompt_version.length).toBeGreaterThan(0);
    }
  });

  it('binds every spoken figure to a stored claim', () => {
    const script = out.job.script!;
    const known = new Set(out.claims.map((c) => c.claim_id));
    for (const beat of script.beats) {
      for (const id of beat.claim_ids) expect(known).toContain(id);
    }
    const orphan = out.checks.find((c) => c.check_name === 'no_unsourced_figures');
    expect(orphan?.result).toBe('pass');
  });

  it('withholds claims that failed the evidence check from the writer', () => {
    const unsafe = out.claims.filter((c) => !c.is_public_safe).map((c) => c.claim_id);
    const cited = new Set(out.job.script!.beats.flatMap((b) => b.claim_ids));
    for (const id of unsafe) expect(cited).not.toContain(id);
    // The fixture deliberately contains at least one claim that cannot be cleared.
    expect(unsafe.length).toBeGreaterThan(0);
  });

  it('gives every claim a reason, whether it passed or not', () => {
    for (const c of out.claims) expect(c.public_safe_reason.length).toBeGreaterThan(10);
  });

  it('speaks the disclosure and repeats it in the description', () => {
    const narration = out.job.script!.beats.map((b) => b.narration).join(' ');
    expect(narration).toContain(DEFAULT_BRAND_SETTINGS.disclosure_text);
    expect(out.job.script!.description_markdown).toContain(DEFAULT_BRAND_SETTINGS.disclosure_text);
  });

  it('lands in the 8–12 minute band', () => {
    const minutes = out.job.scene_plan!.total_ms / 60_000;
    expect(minutes).toBeGreaterThan(7);
    expect(minutes).toBeLessThan(13);
  });

  it('stamps every data scene with a source and an as-of date', () => {
    for (const scene of out.job.scene_plan!.scenes) {
      if (scene.data) {
        expect(scene.data.source_label.length).toBeGreaterThan(3);
        expect(scene.data.as_of_date).toMatch(/^\d{4}-\d{2}-\d{2}$/u);
        expect(scene.data.claim_ids.length).toBeGreaterThan(0);
      }
      if (scene.stat) {
        expect(scene.stat.source_label.length).toBeGreaterThan(3);
        expect(scene.stat.as_of_date).toMatch(/^\d{4}-\d{2}-\d{2}$/u);
      }
    }
  });

  it('stops at needs_review or blocked — never anywhere further on', () => {
    expect(['needs_review', 'blocked']).toContain(out.job.status);
    expect(out.job.approved_at).toBeNull();
  });

  it('passes every non-video blocking gate', () => {
    const blocking = out.checks.filter(
      (c) => c.result === 'fail' && c.severity === 'blocking' && !['video_present', 'pack_complete'].includes(c.check_name),
    );
    expect(blocking.map((c) => `${c.gate}/${c.check_name}: ${c.details.message}`)).toEqual([]);
  });

  it('states a remediation for every failing check', () => {
    for (const c of out.checks.filter((x) => x.result === 'fail')) {
      expect(c.details.remediation.length, `${c.check_name} has no remediation`).toBeGreaterThan(5);
    }
  });
});

describe('quality gates block the things they are supposed to block', () => {
  it('blocks a script that mentions a personal portfolio value', async () => {
    const out = await produceDeepDive();
    const { runAllGates, isBlocked } = await import('@/lib/qa/gates');
    const script = structuredClone(out.job.script!);
    script.beats[3]!.narration = 'My portfolio is up £84,000 this year on this position alone.';

    const checks = runAllGates(await gateContext(out, { script }));
    expect(isBlocked(checks)).toBe(true);
    const hit = checks.find((c) => c.check_name === 'no_private_finance_in_public_copy');
    expect(hit?.result).toBe('fail');
    expect(hit?.details.offenders.join(' ')).toMatch(/portfolio/iu);
  }, 120_000);

  it('blocks a script with a missing disclosure', async () => {
    const out = await produceDeepDive();
    const { runAllGates } = await import('@/lib/qa/gates');
    const script = structuredClone(out.job.script!);
    for (const b of script.beats) b.narration = b.narration.replace(DEFAULT_BRAND_SETTINGS.disclosure_text, 'Thanks for watching.');

    const checks = runAllGates(await gateContext(out, { script }));
    expect(checks.find((c) => c.check_name === 'disclosure_present')?.result).toBe('fail');
  }, 120_000);

  it('blocks a script that instructs the viewer to trade', async () => {
    const out = await produceDeepDive();
    const { runAllGates } = await import('@/lib/qa/gates');
    const script = structuredClone(out.job.script!);
    script.beats[2]!.narration = 'You should buy this before the next print.';

    const checks = runAllGates(await gateContext(out, { script }));
    expect(checks.find((c) => c.check_name === 'no_trade_instruction')?.result).toBe('fail');
    expect(checks.find((c) => c.check_name === 'no_banned_phrases')?.result).toBe('fail');
  }, 120_000);

  it('blocks a figure stated with no claim behind it', async () => {
    const out = await produceDeepDive();
    const { runAllGates } = await import('@/lib/qa/gates');
    const script = structuredClone(out.job.script!);
    script.beats[4]!.narration = 'Margins are heading for 74% next year.';
    script.beats[4]!.claim_ids = [];

    const checks = runAllGates(await gateContext(out, { script }));
    const hit = checks.find((c) => c.check_name === 'no_unsourced_figures');
    expect(hit?.result).toBe('fail');
    expect(hit?.details.offenders.join(' ')).toContain('74%');
  }, 120_000);

  it('blocks certainty about future performance', async () => {
    const out = await produceDeepDive();
    const { runAllGates } = await import('@/lib/qa/gates');
    const script = structuredClone(out.job.script!);
    script.beats[5]!.narration = 'This will definitely re-rate once the cycle turns.';

    const checks = runAllGates(await gateContext(out, { script }));
    expect(checks.find((c) => c.check_name === 'no_performance_certainty')?.result).toBe('fail');
  }, 120_000);

  it('rejects a generated image used as a chart', async () => {
    const out = await produceDeepDive();
    const { runAllGates } = await import('@/lib/qa/gates');
    const plan = structuredClone(out.job.scene_plan!);
    const chartScene = plan.scenes.find((s) => s.data !== null)!;
    // Someone swaps a code-rendered chart for generated imagery, keeping the data.
    chartScene.composition = 'broll';
    chartScene.broll_prompt = 'A cinematic chart of quarterly revenue rising to $4.61 billion';

    const checks = runAllGates(await gateContext(out, { plan }));
    expect(checks.find((c) => c.check_name === 'no_generated_image_as_chart')?.result).toBe('fail');
    expect(checks.find((c) => c.check_name === 'broll_prompts_non_factual')?.result).toBe('fail');
  }, 120_000);

  it('rejects an on-screen figure that is not in the claim ledger', async () => {
    const out = await produceDeepDive();
    const { runAllGates } = await import('@/lib/qa/gates');
    const plan = structuredClone(out.job.scene_plan!);
    const statScene = plan.scenes.find((s) => s.stat !== null);
    if (!statScene?.stat) return; // no stat card in this plan; the chart case covers it
    statScene.stat.value = '$99.9 billion';

    const checks = runAllGates(await gateContext(out, { plan }));
    const hit = checks.find((c) => c.check_name.startsWith('scene_values_match_claims:'));
    expect(hit?.result).toBe('fail');
  }, 120_000);
});

describe('approval', () => {
  it('cannot be performed by the workflow engine', async () => {
    const out = await produceDeepDive();
    if (out.job.status !== 'needs_review') return;
    await expect(out.repo.transition(out.job.id, 'approved_for_archive', 'workflow', 'auto'))
      .rejects.toBeInstanceOf(TransitionError);
    await expect(out.repo.transition(out.job.id, 'archived', 'workflow', 'auto'))
      .rejects.toBeInstanceOf(TransitionError);
  }, 120_000);

  it('requires approval before archival, in that order, by a reviewer', async () => {
    const out = await produceDeepDive();
    if (out.job.status !== 'needs_review') return;

    await expect(out.repo.transition(out.job.id, 'archived', 'reviewer', 'skip approval'))
      .rejects.toBeInstanceOf(TransitionError);

    const approved = await out.repo.transition(out.job.id, 'approved_for_archive', 'reviewer', 'looks right');
    expect(approved.approved_at).not.toBeNull();

    await out.repo.recordReviewEvent({
      id: 'rev-1', content_job_id: out.job.id, reviewer_id: REVIEWER,
      decision: 'approved_for_archive', reason_codes: ['evidence_ok'],
      freeform_feedback: '', created_at: new Date().toISOString(),
    });

    const archived = await out.repo.transition(out.job.id, 'archived', 'reviewer', 'stored for manual upload');
    expect(archived.status).toBe('archived');

    // And archived is the end of the line.
    await expect(out.repo.transition(out.job.id, 'drafting', 'reviewer', 'reopen'))
      .rejects.toBeInstanceOf(TransitionError);
  }, 120_000);
});

describe('idempotency', () => {
  it('does not duplicate sources, claims or assets when a job is re-run', async () => {
    const brand: BrandSettings = { ...DEFAULT_BRAND_SETTINGS, user_id: USER };
    const { repo, engine } = await makeEngine(brand);

    const first = await engine.intake({
      userId: USER, topic: FIXTURE_TOPIC.topic, ticker: FIXTURE_TOPIC.ticker,
      jobType: 'deep_dive', referenceDate: FIXTURE_TOPIC.referenceDate,
    });
    const second = await engine.intake({
      userId: USER, topic: FIXTURE_TOPIC.topic, ticker: FIXTURE_TOPIC.ticker,
      jobType: 'deep_dive', referenceDate: FIXTURE_TOPIC.referenceDate,
    });
    expect(second.id).toBe(first.id);
    expect((await repo.listResearchJobs(USER)).length).toBe(1);

    await engine.runResearch(first.id, brand);
    const sources1 = (await repo.listSourceDocuments(first.id)).length;
    const claims1 = (await repo.listClaims(first.id)).length;

    await engine.runResearch(first.id, brand);
    expect((await repo.listSourceDocuments(first.id)).length).toBe(sources1);
    expect((await repo.listClaims(first.id)).length).toBe(claims1);

    const job = await engine.createContentJob({
      userId: USER, researchJobId: first.id, format: 'deep_dive', workingTitle: 't',
    });
    await engine.produce(job.id, brand, { renderVideo: false });
    const assets1 = (await repo.listAssets(job.id)).length;
    const checks1 = (await repo.listQualityChecks(job.id)).length;

    // A blocked job returns to drafting through a reviewer, then re-produces.
    const current = await repo.getContentJob(job.id);
    if (current?.status === 'blocked') await repo.transition(job.id, 'drafting', 'reviewer', 'retry');
    else if (current?.status === 'needs_review') await repo.transition(job.id, 'rework_required', 'reviewer', 'retry');

    await engine.produce(job.id, brand, { renderVideo: false });
    expect((await repo.listAssets(job.id)).length).toBe(assets1);
    expect((await repo.listQualityChecks(job.id)).length).toBe(checks1);
  }, 180_000);

  it('treats a second trigger with the same key as a no-op', async () => {
    const repo = new MemoryRepository();
    const runner = new InlineJobRunner(repo);
    let runs = 0;
    runner.register<{ day: string }>({
      jobType: 'research_radar',
      idempotencyKey: (i) => `radar:${i.day}`,
      timeoutMs: 5_000, maxAttempts: 2,
      run: async () => { runs += 1; },
    });

    const a = await runner.trigger('research_radar', { day: '2026-08-21' });
    const b = await runner.trigger('research_radar', { day: '2026-08-21' });
    const c = await runner.trigger('research_radar', { day: '2026-08-22' });

    expect(a.deduplicated).toBe(false);
    expect(b.deduplicated).toBe(true);
    expect(b.runId).toBe(a.runId);
    expect(c.deduplicated).toBe(false);
    expect(runs).toBe(2);
  });

  it('retries a technical failure but never a permanent one', async () => {
    const { PermanentJobError } = await import('@/lib/providers/jobs/inline');
    const repo = new MemoryRepository();
    const runner = new InlineJobRunner(repo);

    let flaky = 0;
    runner.register<{ k: string }>({
      jobType: 'flaky', idempotencyKey: (i) => i.k, timeoutMs: 5_000, maxAttempts: 3,
      run: async () => { flaky += 1; if (flaky < 3) throw new Error('socket hang up'); },
    });
    await runner.trigger('flaky', { k: 'a' });
    expect(flaky).toBe(3);

    let permanent = 0;
    runner.register<{ k: string }>({
      jobType: 'compliance', idempotencyKey: (i) => i.k, timeoutMs: 5_000, maxAttempts: 5,
      run: async () => { permanent += 1; throw new PermanentJobError('evidence gate failed'); },
    });
    await runner.trigger('compliance', { k: 'b' });
    expect(permanent).toBe(1);
  });
});

describe('determinism', () => {
  it('produces an identical script from an identical brief', async () => {
    const a = await produceDeepDive();
    const b = await produceDeepDive();
    expect(JSON.stringify(a.job.script)).toBe(JSON.stringify(b.job.script));
    expect(JSON.stringify(a.job.scene_plan)).toBe(JSON.stringify(b.job.scene_plan));
  }, 240_000);
});

// ---------------------------------------------------------------------------

async function gateContext(out: Produced, over: { script?: ContentJob['script']; plan?: ContentJob['scene_plan'] }) {
  const { SvgChartRenderer: R } = await import('@/lib/providers/chart/svg');
  const charts = new R();
  const plan = over.plan ?? out.job.scene_plan!;
  const rendered = new Map<string, string[]>();
  for (const s of plan.scenes) {
    if (!s.data) continue;
    rendered.set(s.scene_id, charts.visibleValues({
      kind: 'line', width: 100, height: 100, series: s.data.series, yLabel: '', xLabel: '',
      sourceLabel: s.data.source_label, asOfDate: s.data.as_of_date, highlightIndex: null, progress: 1,
      palette: { ink: '', inkDim: '', accent: '', accent2: '', grid: '', surface: '' },
    }));
  }
  return {
    contentJobId: out.job.id,
    format: 'deep_dive' as const,
    brand: { ...DEFAULT_BRAND_SETTINGS, user_id: USER },
    script: over.script ?? out.job.script!,
    plan,
    claims: out.claims,
    sources: await out.repo.listSourceDocuments(out.job.research_job_id),
    assets: out.assets,
    critique: null,
    renderedChartValues: rendered,
    audioPeakDbfs: -3,
    loudness: { integratedLufs: -14.1, truePeakDbtp: -1.4, loudnessRange: 6.2 },
    targetLufs: -14,
    musicEnabled: false,
    duckDb: -11,
    narrationByBeat: new Map(plan.scenes.map((s) => [s.beat_ids[0]!, (s.duration_ms - 700) / 1000])),
    captionCueStartsMs: plan.scenes.map((s) => s.start_ms),
    videoBytes: 5_000_000,
    videoAspect: '16:9',
    narrationSeconds: plan.total_ms / 1000,
    runAt: new Date().toISOString(),
  };
}
