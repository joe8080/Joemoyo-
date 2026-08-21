import { writeWav } from '@/lib/providers/voice/wav';

/**
 * Narration assembly.
 *
 * Clips are decoded, resampled to a single rate and laid onto a silent bed at
 * their scene offsets. Doing it here rather than with an ffmpeg filter graph
 * keeps the timing arithmetic in the same place as the caption timing, so the
 * two cannot drift, and it means the assembled track is testable in-process.
 */

export const MASTER_SAMPLE_RATE = 48_000;

export type WavInfo = { sampleRate: number; channels: number; bitsPerSample: number; samples: Float32Array };

export function decodeWav(bytes: Uint8Array): WavInfo {
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const tag = (off: number) => String.fromCharCode(view.getUint8(off), view.getUint8(off + 1), view.getUint8(off + 2), view.getUint8(off + 3));
  if (tag(0) !== 'RIFF' || tag(8) !== 'WAVE') throw new Error('not a RIFF/WAVE file');

  let pos = 12;
  let sampleRate = 44_100, channels = 1, bitsPerSample = 16;
  let dataOff = -1, dataLen = 0;

  while (pos + 8 <= bytes.byteLength) {
    const id = tag(pos);
    const size = view.getUint32(pos + 4, true);
    const body = pos + 8;
    if (id === 'fmt ') {
      channels = view.getUint16(body + 2, true);
      sampleRate = view.getUint32(body + 4, true);
      bitsPerSample = view.getUint16(body + 14, true);
    } else if (id === 'data') {
      dataOff = body; dataLen = size;
    }
    pos = body + size + (size % 2);
  }
  if (dataOff < 0) throw new Error('WAV has no data chunk');
  if (bitsPerSample !== 16) throw new Error(`unsupported bit depth ${bitsPerSample}; expected 16`);

  const frames = Math.floor(dataLen / (2 * channels));
  const out = new Float32Array(frames);
  for (let i = 0; i < frames; i += 1) {
    // Downmix to mono: narration is mono by definition.
    let acc = 0;
    for (let c = 0; c < channels; c += 1) acc += view.getInt16(dataOff + (i * channels + c) * 2, true) / 32_768;
    out[i] = acc / channels;
  }
  return { sampleRate, channels, bitsPerSample, samples: out };
}

/** Linear resample. Adequate for speech and fully deterministic. */
export function resample(samples: Float32Array, from: number, to: number): Float32Array {
  if (from === to) return samples;
  const ratio = to / from;
  const n = Math.round(samples.length * ratio);
  const out = new Float32Array(n);
  for (let i = 0; i < n; i += 1) {
    const src = i / ratio;
    const i0 = Math.floor(src);
    const i1 = Math.min(samples.length - 1, i0 + 1);
    const f = src - i0;
    out[i] = (samples[i0] ?? 0) * (1 - f) + (samples[i1] ?? 0) * f;
  }
  return out;
}

export type Placement = { wav: Uint8Array; startMs: number };

export function assembleNarration(placements: Placement[], totalMs: number): Uint8Array {
  const totalFrames = Math.ceil((totalMs / 1000) * MASTER_SAMPLE_RATE) + MASTER_SAMPLE_RATE;
  const bed = new Float32Array(totalFrames);

  for (const p of placements) {
    const info = decodeWav(p.wav);
    const mono = resample(info.samples, info.sampleRate, MASTER_SAMPLE_RATE);
    const offset = Math.round((p.startMs / 1000) * MASTER_SAMPLE_RATE);
    // 8ms cosine fades stop clip boundaries from clicking.
    const fade = Math.min(Math.floor(MASTER_SAMPLE_RATE * 0.008), Math.floor(mono.length / 2));
    for (let i = 0; i < mono.length; i += 1) {
      const idx = offset + i;
      if (idx < 0 || idx >= bed.length) continue;
      let g = 1;
      if (i < fade) g = 0.5 - 0.5 * Math.cos((Math.PI * i) / fade);
      else if (i > mono.length - fade) g = 0.5 - 0.5 * Math.cos((Math.PI * (mono.length - i)) / fade);
      bed[idx] = (bed[idx] ?? 0) + (mono[i] ?? 0) * g;
    }
  }

  // Peak-normalise to -1.5 dBFS. Never amplify silence: a silent mock track must
  // stay silent rather than have its noise floor lifted into audibility.
  let peak = 0;
  for (const v of bed) { const a = Math.abs(v); if (a > peak) peak = a; }
  const target = 10 ** (-1.5 / 20);
  const gain = peak > 1e-4 ? Math.min(target / peak, 8) : 1;

  const pcm = new Int16Array(bed.length);
  for (let i = 0; i < bed.length; i += 1) {
    const v = Math.max(-1, Math.min(1, (bed[i] ?? 0) * gain));
    pcm[i] = Math.round(v * 32_767);
  }
  return writeWav(pcm, MASTER_SAMPLE_RATE);
}

/** True peak in dBFS, used by the technical QA gate. */
export function peakDbfs(wav: Uint8Array): number {
  const { samples } = decodeWav(wav);
  let peak = 0;
  for (const v of samples) { const a = Math.abs(v); if (a > peak) peak = a; }
  return peak <= 1e-6 ? -Infinity : 20 * Math.log10(peak);
}
