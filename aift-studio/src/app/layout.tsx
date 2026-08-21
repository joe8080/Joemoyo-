import type { Metadata } from 'next';
import Link from 'next/link';
import './globals.css';
import { getRuntime } from '@/lib/server/runtime';
import { getSessionUser, supabaseAuthConfigured } from '@/lib/server/auth';
import { signOutAction } from './actions';

export const metadata: Metadata = {
  title: 'AI Finance Toolkit Studio',
  description: 'Private research-to-production studio. No publishing, no trading.',
  robots: { index: false, follow: false },
};

const NAV = [
  { href: '/', label: 'Dashboard', ico: '◱' },
  { href: '/research', label: 'Research desk', ico: '◈' },
  { href: '/studio', label: 'Content studio', ico: '▤' },
  { href: '/review', label: 'Review room', ico: '✓' },
  { href: '/brand', label: 'Brand studio', ico: '◐' },
  { href: '/log', label: 'System log', ico: '≡' },
  { href: '/security', label: 'Security checklist', ico: '⚿' },
];

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const { mode } = await getRuntime();
  const live = Object.values(mode).filter((m) => m === 'live' || m === 'supabase').length;
  const authOn = supabaseAuthConfigured();
  const user = authOn ? await getSessionUser() : null;

  return (
    <html lang="en-GB">
      <body>
        <div className="shell">
          <aside className="rail">
            <div className="brandmark">
              <span className="dot" />
              <div>
                <b>AI Finance Toolkit</b>
                <span>Studio</span>
              </div>
            </div>

            <nav className="nav">
              {NAV.map((n) => (
                <Link key={n.href} href={n.href}>
                  <span className="ico">{n.ico}</span>
                  {n.label}
                </Link>
              ))}
            </nav>

            <div className="railfoot">
              <b>Owner</b>
              {authOn ? (
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'center' }}>
                  <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>{user?.email ?? 'signed out'}</span>
                  <form action={signOutAction}>
                    <button type="submit" style={{ padding: '2px 8px', fontSize: 11 }}>out</button>
                  </form>
                </div>
              ) : (
                <div style={{ color: 'var(--warn)' }}>local owner — authentication is not enforced</div>
              )}
              <b style={{ marginTop: 12 }}>Providers</b>
              {Object.entries(mode).map(([k, v]) => (
                <div key={k} style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                  <span>{k}</span>
                  <span style={{ color: v === 'live' || v === 'supabase' ? 'var(--pass)' : 'var(--warn)' }}>{v}</span>
                </div>
              ))}
              <div style={{ marginTop: 10, color: 'var(--dimmer)' }}>
                {live === 0
                  ? 'Running entirely on mocks. No credentials are configured.'
                  : `${live} live provider${live === 1 ? '' : 's'} configured.`}
              </div>
              <div style={{ marginTop: 10, color: 'var(--dimmer)' }}>
                No upload, scheduling or trading capability exists in this build.
              </div>
            </div>
          </aside>

          <main className="main">{children}</main>
        </div>
      </body>
    </html>
  );
}
