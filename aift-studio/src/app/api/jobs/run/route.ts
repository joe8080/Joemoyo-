import { createHmac, timingSafeEqual } from 'node:crypto';
import { NextResponse } from 'next/server';
import { env } from '@/lib/env';
import { getRuntime } from '@/lib/server/runtime';
import { registerRoutines } from '@/lib/workflow/routines';

export const dynamic = 'force-dynamic';
export const maxDuration = 300;

/**
 * The scheduler entry point.
 *
 * A platform cron, queue worker or CI job posts here. Requests are HMAC-signed:
 * without `AIFT_JOB_SIGNING_SECRET` set, the route refuses everything rather
 * than falling back to open access, because an unauthenticated job trigger on a
 * private tool is a worse failure than a broken schedule.
 *
 * The response says what ran and where it stopped. It cannot say "published",
 * because no job can reach that state — none exists.
 */
export async function POST(request: Request): Promise<NextResponse> {
  const secret = env().AIFT_JOB_SIGNING_SECRET;
  if (!secret) {
    return NextResponse.json(
      { error: 'AIFT_JOB_SIGNING_SECRET is not configured; the scheduler endpoint is closed.' },
      { status: 503 },
    );
  }

  const raw = await request.text();
  const provided = request.headers.get('x-aift-signature') ?? '';
  const expected = createHmac('sha256', secret).update(raw).digest('hex');

  const a = Buffer.from(provided, 'utf8');
  const b = Buffer.from(expected, 'utf8');
  if (a.length !== b.length || !timingSafeEqual(a, b)) {
    return NextResponse.json({ error: 'invalid signature' }, { status: 401 });
  }

  let body: { job_type?: string; input?: Record<string, unknown> };
  try {
    body = JSON.parse(raw) as typeof body;
  } catch {
    return NextResponse.json({ error: 'body must be JSON' }, { status: 400 });
  }

  const jobType = body.job_type;
  if (jobType !== 'research_radar' && jobType !== 'editorial_production') {
    return NextResponse.json(
      { error: 'job_type must be "research_radar" or "editorial_production"' },
      { status: 400 },
    );
  }

  await registerRoutines();
  const { providers, repo } = await getRuntime();
  const { runId, deduplicated } = await providers.jobs.trigger(jobType, body.input ?? {});
  const runs = await repo.listRuns(50);
  const run = runs.find((r) => r.id === runId);

  return NextResponse.json({
    run_id: runId,
    deduplicated,
    status: run?.status ?? 'unknown',
    error: run?.error_summary ?? null,
    trace: run?.trace.slice(-20) ?? [],
    note: 'Every routine finishes in needs_review or blocked. This system cannot upload, schedule or publish.',
  });
}

export function GET(): NextResponse {
  return NextResponse.json({
    routines: [
      { job_type: 'research_radar', cadence: 'weekdays 07:00', input: { day: 'YYYY-MM-DD' } },
      { job_type: 'editorial_production', cadence: 'weekly', input: { week: 'YYYY-Www', format: 'deep_dive | short' } },
    ],
    auth: 'POST with header x-aift-signature = HMAC-SHA256(body, AIFT_JOB_SIGNING_SECRET)',
  });
}
