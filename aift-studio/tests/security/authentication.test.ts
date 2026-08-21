import { describe, expect, it } from 'vitest';
import { readFile } from 'node:fs/promises';

/**
 * Approval must be an act by an identity, not a step in a pipeline. These tests
 * check the shape of that guarantee in the source, because the runtime path
 * needs Next's request context and the property being protected is structural:
 * *which* code can reach the reviewer transition.
 */
describe('the reviewer boundary', () => {
  it('routes every reviewer decision through requireReviewer', async () => {
    const actions = await readFile('src/app/actions.ts', 'utf8');
    for (const fn of ['approveForArchive', 'archivePack', 'requestRework']) {
      const start = actions.indexOf(`export async function ${fn}(`);
      expect(start, `${fn} is missing`).toBeGreaterThan(-1);
      const body = actions.slice(start, actions.indexOf('\n}', start));
      expect(body, `${fn} does not call requireReviewer`).toContain('await requireReviewer()');
      expect(body, `${fn} does not transition as a reviewer`).toContain("'reviewer'");
      expect(body, `${fn} does not record a review event`).toContain('recordReviewEvent');
    }
  });

  it('never lets a non-reviewer actor reach an approval transition', async () => {
    const actions = await readFile('src/app/actions.ts', 'utf8');
    const engine = await readFile('src/lib/workflow/engine.ts', 'utf8');
    for (const state of ['approved_for_archive', 'archived']) {
      // Only the reviewer actions may name these states in a transition call.
      const inEngine = new RegExp(`transition\\([^)]*'${state}'`, 'u').test(engine);
      expect(inEngine, `the workflow engine must not transition to ${state}`).toBe(false);
      expect(actions).toContain(`'${state}', 'reviewer'`);
    }
  });

  it('fails closed when Supabase Auth is configured but no session exists', async () => {
    const auth = await readFile('src/lib/server/auth.ts', 'utf8');
    const body = auth.slice(auth.indexOf('export async function requireReviewer'));
    expect(body).toContain('throw new NotAuthenticatedError()');
    // The local fallback is explicit and only applies when auth is unconfigured.
    expect(body).toContain('if (!supabaseAuthConfigured()) return LOCAL_OWNER_ID;');
  });

  it('protects every page behind the session when auth is configured', async () => {
    const mw = await readFile('src/middleware.ts', 'utf8');
    expect(mw).toContain('NextResponse.redirect');
    expect(mw).toContain("path === '/login'");
    // The scheduler authenticates by HMAC, not by cookie, so it is exempt here
    // and checked in its own route.
    expect(mw).toContain("path.startsWith('/api/jobs/')");

    const route = await readFile('src/app/api/jobs/run/route.ts', 'utf8');
    expect(route).toContain('timingSafeEqual');
    expect(route).toContain('AIFT_JOB_SIGNING_SECRET is not configured');
    expect(route).toContain('status: 401');
  });

  it('keeps the anon key out of the server-only admin path', async () => {
    const auth = await readFile('src/lib/server/auth.ts', 'utf8');
    expect(auth).toContain("import 'server-only'");
    expect(auth).not.toContain('SERVICE_ROLE');
  });
});
