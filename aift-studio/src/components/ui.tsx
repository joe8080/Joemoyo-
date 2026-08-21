import type { ContentState } from '@/lib/workflow/states';
import type { QualityCheck } from '@/lib/domain';

/** Shared display pieces. Server components — no client JavaScript is shipped. */

const PIPELINE: ContentState[] = [
  'queued', 'researching', 'evidence_ready', 'drafting',
  'visual_planning', 'rendering', 'qa_running', 'needs_review',
  'approved_for_archive', 'archived',
];

const SHORT: Record<string, string> = {
  queued: 'queue', researching: 'research', evidence_ready: 'evidence', drafting: 'draft',
  visual_planning: 'visuals', rendering: 'render', qa_running: 'qa', needs_review: 'review',
  approved_for_archive: 'approved', archived: 'archived',
};

export function Pipeline({ status }: { status: ContentState }) {
  const i = PIPELINE.indexOf(status);
  const stalled = status === 'blocked' || status === 'rework_required';
  return (
    <div className="pipe">
      {PIPELINE.map((s, n) => (
        <span key={s} style={{ display: 'inline-flex', alignItems: 'center' }}>
          {n > 0 && <span className="arrow">›</span>}
          <span className={`s ${n < i ? 'done' : n === i ? 'now' : ''}`}>{SHORT[s]}</span>
        </span>
      ))}
      {stalled && (
        <>
          <span className="arrow">›</span>
          <span className="s bad">{status === 'blocked' ? 'blocked' : 'rework'}</span>
        </>
      )}
    </div>
  );
}

export function StatusPill({ status }: { status: ContentState }) {
  const tone =
    status === 'archived' || status === 'approved_for_archive' ? 'pass'
      : status === 'blocked' || status === 'rework_required' ? 'fail'
        : status === 'needs_review' ? 'info' : 'warn';
  return <span className={`pill ${tone}`}>{status.replace(/_/gu, ' ')}</span>;
}

export function CheckRow({ check }: { check: QualityCheck }) {
  const tone = check.result === 'pass' ? 'pass' : check.severity === 'blocking' ? 'fail' : 'warn';
  const mark = check.result === 'pass' ? '✓' : check.severity === 'blocking' ? '✗' : '!';
  return (
    <div style={{ padding: '11px 0', borderBottom: '1px solid var(--line)' }}>
      <div className="row" style={{ gap: 8 }}>
        <span className={`pill ${tone}`}>{mark} {check.gate}</span>
        <span className="mono" style={{ color: 'var(--dim)' }}>{check.check_name}</span>
      </div>
      <div style={{ marginTop: 6, color: check.result === 'pass' ? 'var(--dim)' : 'var(--ink)' }}>
        {check.details.message}
      </div>
      {check.details.offenders.length > 0 && (
        <ul style={{ margin: '8px 0 0 16px', color: 'var(--dim)', fontSize: 12 }}>
          {check.details.offenders.slice(0, 8).map((o) => (
            <li key={o} className="mono">{o}</li>
          ))}
          {check.details.offenders.length > 8 && <li>…and {check.details.offenders.length - 8} more</li>}
        </ul>
      )}
      {check.details.remediation && (
        <div className="hint" style={{ marginTop: 6 }}><b style={{ color: 'var(--dim)' }}>Fix:</b> {check.details.remediation}</div>
      )}
    </div>
  );
}

export function Stat({ n, l, tone }: { n: string | number; l: string; tone?: 'pass' | 'warn' | 'fail' }) {
  const colour = tone === 'pass' ? 'var(--pass)' : tone === 'warn' ? 'var(--warn)' : tone === 'fail' ? 'var(--fail)' : 'var(--ink)';
  return (
    <div className="card stat">
      <span className="n" style={{ color: colour }}>{n}</span>
      <span className="l">{l}</span>
    </div>
  );
}

export function Empty({ children }: { children: React.ReactNode }) {
  return <div className="empty">{children}</div>;
}

export function fmtDuration(ms: number): string {
  const s = Math.round(ms / 1000);
  return `${Math.floor(s / 60)}m ${String(s % 60).padStart(2, '0')}s`;
}

export function fmtBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1_048_576) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1_048_576).toFixed(1)} MB`;
}
