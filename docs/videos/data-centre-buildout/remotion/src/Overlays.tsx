import React from 'react';
import {OffthreadVideo, staticFile, interpolate} from 'remotion';
import {useAudioData, visualizeAudio} from '@remotion/media-utils';
import {A, WORDS, C, F, STATUS, useT, pr, eo, clamp} from './ui';

/* ---------- plate + colour script (the room takes the colour of the answer) ---------- */
const HUE_KEYS: [number, number][] = [
  [0, 0], [A.q1 - 0.5, 0], [A.q1 + 1, 0],
  [A.q2 - 0.3, -125 * 0 + 0], [A.q2_yes, -125],
  [A.q3_30 - 0.2, -125], [A.q3_30 + 1.2, -165],
  [A.q4_ahead - 0.2, -165], [A.q4_ahead + 1.4, -22],
  [A.q5_notyet - 0.2, -22], [A.q5_notyet + 1.4, -125],
  [A.map - 0.2, -125], [A.map + 1.6, 0], [99999, 0],
];
export const plateHue = (t: number) => interpolate(t, HUE_KEYS.map((k) => k[0]), HUE_KEYS.map((k) => k[1]), {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

export const PlateBG: React.FC = () => {
  const {t} = useT();
  // plate is baked offline (hue script + bloom); here only the cheap dim + scrims
  const dim = interpolate(t, [A.q1 - 0.6, A.q1 + 0.6, A.close - 0.5, A.close + 1.0], [0.86, 0.46, 0.46, 0.72], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <div style={{position: 'absolute', inset: 0, background: '#04060c', overflow: 'hidden'}}>
      <OffthreadVideo src={staticFile('plate_baked.mp4')} muted style={{width: 1920, height: 1080, objectFit: 'cover'}} />
      <div style={{position: 'absolute', inset: 0, background: `rgba(4,6,12,${1 - dim})`}} />
      <div style={{position: 'absolute', inset: 0, background: 'radial-gradient(120% 90% at 50% 40%, rgba(7,11,20,0.25) 0%, rgba(4,6,12,0.78) 100%)'}} />
      <div style={{position: 'absolute', inset: 0, background: 'linear-gradient(180deg, rgba(4,6,12,0.93) 0%, rgba(4,6,12,0.8) 24%, rgba(4,6,12,0.3) 40%, rgba(4,6,12,0.22) 68%, rgba(4,6,12,0.85) 100%)'}} />
    </div>
  );
};

/* ---------- header ---------- */
export const Header: React.FC = () => {
  const {t} = useT();
  const o = eo(pr(t, 0.3, 0.8));
  return (
    <div style={{position: 'absolute', left: 96, top: 44, display: 'flex', alignItems: 'center', gap: 18, opacity: o}}>
      <div style={{width: 58, height: 58, borderRadius: 29, background: C.gold, color: C.ink, display: 'grid', placeItems: 'center', font: `800 21px ${F.disp}`, boxShadow: '0 0 30px rgba(242,184,75,.45)'}}>AFT</div>
      <div>
        <div style={{font: `700 27px ${F.disp}`, letterSpacing: '0.03em'}}>AI FINANCE TOOLKIT</div>
        <div style={{font: `400 22px ${F.body}`, color: C.muted, marginTop: 2}}>The data centre buildout · 5 questions</div>
      </div>
    </div>
  );
};

/* ---------- tracker ---------- */
const QDEF: [string, string, string, string, string][] = [
  ['1', 'Orders', 'q1', 'q1_pace', 'ok'], ['2', 'Chips', 'q2', 'q2_yes', 'warn'], ['3', 'Power', 'q3', 'q3_30', 'alert'], ['4', 'Equipment', 'q4', 'q4_ahead', 'ok'], ['5', 'Payback', 'q5', 'q5_notyet', 'warn'],
];
export const Tracker: React.FC = () => {
  const {t} = useT();
  const show = eo(pr(t, A.fiveq + 0.6, 0.6));
  return (
    <div style={{position: 'absolute', right: 96, top: 50, display: 'flex', gap: 12, opacity: show}}>
      {QDEF.map((d, i) => {
        const ta = A[d[2]], ts = A[d[3]];
        const done = t >= ts, active = t >= ta && !done;
        const col = done ? STATUS[d[4]] : active ? C.teal : 'rgba(150,180,240,.4)';
        const pulse = done ? 1 - pr(t, ts, 1.0) : 0;
        return (
          <div key={i} style={{height: 50, padding: '0 20px', borderRadius: 25, border: `2px solid ${col}`, font: `500 23px ${F.mono}`, color: done ? col : active ? C.fg : C.muted, display: 'flex', alignItems: 'center', gap: 10, background: 'rgba(13,19,34,.62)', backdropFilter: 'blur(12px)', boxShadow: pulse > 0 ? `0 0 ${34 * pulse}px ${col}` : 'none'}}>
            <i style={{width: 14, height: 14, borderRadius: 7, background: done ? col : 'transparent', border: `2px solid ${col}`, boxShadow: done ? `0 0 12px ${col}` : 'none'}} />
            <span>{d[0]} {d[1]}</span>
          </div>
        );
      })}
    </div>
  );
};

/* ---------- captions (word highlight) ---------- */
const CH: {w: string; s: number; e: number}[][] = (() => {
  const out: any[] = [];
  let cur: any[] = [];
  WORDS.forEach((w, i) => {
    cur.push(w);
    const end = /[.?!:]$/.test(w.w) || (/,$/.test(w.w) && cur.length >= 5) || cur.length >= 9;
    if (end || i === WORDS.length - 1) { out.push(cur); cur = []; }
  });
  return out;
})();
export const Captions: React.FC = () => {
  const {t} = useT();
  let idx = -1;
  for (let i = 0; i < CH.length; i++) { if (t >= CH[i][0].s - 0.05) idx = i; else break; }
  if (idx < 0) return null;
  const ch = CH[idx];
  if (t > ch[ch.length - 1].e + 0.6) return null;
  const inn = eo(pr(t, ch[0].s - 0.05, 0.18));
  return (
    <div style={{position: 'absolute', left: 150, right: 150, bottom: 52, display: 'flex', justifyContent: 'center', opacity: inn, transform: `translateY(${(1 - inn) * 14}px)`}}>
      <div style={{padding: '12px 30px 14px', borderRadius: 22, background: 'rgba(5,8,16,0.58)', backdropFilter: 'blur(14px)', border: '1px solid rgba(190,210,255,.16)', font: `700 46px/1.22 ${F.body}`, textAlign: 'center', boxShadow: '0 14px 40px rgba(0,0,0,.45)'}}>
        {ch.map((w, k) => {
          const on = t >= w.s && t <= w.e + 0.05;
          const spoken = t > w.e + 0.05;
          return <span key={k} style={{display: 'inline-block', whiteSpace: 'pre', color: on ? C.gold : spoken ? '#fff' : 'rgba(255,255,255,.5)', transform: on ? 'translateY(-2px) scale(1.06)' : 'none'}}>{w.w + ' '}</span>;
        })}
      </div>
    </div>
  );
};

/* ---------- voice-reactive ribbon ---------- */
export const Waveform: React.FC = () => {
  const {t, f, fps} = useT();
  const data = useAudioData(staticFile('vo.wav'));
  if (!data) return null;
  const N = 64;
  const half = visualizeAudio({fps, frame: f, audioData: data, numberOfSamples: 64, smoothing: true}).slice(0, N / 2);
  const vis = [...half.slice().reverse(), ...half];
  const col = (i: number) => (Math.abs(i - N / 2 + 0.5) < 10 ? C.gold : C.teal);
  return (
    <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: 34, display: 'flex', alignItems: 'flex-end', justifyContent: 'center', gap: 6, opacity: 0.85}}>
      {vis.map((v, i) => {
        const h = clamp(Math.pow(v, 0.5) * 3.2, 0.04, 1) * 30;
        return <div key={i} style={{width: 12, height: h, borderRadius: 6, background: col(i), opacity: 0.35 + 0.65 * clamp(h / 30), boxShadow: `0 0 10px ${col(i)}55`}} />;
      })}
    </div>
  );
};
