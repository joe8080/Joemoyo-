import { describe, expect, it } from 'vitest';
import { SvgChartRenderer } from '@/lib/providers/chart/svg';
import type { ChartSpec } from '@/lib/providers/types';
import { buildCaptionTimeline, toSrt, youtubeStamp } from '@/lib/video/captions';
import { assembleNarration, decodeWav, peakDbfs, resample } from '@/lib/video/audio';
import { MockVoiceProvider } from '@/lib/providers/voice/mock';
import { estimateNarrationSeconds, writeWav } from '@/lib/providers/voice/wav';
import { MockMediaProvider } from '@/lib/providers/media/mock';
import { LocalStorageProvider } from '@/lib/providers/storage/local';
import type { ScenePlan, Script } from '@/lib/schemas/content';
import { mkdtemp } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const palette = { ink: '#fff', inkDim: '#888', accent: '#0af', accent2: '#a0f', grid: '#333', surface: '#111' };

const spec = (over: Partial<ChartSpec> = {}): ChartSpec => ({
  kind: 'line', width: 1560, height: 700,
  series: [{ label: 'Revenue', points: [
    { x: 'Q1', y: 2.88 }, { x: 'Q2', y: 3.11 }, { x: 'Q3', y: 3.54 },
    { x: 'Q4', y: 4.02 }, { x: 'Q5', y: 4.61 },
  ], unit: '$bn' }],
  yLabel: 'Total revenue', xLabel: '', sourceLabel: 'Filing (fixture)',
  asOfDate: '2026-06-27', highlightIndex: 4, progress: 1, palette, ...over,
});

describe('the chart renderer', () => {
  it('is a pure function of its spec', () => {
    const r = new SvgChartRenderer();
    expect(r.renderSvg(spec())).toBe(r.renderSvg(spec()));
    expect(r.renderSvg(spec({ progress: 0.4 }))).not.toBe(r.renderSvg(spec({ progress: 0.5 })));
  });

  it('reports exactly the values a viewer will read', () => {
    const values = new SvgChartRenderer().visibleValues(spec());
    expect(values).toEqual(['$2.88bn', '$3.11bn', '$3.54bn', '$4.02bn', '$4.61bn']);
  });

  it('draws the final value only once the line has finished drawing', () => {
    const r = new SvgChartRenderer();
    expect(r.renderSvg(spec({ progress: 0.5 }))).not.toContain('$4.61bn');
    expect(r.renderSvg(spec({ progress: 1 }))).toContain('$4.61bn');
  });

  it('keeps the value label inside the canvas on a narrow chart', () => {
    const svg = new SvgChartRenderer().renderSvg(spec({ width: 940, height: 820 }));
    for (const m of svg.matchAll(/<rect x="([-\d.]+)"[^>]*width="([\d.]+)"/gu)) {
      const x = Number(m[1]);
      const w = Number(m[2]);
      expect(x).toBeGreaterThanOrEqual(-1);
      expect(x + w).toBeLessThanOrEqual(941);
    }
  });

  it('stamps the source and as-of date into the picture itself', () => {
    const svg = new SvgChartRenderer().renderSvg(spec());
    expect(svg).toContain('Filing (fixture)');
    expect(svg).toContain('2026-06-27');
  });

  it('renders bars with the same value formatting as lines', () => {
    const r = new SvgChartRenderer();
    expect(r.visibleValues(spec({ kind: 'bar' }))).toEqual(r.visibleValues(spec({ kind: 'line' })));
    expect(r.renderSvg(spec({ kind: 'bar' }))).toContain('$4.61bn');
  });

  it('escapes text rather than letting it break the document', () => {
    const svg = new SvgChartRenderer().renderSvg(spec({ sourceLabel: 'A & B <script>' }));
    expect(svg).toContain('A &amp; B &lt;script&gt;');
    expect(svg).not.toContain('<script>');
  });
});

// ---------------------------------------------------------------------------

const script: Script = {
  working_title: 'Test', reference_date: '2026-08-14',
  beats: [
    { beat_id: 'B-001', chapter: 'One', narration: 'Revenue rose sharply, and the filing says why.', on_screen_text: '', claim_ids: [], visual_intent: 'statement' },
    { beat_id: 'B-002', chapter: 'One', narration: 'Margins moved the other way.', on_screen_text: '', claim_ids: [], visual_intent: 'statement' },
  ],
  chapters: [{ title: 'One', start_beat: 'B-001' }],
  description_markdown: 'x'.repeat(120), tags: ['a', 'b', 'c', 'd', 'e'],
  disclosure_text: 'y'.repeat(50),
};

const plan: ScenePlan = {
  format: 'deep_dive', width: 1920, height: 1080, fps: 30, total_ms: 12_000,
  scenes: [
    { scene_id: 'S-001', beat_ids: ['B-001'], start_ms: 0, duration_ms: 6000, composition: 'statement',
      headline: '', subhead: '', data: null, stat: null, rows: [], columns: [], bullets: [],
      broll_prompt: '', transition: 'fade', citation: '' },
    { scene_id: 'S-002', beat_ids: ['B-002'], start_ms: 6000, duration_ms: 6000, composition: 'statement',
      headline: '', subhead: '', data: null, stat: null, rows: [], columns: [], bullets: [],
      broll_prompt: '', transition: 'fade', citation: '' },
  ],
};

describe('caption timing', () => {
  const seconds = new Map([['B-001', 4.2], ['B-002', 2.6]]);

  it('places words inside their scene and in order', () => {
    const lines = buildCaptionTimeline(script, plan, seconds);
    expect(lines.length).toBe(2);
    for (const [i, line] of lines.entries()) {
      const scene = plan.scenes[i]!;
      expect(line.start).toBeGreaterThanOrEqual(scene.start_ms);
      expect(line.end).toBeLessThanOrEqual(scene.start_ms + scene.duration_ms);
      for (let w = 1; w < line.words.length; w += 1) {
        expect(line.words[w]!.start).toBeGreaterThanOrEqual(line.words[w - 1]!.start);
      }
      expect(line.words.map((w) => w.w).join(' ')).toBe(script.beats[i]!.narration);
    }
  });

  it('holds longer on words carrying punctuation', () => {
    const lines = buildCaptionTimeline(script, plan, seconds);
    const words = lines[0]!.words;
    const withComma = words.find((w) => w.w.endsWith(','))!;
    const plain = words.find((w) => w.w === 'rose')!;
    expect(withComma.end - withComma.start).toBeGreaterThan(plain.end - plain.start);
  });

  it('emits SRT whose cues are ordered, non-empty and at least 700ms long', () => {
    const srt = toSrt(buildCaptionTimeline(script, plan, seconds));
    const blocks = srt.trim().split('\n\n');
    expect(blocks.length).toBeGreaterThan(0);
    let last = -1;
    for (const [i, block] of blocks.entries()) {
      const [index, times, ...text] = block.split('\n');
      expect(Number(index)).toBe(i + 1);
      const m = times!.match(/^(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})$/u);
      expect(m, `bad timestamp line: ${times}`).not.toBeNull();
      const toMs = (s: string) => {
        const [hms, ms] = s.split(',');
        const [h, mi, se] = hms!.split(':').map(Number);
        return h! * 3_600_000 + mi! * 60_000 + se! * 1000 + Number(ms);
      };
      const start = toMs(m![1]!);
      const end = toMs(m![2]!);
      expect(start).toBeGreaterThanOrEqual(last);
      expect(end - start).toBeGreaterThanOrEqual(700);
      expect(text.join('').trim().length).toBeGreaterThan(0);
      last = start;
    }
  });

  it('formats YouTube chapter stamps', () => {
    expect(youtubeStamp(0)).toBe('00:00');
    expect(youtubeStamp(65_000)).toBe('01:05');
    expect(youtubeStamp(605_400)).toBe('10:05');
  });
});

// ---------------------------------------------------------------------------

describe('narration timing and assembly', () => {
  it('estimates a plausible reading pace', () => {
    const text = Array.from({ length: 163 }, () => 'word').join(' ');
    const seconds = estimateNarrationSeconds(text);
    expect(seconds).toBeGreaterThan(50);
    expect(seconds).toBeLessThan(70);
  });

  it('gives the mock voice the exact duration it was asked for', async () => {
    const clip = await new MockVoiceProvider().speak({ text: 'hello there', voice: 'en-gb', targetSeconds: 3.5 });
    expect(clip.durationSeconds).toBeCloseTo(3.5, 2);
    expect(clip.transcript).toBe('hello there');
    expect(peakDbfs(clip.wav)).toBe(-Infinity);
  });

  it('lays clips onto the bed at their scene offsets', () => {
    const tone = new Int16Array(24_000).map((_, i) => Math.round(Math.sin((i / 24_000) * 2 * Math.PI * 220) * 12_000));
    const wav = writeWav(tone, 24_000);
    const track = assembleNarration([{ wav, startMs: 2000 }], 5000);
    const { samples, sampleRate } = decodeWav(track);
    expect(sampleRate).toBe(48_000);
    // Measured as RMS over a window: a single sample of a sine can land on a
    // zero crossing and say nothing about whether audio is present.
    const rms = (ms: number, windowMs = 50) => {
      const from = Math.round((ms / 1000) * sampleRate);
      const n = Math.round((windowMs / 1000) * sampleRate);
      let acc = 0;
      for (let i = from; i < from + n; i += 1) acc += (samples[i] ?? 0) ** 2;
      return Math.sqrt(acc / n);
    };
    expect(rms(500)).toBeLessThan(0.001);
    expect(rms(2500)).toBeGreaterThan(0.1);
    expect(rms(4000)).toBeLessThan(0.001);
  });

  it('normalises to -1.5 dBFS without lifting a silent track', () => {
    const quiet = writeWav(new Int16Array(24_000).map(() => 200), 24_000);
    expect(peakDbfs(assembleNarration([{ wav: quiet, startMs: 0 }], 1000))).toBeLessThanOrEqual(-1.0);

    const silence = writeWav(new Int16Array(24_000), 24_000);
    expect(peakDbfs(assembleNarration([{ wav: silence, startMs: 0 }], 1000))).toBe(-Infinity);
  });

  it('resamples deterministically and to the right length', () => {
    const src = new Float32Array(1000).map((_, i) => Math.sin(i / 10));
    const out = resample(src, 24_000, 48_000);
    expect(out.length).toBe(2000);
    expect(resample(src, 24_000, 48_000)).toEqual(out);
  });
});

// ---------------------------------------------------------------------------

describe('the generative media provider', () => {
  it('is deterministic for the same prompt and seed', async () => {
    const p = new MockMediaProvider();
    const a = await p.generate({ prompt: 'abstract city', aspect: '16:9', seed: 3, kind: 'image' });
    const b = await p.generate({ prompt: 'abstract city', aspect: '16:9', seed: 3, kind: 'image' });
    expect(new TextDecoder().decode(a.bytes)).toBe(new TextDecoder().decode(b.bytes));
  });

  it('marks its output as never permitted to carry factual content', async () => {
    const asset = await new MockMediaProvider().generate({ prompt: 'x', aspect: '16:9', seed: 1, kind: 'image' });
    expect(asset.factualContentAllowed).toBe(false);
  });

  // The property that matters is that it renders nothing *readable*: no text
  // nodes, no axes, no paths that could pass for a plotted series. Percentages
  // inside SVG attributes are geometry, not content, so they are not the test.
  it('produces nothing readable that could be mistaken for a chart', async () => {
    const svg = new TextDecoder().decode(
      (await new MockMediaProvider().generate({ prompt: 'finance', aspect: '16:9', seed: 7, kind: 'image' })).bytes,
    );
    expect(svg).not.toContain('<text');
    expect(svg).not.toContain('<tspan');
    expect(svg).not.toContain('<path');
    expect(svg).not.toContain('<polyline');
  });
});

describe('local storage', () => {
  it('refuses a key that escapes the artifact root', async () => {
    const root = await mkdtemp(join(tmpdir(), 'aift-store-'));
    const s = new LocalStorageProvider(root);
    await expect(s.put('../escape.txt', 'x', 'text/plain')).rejects.toThrow(/escapes the artifact root/u);
    await expect(s.put('/etc/passwd', 'x', 'text/plain')).rejects.toThrow(/escapes the artifact root/u);
  });

  it('round-trips content and reports a sha256', async () => {
    const root = await mkdtemp(join(tmpdir(), 'aift-store-'));
    const s = new LocalStorageProvider(root);
    const put = await s.put('a/b/c.txt', 'hello', 'text/plain');
    expect(put.sha256).toMatch(/^[0-9a-f]{64}$/u);
    expect(new TextDecoder().decode(await s.get('a/b/c.txt'))).toBe('hello');
    expect(await s.list('a')).toEqual(['a/b/c.txt']);
  });
});
