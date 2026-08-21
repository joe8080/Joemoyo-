import { existsSync } from 'node:fs';
import { readdirSync } from 'node:fs';
import { join } from 'node:path';
import { env } from '@/lib/env';

/**
 * Resolve a Chromium binary without ever downloading one.
 *
 * Order: explicit override, then any Playwright-managed install on this machine
 * (whatever revision), then the usual system locations. Preferring an existing
 * install over a pinned revision is deliberate — the renderer only needs a
 * headless Chromium, and forcing a download would make the pipeline fail on
 * exactly the machines that already have one.
 */
export function resolveChromiumPath(): string | undefined {
  const explicit = env().AIFT_CHROMIUM_PATH;
  if (explicit && existsSync(explicit)) return explicit;

  const root = process.env.PLAYWRIGHT_BROWSERS_PATH;
  if (root && existsSync(root)) {
    const dirs = readdirSync(root).filter((d) => d.startsWith('chromium')).sort().reverse();
    // Full Chromium first: the headless shell lacks some compositing paths the
    // grain and blur layers rely on.
    const candidates = [
      ...dirs.filter((d) => !d.includes('headless')).map((d) => join(root, d, 'chrome-linux', 'chrome')),
      ...dirs.filter((d) => d.includes('headless')).map((d) => join(root, d, 'chrome-linux', 'headless_shell')),
    ];
    const found = candidates.find((p) => existsSync(p));
    if (found) return found;
  }

  for (const p of [
    '/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome',
    '/usr/bin/google-chrome-stable', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  ]) {
    if (existsSync(p)) return p;
  }
  return undefined;
}
