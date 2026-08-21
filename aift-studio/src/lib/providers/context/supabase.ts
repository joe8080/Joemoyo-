import 'server-only';
import type { ContentContext, BrandSettings } from '@/lib/domain';
import type { PrivateContextProvider } from '@/lib/providers/types';
import { adminClient } from '@/lib/supabase/admin';
import { applyAllowlist, assertContextIsSafe, REDACTION_NOTICE } from './index';

/**
 * Live private-context provider.
 *
 * It calls exactly one database function — `public.aift_content_context`, a
 * SECURITY DEFINER wrapper over `private.aift_content_context` — and nothing
 * else. It never issues a `from('broker_...')`, a `from('trade_journal')` or any
 * other direct table read. The single-RPC shape is what makes the boundary
 * auditable: there is one door, and the redaction lives behind it.
 */
export class SupabaseContextProvider implements PrivateContextProvider {
  readonly name = 'supabase-private-context@1';

  constructor(private readonly allow: BrandSettings['private_context_allowlist']) {}

  async load(referenceDate: string): Promise<ContentContext> {
    const { data, error } = await adminClient().rpc('aift_content_context', {
      p_reference_date: referenceDate,
      p_allow_research_topics: this.allow.research_topics,
      p_allow_agent_rules: this.allow.agent_rules,
      p_allow_intelligence_flags: this.allow.intelligence_flags,
      p_allow_market_snapshots: this.allow.market_snapshots,
      p_allow_macro_indicators: this.allow.macro_indicators,
      p_allow_portfolio_themes: this.allow.portfolio_themes,
    });
    if (error) throw new Error(`aift_content_context failed: ${error.message}`);

    const raw = (data ?? {}) as Partial<ContentContext>;
    const ctx: ContentContext = {
      reference_date: referenceDate,
      research_topics: raw.research_topics ?? [],
      agent_rules: raw.agent_rules ?? [],
      intelligence_flags: raw.intelligence_flags ?? [],
      market_snapshots: raw.market_snapshots ?? [],
      macro_indicators: raw.macro_indicators ?? [],
      portfolio_themes: raw.portfolio_themes ?? [],
      redaction_notice: REDACTION_NOTICE,
    };

    // Second line of defence: even a mis-edited SQL function cannot leak through.
    assertContextIsSafe(ctx);
    const scoped = applyAllowlist(ctx, this.allow);
    assertContextIsSafe(scoped);
    return scoped;
  }
}
