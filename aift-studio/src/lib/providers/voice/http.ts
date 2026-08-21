import type { VoiceClip, VoiceProvider, VoiceRequest } from '@/lib/providers/types';
import { env } from '@/lib/env';
import { wavDurationSeconds } from './wav';
import { ensurePcm16Wav } from '@/lib/video/transcode';

/**
 * Licensed cloud text-to-speech adapter.
 *
 * Deliberately thin and format-strict: it requests WAV so the render pipeline
 * never has to guess a duration, and it preserves the exact transcript and the
 * voice settings on the clip for the QA record.
 */
export class HttpVoiceProvider implements VoiceProvider {
  readonly name = 'http-tts@1';
  readonly isLive = true;

  private readonly apiKey: string;
  private readonly baseUrl: string;
  private readonly defaultVoice: string;

  constructor() {
    const e = env();
    if (!e.AIFT_TTS_API_KEY || !e.AIFT_TTS_BASE_URL) {
      throw new Error('HttpVoiceProvider requires AIFT_TTS_API_KEY and AIFT_TTS_BASE_URL');
    }
    this.apiKey = e.AIFT_TTS_API_KEY;
    this.baseUrl = e.AIFT_TTS_BASE_URL.replace(/\/$/u, '');
    this.defaultVoice = e.AIFT_TTS_VOICE ?? 'default';
  }

  async speak(req: VoiceRequest): Promise<VoiceClip> {
    const voice = req.voice || this.defaultVoice;
    const res = await fetch(`${this.baseUrl}/audio/speech`, {
      method: 'POST',
      headers: { 'content-type': 'application/json', authorization: `Bearer ${this.apiKey}` },
      body: JSON.stringify({ input: req.text, voice, response_format: 'wav' }),
    });
    if (!res.ok) throw new Error(`TTS request failed with HTTP ${res.status}`);

    // WAV is requested, but providers disagree about defaults — ElevenLabs and
    // OpenAI both return MP3 unless told otherwise, and some return 24-bit or
    // Opus regardless. Normalising here keeps that argument out of the mixer.
    const wav = await ensurePcm16Wav(new Uint8Array(await res.arrayBuffer()));
    return {
      wav,
      durationSeconds: wavDurationSeconds(wav),
      generator: this.name,
      voice,
      transcript: req.text,
      settings: { format: 'wav', normalised: 'pcm_s16le' },
    };
  }
}
