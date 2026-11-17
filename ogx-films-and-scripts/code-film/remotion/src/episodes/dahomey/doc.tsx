// Dahomey / Cotonou 1890: documentary scenes. Full-frame pictures moved by code (push, pull, pan, tilt, cross-dissolve),
// with weather and smoke drawn over them, lower thirds, counters, quotes, stamps and framed archive prints.
// Pictures live in public/dahomey/: sNN.jpg = painted reconstructions made for the v1.1 film, a_*.jpg = real period images.
import React from 'react';
import {AbsoluteFill, Img, staticFile, useCurrentFrame, interpolate, Easing, random} from 'remotion';
import {C, DISPLAY, SERIF, MONO, clamp, Rain, Stamp} from '../../kit';

type Move = 'in' | 'out' | 'left' | 'right' | 'up' | 'down' | 'tiltdown';
type Fx = 'rain' | 'smoke' | 'lamp' | 'dust';
type T = {cue?: number; at?: number; until?: number; untilAt?: number};
export type Shot = T & {img: string; move?: Move; fx?: Fx; credit?: string; tall?: number /* tiltdown: picture height in px at 1920 wide */; frame?: number /* show as a framed print this many px tall, on a blurred copy of itself */};
export type Ov = T & (
  | {k: 'lower'; text: string}
  | {k: 'big'; value: number | string; pre?: string; label: string; x?: number; y?: number; color?: string}
  | {k: 'quote'; text: string; by?: string}
  | {k: 'head'; kicker?: string; text: string; sub?: string}
  | {k: 'title'; text: string; sub?: string}
  | {k: 'stamp'; text: string; x: number; y: number; rot?: number; color?: string; size?: number}
  | {k: 'inset'; img: string; cap: string; side?: 'left' | 'right'; w?: number}
  | {k: 'chip'; text: string});
export type Doc = {shots: Shot[]; ov?: Ov[]; note?: string};

const XF = 20; // cross-dissolve between pictures, frames
const eo = (f: number, a: number, d = 16) => interpolate(f, [a, a + d], [0, 1], {...clamp, easing: Easing.bezier(0.22, 1, 0.36, 1)});

const Picture: React.FC<{s: Shot; start: number; end: number}> = ({s, start, end}) => {
  const f = useCurrentFrame(); if (f < start - 1 || f > end + XF) return null;
  const p = interpolate(f, [start, end + XF], [0, 1], clamp); const op = start === 0 ? 1 : interpolate(f, [start, start + XF], [0, 1], clamp);
  const m = s.move ?? 'in'; const arch = s.img.startsWith('a_');
  const sc = m === 'in' ? 1.04 + 0.1 * p : m === 'out' ? 1.14 - 0.1 * p : m === 'tiltdown' ? 1.02 : 1.1;
  const tx = m === 'left' ? 2.4 - 4.8 * p : m === 'right' ? -2.4 + 4.8 * p : 0; const ty = m === 'up' ? 2 - 4 * p : m === 'down' ? -2 + 4 * p : 0;
  const src = staticFile('dahomey/' + s.img);
  if (s.frame) return (<AbsoluteFill style={{opacity: op, background: '#0B0907'}}>
    <Img src={src} style={{width: '100%', height: '100%', objectFit: 'cover', transform: 'scale(1.25)', filter: 'blur(34px) brightness(0.36) saturate(0.7)'}} />
    <AbsoluteFill style={{justifyContent: 'center', paddingLeft: 230, paddingBottom: 210}}>
      <div style={{alignSelf: 'flex-start', background: '#EDE3CB', padding: 16, boxShadow: '0 30px 90px rgba(0,0,0,0.8)', transform: `scale(${0.93 + 0.06 * p}) rotate(-0.7deg)`, transformOrigin: 'left center'}}>
        <Img src={src} style={{height: s.frame, display: 'block', filter: 'contrast(1.03)'}} /></div>
    </AbsoluteFill></AbsoluteFill>);
  if (m === 'tiltdown') return (<AbsoluteFill style={{opacity: op, background: '#0B0907', overflow: 'hidden'}}>
    <Img src={src} style={{position: 'absolute', left: 0, top: 0, width: 1920, transform: `translateY(${-((s.tall ?? 2740) - 1080) * (0.04 + 0.88 * p)}px)`, filter: 'sepia(0.25) contrast(1.05) brightness(0.92)'}} />
  </AbsoluteFill>);
  return (<AbsoluteFill style={{opacity: op, background: '#0B0907'}}>
    <Img src={src} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: '50% 50%',
      transform: `scale(${sc}) translate(${tx}%, ${ty}%)`, filter: arch ? 'sepia(0.25) contrast(1.05) brightness(0.92)' : 'saturate(0.94) contrast(1.05)'}} />
  </AbsoluteFill>);
};

const Smoke: React.FC = () => { const f = useCurrentFrame();
  return (<AbsoluteFill style={{mixBlendMode: 'screen', opacity: 0.55}}>{[0, 1, 2, 3, 4, 5].map((i) => {
    const w = 900 + random('sw' + i) * 700, y = 120 + random('sy' + i) * 520, sp = 0.5 + random('ss' + i) * 0.7;
    const x = ((random('sx' + i) * 2600 + f * sp) % 3000) - 900;
    return <div key={i} style={{position: 'absolute', left: x, top: y, width: w, height: w * 0.45, borderRadius: '50%', background: 'radial-gradient(closest-side, rgba(235,228,214,0.26), rgba(235,228,214,0))', filter: 'blur(30px)'}} />; })}</AbsoluteFill>); };
const Lamp: React.FC = () => { const f = useCurrentFrame(); const o = 0.1 + 0.05 * Math.sin(f / 7) + 0.03 * Math.sin(f / 2.9 + 1);
  return <AbsoluteFill style={{background: 'radial-gradient(60% 70% at 30% 40%, rgba(255,190,110,0.55), rgba(255,190,110,0) 70%)', opacity: o, mixBlendMode: 'screen'}} />; };
const Dust: React.FC = () => { const f = useCurrentFrame();
  return (<svg width={1920} height={1080} style={{position: 'absolute'}}>{Array.from({length: 46}).map((_, i) => {
    const x = (random('dx' + i) * 1920 + f * (0.25 + random('dv' + i) * 0.5)) % 1920, y = (random('dy' + i) * 1080 - f * (0.1 + random('du' + i) * 0.3) + 2160) % 1080;
    return <circle key={i} cx={x} cy={y} r={1.2 + random('dr' + i) * 2} fill="#F3DCA8" opacity={0.1 + 0.25 * Math.abs(Math.sin(f / 30 + i))} />; })}</svg>); };

const Lower: React.FC<{text: string; a: number; z: number}> = ({text, a, z}) => { const f = useCurrentFrame(); if (f < a || f > z) return null;
  const p = eo(f, a, 14) * (1 - interpolate(f, [z - 8, z], [0, 1], clamp));
  return (<div style={{position: 'absolute', left: 60, bottom: 178, opacity: p, transform: `translateX(${(1 - p) * -30}px)`, display: 'flex', alignItems: 'stretch'}}>
    <div style={{width: 7, background: C.gold}} />
    <div style={{background: 'rgba(8,6,4,0.74)', padding: '10px 26px 8px 20px', fontFamily: DISPLAY, fontWeight: 700, fontSize: 40, letterSpacing: 4, color: C.cream, textShadow: '0 2px 10px rgba(0,0,0,0.8)'}}>{text}</div>
  </div>); };
const Big: React.FC<{o: Extract<Ov, {k: 'big'}>; a: number; z: number}> = ({o, a, z}) => { const f = useCurrentFrame(); if (f < a || f > z) return null;
  const p = eo(f, a, 14) * (1 - interpolate(f, [z - 8, z], [0, 1], clamp));
  const val = typeof o.value === 'number' ? Math.round(o.value * interpolate(f, [a, a + 34], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)})).toLocaleString('en-GB') : o.value;
  return (<div style={{position: 'absolute', left: o.x ?? 110, top: o.y ?? 210, opacity: p, transform: `translateY(${(1 - p) * 24}px)`, textShadow: '0 4px 28px rgba(0,0,0,0.9), 0 0 4px rgba(0,0,0,0.9)'}}>
    <div style={{fontFamily: DISPLAY, fontWeight: 900, fontSize: 200, lineHeight: 1, color: o.color ?? C.gold}}>{o.pre}{val}</div>
    <div style={{fontFamily: DISPLAY, fontWeight: 700, fontSize: 44, letterSpacing: 5, color: C.cream, marginTop: 6}}>{o.label}</div>
  </div>); };
const Scrim: React.FC<{p: number; s?: number}> = ({p, s = 0.5}) => <AbsoluteFill style={{background: `rgba(6,4,3,${s * p})`}} />;
const Quote: React.FC<{o: Extract<Ov, {k: 'quote'}>; a: number; z: number}> = ({o, a, z}) => { const f = useCurrentFrame(); if (f < a || f > z) return null;
  const p = eo(f, a, 18) * (1 - interpolate(f, [z - 10, z], [0, 1], clamp));
  return (<><Scrim p={p} /><AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', opacity: p, paddingBottom: 90}}>
    <div style={{maxWidth: 1450, textAlign: 'center', fontFamily: SERIF, fontStyle: 'italic', fontWeight: 600, fontSize: 74, lineHeight: 1.22, color: C.cream, textShadow: '0 3px 22px rgba(0,0,0,0.9)'}}>“{o.text}”</div>
    {o.by && <div style={{marginTop: 30, fontFamily: MONO, fontWeight: 600, fontSize: 28, letterSpacing: 4, color: C.gold}}>{o.by}</div>}
  </AbsoluteFill></>); };
const Head: React.FC<{o: Extract<Ov, {k: 'head'}>; a: number; z: number}> = ({o, a, z}) => { const f = useCurrentFrame(); if (f < a || f > z) return null;
  const p = eo(f, a, 18) * (1 - interpolate(f, [z - 10, z], [0, 1], clamp));
  return (<><Scrim p={p} s={0.56} /><AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', opacity: p, paddingBottom: 80, textShadow: '0 3px 22px rgba(0,0,0,0.9)'}}>
    {o.kicker && <div style={{fontFamily: MONO, fontWeight: 600, fontSize: 28, letterSpacing: 6, color: C.gold, marginBottom: 26}}>{o.kicker}</div>}
    <div style={{maxWidth: 1500, textAlign: 'center', fontFamily: SERIF, fontWeight: 700, fontSize: 88, lineHeight: 1.15, color: C.cream}}>{o.text}</div>
    {o.sub && <div style={{marginTop: 14, maxWidth: 1500, textAlign: 'center', fontFamily: SERIF, fontWeight: 700, fontSize: 80, lineHeight: 1.15, color: C.gold, opacity: eo(f, a + 16, 18)}}>{o.sub}</div>}
    <div style={{height: 4, width: 420 * eo(f, a + 10, 26), background: C.gold, marginTop: 28}} />
  </AbsoluteFill></>); };
const Title: React.FC<{o: Extract<Ov, {k: 'title'}>; a: number; z: number}> = ({o, a, z}) => { const f = useCurrentFrame(); if (f < a || f > z) return null;
  const p = eo(f, a, 24) * (1 - interpolate(f, [z - 10, z], [0, 1], clamp));
  return (<><Scrim p={p} s={0.62} /><AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', opacity: p, textShadow: '0 4px 30px rgba(0,0,0,0.95)'}}>
    <div style={{fontFamily: DISPLAY, fontWeight: 700, fontSize: 26, letterSpacing: 10, color: C.muted, marginBottom: 34}}>ORIGINEX HUMAN ARCHIVES</div>
    <div style={{fontFamily: DISPLAY, fontWeight: 900, fontSize: 132, lineHeight: 1.08, letterSpacing: 4, color: C.gold, textAlign: 'center', maxWidth: 1500, transform: `scale(${0.96 + 0.04 * p})`}}>{o.text}</div>
    <div style={{height: 3, width: 560 * eo(f, a + 14, 30), background: C.gold, margin: '34px 0 26px'}} />
    {o.sub && <div style={{fontFamily: SERIF, fontWeight: 600, fontSize: 48, color: C.cream, opacity: eo(f, a + 24, 20)}}>{o.sub}</div>}
  </AbsoluteFill></>); };
const Inset: React.FC<{o: Extract<Ov, {k: 'inset'}>; a: number; z: number}> = ({o, a, z}) => { const f = useCurrentFrame(); if (f < a || f > z) return null;
  const p = eo(f, a, 18) * (1 - interpolate(f, [z - 10, z], [0, 1], clamp)); const right = (o.side ?? 'right') === 'right'; const w = o.w ?? 600;
  return (<div style={{position: 'absolute', top: 150, ...(right ? {right: 110} : {left: 110}), width: w, opacity: p, transform: `translateY(${(1 - p) * 30}px) rotate(${right ? 1.2 : -1.2}deg) scale(${0.96 + 0.04 * p + 0.012 * interpolate(f, [a, z], [0, 1], clamp)})`}}>
    <div style={{background: '#EDE3CB', padding: 14, boxShadow: '0 24px 70px rgba(0,0,0,0.75)'}}>
      <Img src={staticFile('dahomey/' + o.img)} style={{width: '100%', display: 'block', filter: 'sepia(0.2) contrast(1.04)'}} /></div>
    <div style={{marginTop: 12, background: 'rgba(8,6,4,0.8)', padding: '8px 14px', fontFamily: MONO, fontWeight: 600, fontSize: 21, letterSpacing: 1.5, color: C.cream, lineHeight: 1.35}}>
      <span style={{color: C.gold}}>ARCHIVE · </span>{o.cap}</div>
  </div>); };
const Chip: React.FC<{text: string; a: number; z: number}> = ({text, a, z}) => { const f = useCurrentFrame(); if (f < a || f > z) return null;
  const p = eo(f, a, 14) * (1 - interpolate(f, [z - 8, z], [0, 1], clamp));
  return <div style={{position: 'absolute', left: 60, top: 104, opacity: p, fontFamily: MONO, fontWeight: 600, fontSize: 26, letterSpacing: 3, color: C.ink, background: C.amber, borderRadius: 6, padding: '8px 16px'}}>{text}</div>; };

export const DocScene: React.FC<{doc: Doc; cues: number[]; len: number}> = ({doc, cues, len}) => {
  const f = useCurrentFrame();
  const at = (o: T) => o.at ?? (o.cue !== undefined ? (cues[o.cue] ?? len) : 0);
  const until = (o: T) => Math.min(len, o.untilAt ?? (o.until !== undefined ? (cues[o.until] ?? len) : len));
  const starts = doc.shots.map(at); const cur = starts.reduce((k, s, i) => (f >= s ? i : k), 0); const shot = doc.shots[cur];
  const ov = doc.ov ?? []; const lowers = ov.filter((o) => o.k === 'lower');
  const ovOut = 1 - interpolate(f, [len - 8, len], [0, 1], clamp); const arch = shot.img.startsWith('a_');
  return (<AbsoluteFill>
    {doc.shots.map((s, i) => <Picture key={i} s={s} start={starts[i]} end={i + 1 < starts.length ? starts[i + 1] : len} />)}
    {shot.fx === 'rain' && <Rain n={120} opacity={0.38} />}{shot.fx === 'smoke' && <Smoke />}{shot.fx === 'lamp' && <Lamp />}{!shot.fx && !arch && <Dust />}
    <AbsoluteFill style={{background: 'radial-gradient(120% 90% at 50% 45%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.5) 100%)'}} />
    <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(6,4,3,0.62) 0%, rgba(6,4,3,0) 17%, rgba(6,4,3,0) 60%, rgba(6,4,3,0.82) 100%)'}} />
    <AbsoluteFill style={{opacity: ovOut}}>
      {ov.map((o, i) => { const a = at(o); let z = until(o);
        if (o.k === 'lower') { const nx = lowers.map(at).filter((x) => x > a).sort((p, q) => p - q)[0]; if (nx !== undefined) z = Math.min(z, nx); return <Lower key={i} text={o.text} a={a} z={z} />; }
        if (o.k === 'big') return <Big key={i} o={o} a={a} z={z} />;
        if (o.k === 'quote') return <Quote key={i} o={o} a={a} z={z} />;
        if (o.k === 'head') return <Head key={i} o={o} a={a} z={z} />;
        if (o.k === 'title') return <Title key={i} o={o} a={a} z={z} />;
        if (o.k === 'inset') return <Inset key={i} o={o} a={a} z={z} />;
        if (o.k === 'chip') return <Chip key={i} text={o.text} a={a} z={z} />;
        if (o.k === 'stamp') return f <= z ? <Stamp key={i} at={a} text={o.text} color={o.color} rot={o.rot ?? -5} size={o.size ?? 64} style={{position: 'absolute', right: 100, top: o.y, transformOrigin: 'right center', textShadow: '0 2px 14px rgba(0,0,0,0.85)', background: 'rgba(8,6,4,0.55)'}} /> : null;
        return null; })}
      <div style={{position: 'absolute', right: 60, top: 98, fontFamily: MONO, fontWeight: 600, fontSize: 19, letterSpacing: 1.5, color: 'rgba(240,231,211,0.72)', background: 'rgba(8,6,4,0.55)', padding: '4px 10px', borderRadius: 5}}>
        {arch ? `ARCHIVE · ${shot.credit ?? 'period image'}` : (doc.note ?? 'RECONSTRUCTION · painted for this film, not a period image')}</div>
    </AbsoluteFill>
  </AbsoluteFill>);
};

export const Bg: React.FC<{img: string; len: number; dark?: number}> = ({img, len, dark = 0.72}) => (<AbsoluteFill>
  <Picture s={{img, move: 'in'}} start={0} end={len} /><AbsoluteFill style={{background: `rgba(6,4,3,${dark})`}} /></AbsoluteFill>);

const BAYOL = 'ACCORDING TO GOVERNOR BAYOL';
export const DOC: Record<string, Doc> = {
  S01: {shots: [{img: 's61.jpg', move: 'in'}], ov: [{k: 'lower', text: 'COTONOU · THE NIGHT OF 3 MARCH 1890', at: 18}]},
  S02: {shots: [{img: 's02.jpg', move: 'in', fx: 'rain'}], ov: [{k: 'lower', text: 'STORM ON THE COAST · FROM 7 PM', at: 14, until: 0}, {k: 'big', value: 359, label: 'DEFENDERS', cue: 0, x: 110, y: 230}]},
  S03: {shots: [{img: 's03.jpg', move: 'right', fx: 'rain'}, {img: 's04.jpg', move: 'in', fx: 'rain', cue: 2}], ov: [{k: 'lower', text: 'SENEGALESE TIRAILLEURS · GABONESE', cue: 0}, {k: 'lower', text: 'A FEW EUROPEAN OFFICERS AND GUNNERS', cue: 2}]},
  S04: {shots: [{img: 's05.jpg', move: 'left', fx: 'rain'}], ov: [{k: 'lower', text: 'WATCH IN THIRDS · THROUGH THE NIGHT', cue: 0}]},
  S05: {shots: [{img: 's06.jpg', move: 'in'}, {img: 's07.jpg', move: 'right', cue: 1}], ov: [{k: 'lower', text: 'JUST BEFORE 5 AM · THE NORTH BASTION', at: 12}, {k: 'lower', text: 'LT COMPÉRAT', cue: 0}, {k: 'lower', text: 'SOMETHING MOVING IN THE BRUSH', cue: 1}]},
  S06: {shots: [{img: 's07.jpg', move: 'in'}, {img: 's08.jpg', move: 'out', cue: 1}], ov: [{k: 'lower', text: 'BELLS', at: 8}, {k: 'lower', text: 'TEN PACES FROM THE WALL', cue: 0}]},
  S07: {shots: [{img: 's01.jpg', move: 'in'}], ov: [{k: 'chip', text: BAYOL, at: 24, until: 1}, {k: 'lower', text: 'THE WOMEN SOLDIERS OF DAHOMEY', cue: 0, until: 1}, {k: 'head', kicker: 'THE QUESTION', text: 'What can we actually prove?', cue: 1}]},
  S08: {shots: [{img: 's45.jpg', move: 'in'}], ov: [{k: 'title', text: 'THE GHOST ARMY OF DAHOMEY', sub: 'The women who fought France · 1890', at: 6}]},
  S09: {shots: [{img: 's47.jpg', move: 'in'}, {img: 's09.jpg', move: 'left', cue: 1}], ov: [{k: 'quote', text: 'Make way for me, or I fall on you.', by: 'THE MEANING OF THEIR NAME · TRANSLATION APPROXIMATE', cue: 0, until: 1}, {k: 'lower', text: 'A STANDING CORPS', cue: 1}, {k: 'lower', text: 'PROBABLY THE 1720s · A PALACE GUARD', cue: 2}]},
  S10: {shots: [{img: 's10.jpg', move: 'out'}], ov: [{k: 'big', value: 1500, pre: 'c. ', label: 'WOMEN SOLDIERS · LATE 1870s', cue: 0}]},
  S11: {shots: [{img: 's11.jpg', move: 'right'}, {img: 's66.jpg', move: 'in', cue: 2}], ov: [{k: 'lower', text: 'THORN HEDGES', cue: 0}, {k: 'lower', text: 'WRESTLING', cue: 1}, {k: 'lower', text: 'SURVIVAL EXERCISES · LASTING DAYS', cue: 2}]},
  S12: {shots: [{img: 's12.jpg', move: 'in'}, {img: 's13.jpg', move: 'left', cue: 2}], ov: [{k: 'lower', text: 'MUSKETS · BLADES · AMULETS', at: 10}, {k: 'inset', img: 'a_amazone1895.jpg', cap: 'drawing, 1895 (d’Albéca, La France au Dahomey). Five years after Cotonou.', at: 26, until: 2, w: 290}, {k: 'lower', text: 'THE COLONEL · SILVER HORNS IN HER HAIR', cue: 2}]},
  S13: {shots: [{img: 's14.jpg', move: 'right'}], ov: [{k: 'chip', text: BAYOL, at: 10}, {k: 'inset', img: 'a_bayol.jpg', cap: 'Governor Jean Bayol. Press engraving, 1890.', at: 20, until: 1, w: 280}, {k: 'lower', text: 'THE WOMEN LED THE COLUMN', cue: 0}, {k: 'lower', text: 'THEN THE FETISH PRIESTS', cue: 1}, {k: 'lower', text: 'THE ROYAL GUARDS', cue: 2}, {k: 'lower', text: 'THEN THE REGULAR TROOPS', cue: 3}]},
  S17: {shots: [{img: 's28.jpg', move: 'out'}], ov: [{k: 'lower', text: 'SEVERAL THOUSAND ATTACKERS', at: 8}, {k: 'stamp', text: 'NO RELIABLE COUNT', cue: 0, x: 1130, y: 300}]},
  S18: {shots: [{img: 's44.jpg', move: 'in', fx: 'lamp'}, {img: 's29.jpg', move: 'left', cue: 1}], ov: [{k: 'lower', text: 'ONE EYEWITNESS DISAGREES', at: 8}, {k: 'lower', text: 'ÉDOUARD FOÀ · TRADER · HE WAS THERE', cue: 0}, {k: 'lower', text: '“NOT ENGAGED THAT DAY”', cue: 1}, {k: 'lower', text: 'A FEW TOOK PART OF THEIR OWN ACCORD', cue: 2}, {k: 'lower', text: 'THE REST WATCHED FROM A SHORT DISTANCE', cue: 3}]},
  S19: {shots: [{img: 's34.jpg', move: 'in', fx: 'lamp'}], ov: [{k: 'lower', text: 'BAYOL AND NICOLAS · AGAINST FOÀ', at: 8}, {k: 'stamp', text: 'THE ACCOUNTS DISAGREE', cue: 0, x: 1010, y: 250}]},
  S20: {shots: [{img: 's15.jpg', move: 'in', fx: 'smoke'}, {img: 's16.jpg', move: 'right', fx: 'smoke', cue: 1}], ov: [{k: 'lower', text: 'AT THE PALISADE', at: 10}, {k: 'lower', text: 'THEY FIRED THROUGH THE GAPS', cue: 0}, {k: 'lower', text: 'SOME GOT ONTO THE STOCKADE · THE LINE HELD', cue: 1}]},
  S21: {shots: [{img: 's17.jpg', move: 'in', fx: 'smoke'}, {img: 's30.jpg', move: 'left', cue: 1}], ov: [{k: 'lower', text: 'LT COMPÉRAT · HIT THREE TIMES', at: 12}, {k: 'lower', text: 'A BROKEN SHOULDER BLADE', cue: 0}, {k: 'lower', text: 'HE STAYED IN COMMAND', cue: 1, until: 2}, {k: 'quote', text: 'Stay at your post. I am wounded too, and I am not complaining.', by: 'COMPÉRAT TO HIS SERGEANT · QUOTED IN A FRENCH ACCOUNT', cue: 2}]},
  S22: {shots: [{img: 's32.jpg', move: 'in', fx: 'smoke'}, {img: 's18.jpg', move: 'in', fx: 'smoke', cue: 0}], ov: [{k: 'lower', text: 'THE AGOR POST · BRIEFLY ABANDONED', at: 10}, {k: 'lower', text: 'LEMOYNE’S 2ND COMPANY', cue: 0}, {k: 'lower', text: 'A BAYONET CHARGE', cue: 1}]},
  S23: {shots: [{img: 's19.jpg', move: 'right', fx: 'smoke'}], ov: [{k: 'lower', text: 'SOME LAY FLAT AND LET THE CHARGE PASS', at: 10}, {k: 'lower', text: 'THEN ROSE AND FIRED', cue: 0}, {k: 'lower', text: 'ONE SECTION TURNED ABOUT', cue: 1}]},
  S24: {shots: [{img: 's21.jpg', move: 'in'}], ov: [{k: 'lower', text: 'THE CRUISER SANÉ · SHELLING THE WOODS', at: 10}]},
  S25: {shots: [{img: 's22.jpg', move: 'in'}, {img: 's20.jpg', move: 'left', fx: 'smoke', cue: 1}], ov: [{k: 'lower', text: 'FIRST LIGHT · THE 4TH COMPANY', at: 10}, {k: 'lower', text: 'HAND TO HAND', cue: 0}, {k: 'lower', text: 'OUDARD · OBLIQUE FIRE FROM THE CENTRE', cue: 1}, {k: 'lower', text: 'PANSIER · THE ROUT ON THE RIGHT', cue: 2}]},
  S26: {shots: [{img: 's23.jpg', move: 'in'}, {img: 's24.jpg', move: 'right', fx: 'smoke', cue: 1}, {img: 's31.jpg', move: 'out', cue: 2}], ov: [{k: 'lower', text: '6:15 AM · A SECOND ATTACK', at: 10}, {k: 'lower', text: 'STOPPED AT 200 METRES', cue: 0}, {k: 'lower', text: 'THE SANÉ AND A THREE-GUN BATTERY', cue: 1}, {k: 'lower', text: '9:30 AM · THE LAST ATTACKERS LEAVE', cue: 2}, {k: 'big', value: '4½', label: 'HOURS · APPROXIMATELY', cue: 3, x: 110, y: 230}]},
  S27: {shots: [{img: 's25.jpg', move: 'in', fx: 'smoke'}, {img: 's33.jpg', move: 'left', cue: 1}, {img: 's38.jpg', move: 'in', fx: 'lamp', cue: 3}], ov: [
    {k: 'big', value: 8, label: 'FRENCH SOLDIERS KILLED', at: 12, until: 1, x: 110, y: 150, color: C.blue}, {k: 'big', value: 26, label: 'WOUNDED', cue: 0, until: 1, x: 110, y: 480, color: C.blue},
    {k: 'big', value: 127, label: 'DAHOMEAN DEAD · COUNTED INSIDE THE LINES', cue: 1, until: 3, x: 110, y: 200}, {k: 'lower', text: 'SEVEN OF THEM WERE WOMEN', cue: 2, until: 3},
    {k: 'lower', text: 'ANOTHER COUNT EXISTS · THE PRIMARY ACCOUNT SAYS 127', cue: 3}]},
  S28: {shots: [{img: 'a_bayolmap1889.jpg', move: 'tiltdown', tall: 2740, credit: 'Bayol’s route, Kotonou to Abomey, Nov–Dec 1889. Service géographique des colonies.'}, {img: 's35.jpg', move: 'in', cue: 1}], ov: [{k: 'chip', text: BAYOL, at: 10}, {k: 'inset', img: 'a_bayol.jpg', cap: 'Governor Jean Bayol. Press engraving, 1890.', at: 16, until: 1, w: 270}, {k: 'lower', text: 'ABOMEY · DECEMBER 1889', at: 20}, {k: 'lower', text: 'THEN COTONOU', cue: 0, until: 1}, {k: 'quote', text: 'Nanisca', by: 'THE NAME IS BAYOL’S', cue: 1}]},
  S29: {shots: [{img: 's36.jpg', move: 'in', fx: 'smoke'}, {img: 's32.jpg', move: 'left', cue: 0}], ov: [{k: 'chip', text: BAYOL, at: 10}, {k: 'lower', text: 'THE CHIEF GUNNER', at: 16}, {k: 'lower', text: 'HE LATER FOUND HER BODY', cue: 0}, {k: 'lower', text: 'A CLEAVER · A CARBINE COVERED IN COWRIES', cue: 1}]},
  S30: {shots: [{img: 's64.jpg', move: 'in', fx: 'lamp'}], ov: [{k: 'lower', text: 'A SECOND FRENCH ACCOUNT', at: 10}, {k: 'lower', text: 'IT DOES NOT NAME HER', cue: 0}, {k: 'stamp', text: 'BAYOL ALONE', cue: 1, x: 1180, y: 270, color: C.amber}]},
  S32: {shots: [{img: 's37.jpg', move: 'in'}, {img: 's26.jpg', move: 'out', cue: 2}], ov: [{k: 'lower', text: 'FOÀ WAS PRESENT', at: 10}, {k: 'lower', text: 'TWO OR THREE WOMEN FOUND ALIVE', cue: 0}, {k: 'lower', text: 'ONE VERY YOUNG · GRAVELY WOUNDED', cue: 1}, {k: 'lower', text: 'NONE SURVIVED', cue: 2}]},
  S33: {shots: [{img: 's42.jpg', move: 'in'}], ov: [{k: 'head', kicker: 'BEFORE THE BATTLE', text: 'Who were these women?', sub: 'What had prepared them?', at: 6}]},
  S34: {shots: [{img: 's09.jpg', move: 'in'}, {img: 's48.jpg', move: 'right', cue: 0}, {img: 's39.jpg', move: 'out', cue: 1}, {img: 's65.jpg', move: 'in', cue: 2}], ov: [
    {k: 'lower', text: 'PROBABLY THE 1720s · A PALACE GUARD', at: 12, until: 0}, {k: 'inset', img: 'a_dalzel1793.jpg', cap: 'engraving, 1793: “Armed women, with the King at their head, going to war” (Dalzel).', at: 40, until: 0, w: 560},
    {k: 'big', value: 600, pre: 'c. ', label: '1760s TO 1840s', cue: 0, until: 1}, {k: 'big', value: 6000, label: 'AS MANY AS · UNDER KING GEZO', cue: 1, until: 2}, {k: 'big', value: 1500, pre: 'c. ', label: 'BY THE LATE 1870s', cue: 2}]},
  S35: {shots: [{img: 's11.jpg', move: 'left'}, {img: 's27.jpg', move: 'in', cue: 0}, {img: 's10.jpg', move: 'right', cue: 1}], ov: [{k: 'lower', text: 'SURVIVAL EXERCISES · UP TO NINE DAYS', at: 100, until: 0},
    {k: 'head', text: 'Not a legend.', sub: 'Not invented by a newspaper or a film.', cue: 0, until: 1}, {k: 'inset', img: 'a_frey1890.jpg', cap: 'engraving, 1890, after a photograph: “Les amazones guerrières du Dahomey”.', cue: 1, w: 640},
    {k: 'lower', text: 'A REAL INSTITUTION', cue: 1}, {k: 'lower', text: 'A CHAIN OF COMMAND', cue: 2}, {k: 'lower', text: 'A HISTORY LONGER THAN MOST EUROPEAN ARMIES', cue: 3}]},
  S36: {shots: [{img: 's49.jpg', move: 'in', fx: 'lamp'}], ov: [{k: 'head', kicker: 'THE PICTURES', text: 'The images we often see', sub: 'are not the battle.', at: 6}]},
  S37: {shots: [{img: 'a_forbes1851.jpg', frame: 640, credit: 'F. E. Forbes, Dahomey and the Dahomans (1851). Cropped. Wikimedia Commons, public domain.'}], ov: [{k: 'lower', text: 'FORBES · 1851 · SEH-DONG-HONG-BEH', at: 12}, {k: 'lower', text: 'THE FULL PLATE SHOWS A SEVERED HEAD · CROPPED HERE', cue: 0}, {k: 'stamp', text: 'NOT A PHOTOGRAPH', cue: 1, x: 0, y: 290}, {k: 'stamp', text: 'NOT 1890', cue: 2, x: 0, y: 450, rot: 4}]},
  S38: {shots: [{img: 'a_fortier.jpg', frame: 590, credit: 'Postcard by F.-E. Fortier, early 1900s. Wikimedia Commons, public domain.'}], ov: [{k: 'lower', text: 'FORTIER POSTCARD · EARLY 1900s', at: 12}, {k: 'lower', text: 'CAPTIONED AS SURVIVORS · INDIVIDUAL SERVICE NOT VERIFIED', at: 105}, {k: 'stamp', text: 'NOT THE BATTLE EITHER', cue: 0, x: 0, y: 250, size: 54}]},
  S39: {shots: [{img: 's49.jpg', move: 'left', fx: 'lamp'}, {img: 's50.jpg', move: 'in', fx: 'lamp', cue: 1}], ov: [{k: 'lower', text: 'THE FRENCH PRESS · MARCH 1890', at: 10}, {k: 'lower', text: 'SEVERED HEADS · NOT SHOWN HERE', cue: 0}, {k: 'lower', text: 'LE PETIT PARISIEN · HORNED HELMETS', cue: 1}, {k: 'stamp', text: 'CERTAINLY FICTITIOUS', cue: 2, x: 1080, y: 280}], note: 'ILLUSTRATION · painted for this film, not the original pages'},
  S40: {shots: [{img: 's51.jpg', move: 'in', fx: 'lamp'}], ov: [{k: 'lower', text: 'EXHIBITION PERFORMERS · EUROPE', at: 12}, {k: 'stamp', text: 'NOT SOLDIERS AT WAR', cue: 0, x: 1120, y: 290}], note: 'ILLUSTRATION · painted for this film, not an original photograph'},
  S41: {shots: [{img: 's52.jpg', move: 'in'}, {img: 's53.jpg', move: 'right', cue: 0}], ov: [{k: 'lower', text: 'MUSÉE DU QUAI BRANLY · PARIS', at: 12}, {k: 'lower', text: 'NINE ITEMS · TAKEN ON 4 MARCH 1890', cue: 0}, {k: 'lower', text: 'GIFT OF THE TRADER FOÀ · 1891', cue: 1}], note: 'ILLUSTRATION · painted for this film, not the museum’s objects'},
  S42: {shots: [{img: 's55.jpg', move: 'in'}], ov: [{k: 'lower', text: 'HUMAN REMAINS · NOT SHOWN IN THIS FILM', at: 10}, {k: 'lower', text: 'RESTITUTION CLAIMS BY BENIN', cue: 0}], note: 'ILLUSTRATION · painted for this film'},
  S43: {shots: [{img: 'a_wharf1894.jpg', move: 'in', credit: 'The wharf at Cotonou, 1894. d’Albéca mission.'}, {img: 's41.jpg', move: 'right', cue: 0}, {img: 's56.jpg', move: 'in', fx: 'lamp', cue: 2}], ov: [{k: 'lower', text: 'THE WAR DID NOT END AT COTONOU', at: 10}, {k: 'lower', text: 'OUIDAH · OCTOBER 1890', cue: 0}, {k: 'lower', text: 'AN ANNUAL PAYMENT', cue: 1}, {k: 'lower', text: 'THE FRENCH PARLIAMENT', cue: 2}, {k: 'stamp', text: 'NEVER RATIFIED', at: 484, x: 1160, y: 270}]},
  S44: {shots: [{img: 's57.jpg', move: 'in'}, {img: 's58.jpg', move: 'left', cue: 0}], ov: [{k: 'lower', text: '1892 · GENERAL DODDS · A LARGER FORCE', at: 10}, {k: 'inset', img: 'a_dodds1892.jpg', cap: 'engraving, November 1892: the Dodds column camped at Abomey.', at: 70, until: 0, w: 600}, {k: 'lower', text: 'DOGBA · 1892', cue: 0}, {k: 'stamp', text: 'NOT COTONOU', cue: 1, x: 1200, y: 270}]},
  S45: {shots: [{img: 's59.jpg', move: 'in'}, {img: 's60.jpg', move: 'in', fx: 'lamp', cue: 0}], ov: [{k: 'lower', text: 'THE WOMEN SOLDIERS FOUGHT AGAIN', at: 10, until: 0}, {k: 'quote', text: 'Harpies, drunk on trade gin.', by: 'A FRENCH REPORT · APRIL 1890', cue: 0, until: 1}, {k: 'lower', text: 'A FRENCH REPORT · APRIL 1890', cue: 1}, {k: 'stamp', text: 'A COLONIAL VOICE, NOT A FACT', at: 262, x: 900, y: 300, size: 58}]},
  S46: {shots: [{img: 's40.jpg', move: 'in'}], ov: [{k: 'lower', text: 'DAHOMEY RESISTED FRENCH EXPANSION', at: 12}, {k: 'lower', text: 'IT ALSO PRACTISED SLAVERY', cue: 0, until: 1}, {k: 'head', text: 'Both are true.', cue: 1}]},
  S47: {shots: [{img: 's63.jpg', move: 'in'}, {img: 's43.jpg', move: 'out', cue: 0}], ov: [{k: 'lower', text: 'NAWI · THE LAST KNOWN VETERAN', at: 10}, {k: 'big', value: '1979', label: 'THE YEAR SHE DIED', at: 84, until: 0}, {k: 'lower', text: 'A KINGDOM THAT NO LONGER EXISTED', cue: 0}]},
  S48: {shots: [{img: 's62.jpg', move: 'in'}, {img: 's30.jpg', move: 'left', cue: 1}, {img: 's35.jpg', move: 'in', cue: 2}, {img: 's44.jpg', move: 'right', fx: 'lamp', cue: 3}], ov: [{k: 'head', text: 'The images we have', sub: 'are not the battle.', at: 6, until: 0}, {k: 'lower', text: 'THE BATTLE IS IN THE WORDS', cue: 0}, {k: 'lower', text: 'AN OFFICER · A BROKEN SHOULDER', cue: 1}, {k: 'lower', text: 'A GOVERNOR · A YOUNG WOMAN HE CALLED NANISCA', cue: 2}, {k: 'lower', text: 'A TRADER · OBJECTS SENT TO A MUSEUM', cue: 3}]},
  S49: {shots: [{img: 's01.jpg', move: 'out'}], ov: [{k: 'head', text: 'The women soldiers of Dahomey', sub: 'were real.', at: 8, until: 0}, {k: 'lower', text: 'THE DATE AND THE EVIDENCE · WITHOUT INVENTING IT', cue: 0}]},
};
