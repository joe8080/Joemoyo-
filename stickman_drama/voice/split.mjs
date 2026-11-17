#!/usr/bin/env node
// Splits each character's voice track (one take per character per episode, lines separated by long pauses)
// into one WAV per line: voice/<episode>/<speaker>-<nn>.wav
// Picks whichever take (…-a.mp3 / …-b.mp3) has the cleanest separation between lines.
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const epDir = join(here, '..', 'episodes');

function gaps(file) {
  let out = '';
  try { execFileSync('ffmpeg', ['-hide_banner', '-i', file, '-af', 'silencedetect=noise=-38dB:d=0.2', '-f', 'null', '-'], { stdio: ['ignore', 'ignore', 'pipe'] }); }
  catch (e) { out = String(e.stderr); }
  // ffmpeg writes to stderr even on success
  if (!out) out = execFileSync('sh', ['-c', `ffmpeg -hide_banner -i "${file}" -af silencedetect=noise=-38dB:d=0.2 -f null - 2>&1`]).toString();
  const starts = [...out.matchAll(/silence_start: ([\d.]+)/g)].map((m) => +m[1]);
  const ends = [...out.matchAll(/silence_end: ([\d.]+)/g)].map((m) => +m[1]);
  const dur = +execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', file]).toString();
  return { dur, gaps: starts.map((s, i) => ({ s, e: ends[i] ?? dur })) };
}

for (const f of readdirSync(epDir).filter((f) => f.endsWith('.mjs')).sort()) {
  const ep = (await import(pathToFileURL(join(epDir, f)).href)).default;
  const lines = {};
  for (const shot of ep.shots) for (const b of shot.beats || []) if (b.say) (lines[b.who === 'think' ? 'you' : b.who] ??= []).push(b.say.replace(/\*/g, ''));
  for (const [who, texts] of Object.entries(lines)) {
    const n = texts.length;
    let best = null;
    for (const take of ['a', 'b']) {
      const file = join(here, 'raw', `${ep.id}-${who}-${take}.mp3`);
      if (!existsSync(file)) continue;
      const g = gaps(file);
      const inner = g.gaps.filter((x) => x.s > 0.05 && x.e < g.dur - 0.05).sort((p, q) => q.e - q.s - (p.e - p.s));
      if (inner.length < n - 1) continue;
      const cut = inner.slice(0, n - 1), next = inner[n - 1];
      const margin = (cut.at(-1).e - cut.at(-1).s) / (next ? next.e - next.s : 0.2);
      if (!best || margin > best.margin) best = { file, take, margin, cut: cut.sort((p, q) => p.s - q.s), dur: g.dur, lead: g.gaps.find((x) => x.s <= 0.05)?.e ?? 0, tail: g.gaps.find((x) => x.e >= g.dur - 0.05)?.s ?? g.dur };
    }
    if (!best) { console.log(`✗ ${ep.id} ${who}: no usable take`); process.exitCode = 1; continue; }
    const bounds = [best.lead, ...best.cut.flatMap((c) => [c.s, c.e]), best.tail];
    mkdirSync(join(here, ep.id), { recursive: true });
    console.log(`\n${ep.id} · ${who} · take ${best.take} · separation ${best.margin.toFixed(1)}x`);
    for (let i = 0; i < n; i++) {
      const s = Math.max(0, bounds[i * 2] - 0.04), e = Math.min(best.dur, bounds[i * 2 + 1] + 0.1);
      const outFile = join(here, ep.id, `${who}-${String(i + 1).padStart(2, '0')}.wav`);
      execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-ss', String(s), '-to', String(e), '-i', best.file, '-ac', '1', '-ar', '44100', '-af', 'afade=t=in:d=0.02,areverse,afade=t=in:d=0.05,areverse', outFile]);
      // word-level timings (if the take has an alignment file) -> exact caption sync
      const wf = best.file.replace('.mp3', '.words.json');
      if (existsSync(wf)) {
        const ws = JSON.parse(readFileSync(wf, 'utf8')).words.filter((w) => !/^\[|\]$/.test(w.text) && /[\p{L}\p{N}]/u.test(w.text));
        const mine = ws.filter((w) => w.start >= s - 0.12 && w.start < e);
        writeFileSync(outFile.replace('.wav', '.json'), JSON.stringify(mine.map((w) => +Math.max(0, w.start - s).toFixed(3))));
      }
      const cps = texts[i].length / (e - s);
      console.log(`  ${String(i + 1).padStart(2)} ${(e - s).toFixed(2)}s ${cps.toFixed(0).padStart(3)} ch/s ${cps < 7 || cps > 26 ? '⚠' : ' '} ${texts[i]}`);
    }
  }
}
