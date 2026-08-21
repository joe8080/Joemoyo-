import 'server-only';
import type { Repository } from '@/lib/db/types';
import type { Providers } from '@/lib/providers/types';
import type { BrandSettings, Uuid } from '@/lib/domain';
import { bootstrap } from '@/lib/bootstrap';
import { DEFAULT_BRAND_SETTINGS } from '@/lib/db/defaults';
import { WorkflowEngine } from '@/lib/workflow/engine';
import { FixtureDataRegistry } from '@/lib/workflow/data-registry';
import { providerMode } from '@/lib/env';
import { currentOwnerId, LOCAL_OWNER_ID } from './auth';

/**
 * Process-wide runtime.
 *
 * Held as a module singleton so a local run keeps its state between requests
 * without a database. Every provider here is chosen by configuration, and the
 * `mode` object it exposes is what the UI displays: the studio never says a
 * live provider is configured when the credential is absent.
 */

type Runtime = {
  repo: Repository;
  providers: Providers;
  registry: FixtureDataRegistry;
  engine: WorkflowEngine;
  mode: ReturnType<typeof providerMode>;
};

let cached: Promise<Runtime> | null = null;

export function getRuntime(): Promise<Runtime> {
  cached ??= (async (): Promise<Runtime> => {
    const brand = { ...DEFAULT_BRAND_SETTINGS, user_id: LOCAL_OWNER_ID };
    const { repo, providers, registry, mode } = await bootstrap({ brand });
    const engine = new WorkflowEngine({ repo, providers, registry });
    return { repo, providers, registry, engine, mode };
  })();
  return cached;
}

/** The signed-in owner, or the local owner when Supabase Auth is not configured. */
export async function ownerId(): Promise<Uuid> {
  return currentOwnerId();
}

export async function getBrand(): Promise<BrandSettings> {
  const { repo } = await getRuntime();
  return repo.getBrandSettings(await ownerId());
}

export {
  requireReviewer, NotAuthenticatedError, supabaseAuthConfigured, getSessionUser, signOutSession,
} from './auth';
