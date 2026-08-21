/**
 * Verifies a produced content pack by inspecting the files themselves.
 *
 * The quality gates check the pipeline's own record of what it did. This checks
 * the artefacts on disk — the container, the streams, the caption timing, the
 * hashes — which is the difference between "the render reported success" and
 * "the file is a valid, playable, captioned video".
 *
 *   npm run verify:pack -- .artifacts/<user>/<job>/deep_dive
 */
import { execFile } from 'node:child_process';
import { readFile, readdir, stat } from 'node:fs/promises';
import { join } from 'node:path';
import { promisify } from 'node:util';
import { resolveFfmpegPath } from '@/lib/video/ffmpeg';
import { sha256 } from '@/lib/util/hash';

const run = promisify(execFile);

const dirArg = process.argv[2];
if (!dirArg) {
  console.error('usage: npm run verify:pack -- <pack directory>');
  process.exit(1);
}
const dir: string = dirArg;

type Check = { name: string; ok: boolean; detail: string };
const checks: Check[] = [];
const add = (name: string, ok: boolean, detail: string) => { checks.push({ name, ok, detail }); };

async function probe(path: string): Promise<string> {
  // ffmpeg-static ships ffmpeg but not ffprobe; `-i` with no output writes the
  // stream summary to stderr and exits non-zero, which is expected here.
  try {
    const { stderr } = await run(resolveFfmpegPath(), ['-hide_banner', '-i', path]);
    return stderr;
  } catch (e) {
    return (e as { stderr?: string }).stderr ?? '';
  }
}

async function main(): Promise<void> {
  const files = await readdir(dir);
  const manifestName = files.find((f) => f === 'manifest.json');
  add('manifest present', Boolean(manifestName), manifestName ?? 'manifest.json is missing');

  const required = ['script.md', 'scene_plan.json', 'captions.srt', 'description.md',
    'source_manifest.json', 'thumbnail_brief.json', 'quality_report.md', 'composition.html'];
  for (const f of required) {
    const present = files.includes(f);
    const size = present ? (await stat(join(dir, f))).size : 0;
    add(`${f}`, present && size > 50, present ? `${size} bytes` : 'missing');
  }

  // --- hashes match the manifest -------------------------------------------
  if (manifestName) {
    const manifest = JSON.parse(await readFile(join(dir, manifestName), 'utf8')) as {
      assets: Array<{ type: string; key: string; sha256: string; bytes: number }>;
      aspect_ratio: string; duration_seconds: number;
    };
    let mismatched = 0;
    for (const a of manifest.assets) {
      const name = a.key.split('/').slice(-1)[0]!;
      const path = join(dir, ...a.key.split('/').slice(-2, -1).filter((p) => p !== name), name);
      const bytes = await readFile(path).catch(() => null);
      if (!bytes) continue;
      if (sha256(new Uint8Array(bytes)) !== a.sha256) mismatched += 1;
    }
    add('asset hashes match the manifest', mismatched === 0, `${mismatched} mismatch(es)`);

    // --- the video itself ---------------------------------------------------
    const video = files.find((f) => f.endsWith('.mp4'));
    if (video) {
      const info = await probe(join(dir, video));
      const v = /Video: (\w+).*?, (\d+)x(\d+)/su.exec(info);
      const a = /Audio: (\w+).*?(\d+) Hz/su.exec(info);
      const d = /Duration: (\d+):(\d+):(\d+\.\d+)/u.exec(info);

      add('video stream is H.264', v?.[1] === 'h264', v?.[1] ?? 'no video stream found');
      add('audio stream is AAC', a?.[1] === 'aac', a?.[1] ?? 'no audio stream found');

      if (v) {
        const w = Number(v[2]);
        const h = Number(v[3]);
        const ratio = (w / h).toFixed(3);
        const expected = manifest.aspect_ratio === '9:16' ? (9 / 16).toFixed(3) : (16 / 9).toFixed(3);
        add('aspect ratio matches the manifest', ratio === expected, `${w}×${h} (${ratio}, expected ${expected})`);
      }
      if (d) {
        const seconds = Number(d[1]) * 3600 + Number(d[2]) * 60 + Number(d[3]);
        const drift = Math.abs(seconds - manifest.duration_seconds);
        add('duration matches the scene plan', drift < 1.5, `${seconds.toFixed(2)}s vs ${manifest.duration_seconds.toFixed(2)}s planned`);
      }

      // --- captions cover the runtime ---------------------------------------
      const srt = await readFile(join(dir, 'captions.srt'), 'utf8').catch(() => '');
      const stamps = [...srt.matchAll(/(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> /gu)]
        .map((m) => Number(m[1]) * 3600 + Number(m[2]) * 60 + Number(m[3]) + Number(m[4]) / 1000);
      const last = stamps[stamps.length - 1] ?? 0;
      add('captions span the video', stamps.length > 0 && last <= manifest.duration_seconds,
        `${stamps.length} cues, last at ${last.toFixed(1)}s of ${manifest.duration_seconds.toFixed(1)}s`);
      add('caption cues are in order',
        stamps.every((s, i) => i === 0 || s >= stamps[i - 1]!), `${stamps.length} cues`);
    } else {
      add('rendered video present', false, 'no .mp4 in the pack');
    }
  }

  // --- the report says what the gates found --------------------------------
  const report = await readFile(join(dir, 'quality_report.md'), 'utf8').catch(() => '');
  add('quality report states a verdict', /\*\*Verdict:\*\*/u.test(report),
    report.split('\n').find((l) => l.includes('Verdict')) ?? 'no verdict line');

  const failed = checks.filter((c) => !c.ok);
  const pad = Math.max(...checks.map((c) => c.name.length));
  console.log(`\nPack: ${dir}\n`);
  for (const c of checks) {
    console.log(`  ${c.ok ? '✓' : '✗'} ${c.name.padEnd(pad)}  ${c.detail}`);
  }
  console.log(`\n${checks.length - failed.length}/${checks.length} checks passed\n`);
  if (failed.length > 0) process.exitCode = 1;
}

main().catch((e: unknown) => { console.error(e); process.exitCode = 1; });
