import Link from 'next/link';
import { notFound } from 'next/navigation';
import { getRuntime } from '@/lib/server/runtime';
import { CheckRow, Pipeline, StatusPill, fmtDuration } from '@/components/ui';
import { approveForArchive, archivePack, requestRework } from '../../actions';
import { youtubeStamp } from '@/lib/video/captions';

export const dynamic = 'force-dynamic';

export default async function ReviewRoom({ params }: { params: Promise<{ jobId: string }> }) {
  const { jobId } = await params;
  const { repo } = await getRuntime();
  const job = await repo.getContentJob(jobId);
  if (!job) notFound();

  const [checks, assets, events, claims] = await Promise.all([
    repo.listQualityChecks(jobId),
    repo.listAssets(jobId),
    repo.listReviewEvents(jobId),
    repo.listClaims(job.research_job_id),
  ]);

  const blocking = checks.filter((c) => c.result === 'fail' && c.severity === 'blocking');
  const warnings = checks.filter((c) => c.result === 'fail' && c.severity === 'warning');
  const passed = checks.filter((c) => c.result === 'pass');
  const cited = new Set(job.script?.beats.flatMap((b) => b.claim_ids) ?? []);
  const video = assets.find((a) => a.asset_type === 'video_mp4');

  const canApprove = job.status === 'needs_review';
  const canArchive = job.status === 'approved_for_archive';
  const canRework = job.status === 'needs_review' || job.status === 'blocked';

  return (
    <>
      <div className="pagehead">
        <div>
          <h1>{job.working_title}</h1>
          <div className="row" style={{ gap: 8, marginTop: 8 }}>
            <StatusPill status={job.status} />
            <span className="pill mono">{job.format}</span>
            {job.scene_plan && <span className="pill mono">{fmtDuration(job.scene_plan.total_ms)}</span>}
            {/* A pack that has not reached QA has no verdict yet; saying "all
                checks passed" because zero have run would be a lie of omission. */}
            <span className={`pill ${checks.length === 0 ? 'warn' : blocking.length === 0 ? 'pass' : 'fail'}`}>
              {checks.length === 0
                ? 'quality gates have not run yet'
                : blocking.length === 0 ? 'all blocking checks passed' : `${blocking.length} blocking`}
            </span>
          </div>
        </div>
        <Link className="btn" href={`/studio/${jobId}`}>Open in content studio</Link>
      </div>

      <div className="card"><Pipeline status={job.status} /></div>

      {/* --- the decision ---------------------------------------------------- */}
      <div className="card" style={{ marginTop: 14 }}>
        <h2>Your decision</h2>
        {blocking.length > 0 && (
          <div className="note fail" style={{ marginBottom: 14 }}>
            This pack cannot be approved while {blocking.length} blocking check
            {blocking.length === 1 ? '' : 's'} {blocking.length === 1 ? 'fails' : 'fail'}. Send it
            back for rework, fix the cause, and produce it again.
          </div>
        )}

        <div className="grid g2">
          <form action={approveForArchive}>
            <input type="hidden" name="content_job_id" value={jobId} />
            <div className="field">
              <label htmlFor="feedback-approve">Note (optional)</label>
              <textarea id="feedback-approve" name="feedback" placeholder="What made this one work?" />
            </div>
            <button className="primary" type="submit" disabled={!canApprove}>
              Approve for archive
            </button>
            <p className="hint">
              Marks the pack complete and attributes the decision to you. It does not upload anything.
            </p>
          </form>

          <form action={requestRework}>
            <input type="hidden" name="content_job_id" value={jobId} />
            <div className="field">
              <label htmlFor="reason_codes">Reason codes</label>
              <input id="reason_codes" name="reason_codes" placeholder="thin_evidence, weak_hook, pacing" />
            </div>
            <div className="field">
              <label htmlFor="feedback-rework">What needs to change</label>
              <textarea id="feedback-rework" name="feedback" placeholder="Be specific — this is the record the next run is judged against." />
            </div>
            <button className="danger" type="submit" disabled={!canRework}>
              {job.status === 'blocked' ? 'Unblock and send back to drafting' : 'Send back for rework'}
            </button>
          </form>
        </div>

        {canArchive && (
          <>
            <div className="divider" />
            <form action={archivePack}>
              <input type="hidden" name="content_job_id" value={jobId} />
              <div className="note" style={{ marginBottom: 12 }}>
                Approved. Archiving stores the pack for you to upload by hand. This is the last state
                a pack can reach — there is nothing after it.
              </div>
              <button className="primary" type="submit">Archive content pack</button>
            </form>
          </>
        )}
      </div>

      <div className="grid g2" style={{ marginTop: 14 }}>
        {/* --- preview ------------------------------------------------------ */}
        <div className="card">
          <h2>Preview</h2>
          {video ? (
            <>
              <div className="note" style={{ marginBottom: 12 }}>
                <span className="mono">{video.storage_key.split('/').slice(-1)[0]}</span> ·{' '}
                {video.aspect_ratio} · {video.duration_seconds?.toFixed(1)}s · {video.generator}
              </div>
              <p className="hint">
                Rendered to <code>.artifacts/</code>. Open it in your player — the studio deliberately
                does not stream private media over HTTP.
              </p>
            </>
          ) : (
            <div className="note warn">
              No video rendered for this pack. Produce it with rendering enabled to get an MP4,
              captions and a poster frame.
            </div>
          )}

          <div className="divider" />
          <h3>Chapters</h3>
          {job.script && job.scene_plan ? (
            <div className="mono" style={{ fontSize: 12, color: 'var(--dim)', lineHeight: 2 }}>
              {job.script.chapters.map((c) => {
                const i = job.script!.beats.findIndex((b) => b.beat_id === c.start_beat);
                return (
                  <div key={c.title}>
                    {youtubeStamp(job.scene_plan!.scenes[Math.max(0, i)]?.start_ms ?? 0)}  {c.title}
                  </div>
                );
              })}
            </div>
          ) : <p className="hint">No scene plan yet.</p>}
        </div>

        {/* --- citations ---------------------------------------------------- */}
        <div className="card">
          <h2>Citations in this pack</h2>
          <p className="hint" style={{ marginBottom: 10 }}>
            {cited.size} claim{cited.size === 1 ? '' : 's'} cited of {claims.length} in the ledger.
            Everything cited passed the evidence check; everything withheld is listed with its reason
            on the research desk.
          </p>
          <div className="scroll">
            {claims.filter((c) => cited.has(c.claim_id)).map((c) => (
              <div className="claim" key={c.id}>
                <div className="row" style={{ gap: 8, marginBottom: 4 }}>
                  <span className="mono" style={{ color: 'var(--accent)' }}>{c.claim_id}</span>
                  <span className="pill mono">as of {c.as_of_date ?? 'undated'}</span>
                  <span className="pill mono">{c.confidence.toFixed(2)}</span>
                </div>
                <div style={{ fontSize: 13 }}>{c.claim_text}</div>
                {c.source_excerpt && <div className="excerpt">“{c.source_excerpt}”</div>}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* --- quality --------------------------------------------------------- */}
      <div className="card" style={{ marginTop: 14 }}>
        <h2>Quality gates — {passed.length} passed, {warnings.length} warning{warnings.length === 1 ? '' : 's'}, {blocking.length} blocking</h2>
        {blocking.map((c) => <CheckRow check={c} key={c.id} />)}
        {warnings.map((c) => <CheckRow check={c} key={c.id} />)}
        <details style={{ marginTop: 12 }}>
          <summary style={{ cursor: 'pointer', color: 'var(--dim)', fontSize: 13 }}>
            Show the {passed.length} checks that passed
          </summary>
          <div style={{ marginTop: 10 }}>
            {passed.map((c) => <CheckRow check={c} key={c.id} />)}
          </div>
        </details>
      </div>

      {events.length > 0 && (
        <div className="card" style={{ marginTop: 14 }}>
          <h2>Review history</h2>
          <div className="tablewrap">
            <table>
              <thead><tr><th>When</th><th>Decision</th><th>Reasons</th><th>Feedback</th></tr></thead>
              <tbody>
                {events.map((e) => (
                  <tr key={e.id}>
                    <td className="mono">{e.created_at.slice(0, 19).replace('T', ' ')}</td>
                    <td><span className="pill">{e.decision.replace(/_/gu, ' ')}</span></td>
                    <td className="mono">{e.reason_codes.join(', ')}</td>
                    <td style={{ color: 'var(--dim)' }}>{e.freeform_feedback || '—'}</td>
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
