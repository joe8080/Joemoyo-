// Soundtrack synthesised from scratch: music bed + sound effects, written as a 16-bit stereo WAV.
// No samples, no downloads — every sound is maths.
import { writeFileSync } from 'node:fs';

const SR = 44100;
const TAU = Math.PI * 2;
const midi = (n) => 440 * Math.pow(2, (n - 69) / 12);

function rng(seed) {
  let s = seed >>> 0;
  return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296) * 2 - 1;
}

export function renderAudio(tl, path, voices = {}) {
  const N = Math.ceil((tl.duration + 0.4) * SR);
  const L = new Float32Array(N), R = new Float32Array(N);
  const noise = rng(42);

  // add a mono voice: fn(t) -> sample, written into [L,R] (or a custom pair) at time t0
  let fxGain = 1;
  const add = (t0, len, fn, gain = 1, pan = 0, out = [L, R]) => {
    gain *= fxGain;
    const s = Math.floor(t0 * SR), n = Math.floor(len * SR);
    const gl = gain * (pan > 0 ? 1 - pan : 1), gr = gain * (pan < 0 ? 1 + pan : 1);
    for (let i = 0; i < n; i++) {
      const k = s + i;
      if (k < 0 || k >= N) continue;
      const v = fn(i / SR);
      out[0][k] += v * gl; out[1][k] += v * gr;
    }
  };
  const sweep = (f0, f1, rate) => { let ph = 0; return (t) => { ph += (TAU * (f1 + (f0 - f1) * Math.exp(-t * rate))) / SR; return ph; }; };

  const sfx = {
    boom(c) {
      const ph = sweep(150, 38, 16);
      add(c.t, 1.1, (t) => Math.tanh(2.6 * Math.sin(ph(t))) * Math.exp(-t * 4.2) + noise() * Math.exp(-t * 70) * 0.5, 0.62);
    },
    thud(c) { const ph = sweep(90, 34, 20); add(c.t, 0.8, (t) => Math.sin(ph(t)) * Math.exp(-t * 6), 0.6); },
    whoosh(c) {
      let lp = 0;
      add(c.t - 0.1, 0.3, (t) => { const e = Math.sin((Math.PI * t) / 0.3) ** 2; lp += (noise() - lp) * (0.06 + 0.5 * e); return lp * e; }, 0.5);
    },
    blip(c) {
      const f = c.voice * Math.pow(2, ((c.n * 7) % 5 - 2) / 12);
      add(c.t, 0.07, (t) => { const e = Math.min(1, t / 0.004) * Math.exp(-t * 38); const s = Math.sin(TAU * f * t); return (c.soft ? s : 0.55 * s + 0.45 * Math.sign(s)) * e; }, c.soft ? 0.09 : 0.13, c.soft ? 0 : 0.15);
    },
    pop(c) { const ph = sweep(520, 940, 40); add(c.t, 0.12, (t) => Math.sin(ph(t)) * Math.exp(-t * 30), 0.35); },
    sent(c) { const ph = sweep(900, 560, 40); add(c.t, 0.12, (t) => Math.sin(ph(t)) * Math.exp(-t * 30), 0.3); },
    ding(c) {
      for (const [f, d] of [[1318.5, 0], [1975.5, 0.13]])
        add(c.t + d, 0.9, (t) => (Math.sin(TAU * f * t) + 0.3 * Math.sin(TAU * f * 2.01 * t)) * Math.exp(-t * 5.5), 0.22);
    },
    tick(c) { add(c.t, 0.03, (t) => (Math.sin(TAU * 2100 * t) + noise() * 0.4) * Math.exp(-t * 160), 0.1); },
    heart(c) {
      for (let b = 0; b < c.dur - 0.3; b += 0.82)
        for (const [d, g] of [[0, 1], [0.24, 0.7]]) { const ph = sweep(75, 45, 30); add(c.t + b + d, 0.3, (t) => Math.sin(ph(t)) * Math.exp(-t * 20), 0.55 * g); }
    },
    riser(c) {
      let ph = 0;
      add(c.t, c.dur, (t) => { const p = t / c.dur; ph += (TAU * (180 + 700 * p * p)) / SR; return (Math.sin(ph) * 0.6 + noise() * 0.25) * p * p; }, 0.2);
    },
    cash(c) {
      [84, 88, 91, 96].forEach((n, i) => add(c.t + i * 0.065, 0.7, (t) => (Math.sin(TAU * midi(n) * t) + 0.4 * Math.sin(TAU * midi(n) * 3 * t)) * Math.exp(-t * 7), 0.16, i % 2 ? 0.3 : -0.3));
    },
  };
  // recorded voice lines; the inner voice ("think") gets a short echo so it reads as a thought
  const V = tl.meta.voiced;
  sfx.voice = (c) => {
    const pcm = voices[c.key]?.pcm;
    if (!pcm) return;
    const d1 = Math.floor(0.085 * SR), d2 = Math.floor(0.17 * SR);
    const s0 = Math.floor(c.t * SR);
    for (let i = 0; i < pcm.length + (c.think ? d2 : 0); i++) {
      const k = s0 + i; if (k < 0 || k >= N) continue;
      let v = i < pcm.length ? pcm[i] : 0;
      if (c.think) v = v * 0.85 + 0.38 * (pcm[i - d1] || 0) + 0.18 * (pcm[i - d2] || 0);
      L[k] += v; R[k] += v;
    }
  };
  // with voices on top, pull the effects back so every word stays clear
  const FX = V ? { boom: 0.55, thud: 0.6, whoosh: 0.5, heart: 0.6, tick: 0.7, cash: 0.8, ding: 0.8, riser: 0.7 } : {};
  for (const c of tl.cues) {
    if (!sfx[c.kind]) continue;
    fxGain = FX[c.kind] ?? 1;
    sfx[c.kind](c);
    fxGain = 1;
  }

  // ── music bed: chord arpeggio + pad, one flavour per mood ──
  const MOODS = {
    tense: { bpm: 84, prog: [[45, 48, 52], [45, 48, 52], [41, 45, 48], [40, 44, 47]], kick: false, gain: 1 },
    sad: { bpm: 66, prog: [[45, 48, 52], [41, 45, 48], [36, 40, 43], [43, 47, 50]], kick: false, gain: 1 },
    comedy: { bpm: 118, prog: [[48, 52, 55], [53, 57, 60], [50, 53, 57], [55, 59, 62]], kick: false, gain: 1, decay: 10, bass: true },
    win: { bpm: 112, prog: [[48, 52, 55], [43, 47, 50], [45, 48, 52], [41, 45, 48]], kick: true, gain: 1.1 },
  };
  for (const seg of tl.music) {
    const m = MOODS[seg.mood];
    if (!m) continue; // 'none' = silence
    const ML = new Float32Array(N), MR = new Float32Array(N), out = [ML, MR];
    const e8 = 60 / m.bpm / 2, pat = [0, 2, 1, 2, 0, 2, 1, 2];
    for (let n = 0; seg.t0 + n * e8 < seg.t1; n++) {
      const t0 = seg.t0 + n * e8, chord = m.prog[Math.floor(n / 8) % m.prog.length];
      const f = midi(chord[pat[n % 8]] + 12 + (n % 8 === 5 ? 12 : 0));
      add(t0, 1.3, (t) => (Math.sin(TAU * f * t) + 0.35 * Math.sin(TAU * f * 2 * t) + 0.12 * Math.sin(TAU * f * 3 * t)) * Math.exp(-t * (m.decay || 3.6)) * Math.min(1, t / 0.005), 0.115, n % 2 ? 0.35 : -0.35, out);
      if (m.bass && n % 2 === 0) { const bf = midi(chord[0] - 12 + (n % 4 === 2 ? 7 : 0)); add(t0, 0.5, (t) => (Math.sin(TAU * bf * t) + 0.25 * Math.sin(TAU * bf * 2 * t)) * Math.exp(-t * 7) * Math.min(1, t / 0.006), 0.2, 0, out); }
      if (!m.bass && n % 8 === 0) for (const note of chord) add(t0, e8 * 8 + 0.2, (t) => Math.sin(TAU * midi(note - 12) * t) * Math.min(1, t / 0.4) * Math.min(1, (e8 * 8 + 0.2 - t) / 0.4) * (0.8 + 0.2 * Math.sin(t * 5)), 0.065, 0, out);
      if (m.kick && n % 2 === 0) { const ph = sweep(120, 45, 28); add(t0, 0.25, (t) => Math.sin(ph(t)) * Math.exp(-t * 14), 0.3, 0, out); }
      if (m.kick && n % 2 === 1) add(t0, 0.04, (t) => noise() * Math.exp(-t * 120), 0.05, 0, out);
    }
    const a = Math.floor(seg.t0 * SR), b = Math.min(N, Math.floor(seg.t1 * SR)), fade = 0.3 * SR;
    for (let i = Math.max(0, a - fade); i < Math.min(N, b + fade * 3); i++) {
      const env = i < a ? 0 : Math.min(1, (i - a) / fade) * (i > b ? Math.max(0, 1 - (i - b) / (fade * 3)) : 1);
      L[i] += ML[i] * env * m.gain * (V ? 0.5 : 1); R[i] += MR[i] * env * m.gain * (V ? 0.5 : 1);
    }
  }

  // master: normalise + soft clip, then 16-bit PCM
  let peak = 0;
  for (let i = 0; i < N; i++) peak = Math.max(peak, Math.abs(L[i]), Math.abs(R[i]));
  const g = peak > 0 ? 0.92 / Math.max(peak, 0.6) : 1;
  const DRIVE = 2.0, NORM = Math.tanh(DRIVE); // gentle limiter: lifts the quiet bed, tames the booms
  const buf = Buffer.alloc(44 + N * 4);
  buf.write('RIFF', 0); buf.writeUInt32LE(36 + N * 4, 4); buf.write('WAVEfmt ', 8); buf.writeUInt32LE(16, 16);
  buf.writeUInt16LE(1, 20); buf.writeUInt16LE(2, 22); buf.writeUInt32LE(SR, 24); buf.writeUInt32LE(SR * 4, 28);
  buf.writeUInt16LE(4, 32); buf.writeUInt16LE(16, 34); buf.write('data', 36); buf.writeUInt32LE(N * 4, 40);
  for (let i = 0; i < N; i++) {
    buf.writeInt16LE(Math.round((Math.tanh(L[i] * g * DRIVE) / NORM) * 27500), 44 + i * 4);
    buf.writeInt16LE(Math.round((Math.tanh(R[i] * g * DRIVE) / NORM) * 27500), 46 + i * 4);
  }
  writeFileSync(path, buf);
}
