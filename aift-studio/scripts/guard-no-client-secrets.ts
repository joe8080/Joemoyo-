/**
 * Build guard: prove no secret and no restricted table can reach the browser.
 *
 *  1. No client module (one carrying 'use client') may reference a service-role
 *     key, a provider API key, the server-only env module, or the admin client.
 *  2. No client module may name a restricted table. Broker, trade, benefits,
 *     income and asset-register data has no business in a bundle that ships to a
 *     browser, whatever RLS says about it.
 *  3. The server-only modules must actually import 'server-only', or check (1)
 *     is guarding a door with no lock behind it.
 *
 *   npm run guard:no-secrets
 */
import { readdir, readFile } from 'node:fs/promises';
import { join, relative } from 'node:path';

const ROOT = process.cwd();
const SKIP = new Set(['node_modules', '.next', '.git', '.artifacts', 'out', 'coverage']);

const SECRET_TOKENS = [
  'SUPABASE_SERVICE_ROLE_KEY', 'AIFT_LLM_API_KEY', 'AIFT_MEDIA_API_KEY',
  'AIFT_TTS_API_KEY', 'AIFT_JOB_SIGNING_SECRET',
];

export const RESTRICTED_TABLES = [
  'broker_statements', 'broker_account_snapshots', 'broker_executions',
  'broker_cash_events', 'broker_dividends', 'broker_position_snapshots',
  'broker_import_audit', 'trade_journal', 'decision_log',
  'portfolio_summary', 'portfolio_buckets',
];

const SERVER_ONLY_MODULES = [
  'src/lib/supabase/admin.ts',
  'src/lib/providers/storage/supabase.ts',
  'src/lib/providers/context/supabase.ts',
];

async function* walk(dir: string): AsyncGenerator<string> {
  for (const e of await readdir(dir, { withFileTypes: true })) {
    if (e.isDirectory()) {
      if (SKIP.has(e.name)) continue;
      yield* walk(join(dir, e.name));
    } else if (/\.(ts|tsx)$/u.test(e.name)) {
      yield join(dir, e.name);
    }
  }
}

export async function scanClientBoundary(root = ROOT): Promise<{ clientModules: number; violations: string[] }> {
  const violations: string[] = [];
  let clientModules = 0;

  for await (const path of walk(join(root, 'src'))) {
    const rel = relative(root, path).split('\\').join('/');
    const text = await readFile(path, 'utf8');
    if (!/^\s*['"]use client['"]/mu.test(text)) continue;
    clientModules += 1;

    for (const token of SECRET_TOKENS) {
      if (text.includes(token)) violations.push(`${rel}: client module references secret "${token}"`);
    }
    if (/from\s+['"]@\/lib\/supabase\/admin['"]/u.test(text)) {
      violations.push(`${rel}: client module imports the service-role admin client`);
    }
    if (/from\s+['"]@\/lib\/env['"]/u.test(text)) {
      violations.push(`${rel}: client module imports the server-only env module`);
    }
    for (const table of RESTRICTED_TABLES) {
      if (text.includes(table)) violations.push(`${rel}: client module names restricted table "${table}"`);
    }
  }

  for (const f of SERVER_ONLY_MODULES) {
    const text = await readFile(join(root, f), 'utf8').catch(() => '');
    if (!text.includes("import 'server-only'")) {
      violations.push(`${f}: must import 'server-only' so a client import fails at build time`);
    }
  }

  return { clientModules, violations };
}

const isMain = process.argv[1]?.endsWith('guard-no-client-secrets.ts') ?? false;
if (isMain) {
  const { clientModules, violations } = await scanClientBoundary();
  console.log(`guard:no-secrets — checked ${clientModules} client module(s)`);
  if (violations.length > 0) {
    console.error(`\n✗ ${violations.length} violation(s):\n`);
    for (const v of violations) console.error(`  ${v}`);
    process.exit(1);
  }
  console.log('✓ no secret, admin client or restricted table reachable from a client bundle');
}
