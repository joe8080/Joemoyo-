import { describe, expect, it } from 'vitest';
import { execFile } from 'node:child_process';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { promisify } from 'node:util';
import { renderVideo } from '@/lib/video/render';
import { resolveChromiumPath } from '@/lib/video/chromium';
import { resolveFfmpegPath } from '@/lib/video/ffmpeg';
import { assembleNarration } from '@/lib/video/audio';
import { MockVoiceProvider } from '@/lib/providers/voice/mock';
import { sha256 } from '@/lib/util/hash';

const run = promisify(execFile);
const haveChromium = Boolean(resolveChromiumPath());

/**
 * A frame is meant to be a pure function of time. Everything the visual gates
 * claim rests on that, so it is worth proving rather than asserting: render the
 * same clip on one worker and on three, and compare the pixels.
 *
 * Skipped when no Chromium is installed, rather than failing a machine that
 * simply cannot run it.
 */
const maybe = haveChromium ? describe : describe.skip;

const HTML = `<!doctype html><html><head><style>
html,body{margin:0;width:320px;height:180px;background:#07090d;color:#fff;font-family:sans-serif}
#t{position:absolute;top:60px;left:20px;font-size:28px;font-weight:800}
</style></head><body><div id="t">0</div>
<script>
window.__seek=function(t){document.getElementById('t').textContent='f'+Math.round(t/1000*30);
document.body.style.background='hsl('+((t/30)%360)+' 40% 8%)';};
window.__ready=true;__seek(0);
</script></body></html>`;

async function frameHash(video: string, n: number, dir: string): Promise<string> {
  const out = join(dir, `f${n}.png`);
  await run(resolveFfmpegPath(), [
    '-hide_banner', '-loglevel', 'error', '-y', '-i', video,
    '-vf', `select=eq(n\\,${n})`, '-vframes', '1', out,
  ]);
  return sha256(new Uint8Array(await readFile(out)));
}

maybe('the render engine', () => {
  it('produces identical pixels on one worker and on three', async () => {
    const dir = await mkdtemp(join(tmpdir(), 'aift-render-test-'));
    try {
      const clip = await new MockVoiceProvider().speak({ text: 'x', voice: 'en-gb', targetSeconds: 8 });
      const audio = assembleNarration([{ wav: clip.wav, startMs: 0 }], 8000);
      const base = {
        html: HTML, width: 320, height: 180, fps: 30, totalMs: 8000,
        audioWav: audio, crf: 18, preset: 'ultrafast' as const,
      };

      const single = join(dir, 'single.mp4');
      const parallel = join(dir, 'parallel.mp4');
      const a = await renderVideo({ ...base, outPath: single, workers: 1 });
      const b = await renderVideo({ ...base, outPath: parallel, workers: 3 });

      expect(a.frames).toBe(b.frames);
      expect(a.encoder).toContain('×1');
      expect(b.encoder).toContain('×3');

      // Frames either side of every segment boundary, plus the ends.
      for (const n of [0, 79, 80, 159, 160, 239]) {
        expect(await frameHash(parallel, n, dir), `frame ${n} differs between one worker and three`)
          .toBe(await frameHash(single, n, dir));
      }
    } finally {
      await rm(dir, { recursive: true, force: true });
    }
  }, 300_000);

  it('writes a real H.264 + AAC container', async () => {
    const dir = await mkdtemp(join(tmpdir(), 'aift-render-test-'));
    try {
      const clip = await new MockVoiceProvider().speak({ text: 'x', voice: 'en-gb', targetSeconds: 2 });
      const out = join(dir, 'clip.mp4');
      const result = await renderVideo({
        html: HTML, width: 320, height: 180, fps: 30, totalMs: 2000,
        audioWav: assembleNarration([{ wav: clip.wav, startMs: 0 }], 2000),
        outPath: out, workers: 1, preset: 'ultrafast',
      });
      expect(result.bytes).toBeGreaterThan(1000);

      const info = await run(resolveFfmpegPath(), ['-hide_banner', '-i', out]).catch(
        (e: { stderr?: string }) => ({ stderr: e.stderr ?? '' }),
      );
      expect(info.stderr).toContain('Video: h264');
      expect(info.stderr).toContain('Audio: aac');
      expect(info.stderr).toContain('320x180');
    } finally {
      await rm(dir, { recursive: true, force: true });
    }
  }, 180_000);
});

describe('render engine configuration', () => {
  it('finds a Chromium and an ffmpeg on this machine, or says so plainly', () => {
    // Not an assertion about the environment — a readable statement of it, so a
    // skipped render test above is explained rather than mysterious.
    const chromium = resolveChromiumPath();
    const ffmpeg = resolveFfmpegPath();
    expect(typeof ffmpeg).toBe('string');
    if (!chromium) {
      console.warn('No Chromium found; render tests were skipped. Set AIFT_CHROMIUM_PATH or run `npx playwright install chromium`.');
    }
    expect(chromium === undefined || chromium.length > 0).toBe(true);
  });
});
