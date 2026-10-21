import React from 'react';
import {useCurrentFrame, useVideoConfig, spring, staticFile, delayRender, continueRender} from 'remotion';
import tl from './data/timeline.json';

export const A: Record<string, number> = tl.anchors as any;
export const WORDS: {w: string; s: number; e: number}[] = tl.words as any;
export const DUR = A.end;
export const C = {ink: '#070b14', fg: '#e7ecf6', muted: '#9fabc4', teal: '#2dd4bf', gold: '#f2b84b', ok: '#5bd69a', warn: '#f2b84b', alert: '#f0716b', blue: '#60a5fa', orange: '#ff8a4c', violet: '#a78bfa', pink: '#f472b6', lime: '#a3e635'};
export const F = {disp: "'Bricolage Grotesque', sans-serif", body: "'Atkinson Hyperlegible', sans-serif", mono: "'IBM Plex Mono', monospace"};
export const STATUS: Record<string, string> = {ok: C.ok, warn: C.warn, alert: C.alert};

export const clamp = (x: number, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const pr = (t: number, t0: number, d: number) => clamp((t - t0) / d);
export const eo = (x: number) => 1 - Math.pow(1 - x, 3);
export const eio = (x: number) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);

export const useT = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  return {t: f / fps, f, fps};
};
export const sp = (t: number, t0: number, fps: number, damping = 16, stiffness = 110, mass = 0.9) =>
  spring({frame: Math.max(0, (t - t0) * fps), fps, config: {damping, stiffness, mass}});

/* ---------- fonts ---------- */
const FONT_FILES: [string, string, string][] = [
  ['Bricolage Grotesque', 'BricolageGrotesque-800.ttf', '800'], ['Bricolage Grotesque', 'BricolageGrotesque-700.ttf', '700'],
  ['Atkinson Hyperlegible', 'AtkinsonHyperlegible-400.ttf', '400'], ['Atkinson Hyperlegible', 'AtkinsonHyperlegible-700.ttf', '700'],
  ['IBM Plex Mono', 'IBMPlexMono-400.ttf', '400'], ['IBM Plex Mono', 'IBMPlexMono-500.ttf', '500'],
];
export const FontLoader: React.FC = () => {
  const [h] = React.useState(() => delayRender('fonts'));
  React.useEffect(() => {
    Promise.all(FONT_FILES.map(([fam, file, w]) => new FontFace(fam, `url(${staticFile('fonts/' + file)})`, {weight: w}).load().then((ff) => document.fonts.add(ff))))
      .then(() => continueRender(h)).catch(() => continueRender(h));
  }, []);
  return null;
};

/* ---------- glass card ---------- */
type Kind = 'up' | 'left' | 'right' | 'tilt' | 'pop' | 'none';
export const Glass: React.FC<{x: number; y: number; w: number; h: number; t0?: number; kind?: Kind; hot?: string; pad?: number; radius?: number; style?: React.CSSProperties; children?: React.ReactNode; dark?: number}> = ({x, y, w, h, t0 = -99, kind = 'tilt', hot, pad = 28, radius = 26, style, children, dark = 0.5}) => {
  const {t, fps} = useT();
  const s = sp(t, t0, fps);
  const op = clamp(s * 1.8);
  let tr = '';
  if (kind === 'up') tr = `translateY(${(1 - s) * 50}px)`;
  if (kind === 'left') tr = `translateX(${-(1 - s) * 90}px)`;
  if (kind === 'right') tr = `translateX(${(1 - s) * 90}px)`;
  if (kind === 'tilt') tr = `perspective(1800px) rotateY(${-(1 - s) * 40}deg) translateY(${(1 - s) * 34}px)`;
  if (kind === 'pop') tr = `scale(${0.88 + 0.12 * s})`;
  const sweep = pr(t - t0, 0.15, 1.1);
  return (
    <div style={{position: 'absolute', left: x, top: y, width: w, height: h, opacity: op, transform: tr, transformOrigin: '50% 50%', borderRadius: radius, padding: pad, boxSizing: 'border-box',
      background: `linear-gradient(155deg, rgba(46,66,112,${dark * 0.82}), rgba(12,20,40,${dark + 0.12}))`,
      backdropFilter: 'blur(22px) saturate(1.4)', WebkitBackdropFilter: 'blur(22px) saturate(1.4)',
      border: `1.5px solid ${hot ? hot + '99' : 'rgba(190,210,255,0.24)'}`,
      boxShadow: `0 30px 80px rgba(0,0,0,.5), inset 0 1.5px 0 rgba(255,255,255,.24), inset 0 -50px 90px rgba(20,44,100,.22)${hot ? `, 0 0 46px ${hot}33` : ''}`, overflow: 'hidden', ...style}}>
      <div style={{position: 'absolute', inset: 0, borderRadius: radius, background: 'linear-gradient(115deg, rgba(255,255,255,.10) 0%, rgba(255,255,255,0) 40%)', pointerEvents: 'none'}} />
      <div style={{position: 'absolute', top: -20, bottom: -20, width: 160, left: `${-20 + sweep * 130}%`, background: 'linear-gradient(100deg, rgba(255,255,255,0), rgba(255,255,255,.16), rgba(255,255,255,0))', transform: 'skewX(-18deg)', opacity: sweep > 0 && sweep < 1 ? 1 : 0, pointerEvents: 'none'}} />
      <div style={{position: 'relative', width: '100%', height: '100%'}}>{children}</div>
    </div>
  );
};

/* plain reveal wrapper (absolute) */
export const Rv: React.FC<{x?: number; y?: number; w?: number; h?: number; t0: number; dx?: number; dy?: number; scale?: number; style?: React.CSSProperties; children?: React.ReactNode}> = ({x = 0, y = 0, w, h, t0, dx = 0, dy = 28, scale = 0.96, style, children}) => {
  const {t, fps} = useT();
  const s = sp(t, t0, fps, 18, 120);
  return <div style={{position: 'absolute', left: x, top: y, width: w, height: h, opacity: clamp(s * 1.8), transform: `translate(${dx * (1 - s)}px, ${dy * (1 - s)}px) scale(${scale + (1 - scale) * s})`, ...style}}>{children}</div>;
};

export const Eyebrow: React.FC<{children: React.ReactNode; color?: string; style?: React.CSSProperties}> = ({children, color = C.muted, style}) => (
  <div style={{font: `500 24px ${F.mono}`, letterSpacing: '0.14em', textTransform: 'uppercase', color, ...style}}>{children}</div>
);

/* ---------- rolling odometer ---------- */
const Digit: React.FC<{pos: number; size: number}> = ({pos, size}) => {
  const lh = size * 1.0;
  return (
    <div style={{height: lh, width: size * 0.6, overflow: 'hidden', display: 'inline-block', position: 'relative'}}>
      <div style={{position: 'absolute', left: 0, top: 0, transform: `translateY(${-pos * lh}px)`}}>
        {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0].map((d, i) => <div key={i} style={{height: lh, lineHeight: `${lh}px`, textAlign: 'center'}}>{d}</div>)}
      </div>
    </div>
  );
};
export const Odo: React.FC<{value: number; places: number; size: number; color?: string; prefix?: string; suffix?: string; shadow?: string}> = ({value, places, size, color = C.gold, prefix = '', suffix = '', shadow}) => {
  const v = Math.max(0, value);
  const digs: React.ReactNode[] = [];
  for (let k = places - 1; k >= 0; k--) {
    const x = v / Math.pow(10, k);
    const base = Math.floor(x) % 10;
    const frac = k === 0 ? x - Math.floor(x) : 0;
    const lower = v / Math.pow(10, k - 1 < 0 ? 0 : k - 1);
    const roll = k === 0 ? frac : clamp(((lower % 10) - 8) / 2); // ripple when the next digit is >= 8
    const show = v >= Math.pow(10, k) || k === 0;
    digs.push(<div key={k} style={{opacity: show ? 1 : 0}}><Digit pos={base + roll} size={size} /></div>);
  }
  return (
    <div style={{display: 'flex', alignItems: 'center', font: `800 ${size}px ${F.disp}`, color, letterSpacing: '-0.02em', textShadow: shadow || `0 0 60px ${color}59`}}>
      <span>{prefix}</span>{digs}<span>{suffix}</span>
    </div>
  );
};

/* ---------- scene window ---------- */
export const Win: React.FC<{a: number; b: number; children: React.ReactNode; blur?: boolean}> = ({a, b, children, blur = true}) => {
  const {t} = useT();
  if (t < a - 0.55 || t > b + 0.55) return null;
  const i = eo(pr(t, a - 0.5, 0.5));
  const o = 1 - eo(pr(t, b, 0.5));
  const op = Math.min(i, o);
  const bl = blur ? (1 - op) * 10 : 0;
  return <div style={{position: 'absolute', inset: 0, opacity: op, filter: bl > 0.2 ? `blur(${bl}px)` : undefined, transform: `scale(${1 + (1 - i) * 0.015 + (1 - o) * 0.012})`}}>{children}</div>;
};
export const Grp: React.FC<{a: number; b: number; children: React.ReactNode}> = ({a, b, children}) => {
  const {t} = useT();
  if (t < a - 0.2 || t > b + 0.5) return null;
  const o = eo(pr(t, a - 0.15, 0.45)) * (1 - eo(pr(t, b - 0.35, 0.45)));
  return <div style={{position: 'absolute', inset: 0, opacity: o}}>{children}</div>;
};
export const Src: React.FC<{text: string}> = ({text}) => (
  <div style={{position: 'absolute', left: 96, top: 886, width: 1728, font: `400 22px/1.3 ${F.mono}`, color: '#8793ad'}}>{text}</div>
);

/* ---------- section head with kinetic title + ghost numeral ---------- */
export const QHead: React.FC<{n: number | string; label: string; q: string; skey?: string; stext?: string; st?: number; a: number; eyebrow?: string}> = ({n, label, q, skey, stext, st = 0, a, eyebrow}) => {
  const {t, fps} = useT();
  const words = q.split(' ');
  const ss = skey ? sp(t, st, fps, 12, 140) : 0;
  const col = skey ? STATUS[skey] : C.ok;
  return (
    <>
      <div style={{position: 'absolute', right: 70, top: 20, font: `800 620px/1 ${F.disp}`, color: 'transparent', WebkitTextStroke: '3px rgba(190,210,255,0.10)', opacity: eo(pr(t, a, 1.0)), transform: `translateX(${(1 - eo(pr(t, a, 1.0))) * 120}px)`, letterSpacing: '-0.04em'}}>{n}</div>
      <div style={{position: 'absolute', left: 96, top: 140, right: 96, height: 180}}>
        <Eyebrow style={{opacity: eo(pr(t, a + 0.05, 0.4))}}>{eyebrow ?? `Question ${n} of 5 · ${label}`}</Eyebrow>
        <div style={{display: 'flex', flexWrap: 'wrap', gap: '0 18px', marginTop: 10, font: `800 64px/1.05 ${F.disp}`, letterSpacing: '-0.01em'}}>
          {words.map((w, i) => {
            const s = sp(t, a + 0.12 + i * 0.06, fps, 18, 130);
            return <span key={i} style={{display: 'inline-block', opacity: clamp(s * 1.6), transform: `translateY(${(1 - s) * 36}px)`}}>{w}</span>;
          })}
        </div>
        {skey && (
          <div style={{position: 'absolute', left: 0, top: 124, height: 56, padding: '0 26px', borderRadius: 28, display: 'flex', alignItems: 'center', gap: 14, font: `700 27px ${F.body}`, border: `2px solid ${col}99`, color: col, background: `${col}22`, opacity: clamp(ss * 1.6), transform: `translateX(${-(1 - ss) * 50}px) scale(${0.92 + 0.08 * ss})`, boxShadow: `0 0 ${40 * (1 - pr(t, st, 1.2))}px ${col}`}}>
            <span style={{width: 16, height: 16, borderRadius: 8, background: col, boxShadow: `0 0 14px ${col}`}} />
            <b style={{font: `500 26px ${F.mono}`, letterSpacing: '0.08em'}}>{skey.toUpperCase()}</b>
            <span>{stext}</span>
          </div>
        )}
      </div>
    </>
  );
};

/* ---------- bar rows ---------- */
export const BarRows: React.FC<{rows: {label: string; val: number; color: string; fmt?: (v: number) => string}[]; x: number; y: number; w: number; rowH: number; gap: number; max: number; labW: number; t0s: number[]; lf?: number; vf?: number}> = ({rows, x, y, w, rowH, gap, max, labW, t0s, lf = 27, vf = 44}) => {
  const {t, fps} = useT();
  return (
    <>
      {rows.map((r, i) => {
        const yy = y + i * (rowH + gap);
        const s = sp(t, t0s[i] - 0.1, fps);
        const p = eo(pr(t, t0s[i], 1.1));
        const wpx = w - labW;
        const wv = wpx * (r.val / max) * p;
        return (
          <div key={i} style={{position: 'absolute', left: x, top: yy, width: w, height: rowH, opacity: clamp(s * 1.8), transform: `translateX(${-(1 - s) * 40}px)`}}>
            <div style={{position: 'absolute', left: 0, top: 0, width: labW, height: rowH, display: 'flex', alignItems: 'center', font: `400 ${lf}px/1.15 ${F.body}`, color: C.muted}}>{r.label}</div>
            <div style={{position: 'absolute', left: labW, top: 0, width: wpx, height: rowH, borderRadius: 14, background: 'rgba(150,180,240,.08)'}}>
              <div style={{position: 'absolute', left: 0, top: 0, height: '100%', width: wv, borderRadius: 14, background: `linear-gradient(90deg, ${r.color}cc, ${r.color})`, boxShadow: `0 0 34px ${r.color}66, inset 0 2px 0 rgba(255,255,255,.35)`}} />
              <div style={{position: 'absolute', left: wv + 16, top: 0, height: '100%', display: 'flex', alignItems: 'center', font: `500 ${vf}px ${F.mono}`, color: '#fff', opacity: p > 0.02 ? 1 : 0}}>{r.fmt ? r.fmt(r.val * p) : Math.round(r.val * p) + '%'}</div>
            </div>
          </div>
        );
      })}
    </>
  );
};

/* ---------- ring gauge ---------- */
export const Ring: React.FC<{cx: number; cy: number; r: number; sw: number; frac: number; color: string; track?: string; opacity?: number}> = ({cx, cy, r, sw, frac, color, track = 'rgba(150,180,240,.14)', opacity = 1}) => {
  const c = 2 * Math.PI * r;
  return (
    <svg width={2 * r + 2 * sw} height={2 * r + 2 * sw} style={{position: 'absolute', left: cx - r - sw, top: cy - r - sw, overflow: 'visible', opacity}}>
      <circle cx={r + sw} cy={r + sw} r={r} fill="none" stroke={track} strokeWidth={sw} />
      <circle cx={r + sw} cy={r + sw} r={r} fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round" strokeDasharray={`${c * frac} ${c}`} transform={`rotate(-90 ${r + sw} ${r + sw})`} opacity={frac > 0.004 ? 1 : 0} style={{filter: `drop-shadow(0 0 12px ${color}aa)`}} />
    </svg>
  );
};
