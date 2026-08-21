import 'server-only';
import { cookies } from 'next/headers';
import { createServerClient, type CookieOptions } from '@supabase/ssr';
import { env } from '@/lib/env';
import { stableId } from '@/lib/util/hash';
import type { Uuid } from '@/lib/domain';

/**
 * Owner identity and the reviewer check.
 *
 * Two modes, and the studio is explicit about which one it is in:
 *
 *  - **Authenticated.** With `SUPABASE_URL` and `SUPABASE_ANON_KEY` set, the
 *    owner is the signed-in Supabase user. `requireReviewer()` throws without a
 *    session, so an approval is attributable to a real identity and RLS scopes
 *    every row to it.
 *  - **Local.** Without those, the studio runs as a single local owner. That is
 *    fine on localhost and is not fine on a shared host — the Security Checklist
 *    says so rather than implying the app is protected.
 *
 * The workflow engine can never reach this: `requireReviewer` is only called
 * from the reviewer server actions.
 */

export const LOCAL_OWNER_ID: Uuid = stableId('aift_user', 'owner');

export function supabaseAuthConfigured(): boolean {
  const e = env();
  return Boolean(e.SUPABASE_URL && e.SUPABASE_ANON_KEY);
}

async function serverClient() {
  const e = env();
  const store = await cookies();
  return createServerClient(e.SUPABASE_URL!, e.SUPABASE_ANON_KEY!, {
    cookies: {
      getAll: () => store.getAll(),
      setAll: (list: Array<{ name: string; value: string; options: CookieOptions }>) => {
        // A server component cannot set cookies; the middleware refreshes the
        // session instead. Swallowing here is the documented pattern.
        try {
          for (const c of list) store.set(c.name, c.value, c.options);
        } catch {
          /* read-only context */
        }
      },
    },
  });
}

export type SessionUser = { id: Uuid; email: string | null };

export async function getSessionUser(): Promise<SessionUser | null> {
  if (!supabaseAuthConfigured()) return null;
  const { data, error } = await (await serverClient()).auth.getUser();
  if (error || !data.user) return null;
  return { id: data.user.id, email: data.user.email ?? null };
}

/** The row owner for reads. Falls back to the local owner when auth is off. */
export async function currentOwnerId(): Promise<Uuid> {
  const user = await getSessionUser();
  return user?.id ?? LOCAL_OWNER_ID;
}

export class NotAuthenticatedError extends Error {
  constructor() {
    super('This action requires an authenticated reviewer. Sign in first.');
    this.name = 'NotAuthenticatedError';
  }
}

/**
 * The gate on every approve, rework and archive action. With Supabase Auth
 * configured this is a genuine authentication check; without it, it returns the
 * local owner and the UI states plainly that the installation is unprotected.
 */
export async function requireReviewer(): Promise<Uuid> {
  if (!supabaseAuthConfigured()) return LOCAL_OWNER_ID;
  const user = await getSessionUser();
  if (!user) throw new NotAuthenticatedError();
  return user.id;
}

export async function signInWithPassword(email: string, password: string): Promise<{ error: string | null }> {
  if (!supabaseAuthConfigured()) return { error: 'Supabase Auth is not configured on this installation.' };
  const { error } = await (await serverClient()).auth.signInWithPassword({ email, password });
  return { error: error?.message ?? null };
}

export async function signOutSession(): Promise<void> {
  if (!supabaseAuthConfigured()) return;
  await (await serverClient()).auth.signOut();
}
