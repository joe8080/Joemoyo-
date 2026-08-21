import 'server-only';
import type { Repository } from '@/lib/db/types';
import type { Providers } from '@/lib/providers/types';
import type { BrandSettings, Uuid } from '@/lib/domain';
import { bootstrap } from '@/lib/bootstrap';
import { DEFAULT_BRAND_SETTINGS } from '@/lib/db/defaults';
import { WorkflowEngine } from '@/lib/workflow/engine';
import { FixtureDataRegistry } from '@/lib/workflow/data-registry';
import { stableId } from '@/lib/util/hash';
import { providerMode } from '@/lib/env';

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
    const brand = { ...DEFAULT_BRAND_SETTINGS, user_id: ownerId() };
    const { repo, providers, registry, mode } = await bootstrap({ brand });
    await repo.updateBrandSettings(ownerId(), brand);
    const engine = new WorkflowEngine({ repo, providers, registry });
    return { repo, providers, registry, engine, mode };
  })();
  return cached;
}

/**
 * The owner of this installation.
 *
 * With Supabase configured this becomes the signed-in user id; without it, the
 * studio runs as a single local owner. Either way, every reviewer action calls
 * `requireReviewer()` first, so approval is always attributable to an
 * authenticated identity rather than to the workflow.
 */
export function ownerId(): Uuid {
  return stableId('aift_user', 'owner');
}

export class NotAuthenticatedError extends Error {
  constructor() {
    super('This action requires an authenticated reviewer.');
    this.name = 'NotAuthenticatedError';
  }
}

export async function requireReviewer(): Promise<Uuid> {
  const id = ownerId();
  if (!id) throw new NotAuthenticatedError();
  return id;
}

export async function getBrand(): Promise<BrandSettings> {
  const { repo } = await getRuntime();
  return repo.getBrandSettings(ownerId());
}
