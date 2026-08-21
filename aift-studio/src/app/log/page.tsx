import { getRuntime, ownerId } from '@/lib/server/runtime';
import { Empty } from '@/components/ui';

export const dynamic = 'force-dynamic';

export default async function SystemLog() {
  const { repo, providers, mode } = await getRuntime();
  const runs = await repo.listRuns(60);
  const jobs = await repo.listContentJobs(ownerId());
  const events = (await Promise.all(jobs.map((j) => repo.listReviewEvents(j.id)))).flat()
    .sort((a, b) => b.created_at.localeCompare(a.created_at));

  const totalCost = runs
    .flatMap((r) => r.provider_calls)
    .reduce((n, c) => n + (c.cost_usd ?? 0), 0);

  return (
    <>
      <div className="pagehead">
        <div>
          <h1>System log</h1>
          <p className="sub">
            Every run, the provider and prompt version behind it, its trace, its errors and the
            review decisions that followed. Cost is recorded where a provider reports it.
          </p>
        </div>
      </div>

      <div className="card">
        <h2>Providers in this process</h2>
        <div className="tablewrap">
          <table>
            <thead><tr><th>Port</th><th>Implementation</th><th>Mode</th><th>Live</th></tr></thead>
            <tbody>
              {([['llm', providers.llm.name, mode.llm, providers.llm.isLive],
                 ['research', providers.research.name, 'fixture', providers.research.isLive],
                 ['voice', providers.voice.name, mode.voice, providers.voice.isLive],
                 ['media', providers.media.name, mode.media, providers.media.isLive],
                 ['chart', providers.chart.name, 'deterministic', true],
                 ['storage', providers.storage.name, mode.storage, true],
                 ['context', providers.context.name, mode.database, true],
                 ['jobs', providers.jobs.name, 'server-side', true]] as const).map(([port, impl, m, live]) => (
                <tr key={port}>
                  <td className="mono">{port}</td>
                  <td className="mono" style={{ color: 'var(--dim)' }}>{impl}</td>
                  <td><span className={`pill ${live ? 'pass' : 'warn'}`}>{m}</span></td>
                  <td className="mono">{live ? 'yes' : 'no — mock'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="note" style={{ marginTop: 12 }}>
          Recorded spend this session: <span className="mono">${totalCost.toFixed(4)}</span>. Mock
          providers cost nothing; a live provider that does not report usage shows as unknown rather
          than as zero.
        </div>
      </div>

      <div className="card" style={{ marginTop: 14 }}>
        <h2>Job runs</h2>
        {runs.length === 0 ? <Empty>No scheduled runs yet. The workflow has been driven directly from the UI.</Empty> : (
          <div className="tablewrap">
            <table>
              <thead><tr><th>Type</th><th>Idempotency key</th><th>Status</th><th>Started</th><th>Attempts</th><th>Error</th></tr></thead>
              <tbody>
                {runs.map((r) => (
                  <tr key={r.id}>
                    <td className="mono">{r.job_type}</td>
                    <td className="mono" style={{ color: 'var(--dim)' }}>{r.idempotency_key}</td>
                    <td>
                      <span className={`pill ${r.status === 'succeeded' ? 'pass' : r.status === 'failed' ? 'fail' : 'warn'}`}>
                        {r.status}
                      </span>
                    </td>
                    <td className="mono">{r.started_at.slice(0, 19).replace('T', ' ')}</td>
                    <td className="mono">{r.attempt_count}</td>
                    <td style={{ color: 'var(--fail)' }}>{r.error_summary ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="card" style={{ marginTop: 14 }}>
        <h2>Review decisions</h2>
        {events.length === 0 ? <Empty>No review decisions recorded yet.</Empty> : (
          <div className="tablewrap">
            <table>
              <thead><tr><th>When</th><th>Job</th><th>Decision</th><th>Reasons</th><th>Feedback</th></tr></thead>
              <tbody>
                {events.map((e) => (
                  <tr key={e.id}>
                    <td className="mono">{e.created_at.slice(0, 19).replace('T', ' ')}</td>
                    <td className="mono" style={{ color: 'var(--dim)' }}>{e.content_job_id.slice(0, 8)}…</td>
                    <td><span className="pill">{e.decision.replace(/_/gu, ' ')}</span></td>
                    <td className="mono">{e.reason_codes.join(', ')}</td>
                    <td style={{ color: 'var(--dim)' }}>{e.freeform_feedback || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {runs.some((r) => r.trace.length > 0) && (
        <div className="card" style={{ marginTop: 14 }}>
          <h2>Traces</h2>
          {runs.filter((r) => r.trace.length > 0).map((r) => (
            <details key={r.id} style={{ marginBottom: 10 }}>
              <summary style={{ cursor: 'pointer', color: 'var(--dim)', fontSize: 13 }}>
                {r.job_type} · {r.idempotency_key} · {r.trace.length} entries
              </summary>
              <pre>{r.trace.map((t) => `${t.at}  ${t.level.toUpperCase().padEnd(5)} [${t.stage}] ${t.message}`).join('\n')}</pre>
            </details>
          ))}
        </div>
      )}
    </>
  );
}
