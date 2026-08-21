import { describe, expect, it } from 'vitest';
import { readFile } from 'node:fs/promises';
import { scanForPublishingPaths } from '../../scripts/guard-no-publish';
import { scanClientBoundary } from '../../scripts/guard-no-client-secrets';

/**
 * These are the acceptance criteria stated as absences. An absence is only worth
 * anything if something fails when it stops being true, so the guards run here
 * as well as in CI.
 */
describe('no publishing path exists', () => {
  it('finds no upload scope, no videos.insert, no YouTube credential, no broker API', async () => {
    const { scanned, violations } = await scanForPublishingPaths(process.cwd());
    expect(scanned).toBeGreaterThan(20);
    expect(violations, violations.join('\n')).toEqual([]);
  });

  it('declares no YouTube or brokerage variable in the environment template', async () => {
    const env = await readFile('.env.example', 'utf8');
    const declared = env.split('\n').filter((l) => /^[A-Z][A-Z0-9_]*=/u.test(l)).map((l) => l.split('=')[0]!);
    for (const name of declared) {
      expect(name).not.toMatch(/YOUTUBE|ALPACA|BROKER|TRADING|PLAID|STRIPE/u);
    }
    expect(declared.length).toBeGreaterThan(5);
  });

  it('ships no Google or brokerage client library', async () => {
    const pkg = JSON.parse(await readFile('package.json', 'utf8')) as {
      dependencies: Record<string, string>; devDependencies: Record<string, string>;
    };
    const all = Object.keys({ ...pkg.dependencies, ...pkg.devDependencies });
    for (const dep of all) {
      expect(dep).not.toMatch(/googleapis|google-auth|youtube|alpaca|@polygon|ib-?api/iu);
    }
  });

  it('has no state, route or method whose name implies publication', async () => {
    const { CONTENT_STATES } = await import('@/lib/workflow/states');
    for (const s of CONTENT_STATES) expect(s).not.toMatch(/publish|upload/iu);

    const engine = await readFile('src/lib/workflow/engine.ts', 'utf8');
    expect(engine).not.toMatch(/\b(publish|upload|schedulePost)\s*\(/u);
  });
});

describe('no secret can reach the browser', () => {
  it('finds no client module touching a secret, the admin client or a restricted table', async () => {
    const { violations } = await scanClientBoundary(process.cwd());
    expect(violations, violations.join('\n')).toEqual([]);
  });

  it('keeps the service-role key out of anything a bundler could follow to the client', async () => {
    const admin = await readFile('src/lib/supabase/admin.ts', 'utf8');
    expect(admin).toContain("import 'server-only'");
    const browser = await readFile('src/lib/supabase/browser.ts', 'utf8');
    expect(browser).not.toContain('SERVICE_ROLE');
    expect(browser).not.toContain('@/lib/env');
  });

  // Tested by behaviour rather than by reading the source: feed it a distinctive
  // secret and assert that no substring of it survives into the report.
  it('reports secret presence without leaking any part of a value', async () => {
    const { secretHealth, providerMode } = await import('@/lib/env');
    const secret = 'sk-CANARY-9f3a7c21-do-not-leak';
    const fake = {
      SUPABASE_URL: 'https://example.supabase.co',
      SUPABASE_ANON_KEY: secret,
      SUPABASE_SERVICE_ROLE_KEY: secret,
      AIFT_LLM_API_KEY: secret,
      AIFT_MEDIA_API_KEY: secret,
      AIFT_TTS_API_KEY: secret,
      AIFT_JOB_SIGNING_SECRET: secret,
      AIFT_MEDIA_PROVIDER: 'mock',
      AIFT_TTS_PROVIDER: 'mock',
      AIFT_STORAGE_DRIVER: 'local',
      AIFT_STORAGE_BUCKET: 'aift-private-assets',
      AIFT_APP_BASE_URL: 'http://localhost:3000',
    } as unknown as Parameters<typeof secretHealth>[0];

    const report = JSON.stringify(secretHealth(fake)) + JSON.stringify(providerMode(fake));
    expect(report).not.toContain(secret);
    for (let n = 4; n <= secret.length; n += 4) {
      expect(report, `leaked a ${n}-character prefix`).not.toContain(secret.slice(0, n));
    }
    // It still tells you what is configured.
    expect(report).toContain('SUPABASE_SERVICE_ROLE_KEY');
    expect(JSON.parse(JSON.stringify(secretHealth(fake))).every((r: { present: boolean }) => typeof r.present === 'boolean')).toBe(true);
  });
});
