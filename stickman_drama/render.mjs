#!/usr/bin/env node
// Render an episode script to a vertical 1080x1920 MP4 (video + synthesised audio).
//   node render.mjs episodes/ep1-the-loan.mjs            -> out/ep1-the-loan.mp4
//   node render.mjs episodes/ep1-the-loan.mjs --stills 1,5,9   -> out/stills/*.jpg (quick look, no video)
//   node render.mjs all                                   -> every episode in episodes/
import { createRequire } from 'node:module';
import { spawn, execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, readdirSync, rmSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { compile } from './compile.mjs';
import { renderAudio } from './audio.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const { chromium } = createRequire(import.meta.url)('playwright');
const FPS = 30;

const args = process.argv.slice(2);
const stillsAt = args.includes('--stills') ? args[args.indexOf('--stills') + 1].split(',').map(Number) : null;
let files = args.filter((a, i) => !a.startsWith('--') && args[i - 1] !== '--stills');
if (!files.length || files[0] === 'all')
  files = readdirSync(join(here, 'episodes')).filter((f) => f.endsWith('.mjs')).sort().map((f) => join(here, 'episodes', f));

const out = join(here, 'out');
mkdirSync(join(out, 'stills'), { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
page.on('pageerror', (e) => { console.error('PAGE ERROR:', e.message); process.exitCode = 1; });
await page.setContent('<html><body style="margin:0;background:#000"><canvas id="c" width="1080" height="1920"></canvas></body></html>');
await page.addScriptTag({ content: readFileSync(join(here, 'engine.js'), 'utf8') });
await page.evaluate(() => document.fonts.load('900 40px Inter'));

// Recorded voice lines for an episode: voice/<id>/<speaker>-<nn>.wav
// -> samples for the mix, plus a 30fps loudness curve that drives the lip-sync.
function loadVoices(id) {
  const dir = join(here, 'voice', id), voices = {};
  if (!existsSync(dir)) return voices;
  for (const f of readdirSync(dir).filter((f) => f.endsWith('.wav'))) {
    const raw = execFileSync('ffmpeg', ['-loglevel', 'error', '-i', join(dir, f), '-f', 'f32le', '-ac', '1', '-ar', '44100', '-'], { maxBuffer: 1 << 28 });
    const pcm = new Float32Array(raw.buffer, raw.byteOffset, Math.floor(raw.byteLength / 4)).slice();
    let peak = 0; for (const v of pcm) peak = Math.max(peak, Math.abs(v));
    for (let i = 0; i < pcm.length; i++) pcm[i] *= 0.85 / (peak || 1);
    const win = 44100 / FPS, rms = [];
    for (let i = 0; i < pcm.length; i += win) { let a = 0, n = 0; for (let j = Math.floor(i); j < i + win && j < pcm.length; j++) { a += pcm[j] * pcm[j]; n++; } rms.push(Math.sqrt(a / (n || 1))); }
    const ref = [...rms].sort((a, b) => a - b)[Math.floor(rms.length * 0.9)] || 1;
    let prev = 0;
    const env = rms.map((v) => { const x = Math.min(1, v / ref); prev = x > prev ? x : prev * 0.55 + x * 0.45; return +(prev < 0.1 ? 0 : prev).toFixed(2); });
    const wj = join(dir, f.replace('.wav', '.json'));
    voices[f.replace('.wav', '')] = { dur: pcm.length / 44100, env, pcm, words: existsSync(wj) ? JSON.parse(readFileSync(wj, 'utf8')) : null };
  }
  return voices;
}

const frame = async (t, q = 0.92) =>
  Buffer.from((await page.evaluate(([t, q]) => { window.drawFrame(t); return document.getElementById('c').toDataURL('image/jpeg', q).slice(23); }, [t, q])), 'base64');

for (const file of files) {
  const ep = (await import(pathToFileURL(resolve(file)).href)).default;
  const voices = loadVoices(ep.id);
  const tl = compile(ep, Object.fromEntries(Object.entries(voices).map(([k, v]) => [k, { dur: v.dur, env: v.env, words: v.words }])));
  await page.evaluate((tl) => { window.TL = tl; }, tl);
  console.log(`\n▶ ${ep.id} — ${tl.duration.toFixed(1)}s, ${tl.shots.length} shots, ${Object.keys(voices).length} voice lines`);

  if (stillsAt) {
    const { writeFileSync } = await import('node:fs');
    for (const t of stillsAt) writeFileSync(join(out, 'stills', `${ep.id}-${t.toFixed(1).padStart(5, '0')}.jpg`), await frame(t, 0.8));
    continue;
  }

  const wav = join(out, `${ep.id}.wav`), mp4 = join(out, `${ep.id}.mp4`);
  renderAudio(tl, wav, voices);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-', '-i', wav,
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '23', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', mp4],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((ok, bad) => ff.on('close', (c) => (c ? bad(new Error('ffmpeg exit ' + c)) : ok())));
  const total = Math.ceil(tl.duration * FPS);
  for (let i = 0; i < total; i++) {
    if (!ff.stdin.write(await frame(i / FPS))) await new Promise((r) => ff.stdin.once('drain', r));
    if (i % 150 === 0) process.stdout.write(`  frame ${i}/${total}\r`);
  }
  ff.stdin.end();
  await done;
  rmSync(wav);
  // poster frame for the thumbnail (first big reaction ~1s in)
  (await import('node:fs')).writeFileSync(join(out, `${ep.id}.jpg`), await frame(Math.min(1.2, tl.duration / 2)));
  console.log(`  ✔ ${mp4}`);
}
await browser.close();
