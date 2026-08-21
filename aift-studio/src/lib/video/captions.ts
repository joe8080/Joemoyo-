import type { ScenePlan, Script } from '@/lib/schemas/content';
import type { CaptionLine, CaptionWord } from './compose';

/**
 * Caption timing.
 *
 * Word timings are distributed across the measured clip length by weight —
 * longer words and words carrying punctuation hold longer — which is what makes
 * the on-screen highlight track speech instead of sliding uniformly through it.
 * The same timeline drives the burnt-in captions and the SRT file, so the two
 * can never disagree.
 */

const LEAD_IN_MS = 260;

export function buildCaptionTimeline(
  script: Script,
  plan: ScenePlan,
  narrationSeconds: Map<string, number>,
): CaptionLine[] {
  const lines: CaptionLine[] = [];

  for (const scene of plan.scenes) {
    const beatId = scene.beat_ids[0];
    if (!beatId) continue;
    const beat = script.beats.find((b) => b.beat_id === beatId);
    if (!beat) continue;

    const spokenMs = Math.round((narrationSeconds.get(beatId) ?? 0) * 1000);
    if (spokenMs <= 0) continue;

    const start = scene.start_ms + LEAD_IN_MS;
    const tokens = beat.narration.trim().split(/\s+/u).filter(Boolean);
    if (tokens.length === 0) continue;

    const weights = tokens.map((t) => t.length + (/[.,;:!?—]/u.test(t) ? 3.2 : 0.6));
    const total = weights.reduce((a, b) => a + b, 0);

    let cursor = start;
    const words: CaptionWord[] = tokens.map((w, i) => {
      const span = (weights[i]! / total) * spokenMs;
      const word = { w, start: Math.round(cursor), end: Math.round(cursor + span) };
      cursor += span;
      return word;
    });

    // The planner guarantees the scene is long enough, but a caption that runs
    // past its cut produces an SRT whose cues go backwards — worth making
    // impossible here too rather than only upstream.
    const limit = scene.start_ms + scene.duration_ms;
    for (const w of words) {
      w.start = Math.min(w.start, limit);
      w.end = Math.min(w.end, limit);
    }
    lines.push({ beatId, start, end: Math.min(Math.round(cursor), limit), words });
  }

  return lines;
}

/**
 * SRT built by grouping the word timeline into readable cues — at most two
 * lines of ~42 characters, broken at punctuation where possible.
 */
export function toSrt(lines: CaptionLine[], maxChars = 84): string {
  const cues: Array<{ start: number; end: number; text: string }> = [];

  for (const line of lines) {
    let buf: CaptionWord[] = [];
    const flush = () => {
      if (buf.length === 0) return;
      cues.push({ start: buf[0]!.start, end: buf[buf.length - 1]!.end, text: wrap(buf.map((w) => w.w).join(' ')) });
      buf = [];
    };
    for (const word of line.words) {
      buf.push(word);
      const len = buf.reduce((n, w) => n + w.w.length + 1, 0);
      const breakable = /[.!?]$/u.test(word.w) || (/[,;:—]$/u.test(word.w) && len > maxChars * 0.6);
      if (len >= maxChars || breakable) flush();
    }
    flush();
  }

  return cues
    .map((c, i) => `${i + 1}\n${stamp(c.start)} --> ${stamp(Math.max(c.end, c.start + 700))}\n${c.text}\n`)
    .join('\n');
}

function wrap(text: string): string {
  if (text.length <= 42) return text;
  const words = text.split(' ');
  const mid = Math.ceil(words.length / 2);
  return `${words.slice(0, mid).join(' ')}\n${words.slice(mid).join(' ')}`;
}

function stamp(ms: number): string {
  const t = Math.max(0, Math.round(ms));
  const h = Math.floor(t / 3_600_000);
  const m = Math.floor((t % 3_600_000) / 60_000);
  const s = Math.floor((t % 60_000) / 1000);
  const milli = t % 1000;
  const p = (n: number, w: number) => String(n).padStart(w, '0');
  return `${p(h, 2)}:${p(m, 2)}:${p(s, 2)},${p(milli, 3)}`;
}

export function toChaptersJson(script: Script, plan: ScenePlan): string {
  const chapters = script.chapters.map((c) => {
    const beatIndex = script.beats.findIndex((b) => b.beat_id === c.start_beat);
    const scene = plan.scenes[Math.max(0, beatIndex)];
    return { title: c.title, start_ms: scene?.start_ms ?? 0, start_timecode: youtubeStamp(scene?.start_ms ?? 0) };
  });
  return JSON.stringify({ total_ms: plan.total_ms, chapters }, null, 2);
}

export function youtubeStamp(ms: number): string {
  const t = Math.max(0, Math.round(ms / 1000));
  const m = Math.floor(t / 60);
  const s = t % 60;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}
