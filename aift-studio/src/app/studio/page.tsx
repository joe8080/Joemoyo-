import Link from 'next/link';
import { getRuntime, ownerId } from '@/lib/server/runtime';
import { Empty, Pipeline, StatusPill, fmtDuration } from '@/components/ui';

export const dynamic = 'force-dynamic';

export default async function StudioIndex() {
  const { repo } = await getRuntime();
  const jobs = await repo.listContentJobs(await ownerId());

  return (
    <>
      <div className="pagehead">
        <div>
          <h1>Content studio</h1>
          <p className="sub">Scripts, scene plans, titles and asset manifests, version by version.</p>
        </div>
      </div>
      {jobs.length === 0 ? (
        <div className="card"><Empty>No content jobs yet.</Empty></div>
      ) : (
        <div className="grid g2">
          {jobs.map((j) => (
            <Link className="card" href={`/studio/${j.id}`} key={j.id}>
              <div className="row" style={{ justifyContent: 'space-between' }}>
                <h2 style={{ marginBottom: 0 }}>{j.working_title}</h2>
                <StatusPill status={j.status} />
              </div>
              <div className="row" style={{ gap: 8, margin: '10px 0' }}>
                <span className="pill mono">{j.format}</span>
                <span className="pill mono">v{j.script_version}</span>
                {j.scene_plan && <span className="pill mono">{fmtDuration(j.scene_plan.total_ms)}</span>}
                {j.scene_plan && <span className="pill mono">{j.scene_plan.scenes.length} scenes</span>}
              </div>
              <Pipeline status={j.status} />
            </Link>
          ))}
        </div>
      )}
    </>
  );
}
