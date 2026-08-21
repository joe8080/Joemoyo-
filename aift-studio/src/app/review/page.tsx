import Link from 'next/link';
import { getRuntime, ownerId } from '@/lib/server/runtime';
import { Empty, Pipeline, StatusPill, fmtDuration } from '@/components/ui';

export const dynamic = 'force-dynamic';

export default async function ReviewIndex() {
  const { repo } = await getRuntime();
  const jobs = await repo.listContentJobs(ownerId());
  const queue = jobs.filter((j) => j.status !== 'archived');
  const done = jobs.filter((j) => j.status === 'archived');

  return (
    <>
      <div className="pagehead">
        <div>
          <h1>Review room</h1>
          <p className="sub">
            Nothing leaves this room on its own. Approving a pack marks it complete and stores it;
            it does not upload it, schedule it, or tell anyone about it.
          </p>
        </div>
      </div>

      {queue.length === 0 ? (
        <div className="card"><Empty>Nothing waiting. Produce a pack from the research desk.</Empty></div>
      ) : (
        <div className="grid g2">
          {queue.map((j) => (
            <Link className="card" href={`/review/${j.id}`} key={j.id}>
              <div className="row" style={{ justifyContent: 'space-between' }}>
                <h2 style={{ marginBottom: 0 }}>{j.working_title}</h2>
                <StatusPill status={j.status} />
              </div>
              <div className="row" style={{ gap: 8, margin: '10px 0' }}>
                <span className="pill mono">{j.format}</span>
                {j.scene_plan && <span className="pill mono">{fmtDuration(j.scene_plan.total_ms)}</span>}
              </div>
              <Pipeline status={j.status} />
            </Link>
          ))}
        </div>
      )}

      {done.length > 0 && (
        <div className="card" style={{ marginTop: 14 }}>
          <h2>Archived</h2>
          {done.map((j) => (
            <div key={j.id} className="row" style={{ justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--line)' }}>
              <Link href={`/review/${j.id}`}>{j.working_title}</Link>
              <span className="mono" style={{ color: 'var(--dim)' }}>{j.format} · approved {j.approved_at?.slice(0, 10)}</span>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
