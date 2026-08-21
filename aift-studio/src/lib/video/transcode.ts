import { spawn } from 'node:child_process';
import { resolveFfmpegPath } from './ffmpeg';

/**
 * Audio format normalisation at the provider boundary.
 *
 * The `VoiceProvider` and `MusicProvider` contracts say "16-bit PCM WAV" so the
 * assembler can stay synchronous and deterministic. Real providers do not
 * cooperate: ElevenLabs and OpenAI both default to MP3, and plenty return Opus
 * or 24-bit WAV. Rather than teach the decoder every format, adapters run their
 * bytes through here first.
 */

export async function ffmpegPipe(input: Uint8Array, args: string[]): Promise<Uint8Array> {
  const bin = resolveFfmpegPath();
  return new Promise((resolve, reject) => {
    const p = spawn(bin, ['-hide_banner', '-loglevel', 'error', '-i', 'pipe:0', ...args, 'pipe:1'], {
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    const out: Buffer[] = [];
    let err = '';
    p.stdout.on('data', (c: Buffer) => out.push(c));
    p.stderr.on('data', (c: Buffer) => { err += c.toString(); });
    p.stdin.on('error', () => { /* EPIPE if ffmpeg rejects the input; close carries the reason */ });
    p.on('error', reject);
    p.on('close', (code) => (code === 0
      ? resolve(new Uint8Array(Buffer.concat(out)))
      : reject(new Error(`ffmpeg transcode failed (${code}): ${err.slice(-1500)}`))));
    p.stdin.end(input);
  });
}

/** True when the bytes are already the mono/stereo 16-bit PCM WAV we can decode. */
export function isPcm16Wav(bytes: Uint8Array): boolean {
  if (bytes.byteLength < 44) return false;
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const tag = (o: number) => String.fromCharCode(view.getUint8(o), view.getUint8(o + 1), view.getUint8(o + 2), view.getUint8(o + 3));
  if (tag(0) !== 'RIFF' || tag(8) !== 'WAVE') return false;

  let pos = 12;
  while (pos + 8 <= bytes.byteLength) {
    const id = tag(pos);
    const size = view.getUint32(pos + 4, true);
    if (id === 'fmt ') {
      const format = view.getUint16(pos + 8, true);
      const bits = view.getUint16(pos + 8 + 14, true);
      return format === 1 && bits === 16;
    }
    pos += 8 + size + (size % 2);
  }
  return false;
}

/**
 * Coerce anything ffmpeg can read — MP3, Opus, Ogg, FLAC, AAC, 24-bit or float
 * WAV — into mono 16-bit PCM WAV at the given rate. Already-conforming bytes are
 * returned untouched, so the common path costs nothing.
 */
export async function ensurePcm16Wav(bytes: Uint8Array, sampleRate = 48_000): Promise<Uint8Array> {
  if (isPcm16Wav(bytes)) return bytes;
  return ffmpegPipe(bytes, ['-vn', '-acodec', 'pcm_s16le', '-ac', '1', '-ar', String(sampleRate), '-f', 'wav']);
}

/** Ogg/Opus export, for review copies and anywhere a small speech file is wanted. */
export async function toOpus(wav: Uint8Array, bitrateKbps = 96): Promise<Uint8Array> {
  return ffmpegPipe(wav, ['-vn', '-c:a', 'libopus', '-b:a', `${bitrateKbps}k`, '-f', 'ogg']);
}
