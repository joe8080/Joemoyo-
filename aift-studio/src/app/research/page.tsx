import { getRuntime, ownerId } from '@/lib/server/runtime';
import { Empty } from '@/components/ui';
import { createResearchJob, produceContent } from '../actions';
import { FIXTURE_TOPIC } from '@/lib/fixtures/northwind';

export const dynamic = 'force-dynamic';

export default async function ResearchDesk() {
  const { repo } = await getRuntime();
  const jobs = await repo.listResearchJobs(await ownerId());

  const detail = await Promise.all(jobs.map(async (j) => ({
    job: j,
    sources: await repo.listSourceDocuments(j.id),
    claims: await repo.listClaims(j.id),
  })));

  return (
    <>
      <div className="pagehead">
        <div>
          <h1>Research desk</h1>
          <p className="sub">
            Sources are fetched and stored before anything cites them. A discovery snippet is a
            pointer, never a citation. Every claim below shows the evidence that backs it and, where
            it fails, the specific reason it cannot enter a script.
          </p>
        </div>
      </div>

      <div className="grid g2">
        <div className="card">
          <h2>New research topic</h2>
          <form action={createResearchJob}>
            <div className="field">
              <label htmlFor="topic">Topic</label>
              <input id="topic" name="topic" required defaultValue={FIXTURE_TOPIC.topic}
                placeholder="What question should the evidence answer?" />
              <p className="hint">Write it as a question the evidence can settle, not as a conclusion.</p>
            </div>
            <div className="row">
              <div className="field" style={{ flex: 1 }}>
                <label htmlFor="ticker">Ticker (optional)</label>
                <input id="ticker" name="ticker" defaultValue={FIXTURE_TOPIC.ticker} />
              </div>
              <div className="field" style={{ flex: 1 }}>
                <label htmlFor="reference_date">Reference date</label>
                <input id="reference_date" name="reference_date" type="date" defaultValue={FIXTURE_TOPIC.referenceDate} />
              </div>
            </div>
            <div className="row" style={{ marginTop: 16 }}>
              <button className="primary" type="submit">Collect evidence</button>
            </div>
          </form>
          <div className="note" style={{ marginTop: 14 }}>
            The reference date is not cosmetic. Every figure the pipeline accepts is compared against
            it, and a figure without an as-of date is refused rather than dated by assumption.
          </div>
        </div>

        <div className="card">
          <h2>Source policy in force</h2>
          <ol style={{ margin: '0 0 0 18px', color: 'var(--dim)', fontSize: 13, lineHeight: 1.9 }}>
            <li>Primary filings — 10-Q, 10-K, 20-F, prospectus, exchange notice</li>
            <li>Primary company — IR pages, releases, transcripts</li>
            <li>Primary regulator — SEC, FCA, central banks, statistics agencies</li>
            <li>Specialist — professional research, standards bodies, academia</li>
            <li>Reputable financial journalism</li>
          </ol>
          <div className="divider" />
          <p className="hint">
            A material claim resting only on non-primary evidence needs two independent sources. A
            claim whose stored excerpt does not contain the figure it asserts is refused, even when
            the citation is real — that is the failure mode nobody notices.
          </p>
        </div>
      </div>

      {detail.length === 0 ? (
        <div className="card" style={{ marginTop: 14 }}><Empty>No research jobs yet.</Empty></div>
      ) : detail.map(({ job, sources, claims }) => {
        const safe = claims.filter((c) => c.is_public_safe);
        const unsafe = claims.filter((c) => !c.is_public_safe);
        return (
          <div className="card" key={job.id} style={{ marginTop: 14 }}>
            <div className="row" style={{ justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <h2 style={{ marginBottom: 4 }}>{job.topic}</h2>
                <div className="row" style={{ gap: 8 }}>
                  <span className="pill">{job.status}</span>
                  {job.ticker && <span className="pill mono">{job.ticker}</span>}
                  <span className="pill mono">as of {job.reference_date}</span>
                  <span className="pill pass">{safe.length} public-safe</span>
                  {unsafe.length > 0 && <span className="pill fail">{unsafe.length} withheld</span>}
                </div>
              </div>
              {job.status === 'evidence_ready' && (
                <div style={{ minWidth: 320 }}>
                  {(['deep_dive', 'short'] as const).map((format) => (
                    <form action={produceContent} key={format} style={{ marginBottom: 8 }}>
                      <input type="hidden" name="research_job_id" value={job.id} />
                      <input type="hidden" name="format" value={format} />
                      <div className="row" style={{ justifyContent: 'flex-end' }}>
                        <label style={{ display: 'flex', alignItems: 'center', gap: 6, margin: 0,
                          textTransform: 'none', letterSpacing: 0, fontSize: 12, color: 'var(--dim)' }}>
                          <input type="checkbox" name="with_video" style={{ width: 'auto' }}
                            defaultChecked={format === 'short'} />
                          render video
                        </label>
                        <button type="submit" className={format === 'deep_dive' ? 'primary' : ''}>
                          Produce {format === 'deep_dive' ? 'deep dive' : 'Short'}
                        </button>
                      </div>
                    </form>
                  ))}
                  <p className="hint" style={{ textAlign: 'right' }}>
                    Rendering is frame-exact and takes roughly two minutes per finished minute.
                    Leave it off to inspect the script, evidence and scene plan first — a pack
                    without a video cannot be approved, and the review room will say so.
                  </p>
                </div>
              )}
            </div>

            <div className="divider" />

            <h3>Source register — {sources.length} document{sources.length === 1 ? '' : 's'}</h3>
            <div className="tablewrap">
              <table>
                <thead>
                  <tr><th>Publisher</th><th>Title</th><th>Published</th><th>Accessed</th><th>Tier</th><th>Hash</th><th>Status</th></tr>
                </thead>
                <tbody>
                  {sources.map((s) => (
                    <tr key={s.id}>
                      <td>{s.publisher}</td>
                      <td style={{ maxWidth: 340 }}>{s.title}</td>
                      <td className="mono">{s.published_at ?? '—'}</td>
                      <td className="mono">{s.accessed_at.slice(0, 10)}</td>
                      <td className="mono">{s.source_tier}</td>
                      <td className="mono" title={s.content_hash}>{s.content_hash.slice(0, 10)}…</td>
                      <td>
                        <span className={`pill ${s.retrieval_status === 'fetched' ? 'pass' : 'fail'}`}>
                          {s.retrieval_status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="divider" />

            <h3>Claim ledger — {claims.length} claim{claims.length === 1 ? '' : 's'}</h3>
            <div className="scroll">
              {claims.map((c) => (
                <div className={`claim ${c.is_public_safe ? '' : 'unsafe'}`} key={c.id}>
                  <div className="row" style={{ gap: 8, marginBottom: 6 }}>
                    <span className="mono" style={{ color: 'var(--accent)' }}>{c.claim_id}</span>
                    <span className="pill">{c.claim_type.replace(/_/gu, ' ')}</span>
                    <span className="pill mono">as of {c.as_of_date ?? 'undated'}</span>
                    <span className="pill mono">confidence {c.confidence.toFixed(2)}</span>
                    <span className={`pill ${c.is_public_safe ? 'pass' : 'fail'}`}>
                      {c.is_public_safe ? 'public-safe' : 'withheld from script'}
                    </span>
                  </div>
                  <div>{c.claim_text}</div>
                  {c.source_excerpt && <div className="excerpt">“{c.source_excerpt}”</div>}
                  <div className="hint" style={{ marginTop: 6 }}>{c.public_safe_reason}</div>
                  {c.uncertainty_note && (
                    <div className="hint" style={{ color: 'var(--warn)' }}>Uncertainty: {c.uncertainty_note}</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </>
  );
}
