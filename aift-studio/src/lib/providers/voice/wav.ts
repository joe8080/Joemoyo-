/** Minimal 16-bit PCM WAV writer. Used by the mock voice provider and tests. */
export function writeWav(samples: Int16Array, sampleRate: number): Uint8Array {
  const dataBytes = samples.length * 2;
  const buf = new ArrayBuffer(44 + dataBytes);
  const view = new DataView(buf);
  const ascii = (off: number, s: string) => { for (let i = 0; i < s.length; i += 1) view.setUint8(off + i, s.charCodeAt(i)); };

  ascii(0, 'RIFF');
  view.setUint32(4, 36 + dataBytes, true);
  ascii(8, 'WAVE');
  ascii(12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);          // PCM
  view.setUint16(22, 1, true);          // mono
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  ascii(36, 'data');
  view.setUint32(40, dataBytes, true);
  for (let i = 0; i < samples.length; i += 1) view.setInt16(44 + i * 2, samples[i]!, true);
  return new Uint8Array(buf);
}

export function wavDurationSeconds(wav: Uint8Array): number {
  const view = new DataView(wav.buffer, wav.byteOffset, wav.byteLength);
  const byteRate = view.getUint32(28, true);
  const dataSize = view.getUint32(40, true);
  return byteRate > 0 ? dataSize / byteRate : 0;
}

/**
 * Reading-pace model used for narration timing.
 *
 * 2.72 words per second (≈163 wpm) is a measured mid-point for explainer
 * narration; punctuation adds the pauses a listener expects. Timing derived
 * here is what the caption timing and scene durations are built from, so it has
 * to be a considered figure rather than a guess.
 */
export function estimateNarrationSeconds(text: string): number {
  const words = text.trim().split(/\s+/u).filter(Boolean).length;
  const sentences = (text.match(/[.!?]/gu) ?? []).length;
  const commas = (text.match(/[,;:—]/gu) ?? []).length;
  return words / 2.72 + sentences * 0.42 + commas * 0.16;
}
