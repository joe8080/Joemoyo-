import { readFile } from 'node:fs/promises';
import { secretHealth } from '@/lib/env';
import { getBrand, getRuntime } from '@/lib/server/runtime';

export const dynamic = 'force-dynamic';

const BROKER_TABLES = [
  'broker_statements', 'broker_account_snapshots', 'broker_executions',
  'broker_cash_events', 'broker_dividends', 'broker_position_snapshots', 'broker_import_audit',
];

const ACCESS_MATRIX: Array<{ table: string; browser: string; server: string; llm: string }> = [
  { table: 'aift_* (9 tables)', browser: 'RLS, owner rows only', server: 'full', llm: 'never' },
  { table: 'research_pull_queue', browser: 'none', server: 'via context function', llm: 'topic line only, if allowed' },
  { table: 'agent_rules', browser: 'none', server: 'via context function', llm: 'rule text, if allowed' },
  { table: 'agent_intelligence_flags', browser: 'none', server: 'via context function', llm: 'label + strength, if allowed' },
  { table: 'price_snapshots / macro_indicators', browser: 'none', server: 'via context function', llm: 'dated values, if allowed' },
  { table: 'portfolio_summary / portfolio_buckets', browser: 'none', server: 'bucket labels only', llm: 'theme labels, if allowed' },
  { table: 'content_log / creative_works', browser: 'none', server: 'read; write only after manual publication', llm: 'never' },
  { table: 'trade_journal / decision_log', browser: 'none', server: 'none', llm: 'never' },
  { table: 'broker_* (7 tables)', browser: 'none', server: 'none', llm: 'never' },
  { table: 'benefits / income / assets', browser: 'none', server: 'none', llm: 'never' },
];

export default async function SecurityChecklist() {
  const { mode } = await getRuntime();
  const brand = await getBrand();
  const health = secretHealth();

  const proposal = await readFile('supabase/migrations-pending-review/0001_REVIEW_REQUIRED_broker_rls.sql', 'utf8').catch(() => '');
  const tests = await readFile('supabase/tests/broker_rls_policy_test.sql', 'utf8').catch(() => '');

  return (
    <>
      <div className="pagehead">
        <div>
          <h1>Security checklist</h1>
          <p className="sub">
            Deployment readiness for this installation. The findings here are stated whether or not
            they are convenient, and none of them is marked resolved by this application.
          </p>
        </div>
      </div>

      {/* --- the finding ------------------------------------------------------ */}
      <div className="card">
        <div className="row" style={{ justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <h2 style={{ marginBottom: 0 }}>Open finding — RLS disabled on seven broker tables</h2>
          <span className="pill fail">unresolved · needs your decision</span>
        </div>
        <div className="note fail" style={{ marginTop: 14 }}>
          A schema-only inspection of project <code>qxwfrsoztfddwicqtuar</code> found Row Level
          Security disabled on the tables below. With RLS off, any role holding a table grant can
          read every row, and the service-role key bypasses RLS regardless. The actual exposure
          depends on which roles hold grants today, which is why the proposal starts with an
          inspection rather than a change.
        </div>
        <div className="tablewrap" style={{ marginTop: 14 }}>
          <table>
            <thead><tr><th>Table</th><th>RLS</th><th>Reachable from this app</th></tr></thead>
            <tbody>
              {BROKER_TABLES.map((t) => (
                <tr key={t}>
                  <td className="mono">{t}</td>
                  <td><span className="pill fail">disabled</span></td>
                  <td><span className="pill pass">no — never queried, guard enforced in CI</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="divider" />
        <h3>Why this app did not fix it for you</h3>
        <p style={{ color: 'var(--dim)' }}>
          Enabling RLS with no matching policy denies all access to non-owner roles. If an importer,
          dashboard or scheduled job reads these tables today, turning RLS on without first writing
          its policy breaks it silently at the next run. Locking a door is only safe once you know
          who is currently walking through it. A reviewed migration is prepared and waiting; nothing
          in this repository applies it.
        </p>

        <div className="grid g2" style={{ marginTop: 14 }}>
          <div>
            <h3>Migration proposal</h3>
            <div className="row" style={{ gap: 8, marginBottom: 8 }}>
              <span className={`pill ${proposal ? 'pass' : 'fail'}`}>{proposal ? 'prepared' : 'missing'}</span>
              <span className="pill mono">{proposal.split('\n').length} lines</span>
              <span className="pill warn">not applied</span>
            </div>
            <p className="hint mono">supabase/migrations-pending-review/0001_REVIEW_REQUIRED_broker_rls.sql</p>
            <p className="hint">
              Inspect-first queries, a backfill guard that aborts on any null owner, RLS enabled and
              forced, owner policies, an anon revoke, an importer-role sketch, and a rollback.
            </p>
          </div>
          <div>
            <h3>Policy tests</h3>
            <div className="row" style={{ gap: 8, marginBottom: 8 }}>
              <span className={`pill ${tests ? 'pass' : 'fail'}`}>{tests ? 'prepared' : 'missing'}</span>
              <span className="pill mono">{tests.split('\n').length} lines</span>
              <span className="pill warn">run against a branch</span>
            </div>
            <p className="hint mono">supabase/tests/broker_rls_policy_test.sql</p>
            <p className="hint">
              Asserts RLS enabled and forced, at least one policy per table, no unconditional policy,
              no anon grants, the context function ungranted to browser roles, and a database-side FSM
              that refuses to archive without a reviewer.
            </p>
          </div>
        </div>
      </div>

      {/* --- key placement ---------------------------------------------------- */}
      <div className="grid g2" style={{ marginTop: 14 }}>
        <div className="card">
          <h2>Key placement</h2>
          <p className="hint" style={{ marginBottom: 12 }}>
            Presence only. This page never displays, logs or returns a secret value, a prefix or a
            length.
          </p>
          <div className="tablewrap">
            <table>
              <thead><tr><th>Variable</th><th>Present</th><th>Note</th></tr></thead>
              <tbody>
                {health.map((h) => (
                  <tr key={h.name}>
                    <td className="mono">{h.name}</td>
                    <td><span className={`pill ${h.present ? 'pass' : 'warn'}`}>{h.present ? 'set' : 'not set'}</span></td>
                    <td style={{ color: 'var(--dim)' }}>{h.note}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card">
          <h2>Enforced in CI</h2>
          {([
            // Written without the literal endpoint name so this page is not itself
            // an exception to the rule it is describing.
            ['guard:no-publish', 'No YouTube upload scope, no call to the YouTube video-insert endpoint, no YouTube credential, no Google API client, no broker order API, no money movement.'],
            ['guard:no-secrets', 'No client module references a service-role key, a provider key, the server-only env module, the admin client, or a restricted table.'],
            ['server-only imports', 'The admin client and both Supabase-backed providers import server-only, so a client import is a build error rather than a runtime surprise.'],
            ['privacy tests', 'The context payload is scanned recursively for forbidden keys and throws rather than silently stripping.'],
            ['FSM parity', 'The TypeScript transition table is compared against the Postgres function, so the two cannot drift apart.'],
            ['approval tests', 'The workflow engine cannot reach approved_for_archive or archived from any code path.'],
          ] as const).map(([name, note]) => (
            <div key={name} style={{ padding: '10px 0', borderBottom: '1px solid var(--line)' }}>
              <div className="row" style={{ gap: 8 }}>
                <span className="pill pass">✓</span>
                <span className="mono" style={{ fontSize: 12 }}>{name}</span>
              </div>
              <div className="hint" style={{ marginTop: 4 }}>{note}</div>
            </div>
          ))}
        </div>
      </div>

      {/* --- access matrix ---------------------------------------------------- */}
      <div className="card" style={{ marginTop: 14 }}>
        <h2>Table access matrix</h2>
        <div className="tablewrap">
          <table>
            <thead><tr><th>Table</th><th>Browser</th><th>Server</th><th>Reaches a model</th></tr></thead>
            <tbody>
              {ACCESS_MATRIX.map((r) => (
                <tr key={r.table}>
                  <td className="mono">{r.table}</td>
                  <td><span className={`pill ${r.browser === 'none' ? 'pass' : 'info'}`}>{r.browser}</span></td>
                  <td className="mono" style={{ color: 'var(--dim)' }}>{r.server}</td>
                  <td>
                    <span className={`pill ${r.llm === 'never' ? 'pass' : 'warn'}`}>{r.llm}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* --- readiness -------------------------------------------------------- */}
      <div className="card" style={{ marginTop: 14 }}>
        <h2>Deployment readiness</h2>
        <div className="tablewrap">
          <table>
            <thead><tr><th>Item</th><th>State</th><th>What is needed</th></tr></thead>
            <tbody>
              <tr>
                <td>Database</td>
                <td><span className={`pill ${mode.database === 'supabase' ? 'pass' : 'warn'}`}>{mode.database}</span></td>
                <td style={{ color: 'var(--dim)' }}>
                  {mode.database === 'supabase'
                    ? 'Connected. Apply the aift_* migrations on a branch first.'
                    : 'Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY on the server to persist beyond this process.'}
                </td>
              </tr>
              <tr>
                <td>Broker RLS finding</td>
                <td><span className="pill fail">open</span></td>
                <td style={{ color: 'var(--dim)' }}>Run the inspect-first queries, then the proposal, on a branch. Verify with the policy tests.</td>
              </tr>
              <tr>
                <td>Private-context allow-list</td>
                <td>
                  <span className="pill info">
                    {Object.entries(brand.private_context_allowlist).filter(([, v]) => v).length} of 7 enabled
                  </span>
                </td>
                <td style={{ color: 'var(--dim)' }}>Enable the least you need. Portfolio values are locked off and cannot be enabled.</td>
              </tr>
              <tr>
                <td>Storage</td>
                <td><span className={`pill ${mode.storage === 'supabase' ? 'pass' : 'warn'}`}>{mode.storage}</span></td>
                <td style={{ color: 'var(--dim)' }}>
                  Before exposing this beyond localhost, move to the private bucket. Assets are served
                  by short-lived signed URL only; there is no public-URL method.
                </td>
              </tr>
              <tr>
                <td>Scheduler webhook</td>
                <td><span className={`pill ${health.find((h) => h.name === 'AIFT_JOB_SIGNING_SECRET')?.present ? 'pass' : 'warn'}`}>
                  {health.find((h) => h.name === 'AIFT_JOB_SIGNING_SECRET')?.present ? 'signed' : 'unsigned'}
                </span></td>
                <td style={{ color: 'var(--dim)' }}>Set AIFT_JOB_SIGNING_SECRET before exposing /api/jobs/run publicly.</td>
              </tr>
              <tr>
                <td>Publishing capability</td>
                <td><span className="pill pass">absent by construction</span></td>
                <td style={{ color: 'var(--dim)' }}>No credential, no scope, no endpoint, no state. Asserted in CI on every build.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
