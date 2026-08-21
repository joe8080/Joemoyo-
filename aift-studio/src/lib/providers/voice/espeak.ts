import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import type { VoiceClip, VoiceProvider, VoiceRequest } from '@/lib/providers/types';
import { wavDurationSeconds } from './wav';
import { ensurePcm16Wav } from '@/lib/video/transcode';

const run = promisify(execFile);

/**
 * Offline preview voice via the `espeak-ng` binary.
 *
 * Not a broadcast voice — it exists so the owner can hear pacing, emphasis and
 * caption sync before paying for a licensed one. `isAvailable()` probes for the
 * binary so the provider degrades to the silent track instead of failing a run.
 */
export class EspeakVoiceProvider implements VoiceProvider {
  readonly name = 'espeak-ng-preview@1';
  readonly isLive = false;

  static async isAvailable(): Promise<boolean> {
    try {
      await run('espeak-ng', ['--version']);
      return true;
    } catch {
      return false;
    }
  }

  async speak(req: VoiceRequest): Promise<VoiceClip> {
    const dir = await mkdtemp(join(tmpdir(), 'aift-tts-'));
    const out = join(dir, 'clip.wav');
    try {
      // Words-per-minute is tuned to the same reading pace the timing model uses.
      await run('espeak-ng', ['-v', req.voice || 'en-gb', '-s', '163', '-p', '38', '-g', '4', '-w', out, req.text], {
        maxBuffer: 32 * 1024 * 1024,
      });
      const wav = await ensurePcm16Wav(new Uint8Array(await readFile(out)));
      return {
        wav,
        durationSeconds: wavDurationSeconds(wav),
        generator: this.name,
        voice: req.voice || 'en-gb',
        transcript: req.text,
        settings: { wpm: 163, pitch: 38, gap: 4 },
      };
    } finally {
      await rm(dir, { recursive: true, force: true });
    }
  }
}
