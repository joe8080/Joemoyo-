import type { ContentContext, BrandSettings } from '@/lib/domain';
import type { PrivateContextProvider } from '@/lib/providers/types';

export const REDACTION_NOTICE =
  'Redacted research context. Broker, trade, benefits, income, asset-register, account-identifier and ' +
  'personal-name fields are excluded at the database boundary and are not retrievable through this path.';

/**
 * Field names that must never appear in a context payload, at any depth.
 * `assertContextIsSafe` runs on every load in every provider, including the
 * live one — belt and braces around the database-side redaction.
 */
export const FORBIDDEN_CONTEXT_KEYS: readonly string[] = [
  'account_number', 'account_id', 'account_name', 'broker', 'broker_id', 'statement',
  'execution', 'executions', 'cash_event', 'dividend', 'holding', 'holdings', 'position',
  'positions', 'quantity', 'cost_basis', 'market_value', 'portfolio_value', 'balance',
  'benefit', 'benefits', 'income', 'salary', 'asset_register', 'serial_number',
  'first_name', 'last_name', 'full_name', 'email', 'phone', 'address', 'national_insurance',
  'trade_journal', 'decision_log', 'pnl', 'profit_loss', 'realised', 'unrealised',
];

export class ContextRedactionError extends Error {
  constructor(public readonly offenders: string[]) {
    super(`private context contained forbidden fields: ${offenders.join(', ')}`);
    this.name = 'ContextRedactionError';
  }
}

/** Recursive key scan. Throws rather than silently stripping, so a leak is loud. */
export function assertContextIsSafe(value: unknown, path = '$'): void {
  const offenders: string[] = [];
  const walk = (v: unknown, p: string): void => {
    if (Array.isArray(v)) { v.forEach((item, i) => walk(item, `${p}[${i}]`)); return; }
    if (v && typeof v === 'object') {
      for (const [k, val] of Object.entries(v)) {
        const norm = k.toLowerCase();
        if (FORBIDDEN_CONTEXT_KEYS.some((f) => norm === f || norm.endsWith(`_${f}`) || norm.startsWith(`${f}_`))) {
          offenders.push(`${p}.${k}`);
        }
        walk(val, `${p}.${k}`);
      }
    }
  };
  walk(value, path);
  if (offenders.length > 0) throw new ContextRedactionError(offenders);
}

/** Applies the owner's allow-list. Every flag is off until deliberately enabled. */
export function applyAllowlist(ctx: ContentContext, allow: BrandSettings['private_context_allowlist']): ContentContext {
  return {
    reference_date: ctx.reference_date,
    research_topics: allow.research_topics ? ctx.research_topics : [],
    agent_rules: allow.agent_rules ? ctx.agent_rules : [],
    intelligence_flags: allow.intelligence_flags ? ctx.intelligence_flags : [],
    market_snapshots: allow.market_snapshots ? ctx.market_snapshots : [],
    macro_indicators: allow.macro_indicators ? ctx.macro_indicators : [],
    // `portfolio_values` has no branch here on purpose. No code path in this
    // repository puts a portfolio value into an LLM payload.
    portfolio_themes: allow.portfolio_themes ? ctx.portfolio_themes : [],
    redaction_notice: REDACTION_NOTICE,
  };
}

export class MockContextProvider implements PrivateContextProvider {
  readonly name = 'mock-context@1';

  constructor(private readonly allow: BrandSettings['private_context_allowlist']) {}

  async load(referenceDate: string): Promise<ContentContext> {
    const raw: ContentContext = {
      reference_date: referenceDate,
      research_topics: [
        { topic: 'Advanced packaging capacity as a semiconductor bottleneck', ticker: 'NWSC', priority: 1, requested_fields: ['segment_mix', 'commitments'] },
        { topic: 'How to read customer-concentration disclosure', ticker: null, priority: 2, requested_fields: [] },
      ],
      agent_rules: [
        { rule_name: 'no_personalised_advice', rule_text: 'Never issue buy, sell, add, trim or cut instructions in public content.', scope: 'content' },
        { rule_name: 'dated_figures_only', rule_text: 'Every market or financial figure carries an as-of date and a source.', scope: 'research' },
        { rule_name: 'two_source_rule', rule_text: 'Material non-primary claims require two independent sources.', scope: 'research' },
      ],
      intelligence_flags: [{ label: 'semiconductor supply chain', strength: 'high' }],
      market_snapshots: [],
      macro_indicators: [],
      portfolio_themes: ['semiconductors', 'infrastructure'],
      redaction_notice: REDACTION_NOTICE,
    };
    const scoped = applyAllowlist(raw, this.allow);
    assertContextIsSafe(scoped);
    return scoped;
  }
}
