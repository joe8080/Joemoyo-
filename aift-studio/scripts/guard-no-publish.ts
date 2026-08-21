/**
 * Build guard: prove that this repository cannot publish to YouTube.
 *
 * The acceptance criterion is an *absence*, and absences rot silently — someone
 * adds a helper six months from now and nobody notices. So it is asserted here,
 * in CI, over the actual source text, and the build fails if it stops being true.
 *
 *   npm run guard:no-publish
 */
import { readdir, readFile, stat } from 'node:fs/promises';
import { join, relative } from 'node:path';

const ROOT = process.cwd();
const SKIP_DIRS = new Set(['node_modules', '.next', '.git', '.artifacts', 'out', 'coverage', 'dist']);
const SCAN_EXT = /\.(ts|tsx|js|jsx|mjs|cjs|json|sql|md|yml|yaml)$/u;

/**
 * Files permitted to contain the forbidden strings, because their job is to
 * name them: this guard, the docs that explain the boundary, and the runtime
 * gate that restates it in the review room.
 */
const ALLOWED = new Set([
  'scripts/guard-no-publish.ts',
  'docs/SECURITY.md', 'docs/WORKFLOW.md', 'docs/CONTENT_POLICY.md', 'README.md',
  '.env.example',
  'src/lib/qa/gates.ts',
  'supabase/migrations/20260821000100_aift_core.sql',
  'tests/security/no-publishing.test.ts',
]);

type Rule = { name: string; re: RegExp; why: string };

export const RULES: Rule[] = [
  {
    name: 'youtube-upload-scope',
    re: /auth\/youtube(\.upload|\.force-ssl|partner)?/iu,
    why: 'A YouTube OAuth scope would make uploading possible. Version one must not request one.',
  },
  {
    name: 'videos-insert-endpoint',
    re: /videos\s*\.\s*insert|youtube\/v3\/videos|uploads\.youtube\.com|googleapis\.com\/upload\/youtube/iu,
    why: 'This is the YouTube upload endpoint. Calling it is out of scope for version one.',
  },
  {
    name: 'youtube-credentials',
    re: /YOUTUBE_(CLIENT_ID|CLIENT_SECRET|REFRESH_TOKEN|API_KEY|ACCESS_TOKEN)/u,
    why: 'No YouTube credential may exist in this build, not even as an unused variable.',
  },
  {
    name: 'youtube-client-library',
    re: /from\s+['"](googleapis|google-auth-library|@googleapis\/youtube)['"]/u,
    why: 'A Google API client is the first step to an upload path. Not in version one.',
  },
  {
    name: 'broker-or-order-api',
    re: /\b(place|submit|create)_?(order|trade)\b|\/v2\/orders\b|alpaca\.markets|interactive\s?brokers/iu,
    why: 'This is research and content tooling. It never places an order or touches a broker.',
  },
  {
    name: 'money-movement',
    re: /\b(transfer_funds|withdraw_funds|initiate_payment|ach_transfer|wire_transfer)\b/iu,
    why: 'The product never moves money.',
  },
];

export async function* walkSource(dir: string): AsyncGenerator<string> {
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    if (entry.isDirectory()) {
      if (SKIP_DIRS.has(entry.name)) continue;
      yield* walkSource(join(dir, entry.name));
    } else if (SCAN_EXT.test(entry.name) || entry.name === '.env.example') {
      yield join(dir, entry.name);
    }
  }
}

export async function scanForPublishingPaths(root = ROOT): Promise<{ scanned: number; violations: string[] }> {
  const violations: string[] = [];
  let scanned = 0;

  for await (const path of walkSource(root)) {
    const rel = relative(root, path).split('\\').join('/');
    if (ALLOWED.has(rel)) continue;
    const info = await stat(path);
    if (info.size > 2_000_000) continue;
    const text = await readFile(path, 'utf8');
    scanned += 1;

    for (const rule of RULES) {
      const m = text.match(rule.re);
      if (!m) continue;
      const line = text.slice(0, m.index ?? 0).split('\n').length;
      violations.push(`${rel}:${line}  [${rule.name}]  matched "${m[0]}"\n      ${rule.why}`);
    }
  }
  return { scanned, violations };
}

const isMain = process.argv[1]?.endsWith('guard-no-publish.ts') ?? false;
if (isMain) {
  const { scanned, violations } = await scanForPublishingPaths();
  console.log(`guard:no-publish — scanned ${scanned} files against ${RULES.length} rules`);
  if (violations.length > 0) {
    console.error(`\n✗ ${violations.length} violation(s):\n`);
    for (const v of violations) console.error(`  ${v}\n`);
    console.error('This build must not be able to upload, schedule, publish, trade or move money.');
    process.exit(1);
  }
  console.log('✓ no upload scope, no videos.insert, no YouTube credential, no broker or payment API');
}
