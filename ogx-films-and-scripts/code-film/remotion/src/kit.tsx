// OGX code-film kit: palette, fonts, motion helpers and frame furniture shared by every episode.
// Adapted from the AIFT explainer kit (that template is untouched); this one carries the OGX archive look.
import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig, continueRender, delayRender, random} from 'remotion';
import GEO from './geo.json';

export const C = {
  bg: '#0B0907', bg2: '#19130C', sea: '#0A1216', land: '#1C1710', landLine: '#5A4A33',
  cream: '#F0E7D3', text2: '#CFC4AB', muted: '#948871', gold: '#DDB25A', goldDim: '#7E6630',
  red: '#CC4A32', teal: '#63B8AA', blue: '#86AEE0', amber: '#E79A3C', line: '#3B3023', paper: '#E9DFC8', ink: '#16110B',
};
export const DISPLAY = "'Cinzel', serif";
export const SERIF = "'Source Serif', Georgia, serif";
export const SANS = "'Inter', system-ui, sans-serif";
export const MONO = "'Plex', ui-monospace, monospace";

// ---------- fonts ----------
const fontHandle = delayRender('fonts');
const ff = (fam: string, file: string, weight: string, style = 'normal') => new FontFace(fam, `url(${staticFile('fonts/' + file)})`, {weight, style}).load();
Promise.all([
  ff('Cinzel', 'cinzel-latin-600-normal.woff2', '600'), ff('Cinzel', 'cinzel-latin-700-normal.woff2', '700'), ff('Cinzel', 'cinzel-latin-900-normal.woff2', '900'),
  ff('Source Serif', 'source-serif-4-latin-400-italic.woff2', '400', 'italic'), ff('Source Serif', 'source-serif-4-latin-600-normal.woff2', '600'), ff('Source Serif', 'source-serif-4-latin-700-normal.woff2', '700'),
  ff('Inter', 'inter-latin-500-normal.woff2', '500'), ff('Inter', 'inter-latin-700-normal.woff2', '700'), ff('Inter', 'inter-latin-800-normal.woff2', '800'),
  ff('Plex', 'ibm-plex-mono-latin-500-normal.woff2', '500'), ff('Plex', 'ibm-plex-mono-latin-600-normal.woff2', '600'),
]).then((fs) => { fs.forEach((f) => (document as any).fonts.add(f)); continueRender(fontHandle); });

// ---------- motion helpers ----------
export const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
export const ease = (f: number, at: number, d = 16) => interpolate(f, [at, at + d], [0, 1], {...clamp, easing: Easing.bezier(0.22, 1, 0.36, 1)});
export const lin = (f: number, a: number, b: number, from = 0, to = 1) => interpolate(f, [a, b], [from, to], clamp);
export const cu = (cues: number[], k: number, fallback = 99999) => (k < cues.length ? cues[k] : fallback);
export const usePop = (at: number, damping = 13) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  return spring({frame: f - at, fps, config: {damping, stiffness: 170, mass: 0.7}});
};
type Kid = {children?: React.ReactNode; style?: React.CSSProperties};
export const Fade: React.FC<Kid & {at: number; dy?: number; dx?: number; d?: number}> = ({at, dy = 26, dx = 0, d = 16, children, style}) => {
  const f = useCurrentFrame(); const p = ease(f, at, d);
  return <div style={{opacity: p, transform: `translate(${(1 - p) * dx}px, ${(1 - p) * dy}px)`, ...style}}>{children}</div>;
};
export const Pop: React.FC<Kid & {at: number; from?: number}> = ({at, from = 0.6, children, style}) => {
  const s = usePop(at); const f = useCurrentFrame();
  return <div style={{transform: `scale(${from + (1 - from) * s})`, opacity: lin(f, at, at + 5), ...style}}>{children}</div>;
};
export const Count: React.FC<{to: number; at: number; dur?: number; style?: React.CSSProperties; pre?: string; post?: string}> = ({to, at, dur = 36, style, pre = '', post = ''}) => {
  const f = useCurrentFrame();
  const v = Math.round(to * interpolate(f, [at, at + dur], [0, 1], {...clamp, easing: Easing.bezier(0.16, 1, 0.3, 1)}));
  return <span style={{fontVariantNumeric: 'tabular-nums', ...style}}>{pre}{v.toLocaleString('en-GB')}{post}</span>;
};
export const Typed: React.FC<{text: string; at: number; cps?: number; style?: React.CSSProperties}> = ({text, at, cps = 34, style}) => {
  const f = useCurrentFrame(); const n = Math.max(0, Math.floor(((f - at) / 30) * cps));
  return <span style={style}>{text.slice(0, n)}<span style={{opacity: n < text.length && n > 0 ? 1 : 0, color: C.gold}}>▍</span></span>;
};
// SVG stroke that draws itself. Put inside an <svg>.
export const Draw: React.FC<{d: string; at: number; dur?: number; color?: string; w?: number; dash?: string; opacity?: number; marker?: string}> = ({d, at, dur = 24, color = C.gold, w = 5, dash, opacity = 1, marker}) => {
  const f = useCurrentFrame(); const p = ease(f, at, dur);
  if (dash) return <path d={d} fill="none" stroke={color} strokeWidth={w} strokeDasharray={dash} strokeLinecap="round" opacity={opacity * p} markerEnd={marker} />;
  return <path d={d} fill="none" stroke={color} strokeWidth={w} strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - p} opacity={p > 0 ? opacity : 0} markerEnd={p > 0.97 ? marker : undefined} />;
};
export const Stamp: React.FC<{at: number; text: string; color?: string; rot?: number; size?: number; style?: React.CSSProperties}> = ({at, text, color = C.red, rot = -6, size = 54, style}) => {
  const f = useCurrentFrame(); const p = ease(f, at, 8);
  return <div style={{transform: `rotate(${rot}deg) scale(${interpolate(p, [0, 1], [2.2, 1])})`, opacity: p, border: `6px solid ${color}`, color, borderRadius: 10, padding: '8px 26px', fontFamily: DISPLAY, fontWeight: 900, fontSize: size, letterSpacing: 3, textTransform: 'uppercase', background: 'rgba(11,9,7,0.72)', whiteSpace: 'nowrap', display: 'inline-block', ...style}}>{text}</div>;
};
export const shake = (f: number, at: number, amp = 1.4) => { const d = f - at; if (d < 0 || d > 12) return 'none'; const a = (12 - d) * amp; return `translate(${Math.sin(d * 7) * a}px, ${Math.cos(d * 9) * a}px)`; };

// ---------- type ----------
export const H: React.FC<Kid & {size?: number; color?: string}> = ({children, size = 76, color = C.cream, style}) => <div style={{fontFamily: DISPLAY, fontWeight: 700, fontSize: size, color, letterSpacing: 2, lineHeight: 1.1, ...style}}>{children}</div>;
export const Body: React.FC<Kid & {size?: number; color?: string}> = ({children, size = 44, color = C.text2, style}) => <div style={{fontFamily: SERIF, fontWeight: 600, fontSize: size, color, lineHeight: 1.3, ...style}}>{children}</div>;
export const Label: React.FC<Kid & {size?: number; color?: string}> = ({children, size = 28, color = C.gold, style}) => <div style={{fontFamily: MONO, fontWeight: 600, fontSize: size, color, letterSpacing: 3, textTransform: 'uppercase', ...style}}>{children}</div>;
export const Center: React.FC<Kid> = ({children, style}) => <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', flexDirection: 'column', ...style}}>{children}</AbsoluteFill>;
export const Rule: React.FC<{at: number; w?: number; color?: string}> = ({at, w = 420, color = C.gold}) => { const f = useCurrentFrame(); return <div style={{height: 3, width: w * ease(f, at, 22), background: color, margin: '22px 0'}} />; };

// ---------- frame furniture ----------
export const Backdrop: React.FC = () => {
  const f = useCurrentFrame();
  return (<AbsoluteFill style={{background: `radial-gradient(ellipse at ${48 + Math.sin(f / 140) * 6}% ${40 + Math.cos(f / 170) * 5}%, #2A1F12 0%, #17110A 45%, ${C.bg} 82%)`}}>
    <AbsoluteFill style={{backgroundImage: 'linear-gradient(rgba(221,178,90,0.045) 1px, transparent 1px), linear-gradient(90deg, rgba(221,178,90,0.045) 1px, transparent 1px)', backgroundSize: '96px 96px'}} />
    <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,0.55) 100%)'}} />
  </AbsoluteFill>);
};
export const Grain: React.FC = () => { const f = useCurrentFrame();
  return <AbsoluteFill style={{backgroundImage: `url(${staticFile('grain.png')})`, backgroundPosition: `${(f * 37) % 256}px ${(f * 91) % 256}px`, opacity: 0.09, mixBlendMode: 'overlay', pointerEvents: 'none'}} />; };
export const Brand: React.FC<{chapter?: string}> = ({chapter}) => (<>
  <div style={{position: 'absolute', left: 60, top: 46, display: 'flex', alignItems: 'center', gap: 16}}>
    <div style={{width: 12, height: 12, background: C.gold, transform: 'rotate(45deg)'}} />
    <span style={{fontFamily: DISPLAY, fontWeight: 700, fontSize: 22, color: C.muted, letterSpacing: 6}}>ORIGINEX HUMAN ARCHIVES</span>
  </div>
  {chapter && <div style={{position: 'absolute', right: 60, top: 40, fontFamily: MONO, fontWeight: 600, fontSize: 22, color: C.gold, letterSpacing: 3, border: `1.5px solid ${C.goldDim}`, borderRadius: 6, padding: '8px 16px', background: 'rgba(11,9,7,0.6)'}}>{chapter}</div>}
</>);
export type Tag = 'PRIMARY ACCOUNT' | 'ONE WITNESS' | 'ONE SOURCE' | 'DISPUTED' | 'DIAGRAM' | 'CONTEXT' | 'ESTIMATE' | 'LATER IMAGE' | 'MUSEUM RECORD' | 'ACCORDING TO BAYOL';
const TAGC: Record<string, string> = {'PRIMARY ACCOUNT': C.gold, 'ONE WITNESS': C.amber, 'ONE SOURCE': C.amber, DISPUTED: C.red, DIAGRAM: C.teal, CONTEXT: C.muted, ESTIMATE: C.blue, 'LATER IMAGE': C.blue, 'MUSEUM RECORD': C.gold, 'ACCORDING TO BAYOL': C.amber};
export const Source: React.FC<{tag?: Tag; text?: string}> = ({tag = 'CONTEXT', text}) => (
  <div style={{position: 'absolute', left: 60, bottom: 34, display: 'flex', alignItems: 'center', gap: 16, maxWidth: 1800}}>
    <span style={{fontFamily: MONO, fontWeight: 600, fontSize: 20, color: C.ink, background: TAGC[tag], borderRadius: 5, padding: '4px 10px', letterSpacing: 1.5, whiteSpace: 'nowrap'}}>{tag}</span>
    {text && <span style={{fontFamily: MONO, fontWeight: 500, fontSize: 21, color: C.muted, whiteSpace: 'nowrap'}}>{text}</span>}
  </div>);
// word-level captions: chunks of up to 6 words, the spoken word in gold
export const Captions: React.FC<{words: [string, number][]; len: number}> = ({words, len}) => {
  const f = useCurrentFrame(); if (!words.length) return null;
  const chunks: [string, number][][] = []; let cur: [string, number][] = [];
  words.forEach((w, i) => { cur.push(w); if (cur.length >= 6 || /[.?!:]$/.test(w[0]) || i === words.length - 1) { chunks.push(cur); cur = []; } });
  let k = 0; for (let i = 0; i < chunks.length; i++) if (f >= chunks[i][0][1] - 2) k = i;
  if (f < chunks[0][0][1] - 4) return null;
  const ch = chunks[k]; const endAt = k + 1 < chunks.length ? chunks[k + 1][0][1] : len; if (f > endAt + 20) return null;
  return (<div style={{position: 'absolute', left: 0, right: 0, bottom: 86, display: 'flex', justifyContent: 'center'}}>
    <div style={{background: 'rgba(8,6,4,0.78)', borderRadius: 12, padding: '10px 26px', fontFamily: SANS, fontWeight: 700, fontSize: 40, letterSpacing: 0.2}}>
      {ch.map(([w, t], i) => <span key={i} style={{color: f >= t - 1 ? (i + 1 < ch.length && f >= ch[i + 1][1] - 1 ? C.cream : C.gold) : 'rgba(240,231,211,0.45)', marginRight: 12}}>{w}</span>)}
    </div></div>);
};
// scene wrapper: soft push-in, quick out
export const SceneShell: React.FC<{len: number; children: React.ReactNode; tag?: Tag; source?: string; chapter?: string; bare?: boolean}> = ({len, children, tag, source, chapter, bare}) => {
  const f = useCurrentFrame(); const pin = ease(f, 0, 12); const pout = lin(f, len - 7, len);
  return (<AbsoluteFill>
    <AbsoluteFill style={{opacity: pin * (1 - pout), transform: `scale(${0.975 + 0.025 * pin + 0.02 * pout})`}}>{children}</AbsoluteFill>
    {!bare && <Brand chapter={chapter} />}
    {(tag || source) && <div style={{opacity: pin * (1 - pout)}}><Source tag={tag} text={source} /></div>}
  </AbsoluteFill>);
};

// ---------- reusable picture pieces ----------
// simple soldier glyph (no face, no insignia): head, body, long gun
export const Figure: React.FC<{x: number; y: number; h?: number; color?: string; gun?: boolean; opacity?: number; lean?: number}> = ({x, y, h = 90, color = C.gold, gun = true, opacity = 1, lean = 0}) => (
  <g transform={`translate(${x} ${y}) rotate(${lean})`} opacity={opacity}>
    <circle cx={0} cy={-h * 0.86} r={h * 0.13} fill={color} />
    <path d={`M ${-h * 0.2} ${-h * 0.7} Q 0 ${-h * 0.8} ${h * 0.2} ${-h * 0.7} L ${h * 0.16} 0 L ${-h * 0.16} 0 Z`} fill={color} />
    {gun && <line x1={h * 0.1} y1={-h * 0.5} x2={h * 0.36} y2={-h * 1.18} stroke={color} strokeWidth={h * 0.045} strokeLinecap="round" />}
  </g>);
export const Rain: React.FC<{n?: number; opacity?: number}> = ({n = 90, opacity = 0.5}) => { const f = useCurrentFrame();
  return (<svg width={1920} height={1080} style={{position: 'absolute'}}>{Array.from({length: n}).map((_, i) => {
    const x0 = random('rx' + i) * 2200 - 100, sp = 34 + random('rs' + i) * 26, ln = 30 + random('rl' + i) * 50;
    const y = ((random('ry' + i) * 1300 + f * sp) % 1300) - 110; const x = x0 - y * 0.22;
    return <line key={i} x1={x} y1={y} x2={x - ln * 0.22} y2={y + ln} stroke="#9FB4C4" strokeWidth={2} opacity={opacity * (0.3 + random('ro' + i) * 0.7)} />; })}</svg>); };
export const Palisade: React.FC<{y?: number; h?: number; gaps?: number[]; gapP?: number; color?: string}> = ({y = 1080, h = 300, gaps = [], gapP = 0, color = '#0A0806'}) => (
  <svg width={1920} height={1080} style={{position: 'absolute'}}>{Array.from({length: 49}).map((_, i) => {
    const x = i * 40 - 10; const hh = h + random('ph' + i) * 40; const gi = gaps.indexOf(i); const g = gi >= 0 ? gapP : 0; const dir = gi % 2 ? 1 : -1;
    return <path key={i} transform={`rotate(${g * 24 * dir} ${x + 18} ${y})`} d={`M ${x} ${y} L ${x} ${y - hh + 26} L ${x + 18} ${y - hh} L ${x + 36} ${y - hh + 26} L ${x + 36} ${y} Z`} fill={color} stroke="#3A2E1F" strokeWidth={2} />; })}</svg>);

// West Africa map. k = geo units per screen pixel (2.1 = whole region, 0.2 = close on the Bight of Benin).
const G = GEO as unknown as {W: number; H: number; countries: {name: string; d: string}[]; pts: Record<string, [number, number]>};
export const PT = G.pts;
export const GeoMap: React.FC<{cx: number; cy: number; k: number; hi?: string[]; children?: React.ReactNode}> = ({cx, cy, k, hi = ['Benin'], children}) => (
  <svg width={1920} height={1080} viewBox={`${cx - 960 * k} ${cy - 540 * k} ${1920 * k} ${1080 * k}`} style={{position: 'absolute', background: C.sea}}>
    {G.countries.map((c) => <path key={c.name} d={c.d} fill={hi.includes(c.name) ? '#4A3A1C' : C.land} stroke={hi.includes(c.name) ? C.gold : C.landLine} strokeWidth={hi.includes(c.name) ? 2.2 : 1.2} vectorEffect="non-scaling-stroke" />)}
    {children}
  </svg>);
// label that keeps its on-screen size at any zoom: pass k
export const Pin: React.FC<{p: [number, number]; k: number; text: string; at: number; color?: string; dx?: number; dy?: number; size?: number; sub?: string; pulse?: boolean}> = ({p, k, text, at, color = C.cream, dx = 16, dy = 8, size = 30, sub, pulse}) => {
  const f = useCurrentFrame(); const a = ease(f, at, 14); const r = pulse ? 8 + ((f - at) % 45) * 0.7 : 0;
  return (<g opacity={a}>
    {pulse && f > at && <circle cx={p[0]} cy={p[1]} r={r * k} fill="none" stroke={color} strokeWidth={2 * k} opacity={1 - ((f - at) % 45) / 45} />}
    <circle cx={p[0]} cy={p[1]} r={7 * k} fill={color} stroke={C.bg} strokeWidth={2 * k} />
    <text x={p[0] + dx * k} y={p[1] + dy * k} fontFamily="Cinzel, serif" fontWeight={700} fontSize={size * k} fill={color} stroke={C.bg} strokeWidth={5 * k} paintOrder="stroke" letterSpacing={2 * k}>{text}</text>
    {sub && <text x={p[0] + dx * k} y={p[1] + (dy + size * 0.95) * k} fontFamily="Plex, monospace" fontWeight={500} fontSize={size * 0.62 * k} fill={C.text2} stroke={C.bg} strokeWidth={4 * k} paintOrder="stroke">{sub}</text>}
  </g>);
};
