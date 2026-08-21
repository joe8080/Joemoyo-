import { describe, expect, it } from 'vitest';
import { DEFAULT_DUCK, decodeWav, mixWithBed, peakDbfs } from '@/lib/video/audio';
import { measureLoudness, normaliseLoudness, TARGET_LUFS } from '@/lib/video/loudness';
import { ensurePcm16Wav, isPcm16Wav, toOpus } from '@/lib/video/transcode';
import { ProceduralMusicProvider } from '@/lib/providers/music/procedural';
import { writeWav } from '@/lib/providers/voice/wav';

const RATE = 48_000;

function tone(seconds: number, hz: number, amp = 0.5): Uint8Array {
  const n = Math.round(seconds * RATE);
  const pcm = new Int16Array(n);
  for (let i = 0; i < n; i += 1) pcm[i] = Math.round(Math.sin((2 * Math.PI * hz * i) / RATE) * amp * 32_767);
  return writeWav(pcm, RATE);
}

function silence(seconds: number): Uint8Array {
  return writeWav(new Int16Array(Math.round(seconds * RATE)), RATE);
}

/**
 * Speech for the first half, nothing for the second.
 *
 * Deliberately quiet — loud enough to open the ducker (which triggers above
 * -45 dBFS) but quiet enough that the bed, not the speech, dominates the
 * measured level. Otherwise the measurement is of the speech and says nothing
 * about whether the bed moved.
 */
function halfSpeech(seconds: number, amp = 0.01): Uint8Array {
  const n = Math.round(seconds * RATE);
  const pcm = new Int16Array(n);
  for (let i = 0; i < n / 2; i += 1) pcm[i] = Math.round(Math.sin((2 * Math.PI * 200 * i) / RATE) * amp * 32_767);
  return writeWav(pcm, RATE);
}

function rms(wav: Uint8Array, fromSec: number, toSec: number): number {
  const { samples } = decodeWav(wav);
  const a = Math.round(fromSec * RATE);
  const b = Math.min(samples.length, Math.round(toSec * RATE));
  let acc = 0;
  for (let i = a; i < b; i += 1) acc += (samples[i] ?? 0) ** 2;
  return Math.sqrt(acc / Math.max(1, b - a));
}

describe('format normalisation at the provider boundary', () => {
  it('recognises conforming PCM and leaves it untouched', async () => {
    const wav = tone(0.5, 440);
    expect(isPcm16Wav(wav)).toBe(true);
    expect(await ensurePcm16Wav(wav)).toBe(wav);
  });

  it('accepts what real text-to-speech providers actually return', async () => {
    // Opus in Ogg is the case that used to throw at decode; MP3 is the default
    // for both ElevenLabs and OpenAI.
    const opus = await toOpus(tone(1, 440));
    expect(isPcm16Wav(opus)).toBe(false);

    const recovered = await ensurePcm16Wav(opus);
    expect(isPcm16Wav(recovered)).toBe(true);
    const { sampleRate, samples } = decodeWav(recovered);
    expect(sampleRate).toBe(48_000);
    expect(samples.length).toBeGreaterThan(RATE * 0.9);
  }, 60_000);
});

describe('loudness', () => {
  it('measures a known tone in LUFS and dBTP', async () => {
    const m = await measureLoudness(tone(4, 1000, 0.5));
    expect(m.integratedLufs).toBeGreaterThan(-20);
    expect(m.integratedLufs).toBeLessThan(-3);
    expect(m.truePeakDbtp).toBeGreaterThan(-10);
  }, 60_000);

  it('lands a quiet track on the delivery target', async () => {
    const quiet = tone(5, 300, 0.02);
    const before = await measureLoudness(quiet);
    expect(before.integratedLufs).toBeLessThan(TARGET_LUFS - 6);

    const { after, gainDb } = await normaliseLoudness(quiet, TARGET_LUFS);
    expect(gainDb).toBeGreaterThan(0);
    expect(Math.abs(after.integratedLufs - TARGET_LUFS)).toBeLessThan(1);
    expect(after.truePeakDbtp).toBeLessThanOrEqual(-0.5);
  }, 90_000);

  it('never lifts silence', async () => {
    const { wav, gainDb } = await normaliseLoudness(silence(2), TARGET_LUFS);
    expect(gainDb).toBe(0);
    expect(peakDbfs(wav)).toBe(-Infinity);
  }, 60_000);

  it('holds the true-peak ceiling rather than hitting the target', async () => {
    // Already near full scale: raising it to -14 LUFS would clip, so the
    // ceiling has to win.
    const hot = tone(4, 500, 0.99);
    const { after } = await normaliseLoudness(hot, TARGET_LUFS);
    expect(after.truePeakDbtp).toBeLessThanOrEqual(-0.5);
  }, 90_000);
});

describe('the music bed', () => {
  it('is deterministic and carries its provenance', async () => {
    const p = new ProceduralMusicProvider();
    const a = await p.generate({ durationSeconds: 3, mood: 'analytical', seed: 7 });
    const b = await p.generate({ durationSeconds: 3, mood: 'analytical', seed: 7 });
    expect(Buffer.from(a.wav).equals(Buffer.from(b.wav))).toBe(true);
    expect(a.licence.length).toBeGreaterThan(10);
    expect(a.provenance).toContain('seed 7');
    expect(a.durationSeconds).toBeCloseTo(3, 1);
  });

  it('stays out of the speech band', async () => {
    const bed = await new ProceduralMusicProvider().generate({ durationSeconds: 4, mood: 'analytical', seed: 1 });
    // The pad is low-passed twice; nothing near full scale should survive.
    expect(peakDbfs(bed.wav)).toBeLessThan(-6);
  });
});

describe('ducking', () => {
  it('pulls the bed down under speech and releases it after', async () => {
    const speech = halfSpeech(6);
    const bed = tone(6, 500, 0.5);
    const mix = mixWithBed(speech, bed, DEFAULT_DUCK);

    // Sampled well inside each half so attack and release have settled.
    const under = rms(mix, 2.0, 2.5);
    const clear = rms(mix, 5.0, 5.5);
    expect(clear).toBeGreaterThan(under * 1.8);
    // And the duck is roughly the depth that was asked for.
    const measuredDuckDb = 20 * Math.log10(under / clear);
    expect(measuredDuckDb).toBeLessThan(DEFAULT_DUCK.duckDb + 6);
  });

  it('leaves the bed alone when nothing is speaking', () => {
    const mix = mixWithBed(silence(4), tone(4, 500, 0.5), DEFAULT_DUCK);
    expect(rms(mix, 1, 2)).toBeGreaterThan(0.01);
  });

  it('loops a bed shorter than the programme', () => {
    const mix = mixWithBed(silence(6), tone(2, 500, 0.5), DEFAULT_DUCK);
    expect(rms(mix, 5, 6)).toBeGreaterThan(0.01);
  });

  it('keeps the narration at full level', () => {
    const speech = tone(3, 200, 0.5);
    const mix = mixWithBed(speech, silence(3), DEFAULT_DUCK);
    expect(rms(mix, 1, 2)).toBeCloseTo(rms(speech, 1, 2), 2);
  });
});
