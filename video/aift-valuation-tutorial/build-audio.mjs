/**
 * Assembles the final audio bed and emits timing.json, which the composition
 * reads to place every chapter against the real voiceover.
 *
 *   node build-audio.mjs
 *
 * Output:
 *   assets/audio/narration.wav  — VO parts concatenated with the gaps below
 *   assets/audio/final-mix.wav  — narration + music ducked underneath
 *   timing.json                 — per-part start/end, used by build.mjs
 */
import { execSync } from "node:child_process";
import { writeFileSync } from "node:fs";

const A = "assets/audio";
const PARTS = Array.from({ length: 10 }, (_, i) => `vo-${String(i + 1).padStart(2, "0")}`);

const LEAD_IN = 5.0; // title card before the first word
const TAIL = 13.0; // outro card after the last word

/**
 * Silence AFTER each part. These are not padding — each one sits on a beat
 * where the viewer needs to read something before the narration moves on.
 */
const GAP_AFTER = {
  "vo-01": 4.0,
  "vo-02": 12.0, // the #VALUE! cascade — let it land
  "vo-03": 6.0,
  "vo-04": 5.0,
  "vo-05": 6.0,
  "vo-06": 14.0, // the all-negative FCF row — the hardest beat in the video
  "vo-07": 13.0, // Gordon vs exit multiple, side by side
  "vo-08": 8.0,
  "vo-09": 12.0, // sensitivity table filling in
  "vo-10": 0,
};

function dur(f) {
  return parseFloat(
    execSync(`ffprobe -v error -show_entries format=duration -of csv=p=0 ${f}`).toString().trim(),
  );
}

const parts = PARTS.map((p) => ({ id: p, file: `${A}/${p}.mp3`, dur: dur(`${A}/${p}.mp3`) }));

let t = LEAD_IN;
for (const p of parts) {
  p.start = round(t);
  p.end = round(t + p.dur);
  p.gapAfter = GAP_AFTER[p.id] ?? 4;
  t = p.end + p.gapAfter;
}
const TOTAL = round(t + TAIL - (parts.at(-1).gapAfter ?? 0));

function round(n) {
  return Math.round(n * 1000) / 1000;
}

// --- narration: each part padded with its trailing silence, then concatenated
const filters = [];
parts.forEach((p, i) => {
  filters.push(`[${i}:a]aresample=44100,aformat=sample_fmts=s16:channel_layouts=stereo,apad=pad_dur=${p.gapAfter}[p${i}]`);
});
const inputs = parts.map((p) => `-i ${p.file}`).join(" ");
const concat = parts.map((_, i) => `[p${i}]`).join("") + `concat=n=${parts.length}:v=0:a=1[cat]`;
// lead-in silence in front
filters.push(concat);
filters.push(`[cat]adelay=${Math.round(LEAD_IN * 1000)}|${Math.round(LEAD_IN * 1000)},apad=whole_dur=${TOTAL}[narr]`);

execSync(
  `ffmpeg -y -loglevel error ${inputs} -filter_complex "${filters.join(";")}" -map "[narr]" -c:a pcm_s16le ${A}/narration.wav`,
  { stdio: "inherit" },
);

// --- mix: music ducked under the narration via sidechain compression
execSync(
  `ffmpeg -y -loglevel error -i ${A}/narration.wav -i ${A}/music-bed-loop.wav ` +
    `-filter_complex "` +
    `[0:a]aformat=sample_fmts=s16:sample_rates=44100:channel_layouts=stereo,volume=1.0[vo];` +
    `[1:a]aformat=sample_fmts=s16:sample_rates=44100:channel_layouts=stereo,atrim=0:${TOTAL},volume=0.16[bed];` +
    `[vo]asplit=2[vo1][vokey];` +
    `[bed][vokey]sidechaincompress=threshold=0.04:ratio=8:attack=15:release=700:makeup=1[duck];` +
    `[vo1][duck]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,` +
    `afade=t=in:st=0:d=1.5,afade=t=out:st=${round(TOTAL - 2.5)}:d=2.5,alimiter=limit=0.95[out]"` +
    ` -map "[out]" -c:a pcm_s16le ${A}/final-mix.wav`,
  { stdio: "inherit" },
);

writeFileSync(
  "timing.json",
  JSON.stringify({ total: TOTAL, leadIn: LEAD_IN, tail: TAIL, parts }, null, 2),
);

console.log(`narration ${round(parts.reduce((s, p) => s + p.dur, 0))}s`);
console.log(`total     ${TOTAL}s  (${Math.floor(TOTAL / 60)}m ${Math.round(TOTAL % 60)}s)`);
parts.forEach((p) => console.log(`  ${p.id}  ${p.start.toFixed(1)} → ${p.end.toFixed(1)}  (+${p.gapAfter}s)`));
