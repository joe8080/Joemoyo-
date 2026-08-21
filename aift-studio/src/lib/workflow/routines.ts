import 'server-only';
import type { JobDefinition } from '@/lib/providers/types';
import { getBrand, getRuntime, ownerId } from '@/lib/server/runtime';
import { PermanentJobError } from '@/lib/providers/jobs/inline';

/**
 * The two recurring routines.
 *
 * Both are server-side job definitions with an idempotency key, a timeout and a
 * bounded retry policy. Neither can advance a job past `needs_review`, and
 * neither retries a compliance or evidence failure — those raise
 * `PermanentJobError`, which the runner records and stops on.
 *
 * Scheduling is external on purpose: a platform cron or queue calls
 * `/api/jobs/run`. Nothing here uses a browser timer or setInterval.
 */

export type RadarInput = { day: string };
export type ProductionInput = { week: string; format: 'deep_dive' | 'short' };

export const researchRadar: JobDefinition<RadarInput> = {
  jobType: 'research_radar',
  idempotencyKey: (i) => `research_radar:${i.day}`,
  timeoutMs: 10 * 60_000,
  maxAttempts: 3,
  async run(input, ctx) {
    const { engine, repo } = await getRuntime();
    const brand = await getBrand();

    ctx.log('info', 'radar', `building the private evidence digest for ${input.day}`);
    const context = await (await getRuntime()).providers.context.load(input.day);

    if (context.research_topics.length === 0) {
      // Not a technical failure — there is simply nothing queued. Retrying a
      // second time would produce the same nothing.
      throw new PermanentJobError('no research topics are queued; nothing to promote to a candidate');
    }

    for (const topic of context.research_topics.slice(0, 3)) {
      const job = await engine.intake({
        userId: ownerId(), topic: topic.topic, ticker: topic.ticker,
        jobType: 'radar', referenceDate: input.day,
      });
      const { claims } = await engine.runResearch(job.id, brand);
      const safe = claims.filter((c) => c.is_public_safe).length;

      // A candidate is only promoted when the evidence is actually good enough.
      if (safe < 3) {
        ctx.log('warn', 'radar', `"${topic.topic}" produced only ${safe} public-safe claim(s); leaving it as research, not a candidate`);
        await repo.updateResearchJob(job.id, { failure_reason: `insufficient evidence: ${safe} public-safe claims` });
        continue;
      }
      ctx.log('info', 'radar', `"${topic.topic}" is a candidate: ${safe} public-safe claims`);
    }
  },
};

export const editorialProduction: JobDefinition<ProductionInput> = {
  jobType: 'editorial_production',
  idempotencyKey: (i) => `editorial_production:${i.week}:${i.format}`,
  timeoutMs: 45 * 60_000,
  maxAttempts: 2,
  async run(input, ctx) {
    const { engine, repo } = await getRuntime();
    const brand = await getBrand();

    const candidates = (await repo.listResearchJobs(ownerId()))
      .filter((j) => j.status === 'evidence_ready' && !j.failure_reason);
    const chosen = candidates[0];
    if (!chosen) throw new PermanentJobError('no research job with sufficient evidence is available');

    ctx.log('info', 'production', `producing "${chosen.topic}" as ${input.format}`);
    const job = await engine.createContentJob({
      userId: ownerId(), researchJobId: chosen.id, format: input.format, workingTitle: chosen.topic,
    });

    const { blocked } = await engine.produce(job.id, brand, { renderVideo: true });
    ctx.log(blocked ? 'warn' : 'info', 'production',
      blocked ? 'pack is blocked by quality gates and is waiting for you' : 'pack is in needs_review and is waiting for you');
    // Either way the routine stops here. It cannot approve, archive or publish.
  },
};

export async function registerRoutines(): Promise<void> {
  const { providers } = await getRuntime();
  providers.jobs.register(researchRadar);
  providers.jobs.register(editorialProduction);
}
