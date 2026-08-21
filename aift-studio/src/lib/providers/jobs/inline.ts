import type { JobContext, JobDefinition, JobRunner } from '@/lib/providers/types';
import type { Repository } from '@/lib/db/types';
import { stableId } from '@/lib/util/hash';

/**
 * In-process job runner.
 *
 * Deliberately *not* a browser timer and not a `setInterval`. Scheduling is an
 * external concern: a platform cron, a queue worker or a signed webhook calls
 * `trigger`. This class only owns execution — idempotency, timeout, bounded
 * retry and the trace record.
 *
 * Retries are for technical failures only. A `PermanentJobError` — which is what
 * a compliance or evidence failure raises — is recorded and never retried.
 */
export class PermanentJobError extends Error {
  constructor(message: string) { super(message); this.name = 'PermanentJobError'; }
}

export class InlineJobRunner implements JobRunner {
  readonly name = 'inline-runner@1';
  private readonly defs = new Map<string, JobDefinition<unknown>>();

  constructor(private readonly repo: Repository) {}

  register<T>(def: JobDefinition<T>): void {
    this.defs.set(def.jobType, def as JobDefinition<unknown>);
  }

  async trigger<T>(jobType: string, input: T): Promise<{ runId: string; deduplicated: boolean }> {
    const def = this.defs.get(jobType);
    if (!def) throw new Error(`no job registered for type "${jobType}"`);

    const idempotencyKey = (def.idempotencyKey as (i: T) => string)(input);
    const runId = stableId('aift_job_run', `${jobType}:${idempotencyKey}`);

    const { deduplicated } = await this.repo.beginRun({
      id: runId,
      job_type: jobType,
      idempotency_key: idempotencyKey,
      status: 'running',
      started_at: new Date().toISOString(),
      finished_at: null,
      attempt_count: 0,
      error_summary: null,
    });

    if (deduplicated) {
      await this.repo.appendRunTrace(runId, {
        at: new Date().toISOString(), stage: 'runner', level: 'info',
        message: `duplicate trigger for idempotency key "${idempotencyKey}" — no work performed`,
      });
      return { runId, deduplicated: true };
    }

    let lastError: unknown = null;
    for (let attempt = 1; attempt <= def.maxAttempts; attempt += 1) {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), def.timeoutMs);
      const ctx: JobContext = {
        runId,
        signal: controller.signal,
        log: (level, stage, message) => {
          void this.repo.appendRunTrace(runId, { at: new Date().toISOString(), stage, level, message });
        },
        recordProviderCall: (usage) => {
          void this.repo.appendProviderCall(runId, {
            provider: usage.provider, model: usage.model, prompt_version: usage.promptVersion,
            input_tokens: usage.inputTokens, output_tokens: usage.outputTokens, cost_usd: usage.costUsd,
          });
        },
      };

      try {
        await def.run(input, ctx);
        clearTimeout(timer);
        await this.repo.finishRun(runId, 'succeeded', null);
        return { runId, deduplicated: false };
      } catch (err) {
        clearTimeout(timer);
        lastError = err;
        const permanent = err instanceof PermanentJobError;
        ctx.log('error', 'runner', `attempt ${attempt}/${def.maxAttempts} failed${permanent ? ' (permanent)' : ''}: ${message(err)}`);
        if (permanent) break;
        if (attempt < def.maxAttempts) {
          await sleep(Math.min(8_000, 250 * 2 ** attempt));
        }
      }
    }

    await this.repo.finishRun(runId, 'failed', message(lastError));
    return { runId, deduplicated: false };
  }
}

function message(err: unknown): string {
  return err instanceof Error ? err.message : String(err);
}
function sleep(ms: number): Promise<void> {
  return new Promise((r) => { setTimeout(r, ms); });
}
