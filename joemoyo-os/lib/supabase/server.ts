import { createClient } from "@supabase/supabase-js";

/**
 * Server-side Supabase client (the Vault).
 * Uses the service-role key when present so OS modules can read/write
 * agent data, portfolio rows, content calendar, etc. Never import this
 * into a client component.
 */
export function vaultClient() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key =
    process.env.SUPABASE_SERVICE_ROLE_KEY ?? process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) return null;
  return createClient(url, key, { auth: { persistSession: false } });
}

export function vaultReady(): boolean {
  return Boolean(
    process.env.NEXT_PUBLIC_SUPABASE_URL &&
      (process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY),
  );
}
