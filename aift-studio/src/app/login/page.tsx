import { redirect } from 'next/navigation';
import { getSessionUser, signInWithPassword, supabaseAuthConfigured } from '@/lib/server/auth';

export const dynamic = 'force-dynamic';

async function signIn(form: FormData): Promise<void> {
  'use server';
  const { error } = await signInWithPassword(
    String(form.get('email') ?? ''), String(form.get('password') ?? ''),
  );
  if (error) redirect(`/login?error=${encodeURIComponent(error)}`);
  redirect('/');
}

export default async function Login({ searchParams }: { searchParams: Promise<{ error?: string }> }) {
  const { error } = await searchParams;

  if (!supabaseAuthConfigured()) {
    return (
      <div style={{ maxWidth: 560, margin: '10vh auto' }}>
        <h1>Sign in</h1>
        <div className="note warn" style={{ marginTop: 16 }}>
          Supabase Auth is not configured on this installation, so there is no sign-in to perform.
          The studio is running as a single local owner. That is fine on localhost; before putting it
          anywhere else, set <code>SUPABASE_URL</code> and <code>SUPABASE_ANON_KEY</code> and create
          the owner account.
        </div>
        <a className="btn" href="/" style={{ marginTop: 18 }}>Continue to the dashboard</a>
      </div>
    );
  }

  if (await getSessionUser()) redirect('/');

  return (
    <div style={{ maxWidth: 420, margin: '12vh auto' }}>
      <div className="brandmark" style={{ marginBottom: 24 }}>
        <span className="dot" />
        <div><b>AI Finance Toolkit</b><span>Studio</span></div>
      </div>
      <div className="card">
        <h2>Sign in</h2>
        <p className="hint" style={{ marginBottom: 16 }}>
          This is a private, single-owner studio. There is no sign-up: the owner account is created
          in Supabase.
        </p>
        {error && <div className="note fail" style={{ marginBottom: 14 }}>{error}</div>}
        <form action={signIn}>
          <div className="field">
            <label htmlFor="email">Email</label>
            <input id="email" name="email" type="email" required autoComplete="username" />
          </div>
          <div className="field">
            <label htmlFor="password">Password</label>
            <input id="password" name="password" type="password" required autoComplete="current-password" />
          </div>
          <button className="primary" type="submit" style={{ marginTop: 18, width: '100%', justifyContent: 'center' }}>
            Sign in
          </button>
        </form>
      </div>
    </div>
  );
}
