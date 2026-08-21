import Link from 'next/link';
import { getRuntime, ownerId } from '@/lib/server/runtime';
import { Empty, Pipeline, Stat, StatusPill, fmtDuration } from '@/components/ui';
import { seedFixtureTopic } from './actions';

export const dynamic = 'force-dynamic';

export default async function Dashboard() {
  const { repo, mode } = await getRuntime();
  const user = await ownerId();
  const research = await repo.listResearchJobs(user);
  const jobs = await repo.listContentJobs(user);

  const checksByJob = new Map(await Promise.all(
    jobs.map(async (j) => [j.id, await repo.listQualityChecks(j.id)] as const),
  ));

  const needsReview = jobs.filter((j) => j.status === 'needs_review');
  const blocked = jobs.filter((j) => j.status === 'blocked' || j.status === 'rework_required');
  const archived = jobs.filter((j) => j.status === 'archived');

  const allChecks = [...checksByJob.values()].flat();
  const passRate = allChecks.length > 0
    ? Math.round((allChecks.filter((c) => c.result === 'pass').length / allChecks.length) * 100)
    : 0;

  return (
    <>
      <div className="pagehead">
        <div>
          <h1>Dashboard</h1>
          <p className="sub">
            Everything this studio produces stops at review. There is no publish step, no upload
            credential and no scheduled post — a finished pack waits here until you approve it and
            upload it yourself.
          </p>
        </div>
        <form action={seedFixtureTopic}>
          <button className="primary" type="submit">Run the fixture topic</button>
        </form>
      </div>

      <div className="grid g4">
        <Stat n={needsReview.length} l="Needs your review" tone={needsReview.length > 0 ? 'pass' : undefined} />
        <Stat n={blocked.length} l="Blocked or in rework" tone={blocked.length > 0 ? 'fail' : undefined} />
        <Stat n={research.length} l="Research jobs" />
        <Stat n={allChecks.length > 0 ? `${passRate}%` : '—'} l="Quality checks passing" />
      </div>

      <div className="card" style={{ marginTop: 14 }}>
        <h2>Content jobs</h2>
        {jobs.length === 0 ? (
          <Empty>
            Nothing in flight. Run the fixture topic above, or create your own on the{' '}
            <Link href="/research" style={{ color: 'var(--accent)' }}>research desk</Link>.
          </Empty>
        ) : (
          <div className="tablewrap">
            <table>
              <thead>
                <tr>
                  <th>Title</th><th>Format</th><th>Status</th><th>Runtime</th><th>Blocking</th><th>Pipeline</th><th />
                </tr>
              </thead>
              <tbody>
                {jobs.map((j) => {
                  const checks = checksByJob.get(j.id) ?? [];
                  const bad = checks.filter((c) => c.result === 'fail' && c.severity === 'blocking').length;
                  return (
                    <tr key={j.id}>
                      <td style={{ maxWidth: 320 }}>{j.working_title}</td>
                      <td className="mono">{j.format}</td>
                      <td><StatusPill status={j.status} /></td>
                      <td className="mono">{j.scene_plan ? fmtDuration(j.scene_plan.total_ms) : '—'}</td>
                      <td className="mono" style={{ color: bad > 0 ? 'var(--fail)' : 'var(--dim)' }}>{bad || '—'}</td>
                      <td><Pipeline status={j.status} /></td>
                      <td>
                        <Link className="btn" href={`/review/${j.id}`} style={{ padding: '5px 11px', fontSize: 12 }}>
                          Open
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="grid g2" style={{ marginTop: 14 }}>
        <div className="card">
          <h2>Scheduled routines</h2>
          <p className="hint" style={{ marginBottom: 12 }}>
            Both routines are server-side job definitions. Nothing in this product runs on a browser
            timer, and neither routine can advance a job past review.
          </p>
          <div className="tablewrap">
            <table>
              <thead><tr><th>Routine</th><th>Cadence</th><th>Ends in</th></tr></thead>
              <tbody>
                <tr>
                  <td>Research radar</td>
                  <td className="mono">weekdays, 07:00</td>
                  <td><span className="pill info">topic candidate</span></td>
                </tr>
                <tr>
                  <td>Editorial production</td>
                  <td className="mono">weekly, Sunday 06:00</td>
                  <td><span className="pill info">needs_review</span></td>
                </tr>
              </tbody>
            </table>
          </div>
          <div className="note" style={{ marginTop: 12 }}>
            Trigger them from your platform scheduler with a signed request to{' '}
            <code>/api/jobs/run</code>. Each carries an idempotency key, so a duplicate firing is a
            no-op rather than a second pack.
          </div>
        </div>

        <div className="card">
          <h2>What is actually running</h2>
          <dl className="kv">
            {Object.entries(mode).map(([k, v]) => (
              <span key={k} style={{ display: 'contents' }}>
                <dt>{k}</dt>
                <dd style={{ color: v === 'live' || v === 'supabase' ? 'var(--pass)' : 'var(--warn)' }}>{v}</dd>
              </span>
            ))}
          </dl>
          <div className="divider" />
          <p className="hint">
            Anything reading <code>mock</code> has no credential configured. The workflow still runs
            end to end, and the packs it produces are complete and inspectable — they are just not
            model-written or voiced. The studio will not tell you a provider is live when it is not.
          </p>
        </div>
      </div>

      {archived.length > 0 && (
        <div className="card" style={{ marginTop: 14 }}>
          <h2>Archived packs — ready for you to upload by hand</h2>
          <div className="tablewrap">
            <table>
              <thead><tr><th>Title</th><th>Format</th><th>Approved</th></tr></thead>
              <tbody>
                {archived.map((j) => (
                  <tr key={j.id}>
                    <td>{j.working_title}</td>
                    <td className="mono">{j.format}</td>
                    <td className="mono">{j.approved_at?.slice(0, 19).replace('T', ' ') ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}
