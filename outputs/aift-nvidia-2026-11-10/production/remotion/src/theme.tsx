import React from 'react';
import {AbsoluteFill, Easing, continueRender, delayRender, interpolate, staticFile, useCurrentFrame} from 'remotion';

// AIFT bright glass broadcast theme: gold, black, white, restrained lime. Red = negative price moves only.
export const T = {
  bg: '#070706',
  gold: '#F6C445',
  gold2: '#C9962C',
  lime: '#C9F23E',
  white: '#FFFFFF',
  text: '#FAF7EE',
  text2: '#D9D3C2',
  muted: '#A39C89',
  faint: '#6B6658',
  red: '#FF4D4D',
  edge: 'rgba(255,255,255,0.42)',
};
export const SANS = "'Inter', system-ui, sans-serif";
export const MONO = "'IBM Plex Mono', ui-monospace, monospace";
export const SERIF = "'Source Serif 4', Georgia, serif";
export const SNAPSHOT = 'Research snapshot · 10 Nov 2026 · morning, UK time';

const FONTS: [string, string, string, string][] = [
  ['Inter', 'fonts/inter-latin-400-normal.woff2', '400', 'normal'],
  ['Inter', 'fonts/inter-latin-500-normal.woff2', '500', 'normal'],
  ['Inter', 'fonts/inter-latin-600-normal.woff2', '600', 'normal'],
  ['Inter', 'fonts/inter-latin-700-normal.woff2', '700', 'normal'],
  ['Inter', 'fonts/inter-latin-800-normal.woff2', '800', 'normal'],
  ['IBM Plex Mono', 'fonts/ibm-plex-mono-latin-500-normal.woff2', '500', 'normal'],
  ['IBM Plex Mono', 'fonts/ibm-plex-mono-latin-600-normal.woff2', '600', 'normal'],
  ['Source Serif 4', 'fonts/source-serif-4-latin-400-italic.woff2', '400', 'italic'],
  ['Source Serif 4', 'fonts/source-serif-4-latin-600-normal.woff2', '600', 'normal'],
  ['Source Serif 4', 'fonts/source-serif-4-latin-700-normal.woff2', '700', 'normal'],
];
let fontsStarted = false;
export const loadFonts = () => {
  if (fontsStarted || typeof document === 'undefined') return;
  fontsStarted = true;
  const h = delayRender('fonts');
  Promise.all(FONTS.map(([fam, file, weight, style]) => new FontFace(fam, `url(${staticFile(file)})`, {weight, style}).load().then((ff) => (document.fonts as any).add(ff))))
    .then(() => continueRender(h))
    .catch(() => continueRender(h));
};
loadFonts();

const EASE = Easing.bezier(0.22, 1, 0.36, 1);
export const prog = (f: number, at: number, dur = 18) => interpolate(f, [at, at + dur], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: EASE});
export const lin = (f: number, at: number, dur: number) => interpolate(f, [at, at + dur], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
// cue accessor: frames from scene start for mark k (falls back to the last cue)
export const cu = (cues: number[], k: number) => cues[Math.min(k, cues.length - 1)];
export type SP = {len: number; cues: number[]};

export const Rv: React.FC<{at: number; dur?: number; y?: number; x?: number; s?: number; style?: React.CSSProperties; children: React.ReactNode}> = ({at, dur = 18, y = 22, x = 0, s = 1, style, children}) => {
  const f = useCurrentFrame();
  const p = prog(f, at, dur);
  return <div style={{opacity: p, transform: `translate(${(1 - p) * x}px, ${(1 - p) * y}px) scale(${s + (1 - s) * p})`, ...style}}>{children}</div>;
};
// brightness for "one at a time" focus: 1 while active, `low` otherwise
export const focus = (f: number, from: number, to: number, low = 0.34) => {
  const a = prog(f, from, 12);
  const b = prog(f, to, 12);
  return low + (1 - low) * Math.max(0, a - b);
};

export const Background: React.FC = () => {
  const f = useCurrentFrame();
  const t = f / 30;
  const gx = 22 + 9 * Math.sin(t / 19);
  const gy = 16 + 6 * Math.cos(t / 23);
  const hx = 82 + 7 * Math.cos(t / 17);
  const hy = 88 + 5 * Math.sin(t / 29);
  const sweep = ((t * 14) % 260) - 80;
  const off = (f * 0.1) % 56;
  return (
    <AbsoluteFill style={{background: T.bg}}>
      <AbsoluteFill style={{background: `radial-gradient(1100px 760px at ${gx}% ${gy}%, rgba(246,196,69,0.34) 0%, rgba(201,150,44,0.13) 38%, transparent 70%)`}} />
      <AbsoluteFill style={{background: `radial-gradient(900px 640px at ${hx}% ${hy}%, rgba(246,196,69,0.20) 0%, rgba(201,242,62,0.05) 40%, transparent 68%)`}} />
      <AbsoluteFill style={{background: 'radial-gradient(1500px 900px at 50% 46%, rgba(255,255,255,0.055) 0%, transparent 62%)'}} />
      <AbsoluteFill
        style={{
          backgroundImage: 'radial-gradient(rgba(255,255,255,0.13) 1.2px, transparent 1.3px)',
          backgroundSize: '56px 56px',
          backgroundPosition: `${-off}px ${-off * 0.6}px`,
          maskImage: 'radial-gradient(ellipse at center, black 30%, transparent 92%)',
          WebkitMaskImage: 'radial-gradient(ellipse at center, black 30%, transparent 92%)',
        }}
      />
      <AbsoluteFill style={{background: `linear-gradient(112deg, transparent ${sweep - 14}%, rgba(255,255,255,0.045) ${sweep}%, transparent ${sweep + 14}%)`}} />
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, transparent 58%, rgba(0,0,0,0.6) 100%)'}} />
    </AbsoluteFill>
  );
};

// glass panel with visible edge, top highlight and slow sheen
export const Glass: React.FC<{style?: React.CSSProperties; tone?: 'clear' | 'gold' | 'lime' | 'dark'; dashed?: boolean; r?: number; children?: React.ReactNode}> = ({style, tone = 'clear', dashed = false, r = 28, children}) => {
  const f = useCurrentFrame();
  const sheen = ((f * 0.35) % 220) - 60;
  const tint =
    tone === 'gold'
      ? 'linear-gradient(150deg, rgba(246,196,69,0.26) 0%, rgba(246,196,69,0.09) 46%, rgba(255,255,255,0.03) 100%)'
      : tone === 'lime'
        ? 'linear-gradient(150deg, rgba(201,242,62,0.20) 0%, rgba(201,242,62,0.06) 46%, rgba(255,255,255,0.03) 100%)'
        : tone === 'dark'
          ? 'linear-gradient(150deg, rgba(20,19,16,0.92) 0%, rgba(12,12,10,0.88) 100%)'
          : 'linear-gradient(150deg, rgba(255,255,255,0.19) 0%, rgba(255,255,255,0.075) 46%, rgba(255,255,255,0.035) 100%)';
  const edge = tone === 'gold' ? 'rgba(246,196,69,0.75)' : tone === 'lime' ? 'rgba(201,242,62,0.7)' : T.edge;
  return (
    <div
      style={{
        position: 'relative',
        borderRadius: r,
        background: tint,
        border: `${dashed ? 2.5 : 1.5}px ${dashed ? 'dashed' : 'solid'} ${edge}`,
        boxShadow: '0 36px 80px rgba(0,0,0,0.5), 0 2px 0 rgba(255,255,255,0.05), inset 0 1.5px 0 rgba(255,255,255,0.5), inset 0 -1px 0 rgba(255,255,255,0.07)',
        overflow: 'hidden',
        boxSizing: 'border-box',
        ...style,
      }}
    >
      <div style={{position: 'absolute', inset: 0, background: `linear-gradient(115deg, transparent ${sheen - 9}%, rgba(255,255,255,0.075) ${sheen}%, transparent ${sheen + 9}%)`, pointerEvents: 'none'}} />
      {children}
    </div>
  );
};

// purposeful parallax: content layers drift at different depths over the scene
export const Para: React.FC<{len: number; depth?: number; style?: React.CSSProperties; children: React.ReactNode}> = ({len, depth = 1, style, children}) => {
  const f = useCurrentFrame();
  const p = interpolate(f, [0, Math.max(1, len)], [-1, 1], {extrapolateRight: 'clamp'});
  return <div style={{position: 'absolute', inset: 0, transform: `translate(${p * -7 * depth}px, ${p * -3 * depth}px) scale(${1 + (p + 1) * 0.006 * depth})`, transformOrigin: '50% 46%', ...style}}>{children}</div>;
};

export type Kind = 'CONFIRMED' | 'REPORTED' | 'ANALYSIS' | 'SCENARIO' | 'SCHEDULED' | 'CALCULATION' | 'REQUESTED' | 'UNRESOLVED' | 'GUIDANCE' | 'ALLEGED';
const kindCol = (k: string) => (k === 'CONFIRMED' ? T.lime : k === 'ANALYSIS' || k === 'CALCULATION' ? T.white : k === 'UNRESOLVED' ? T.text2 : T.gold);
export const Chip: React.FC<{kind: string; size?: number; style?: React.CSSProperties}> = ({kind, size = 22, style}) => {
  const col = kindCol(kind);
  const dashed = ['SCENARIO', 'REQUESTED', 'SCHEDULED', 'GUIDANCE', 'ALLEGED', 'UNRESOLVED'].includes(kind);
  return (
    <span style={{display: 'inline-flex', alignItems: 'center', gap: size * 0.45, fontFamily: MONO, fontSize: size, fontWeight: 600, letterSpacing: size * 0.09, color: col, border: `2px ${dashed ? 'dashed' : 'solid'} ${col}`, borderRadius: 8, padding: `${size * 0.26}px ${size * 0.6}px`, background: 'rgba(0,0,0,0.45)', whiteSpace: 'nowrap', ...style}}>
      <span style={{width: size * 0.42, height: size * 0.42, borderRadius: 2, background: col, display: 'inline-block'}} />
      {kind}
    </span>
  );
};

export const Shell: React.FC<{chapter?: string; kind?: string; source: string; len: number; children: React.ReactNode}> = ({chapter, kind, source, len, children}) => (
  <AbsoluteFill>
    <div style={{position: 'absolute', top: 40, left: 96, right: 96, display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontFamily: MONO, fontSize: 20, letterSpacing: 2.6, textTransform: 'uppercase', color: T.muted}}>
      <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
        <div style={{width: 14, height: 14, background: T.lime, borderRadius: 3}} />
        <span style={{color: T.text, fontWeight: 600}}>AI Finance Toolkit</span>
        {chapter ? <span style={{color: T.faint}}>/</span> : null}
        {chapter ? <span style={{color: T.gold}}>{chapter}</span> : null}
      </div>
      <div style={{color: T.text2}}>{SNAPSHOT}</div>
    </div>
    <Para len={len} depth={1}>{children}</Para>
    <div style={{position: 'absolute', bottom: 30, left: 96, right: 96, display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 30}}>
      <div style={{display: 'flex', gap: 14, alignItems: 'center', fontFamily: SANS, fontSize: 23, color: T.text2, letterSpacing: 0.2, minWidth: 0}}>
        <span style={{fontFamily: MONO, textTransform: 'uppercase', letterSpacing: 2.4, fontSize: 18, color: T.gold, fontWeight: 600, flexShrink: 0}}>Source</span>
        <div style={{height: 22, width: 2, background: T.faint, flexShrink: 0}} />
        <span style={{whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis'}}>{source}</span>
      </div>
      {kind ? <Chip kind={kind} size={20} style={{flexShrink: 0}} /> : null}
    </div>
  </AbsoluteFill>
);

export const H1: React.FC<{at?: number; kicker?: string; size?: number; top?: number; style?: React.CSSProperties; children: React.ReactNode}> = ({at = 0, kicker, size = 62, top = 112, style, children}) => (
  <Rv at={at} style={{position: 'absolute', left: 96, right: 96, top, ...style}}>
    {kicker ? <div style={{fontFamily: MONO, fontSize: 22, letterSpacing: 4, textTransform: 'uppercase', color: T.lime, fontWeight: 600, marginBottom: 10}}>{kicker}</div> : null}
    <div style={{fontFamily: SANS, fontSize: size, fontWeight: 800, color: T.white, letterSpacing: -1.6, lineHeight: 1.06}}>{children}</div>
  </Rv>
);

// animated marker highlight behind inline text
export const Hl: React.FC<{at: number; color?: string; children: React.ReactNode}> = ({at, color = 'rgba(246,196,69,0.42)', children}) => {
  const f = useCurrentFrame();
  const p = prog(f, at, 20);
  return (
    <span style={{position: 'relative', display: 'inline', backgroundImage: `linear-gradient(${color}, ${color})`, backgroundRepeat: 'no-repeat', backgroundSize: `${p * 100}% 88%`, backgroundPosition: '0 60%', padding: '0 6px', margin: '0 -6px', borderRadius: 4, boxDecorationBreak: 'clone', WebkitBoxDecorationBreak: 'clone'}}>{children}</span>
  );
};

export const Num: React.FC<{to: number; at: number; dur?: number; fmt: (v: number) => string; style?: React.CSSProperties}> = ({to, at, dur = 34, fmt, style}) => {
  const f = useCurrentFrame();
  const p = interpolate(f, [at, at + dur], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.16, 1, 0.3, 1)});
  return <span style={{fontVariantNumeric: 'tabular-nums', ...style}}>{fmt(to * p)}</span>;
};

// "official source" paper card: outlet, date, verbatim headline; children = excerpt
export const SourceCard: React.FC<{outlet: string; date: string; headline: string; tag?: string; hsize?: number; style?: React.CSSProperties; children?: React.ReactNode}> = ({outlet, date, headline, tag, hsize = 44, style, children}) => (
  <div style={{background: 'linear-gradient(180deg, #FFFDF6 0%, #F3EEDF 100%)', borderRadius: 18, boxShadow: '0 40px 90px rgba(0,0,0,0.6), 0 0 0 1.5px rgba(255,255,255,0.7)', padding: '34px 44px 38px', color: '#14130F', boxSizing: 'border-box', ...style}}>
    <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontFamily: MONO, fontSize: 21, letterSpacing: 2, textTransform: 'uppercase', color: '#5A5546', borderBottom: '2px solid #14130F', paddingBottom: 14}}>
      <span style={{fontWeight: 600, color: '#14130F'}}>{outlet}</span>
      <span>{date}</span>
    </div>
    <div style={{fontFamily: SERIF, fontWeight: 700, fontSize: hsize, lineHeight: 1.12, letterSpacing: -0.6, marginTop: 20}}>{headline}</div>
    {children}
    {tag ? <div style={{marginTop: 18, fontFamily: MONO, fontSize: 18, letterSpacing: 1.6, textTransform: 'uppercase', color: '#7A735F'}}>{tag}</div> : null}
  </div>
);

export const SectionCard: React.FC<{num: string; title: string; len: number}> = ({num, title, len}) => {
  const f = useCurrentFrame();
  const p = prog(f, 2, 16);
  const out = interpolate(f, [len - 12, len], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', opacity: out}}>
      <Glass style={{padding: '46px 70px', transform: `scale(${0.96 + 0.04 * p})`, opacity: p}}>
        <div style={{display: 'flex', alignItems: 'center', gap: 34}}>
          <div style={{fontFamily: MONO, fontSize: 64, color: T.lime, fontWeight: 600}}>{num}</div>
          <div style={{width: 3, height: 86, background: T.gold, transform: `scaleY(${p})`}} />
          <div style={{fontFamily: SANS, fontSize: 82, color: T.white, fontWeight: 800, letterSpacing: -2, clipPath: `inset(0 ${100 - p * 100}% 0 0)`}}>{title}</div>
        </div>
      </Glass>
    </AbsoluteFill>
  );
};

export const Bullet: React.FC<{at: number; color?: string; size?: number; style?: React.CSSProperties; children: React.ReactNode}> = ({at, color = T.gold, size = 38, style, children}) => (
  <Rv at={at} x={-18} y={0} style={{display: 'flex', gap: 20, alignItems: 'flex-start', fontFamily: SANS, fontSize: size, color: T.text, lineHeight: 1.22, fontWeight: 500, ...style}}>
    <span style={{flexShrink: 0, width: size * 0.36, height: size * 0.36, marginTop: size * 0.44, background: color, borderRadius: 3, transform: 'rotate(45deg)'}} />
    <span>{children}</span>
  </Rv>
);

// crossed-out statement ("this is NOT ...") — line-through draws across wrapped lines
export const Not: React.FC<{at: number; size?: number; style?: React.CSSProperties; children: React.ReactNode}> = ({at, size = 40, style, children}) => {
  const f = useCurrentFrame();
  const p = prog(f, at + 10, 16);
  return (
    <Rv at={at} style={{display: 'flex', alignItems: 'flex-start', gap: 20, fontFamily: SANS, fontSize: size, fontWeight: 600, color: T.text, lineHeight: 1.2, ...style}}>
      <span style={{flexShrink: 0, fontFamily: MONO, fontSize: size * 0.6, fontWeight: 600, letterSpacing: 2, color: T.bg, background: T.white, borderRadius: 6, padding: '4px 12px', marginTop: size * 0.12}}>NOT</span>
      <span style={{textDecorationLine: 'line-through', textDecorationThickness: Math.max(3, size * 0.08), textDecorationColor: `rgba(246,196,69,${p})`}}>{children}</span>
    </Rv>
  );
};
