import { describe, expect, it } from 'vitest';
import { buildDocument, escapeHtml, type PreparedScene } from '@/lib/video/compose';
import { buildCaptionTimeline, toSrt } from '@/lib/video/captions';
import { stylesheet } from '@/lib/video/theme';
import { DEFAULT_BRAND_SETTINGS } from '@/lib/db/defaults';
import type { ScenePlan, Script } from '@/lib/schemas/content';

const brand = { ...DEFAULT_BRAND_SETTINGS, user_id: 'u' };

const script: Script = {
  working_title: 'Reading A Quarter Properly',
  reference_date: '2026-08-14',
  beats: [
    { beat_id: 'B-001', chapter: 'Open', narration: 'One line did most of the work here.', on_screen_text: 'Reading A Quarter Properly', claim_ids: [], visual_intent: 'title_card' },
    { beat_id: 'B-002', chapter: 'Open', narration: 'Revenue was 4.61 billion dollars in the quarter. As of 27 June 2026.', on_screen_text: '$4.61bn', claim_ids: ['C-001'], visual_intent: 'stat_reveal' },
    { beat_id: 'B-003', chapter: 'Close', narration: DEFAULT_BRAND_SETTINGS.disclosure_text, on_screen_text: 'Not financial advice', claim_ids: [], visual_intent: 'disclosure' },
  ],
  chapters: [{ title: 'Open', start_beat: 'B-001' }, { title: 'Close', start_beat: 'B-003' }],
  description_markdown: 'x'.repeat(120),
  tags: ['a', 'b', 'c', 'd', 'e'],
  disclosure_text: DEFAULT_BRAND_SETTINGS.disclosure_text,
};

const plan: ScenePlan = {
  format: 'deep_dive', width: 1920, height: 1080, fps: 30, total_ms: 18_000,
  scenes: [
    { scene_id: 'S-001', beat_ids: ['B-001'], start_ms: 0, duration_ms: 5000, composition: 'title_card',
      headline: 'Reading A Quarter Properly', subhead: '', data: null, stat: null, rows: [], columns: [],
      bullets: [], broll_prompt: '', transition: 'fade', citation: '' },
    { scene_id: 'S-002', beat_ids: ['B-002'], start_ms: 5000, duration_ms: 6000, composition: 'stat_reveal',
      headline: '$4.61bn', subhead: 'Reported in the filing', data: null,
      stat: { value: '$4.61bn', caption: 'Reported in the filing', source_label: 'Filing (fixture)', as_of_date: '2026-06-27', claim_ids: ['C-001'] },
      rows: [], columns: [], bullets: [], broll_prompt: '', transition: 'rise', citation: 'C-001 · as of 2026-06-27' },
    { scene_id: 'S-003', beat_ids: ['B-003'], start_ms: 11_000, duration_ms: 7000, composition: 'disclosure',
      headline: 'Not financial advice', subhead: '', data: null, stat: null, rows: [], columns: [],
      bullets: [], broll_prompt: '', transition: 'fade', citation: '' },
  ],
};

const seconds = new Map([['B-001', 3.0], ['B-002', 4.6], ['B-003', 5.5]]);
const captions = buildCaptionTimeline(script, plan, seconds);
const prepared: PreparedScene[] = plan.scenes.map((scene) => ({ scene }));

function doc(): string {
  return buildDocument({ plan, script, brand, prepared, captions, formatLabel: 'Deep dive' });
}

describe('the composed document', () => {
  it('is self-contained: no network request of any kind', () => {
    const html = doc();
    expect(html).not.toMatch(/<script[^>]+src=/u);
    expect(html).not.toMatch(/<link[^>]+href=/u);
    expect(html).not.toMatch(/https?:\/\/(?!www\.w3\.org)/u);
    expect(html).not.toContain('fetch(');
  });

  // This is the property the whole audit story rests on: if a frame depended on
  // wall-clock or on animation callbacks, a re-render would not be identical and
  // "the numbers on screen are verifiable" would be a claim rather than a fact.
  it('exposes a seek function and nothing time-dependent', () => {
    const html = doc();
    expect(html).toContain('window.__seek');
    expect(html).toContain('window.__ready');
    expect(html).not.toContain('requestAnimationFrame');
    expect(html).not.toContain('Date.now');
    expect(html).not.toContain('setInterval');
    expect(html).not.toContain('@keyframes');
    // `transition:none` is the point — the caption highlight must snap to the
    // seeked time, not ease towards it a frame late.
    expect(html).toContain('transition:none');
    expect(html).not.toMatch(/transition:\s*(?!none)/u);
  });

  it('carries every scene and tags it with its composition', () => {
    const html = doc();
    for (const s of plan.scenes) {
      expect(html).toContain(`data-id="${s.scene_id}"`);
      expect(html).toContain(`data-comp="${s.composition}"`);
    }
  });

  it('shows the source, as-of date and claim id on the stat card', () => {
    const html = doc();
    expect(html).toContain('Filing (fixture)');
    expect(html).toContain('2026-06-27');
    expect(html).toContain('C-001');
  });

  it('speaks the disclosure and puts it on screen', () => {
    const html = doc();
    expect(captions.map((c) => c.words.map((w) => w.w).join(' ')).join(' '))
      .toContain(DEFAULT_BRAND_SETTINGS.disclosure_text);
    expect(html).toContain('Not financial advice');
  });

  it('escapes text rather than letting it inject markup', () => {
    const nasty = { ...script, working_title: '</script><img src=x onerror=alert(1)>' };
    const html = buildDocument({ plan, script: nasty, brand, prepared, captions, formatLabel: 'Deep dive' });
    expect(html).not.toContain('<img src=x');
    expect(escapeHtml('<b>&"\'')).toBe('&lt;b&gt;&amp;&quot;&#39;');
  });

  it('contains no private-finance language', () => {
    const html = doc();
    for (const re of [/my portfolio/iu, /account number/iu, /broker statement/iu, /my holdings/iu]) {
      expect(html).not.toMatch(re);
    }
  });

  it('renders identically for identical input', () => {
    expect(doc()).toBe(doc());
  });
});

describe('captions and the narration they came from', () => {
  it('reconstruct the narration exactly, word for word', () => {
    for (const line of captions) {
      const beat = script.beats.find((b) => b.beat_id === line.beatId)!;
      expect(line.words.map((w) => w.w).join(' ')).toBe(beat.narration.trim());
    }
  });

  it('produce SRT whose text is drawn only from the narration', () => {
    const srt = toSrt(captions);
    const spoken = script.beats.map((b) => b.narration).join(' ').replace(/\s+/gu, ' ');
    const cueText = srt.split('\n\n')
      .map((b) => b.split('\n').slice(2).join(' '))
      .join(' ').replace(/\s+/gu, ' ').trim();
    for (const word of cueText.split(' ').filter(Boolean)) {
      expect(spoken, `"${word}" is in the captions but not in the narration`).toContain(word);
    }
  });

  it('never runs a caption past the end of its scene', () => {
    for (const line of captions) {
      const scene = plan.scenes.find((s) => s.beat_ids.includes(line.beatId))!;
      expect(line.end).toBeLessThanOrEqual(scene.start_ms + scene.duration_ms);
    }
  });
});

describe('the stylesheet', () => {
  it('writes the brand palette straight in, so changing a token changes every frame', () => {
    const css = stylesheet(brand.visual_style, 1920, 1080);
    expect(css).toContain(brand.visual_style.accent);
    expect(css).toContain(brand.visual_style.background);
    expect(css).toContain(brand.visual_style.display_font);
  });

  it('lays out differently for a vertical canvas', () => {
    expect(stylesheet(brand.visual_style, 1920, 1080)).not.toBe(stylesheet(brand.visual_style, 1080, 1920));
  });
});
