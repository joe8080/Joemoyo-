import { spawn } from 'node:child_process';
import { resolveFfmpegPath } from './ffmpeg';
import { decodeWav } from './audio';
import { writeWav } from '@/lib/providers/voice/wav';

/**
 * Loudness measurement and normalisation.
 *
 * Peak level says nothing about how loud something sounds. YouTube normalises
 * playback to roughly -14 LUFS integrated, so a pack that peaks politely at
 * -1.5 dBFS can still arrive quiet, or arrive crushed — and a peak gate would
 * pass both. These are the numbers that describe delivery.
 */

export type Loudness = {
  integratedLufs: number;
  truePeakDbtp: number;
  loudnessRange: number;
};

/** YouTube's playback target. Everything here is measured against it. */
export const TARGET_LUFS = -14;
export const TRUE_PEAK_CEILING_DBTP = -1;

/**
 * ebur128 reports digital silence as -70 LUFS, its floor, not as -infinity.
 * Anything at or below this is treated as having no programme content: lifting
 * it to target would apply 56 dB of gain to a noise floor.
 */
export const SILENCE_FLOOR_LUFS = -60;

/** No amount of normalisation should turn a near-silent take into a usable one. */
export const MAX_GAIN_DB = 24;

export async function measureLoudness(wav: Uint8Array): Promise<Loudness> {
  const bin = resolveFfmpegPath();
  const stderr = await new Promise<string>((resolve, reject) => {
    const p = spawn(bin, ['-hide_banner', '-nostats', '-i', 'pipe:0', '-af', 'ebur128=peak=true', '-f', 'null', '-'], {
      stdio: ['pipe', 'ignore', 'pipe'],
    });
    let err = '';
    p.stderr.on('data', (c: Buffer) => { err += c.toString(); });
    p.stdin.on('error', () => { /* EPIPE; close carries the reason */ });
    p.on('error', reject);
    p.on('close', () => resolve(err));
    p.stdin.end(wav);
  });

  // The summary block is the last one printed; read from its end backwards.
  const summary = stderr.slice(stderr.lastIndexOf('Integrated loudness'));
  const num = (label: string): number => {
    const m = new RegExp(`${label}:\\s*(-?[\\d.]+|-inf)`, 'u').exec(summary);
    if (!m) return -Infinity;
    return m[1] === '-inf' ? -Infinity : Number(m[1]);
  };

  return {
    integratedLufs: num('I'),
    truePeakDbtp: num('Peak'),
    loudnessRange: num('LRA'),
  };
}

/**
 * Apply a fixed gain so the track lands on `target` LUFS, then hold it below the
 * true-peak ceiling.
 *
 * A single measured gain rather than a compressor: the narration has already
 * been assembled and we want the mix we shipped to be the mix that was checked,
 * not one a dynamics processor reshaped afterwards. Silence is left silent.
 */
export async function normaliseLoudness(
  wav: Uint8Array, target = TARGET_LUFS, ceilingDbtp = TRUE_PEAK_CEILING_DBTP,
): Promise<{ wav: Uint8Array; before: Loudness; after: Loudness; gainDb: number }> {
  const before = await measureLoudness(wav);
  if (!Number.isFinite(before.integratedLufs) || before.integratedLufs <= SILENCE_FLOOR_LUFS) {
    return { wav, before, after: before, gainDb: 0 };
  }

  const wanted = Math.min(target - before.integratedLufs, MAX_GAIN_DB);
  const headroom = ceilingDbtp - before.truePeakDbtp;
  const gainDb = Math.min(wanted, Number.isFinite(headroom) ? headroom : wanted);
  const gain = 10 ** (gainDb / 20);

  const { samples, sampleRate } = decodeWav(wav);
  const pcm = new Int16Array(samples.length);
  for (let i = 0; i < samples.length; i += 1) {
    const v = Math.max(-1, Math.min(1, (samples[i] ?? 0) * gain));
    pcm[i] = Math.round(v * 32_767);
  }
  const out = writeWav(pcm, sampleRate);
  return { wav: out, before, after: await measureLoudness(out), gainDb };
}
