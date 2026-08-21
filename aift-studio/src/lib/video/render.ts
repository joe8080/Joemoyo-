import { spawn } from 'node:child_process';
import { mkdtemp, rm, stat, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { chromium, type Browser, type Page } from 'playwright-core';
import { resolveChromiumPath } from './chromium';
import { resolveFfmpegPath } from './ffmpeg';

/**
 * Frame-exact renderer.
 *
 * The page is loaded once and then *seeked*, frame by frame, into a JPEG stream
 * piped straight to ffmpeg. Nothing touches disk between Chromium and the
 * encoder, and no frame depends on how long the previous one took — a slow
 * machine produces the same file as a fast one, just later.
 *
 * There is deliberately no upload step anywhere in this module. It writes a file
 * and returns its path.
 */

export type RenderOptions = {
  html: string;
  width: number;
  height: number;
  fps: number;
  totalMs: number;
  audioWav: Uint8Array | null;
  outPath: string;
  crf?: number;
  preset?: string;
  jpegQuality?: number;
  onProgress?: (frame: number, total: number) => void;
};

export type RenderResult = {
  path: string;
  bytes: number;
  frames: number;
  durationSeconds: number;
  encoder: string;
};

export async function renderVideo(opts: RenderOptions): Promise<RenderResult> {
  const executablePath = resolveChromiumPath();
  if (!executablePath) {
    throw new Error(
      'No Chromium binary found. Set AIFT_CHROMIUM_PATH, or install one with `npx playwright install chromium`.',
    );
  }

  const ffmpegPath = resolveFfmpegPath();
  const frames = Math.max(1, Math.round((opts.totalMs / 1000) * opts.fps));
  const workdir = await mkdtemp(join(tmpdir(), 'aift-render-'));
  const audioPath = join(workdir, 'narration.wav');
  if (opts.audioWav) await writeFile(audioPath, opts.audioWav);

  const args = [
    '-hide_banner', '-loglevel', 'error', '-y',
    '-f', 'image2pipe', '-framerate', String(opts.fps), '-i', 'pipe:0',
    ...(opts.audioWav ? ['-i', audioPath] : []),
    '-map', '0:v:0',
    ...(opts.audioWav ? ['-map', '1:a:0'] : []),
    '-c:v', 'libx264',
    '-preset', opts.preset ?? 'medium',
    '-crf', String(opts.crf ?? 19),
    '-pix_fmt', 'yuv420p',
    '-profile:v', 'high',
    '-level', '4.2',
    '-g', String(opts.fps * 2),
    '-movflags', '+faststart',
    ...(opts.audioWav ? ['-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2'] : []),
    '-shortest',
    opts.outPath,
  ];

  const ff = spawn(ffmpegPath, args, { stdio: ['pipe', 'inherit', 'pipe'] });
  let ffErr = '';
  ff.stderr.on('data', (c: Buffer) => { ffErr += c.toString(); });

  const ffDone = new Promise<void>((resolve, reject) => {
    ff.on('error', reject);
    ff.on('close', (code) => (code === 0 ? resolve() : reject(new Error(`ffmpeg exited ${code}: ${ffErr.slice(-4000)}`))));
  });

  let browser: Browser | null = null;
  try {
    browser = await chromium.launch({
      executablePath,
      args: [
        '--force-device-scale-factor=1',
        '--disable-lcd-text',
        '--font-render-hinting=none',
        '--hide-scrollbars',
        '--disable-dev-shm-usage',
        // Determinism: no smooth-scroll or occlusion heuristics between seeks.
        '--disable-features=PaintHolding,IntensiveWakeUpThrottling',
      ],
    });
    const page: Page = await browser.newPage({
      viewport: { width: opts.width, height: opts.height },
      deviceScaleFactor: 1,
      reducedMotion: 'reduce',
    });

    await page.setContent(opts.html, { waitUntil: 'load' });
    await page.waitForFunction('window.__ready === true', undefined, { timeout: 30_000 });
    // Let webfonts and the grain layer settle before the first capture.
    await page.evaluate(() => document.fonts?.ready);

    const step = 1000 / opts.fps;
    for (let f = 0; f < frames; f += 1) {
      const t = Math.round(f * step);
      await page.evaluate((ms) => {
        (window as unknown as { __seek: (n: number) => void }).__seek(ms);
      }, t);
      const buf = await page.screenshot({ type: 'jpeg', quality: opts.jpegQuality ?? 92 });
      if (!ff.stdin.write(buf)) {
        await new Promise<void>((resolve) => ff.stdin.once('drain', resolve));
      }
      if (opts.onProgress && (f % 30 === 0 || f === frames - 1)) opts.onProgress(f + 1, frames);
    }

    ff.stdin.end();
    await ffDone;
  } finally {
    await browser?.close().catch(() => undefined);
    await rm(workdir, { recursive: true, force: true });
  }

  const info = await stat(opts.outPath);
  return {
    path: opts.outPath,
    bytes: info.size,
    frames,
    durationSeconds: frames / opts.fps,
    encoder: `libx264 crf${opts.crf ?? 19} ${opts.preset ?? 'medium'}`,
  };
}

/** Single-frame capture, used for thumbnails and the review-room poster image. */
export async function renderStill(opts: {
  html: string; width: number; height: number; atMs: number; outPath: string;
}): Promise<{ path: string; bytes: number }> {
  const executablePath = resolveChromiumPath();
  if (!executablePath) throw new Error('No Chromium binary found for still capture.');

  const browser = await chromium.launch({ executablePath, args: ['--force-device-scale-factor=1', '--hide-scrollbars'] });
  try {
    const page = await browser.newPage({ viewport: { width: opts.width, height: opts.height }, deviceScaleFactor: 1 });
    await page.setContent(opts.html, { waitUntil: 'load' });
    await page.waitForFunction('window.__ready === true', undefined, { timeout: 30_000 });
    await page.evaluate((ms) => {
      (window as unknown as { __seek: (n: number) => void }).__seek(ms);
    }, opts.atMs);
    await page.screenshot({ path: opts.outPath, type: 'png' });
  } finally {
    await browser.close().catch(() => undefined);
  }
  const info = await stat(opts.outPath);
  return { path: opts.outPath, bytes: info.size };
}
