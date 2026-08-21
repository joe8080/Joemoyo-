import type { VoiceProvider } from '@/lib/providers/types';
import { env } from '@/lib/env';
import { MockVoiceProvider } from './mock';
import { EspeakVoiceProvider } from './espeak';
import { HttpVoiceProvider } from './http';

export async function createVoiceProvider(): Promise<VoiceProvider> {
  const e = env();
  if (e.AIFT_TTS_PROVIDER === 'http' && e.AIFT_TTS_API_KEY && e.AIFT_TTS_BASE_URL) return new HttpVoiceProvider();
  if (e.AIFT_TTS_PROVIDER === 'espeak' && (await EspeakVoiceProvider.isAvailable())) return new EspeakVoiceProvider();
  return new MockVoiceProvider();
}

export { MockVoiceProvider, EspeakVoiceProvider, HttpVoiceProvider };
