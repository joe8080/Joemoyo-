import { existsSync } from 'node:fs';
import { createRequire } from 'node:module';
import { env } from '@/lib/env';

const require_ = createRequire(import.meta.url);

/** Resolve an ffmpeg binary: explicit override, bundled static build, then PATH. */
export function resolveFfmpegPath(): string {
  const explicit = env().AIFT_FFMPEG_PATH;
  if (explicit && existsSync(explicit)) return explicit;
  try {
    const mod = require_('ffmpeg-static') as string | { default?: string };
    const p = typeof mod === 'string' ? mod : mod.default;
    if (p && existsSync(p)) return p;
  } catch {
    // fall through
  }
  for (const p of ['/usr/bin/ffmpeg', '/usr/local/bin/ffmpeg', '/opt/homebrew/bin/ffmpeg']) {
    if (existsSync(/* turbopackIgnore: true */ p)) return p;
  }
  return 'ffmpeg';
}
