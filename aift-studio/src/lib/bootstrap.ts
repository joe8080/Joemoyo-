import type { Providers } from '@/lib/providers/types';
import type { BrandSettings } from '@/lib/domain';
import type { Repository } from '@/lib/db/types';
import { env, providerMode } from '@/lib/env';
import { MemoryRepository } from '@/lib/db/memory';
import { createLLMProvider } from '@/lib/providers/llm';
import { MockResearchProvider } from '@/lib/providers/research/mock';
import { SvgChartRenderer } from '@/lib/providers/chart/svg';
import { MockMediaProvider } from '@/lib/providers/media/mock';
import { createVoiceProvider } from '@/lib/providers/voice';
import { LocalStorageProvider } from '@/lib/providers/storage/local';
import { InlineJobRunner } from '@/lib/providers/jobs/inline';
import { MockContextProvider } from '@/lib/providers/context';
import { FixtureDataRegistry } from '@/lib/workflow/data-registry';

/**
 * Assembles the running system from configuration.
 *
 * Anything with no credential resolves to its mock. The returned `mode` object
 * is what the UI displays — the studio never claims a live provider is
 * configured when it is not.
 */
export async function bootstrap(opts?: { repo?: Repository; brand?: BrandSettings }): Promise<{
  repo: Repository;
  providers: Providers;
  registry: FixtureDataRegistry;
  mode: ReturnType<typeof providerMode>;
}> {
  const e = env();
  const repo = opts?.repo ?? new MemoryRepository();
  const brand = opts?.brand;
  const allow = brand?.private_context_allowlist ?? {
    research_topics: true, agent_rules: true, intelligence_flags: false,
    market_snapshots: false, macro_indicators: false, portfolio_themes: false, portfolio_values: false,
  };

  const storage = e.AIFT_STORAGE_DRIVER === 'supabase' && e.SUPABASE_URL && e.SUPABASE_SERVICE_ROLE_KEY
    ? new (await import('@/lib/providers/storage/supabase')).SupabaseStorageProvider()
    : new LocalStorageProvider();

  const context = e.SUPABASE_URL && e.SUPABASE_SERVICE_ROLE_KEY
    ? new (await import('@/lib/providers/context/supabase')).SupabaseContextProvider(allow)
    : new MockContextProvider(allow);

  const providers: Providers = {
    llm: createLLMProvider(),
    research: new MockResearchProvider(),
    chart: new SvgChartRenderer(),
    media: new MockMediaProvider(),
    voice: await createVoiceProvider(),
    storage,
    jobs: new InlineJobRunner(repo),
    context,
  };

  return { repo, providers, registry: new FixtureDataRegistry(), mode: providerMode(e) };
}
