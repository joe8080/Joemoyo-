import { describe, expect, it } from 'vitest';
import { readFile } from 'node:fs/promises';
import {
  ContextRedactionError, FORBIDDEN_CONTEXT_KEYS, MockContextProvider,
  applyAllowlist, assertContextIsSafe,
} from '@/lib/providers/context';
import { DEFAULT_BRAND_SETTINGS } from '@/lib/db/defaults';
import type { ContentContext } from '@/lib/domain';

const allowAll = {
  research_topics: true, agent_rules: true, intelligence_flags: true,
  market_snapshots: true, macro_indicators: true, portfolio_themes: true,
  portfolio_values: false,
};

describe('the private-context boundary', () => {
  it('throws — loudly — when a forbidden field appears at any depth', () => {
    expect(() => assertContextIsSafe({ a: { b: [{ market_value: 12_345 }] } })).toThrow(ContextRedactionError);
    expect(() => assertContextIsSafe({ nested: { broker_statement: 'x' } })).toThrow(ContextRedactionError);
    expect(() => assertContextIsSafe({ ok: 1, deep: { deeper: { account_number: 'ABC123' } } })).toThrow(ContextRedactionError);
  });

  it('names the offending path rather than silently stripping it', () => {
    try {
      assertContextIsSafe({ portfolio: { positions: [] } });
      throw new Error('expected a redaction error');
    } catch (e) {
      expect(e).toBeInstanceOf(ContextRedactionError);
      expect((e as ContextRedactionError).offenders.join(',')).toContain('positions');
    }
  });

  it('covers every category the hand-off excludes', () => {
    for (const key of ['broker', 'statement', 'execution', 'cash_event', 'dividend', 'holdings',
      'positions', 'cost_basis', 'market_value', 'portfolio_value', 'benefits', 'income',
      'asset_register', 'serial_number', 'trade_journal', 'decision_log', 'pnl']) {
      expect(FORBIDDEN_CONTEXT_KEYS).toContain(key);
    }
  });

  it('returns nothing at all under the shipped default allow-list', async () => {
    const provider = new MockContextProvider(DEFAULT_BRAND_SETTINGS.private_context_allowlist);
    const ctx = await provider.load('2026-08-14');
    expect(ctx.market_snapshots).toEqual([]);
    expect(ctx.portfolio_themes).toEqual([]);
    expect(ctx.intelligence_flags).toEqual([]);
    // Topics and rules are the deliberate, minimal starting scope.
    expect(ctx.research_topics.length).toBeGreaterThan(0);
    expect(ctx.agent_rules.length).toBeGreaterThan(0);
  });

  it('produces a payload that passes its own scan even with every flag on', async () => {
    const ctx = await new MockContextProvider(allowAll).load('2026-08-14');
    expect(() => assertContextIsSafe(ctx)).not.toThrow();
    expect(ctx.redaction_notice).toMatch(/excluded at the database boundary/u);
  });

  it('drops a category the moment its flag is off', () => {
    const raw: ContentContext = {
      reference_date: '2026-08-14',
      research_topics: [{ topic: 't', ticker: null, priority: 1, requested_fields: [] }],
      agent_rules: [{ rule_name: 'r', rule_text: 'x', scope: 's' }],
      intelligence_flags: [{ label: 'f', strength: 'high' }],
      market_snapshots: [{ symbol: 'X', metric: 'close', value: 1, unit: 'USD', as_of: '2026-08-14', source: 's' }],
      macro_indicators: [{ indicator: 'i', value: 1, unit: '%', as_of: '2026-08-14', source: 's' }],
      portfolio_themes: ['semis'],
      redaction_notice: '',
    };
    const scoped = applyAllowlist(raw, { ...allowAll, market_snapshots: false, portfolio_themes: false });
    expect(scoped.market_snapshots).toEqual([]);
    expect(scoped.portfolio_themes).toEqual([]);
    expect(scoped.macro_indicators.length).toBe(1);
  });

  it('has no branch anywhere that could pass a portfolio value through', async () => {
    const src = await readFile('src/lib/providers/context/index.ts', 'utf8');
    // The flag is read nowhere; there is no `allow.portfolio_values ? ... : ...`.
    expect(src).not.toMatch(/allow\.portfolio_values\s*\?/u);
    expect(DEFAULT_BRAND_SETTINGS.private_context_allowlist.portfolio_values).toBe(false);
  });
});

describe('the live context provider', () => {
  it('reads through exactly one database function and no table', async () => {
    const src = await readFile('src/lib/providers/context/supabase.ts', 'utf8');
    expect(src).toContain("import 'server-only'");
    expect(src).toContain("rpc('aift_content_context'");
    // No direct table reads at all — the boundary is one door, not a policy.
    expect(src).not.toMatch(/\.from\(/u);
  });

  it('re-scans the payload after the database has already redacted it', async () => {
    const src = await readFile('src/lib/providers/context/supabase.ts', 'utf8');
    const calls = src.match(/assertContextIsSafe\(/gu) ?? [];
    expect(calls.length).toBeGreaterThanOrEqual(2);
  });
});

describe('the context SQL function', () => {
  it('selects from no restricted table', async () => {
    const body = stripComments(
      (await readFile('supabase/migrations/20260821000200_private_context.sql', 'utf8'))
        .slice((await readFile('supabase/migrations/20260821000200_private_context.sql', 'utf8'))
          .indexOf('create or replace function private.aift_content_context')),
    );
    for (const table of [
      'broker_statements', 'broker_account_snapshots', 'broker_executions',
      'broker_cash_events', 'broker_dividends', 'broker_position_snapshots',
      'broker_import_audit', 'trade_journal', 'decision_log',
    ]) {
      expect(body, `${table} must not be selected in the context function`).not.toMatch(
        new RegExp(`from\\s+public\\.${table}`, 'iu'),
      );
    }
  });

  it('is not granted to a browser role', async () => {
    const sql = await readFile('supabase/migrations/20260821000200_private_context.sql', 'utf8');
    expect(sql).toMatch(/revoke all on function public\.aift_content_context[^;]*from public, anon/u);
    expect(sql).not.toMatch(/grant execute on function public\.aift_content_context[^;]*to authenticated/u);
  });

  // Comments are stripped first: the migration's own prose names the columns it
  // excludes, which is exactly what you want a reviewer to read and exactly what
  // would make a naive substring scan pass for the wrong reason.
  it('never selects a value, quantity or cost-basis column even where flags allow data', async () => {
    const sql = await readFile('supabase/migrations/20260821000200_private_context.sql', 'utf8');
    const body = stripComments(sql.slice(sql.indexOf('create or replace function private.aift_content_context')));
    for (const col of ['cost_basis', 'market_value', 'quantity', 'shares_held', 'total_value', 'account_id']) {
      expect(body, `${col} must not be referenced in executable SQL`).not.toContain(col);
    }
  });
});

function stripComments(sql: string): string {
  return sql
    .split('\n')
    .map((line) => line.replace(/--.*$/u, ''))
    .join('\n')
    .replace(/\/\*[\s\S]*?\*\//gu, '');
}
