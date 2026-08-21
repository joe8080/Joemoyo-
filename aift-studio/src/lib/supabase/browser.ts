import { createBrowserClient } from '@supabase/ssr';

/**
 * Browser client. Anon key only — every table it can reach is RLS-protected and
 * scoped to the signed-in owner.
 *
 * The broker/trade/benefits tables are never queried from here. `scripts/guard-no-client-secrets.ts`
 * fails the build if a client module references them or any service-role key.
 */
export function browserClient(url: string, anonKey: string) {
  return createBrowserClient(url, anonKey);
}
