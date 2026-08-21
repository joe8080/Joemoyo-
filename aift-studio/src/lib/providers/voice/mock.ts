import type { VoiceClip, VoiceProvider, VoiceRequest } from '@/lib/providers/types';
import { estimateNarrationSeconds, writeWav } from './wav';

/**
 * Silent narration track with the *correct* duration.
 *
 * Silence is the honest default when no licensed voice is configured: the video
 * has real, verifiable pacing and real caption timing, and nobody can mistake a
 * synthetic filler voice for the finished thing. Swap in `espeak` for a rough
 * audible preview or `http` for a licensed voice; the timing model is shared.
 */
export class MockVoiceProvider implements VoiceProvider {
  readonly name = 'silent-timed-narration@1';
  readonly isLive = false;
  private readonly sampleRate = 24_000;

  async speak(req: VoiceRequest): Promise<VoiceClip> {
    const seconds = req.targetSeconds ?? estimateNarrationSeconds(req.text);
    const n = Math.max(1, Math.round(seconds * this.sampleRate));
    return {
      wav: writeWav(new Int16Array(n), this.sampleRate),
      durationSeconds: n / this.sampleRate,
      generator: this.name,
      voice: req.voice,
      transcript: req.text,
      settings: { sampleRate: this.sampleRate, mode: 'silent-placeholder' },
    };
  }
}
