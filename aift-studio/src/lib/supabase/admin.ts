import 'server-only';
import { createClient, type SupabaseClient } from '@supabase/supabase-js';
import { env } from '@/lib/env';

/**
 * Service-role client. Bypasses RLS, so it exists only here, only on the server,
 * and only for: the private-context RPC, storage in the private bucket, and the
 * worker's own `aift_*` writes.
 *
 * The `server-only` import above makes importing this file from a client
 * component a build error rather than a runtime surprise.
 */
let cached: SupabaseClient | null = null;

export function adminClient(): SupabaseClient {
  if (cached) return cached;
  const e = env();
  if (!e.SUPABASE_URL || !e.SUPABASE_SERVICE_ROLE_KEY) {
    throw new Error('Supabase admin client requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (server-side only)');
  }
  cached = createClient(e.SUPABASE_URL, e.SUPABASE_SERVICE_ROLE_KEY, {
    auth: { persistSession: false, autoRefreshToken: false },
    global: { headers: { 'x-aift-client': 'server-worker' } },
  });
  return cached;
}

export function hasAdminCredentials(): boolean {
  const e = env();
  return Boolean(e.SUPABASE_URL && e.SUPABASE_SERVICE_ROLE_KEY);
}
