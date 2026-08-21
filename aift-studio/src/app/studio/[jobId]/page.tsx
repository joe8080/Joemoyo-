import Link from 'next/link';
import { notFound } from 'next/navigation';
import { getRuntime } from '@/lib/server/runtime';
import { Pipeline, StatusPill, fmtBytes, fmtDuration } from '@/components/ui';
import { youtubeStamp } from '@/lib/video/captions';

export const dynamic = 'force-dynamic';

export default async function ContentStudio({ params }: { params: Promise<{ jobId: string }> }) {
  const { jobId } = await params;
  const { repo } = await getRuntime();
  const job = await repo.getContentJob(jobId);
  if (!job) notFound();

  const assets = await repo.listAssets(jobId);
  const claims = await repo.listClaims(job.research_job_id);
  const claimById = new Map(claims.map((c) => [c.claim_id, c]));
  const plan = job.scene_plan;
  const script = job.script;

  return (
    <>
      <div className="pagehead">
        <div>
          <h1>{job.working_title}</h1>
          <div className="row" style={{ gap: 8, marginTop: 8 }}>
            <StatusPill status={job.status} />
            <span className="pill mono">{job.format}</span>
            <span className="pill mono">script v{job.script_version}</span>
            {plan && <span className="pill mono">{plan.width}×{plan.height} @ {plan.fps}fps</span>}
            {plan && <span className="pill mono">{fmtDuration(plan.total_ms)}</span>}
          </div>
        </div>
        <Link className="btn" href={`/review/${jobId}`}>Open in review room</Link>
      </div>

      <div className="card"><Pipeline status={job.status} /></div>

      {job.editorial_plan && (
        <div className="grid g2" style={{ marginTop: 14 }}>
          <div className="card">
            <h2>Title options</h2>
            <div className="tablewrap">
              <table>
                <thead><tr><th>Title</th><th>Why</th><th>Overpromise</th></tr></thead>
                <tbody>
                  {job.editorial_plan.title_options.map((t) => (
                    <tr key={t.title}>
                      <td>{t.title}</td>
                      <td style={{ color: 'var(--dim)' }}>{t.why_it_works}</td>
                      <td>
                        <span className={`pill ${t.overpromise_risk === 'low' ? 'pass' : t.overpromise_risk === 'medium' ? 'warn' : 'fail'}`}>
                          {t.overpromise_risk}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <div className="card">
            <h2>Angle and promise</h2>
            <p style={{ color: 'var(--dim)' }}>{job.editorial_plan.angle}</p>
            <div className="divider" />
            <h3>Audience promise</h3>
            <p>{job.editorial_plan.audience_promise}</p>
            <div className="divider" />
            <h3>Hook</h3>
            <p>{job.editorial_plan.hook}</p>
          </div>
        </div>
      )}

      {script && plan && (
        <div className="card" style={{ marginTop: 14 }}>
          <h2>Script — {script.beats.length} beats</h2>
          <p className="hint" style={{ marginBottom: 12 }}>
            Every beat that states a figure carries the claim id behind it. A beat with a figure and
            no claim id cannot reach review.
          </p>
          <div className="scroll">
            {script.beats.map((b, i) => {
              const scene = plan.scenes[i];
              return (
                <div className="beat" key={b.beat_id}>
                  <div className="meta">
                    <span className="mono" style={{ color: 'var(--accent)' }}>{b.beat_id}</span>
                    <span className="pill mono">{scene ? youtubeStamp(scene.start_ms) : '—'}</span>
                    <span className="pill">{b.chapter}</span>
                    <span className="pill mono">{scene?.composition ?? b.visual_intent}</span>
                    {scene && <span className="pill mono">{(scene.duration_ms / 1000).toFixed(1)}s</span>}
                    {b.claim_ids.map((id) => (
                      <span key={id} className={`pill ${claimById.get(id)?.is_public_safe ? 'pass' : 'fail'}`}>{id}</span>
                    ))}
                  </div>
                  <div>{b.narration}</div>
                  {b.on_screen_text && (
                    <div className="hint">On screen: <span className="mono">{b.on_screen_text}</span></div>
                  )}
                  {scene?.data && (
                    <div className="hint">
                      Chart data: <span className="mono">{scene.data.series[0]?.points.map((p) => `${p.x}=${p.y}`).join('  ')}</span>
                      {' · '}{scene.data.source_label} · as of {scene.data.as_of_date}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {job.thumbnail_brief && (
        <div className="card" style={{ marginTop: 14 }}>
          <h2>Thumbnail brief</h2>
          <dl className="kv">
            <dt>Primary text</dt><dd>{job.thumbnail_brief.primary_text}</dd>
            <dt>Secondary text</dt><dd>{job.thumbnail_brief.secondary_text || '—'}</dd>
            <dt>Palette</dt><dd>{job.thumbnail_brief.palette.join('  ')}</dd>
          </dl>
          <div className="divider" />
          <p style={{ color: 'var(--dim)' }}>{job.thumbnail_brief.concept}</p>
          <p style={{ color: 'var(--dim)', marginTop: 8 }}>{job.thumbnail_brief.visual_direction}</p>
          <div className="divider" />
          <h3>Forbidden</h3>
          <ul style={{ margin: '0 0 0 18px', color: 'var(--fail)', fontSize: 13 }}>
            {job.thumbnail_brief.forbidden.map((f) => <li key={f}>{f}</li>)}
          </ul>
        </div>
      )}

      <div className="card" style={{ marginTop: 14 }}>
        <h2>Asset manifest — {assets.length} file{assets.length === 1 ? '' : 's'}</h2>
        <div className="tablewrap">
          <table>
            <thead><tr><th>Type</th><th>Key</th><th>Size</th><th>SHA-256</th><th>Generator</th><th>Prompt</th></tr></thead>
            <tbody>
              {assets.map((a) => (
                <tr key={a.id}>
                  <td className="mono">{a.asset_type}</td>
                  <td className="mono" style={{ maxWidth: 260, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {a.storage_key.split('/').slice(-2).join('/')}
                  </td>
                  <td className="mono">{fmtBytes(a.bytes)}</td>
                  <td className="mono" title={a.sha256}>{a.sha256.slice(0, 12)}…</td>
                  <td className="mono" style={{ color: 'var(--dim)' }}>{a.generator}</td>
                  <td className="mono" style={{ color: 'var(--dim)' }}>{a.prompt_version}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
