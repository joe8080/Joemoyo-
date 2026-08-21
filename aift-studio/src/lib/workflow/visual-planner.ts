import type { Scene, ScenePlan, Script, ScriptBeat, Claim } from '@/lib/schemas/content';
import { sceneSchema, scenePlanSchema } from '@/lib/schemas/content';
import type { BrandSettings } from '@/lib/domain';
import type { DataRegistry } from './data-registry';

/**
 * Scene planning is deterministic code, not a model call.
 *
 * Everything a viewer reads as a number — chart points, stat values, table cells,
 * source stamps — is assembled here from the claim ledger and the data registry.
 * The model's role in this stage is limited to atmosphere: B-roll prompt text
 * for scenes that carry no figures.
 *
 * Durations come from the measured narration clips, so picture and voice are in
 * sync by construction rather than by adjustment afterwards.
 */

export type PlanInput = {
  script: Script;
  claims: Claim[];
  brand: BrandSettings;
  registry: DataRegistry;
  format: 'deep_dive' | 'short';
  /** beat_id → measured narration seconds. */
  narrationSeconds: Map<string, number>;
  /** Both readings, so the comparison card is filled from the brief itself. */
  bullCase: string[];
  bearCase: string[];
  /** claim_id → the publisher string a viewer will see stamped on the frame. */
  sourceLabels: Map<string, string>;
};

/** What a viewer needs to know about a figure before they read it. */
const CLAIM_KIND_LABEL: Record<string, string> = {
  financial_statement: 'Reported in the filing',
  forecast_or_guidance: 'Company guidance — an estimate',
  market_cap: 'Market capitalisation',
  price_or_performance: 'Price / performance',
  valuation: 'Valuation multiple',
  insider_or_ownership: 'Ownership / concentration disclosure',
  causal: 'Company’s own risk language',
  rating_or_recommendation: 'Third-party rating',
  definitional: 'Definition',
  contextual: 'Context — outside estimate',
};

const DIMENSIONS = {
  deep_dive: { width: 1920, height: 1080, fps: 30 },
  short: { width: 1080, height: 1920, fps: 30 },
} as const;

/** Air on either side of speech so cuts do not clip the first or last word. */
const LEAD_IN_MS = 260;
const TAIL_MS = 420;
const MIN_SCENE_MS = 1600;
const MAX_SCENE_MS = 30_000;

export function planScenes(input: PlanInput): ScenePlan {
  const dims = DIMENSIONS[input.format];
  const claimById = new Map(input.claims.map((c) => [c.claim_id, c]));
  const scenes: Scene[] = [];
  let cursor = 0;

  for (const [i, beat] of input.script.beats.entries()) {
    const spoken = (input.narrationSeconds.get(beat.beat_id) ?? 0) * 1000;
    const raw = Math.round(spoken + LEAD_IN_MS + TAIL_MS);
    const duration = Math.min(MAX_SCENE_MS, Math.max(MIN_SCENE_MS, raw));

    const beatClaims = beat.claim_ids.map((id) => claimById.get(id)).filter((c): c is Claim => Boolean(c));
    const scene = buildScene({
      beat, index: i, startMs: cursor, durationMs: duration,
      claims: beatClaims, registry: input.registry, brand: input.brand, format: input.format,
      bullCase: input.bullCase, bearCase: input.bearCase, sourceLabels: input.sourceLabels,
    });
    scenes.push(sceneSchema.parse(scene));
    cursor += duration;
  }

  return scenePlanSchema.parse({
    format: input.format,
    width: dims.width,
    height: dims.height,
    fps: dims.fps,
    total_ms: cursor,
    scenes,
  });
}

function buildScene(args: {
  beat: ScriptBeat; index: number; startMs: number; durationMs: number;
  claims: Claim[]; registry: DataRegistry; brand: BrandSettings; format: 'deep_dive' | 'short';
  bullCase: string[]; bearCase: string[]; sourceLabels: Map<string, string>;
}): Scene {
  const { beat, startMs, durationMs, claims, registry, brand } = args;
  const claimIds = claims.map((c) => c.claim_id);
  const base = {
    scene_id: `S-${String(args.index + 1).padStart(3, '0')}`,
    beat_ids: [beat.beat_id],
    start_ms: startMs,
    duration_ms: durationMs,
    headline: beat.on_screen_text,
    subhead: '',
    data: null,
    stat: null,
    rows: [],
    columns: [],
    bullets: [],
    broll_prompt: '',
    transition: pickTransition(args.index),
    citation: claims[0] ? citationFor(claims[0]) : '',
  };

  // A chart composition is only permitted where real, dated, sourced rows exist.
  if (beat.visual_intent === 'line_chart' || beat.visual_intent === 'bar_chart') {
    const series = registry.findForClaims(claimIds);
    if (!series) {
      return { ...base, composition: 'statement', headline: beat.on_screen_text || beat.chapter };
    }
    return {
      ...base,
      composition: beat.visual_intent,
      headline: series.label,
      // No subhead: the caption already carries the sentence, and printing it
      // twice in one frame is the fastest way to make a chart look cluttered.
      subhead: '',
      data: {
        series: [{ label: series.label, points: series.points, unit: series.unit }],
        y_label: series.label,
        x_label: '',
        source_label: series.sourceLabel,
        as_of_date: series.asOf,
        claim_ids: claimIds.length > 0 ? claimIds : series.claimIds,
        highlight_index: series.points.length - 1,
      },
    };
  }

  if (beat.visual_intent === 'stat_reveal') {
    const claim = claims[0];
    const series = registry.findForClaims(claimIds);
    const figure = firstFigure(claim?.claim_text ?? '');
    if (claim && figure && claim.as_of_date) {
      // A stat card is a chart with one number: it earns a source stamp and a
      // draw-on chart underneath when the registry has the series.
      if (series) {
        return {
          ...base,
          composition: 'line_chart',
          headline: series.label,
          subhead: '',
          data: {
            series: [{ label: series.label, points: series.points, unit: series.unit }],
            y_label: series.label, x_label: '',
            source_label: series.sourceLabel, as_of_date: series.asOf,
            claim_ids: claimIds, highlight_index: series.points.length - 1,
          },
        };
      }
      return {
        ...base,
        composition: 'stat_reveal',
        headline: figure,
        // The kicker names what kind of number this is — reported, guided, an
        // estimate — because that distinction is the whole point of the card.
        subhead: CLAIM_KIND_LABEL[claim.claim_type] ?? 'Stored claim',
        stat: {
          value: figure,
          caption: CLAIM_KIND_LABEL[claim.claim_type] ?? 'Stored claim',
          source_label: args.sourceLabels.get(claim.claim_id) ?? 'Stored source register',
          as_of_date: claim.as_of_date,
          claim_ids: claimIds,
        },
      };
    }
    return { ...base, composition: 'statement' };
  }

  if (beat.visual_intent === 'comparison_table') {
    const n = Math.min(3, Math.max(args.bullCase.length, args.bearCase.length));
    const rows = Array.from({ length: n }, (_, i) => ({
      label: `row-${i + 1}`,
      values: [
        trim(stripParenthetical(args.bullCase[i] ?? ''), 150),
        trim(stripParenthetical(args.bearCase[i] ?? ''), 150),
      ],
    }));
    return {
      ...base,
      composition: 'comparison_table',
      headline: beat.on_screen_text || 'Same evidence, two readings',
      columns: ['Supportive reading', 'Cautionary reading'],
      rows,
    };
  }

  if (beat.visual_intent === 'broll') {
    return {
      ...base,
      composition: 'broll',
      // Constrained by construction: no figures, no logos, no screens showing data.
      broll_prompt:
        'Abstract atmospheric texture: slow-moving light across dark surfaces, shallow depth of field, ' +
        'no text, no charts, no numbers, no logos, no readable screens, no people. Cinematic, low contrast, ' +
        `palette ${brand.visual_style.accent} and ${brand.visual_style.accent_2}.`,
    };
  }

  // What the card shows depends on what the beat is doing.
  //
  //  - A beat that *states* a claim shows the figures. The caption already has
  //    the sentence; repeating it word for word costs the frame its hierarchy.
  //  - A beat that *explains* one — the mechanism beats, which carry no on-screen
  //    text of their own — shows its own opening line, so the card supports the
  //    point being made rather than re-displaying a number just shown.
  //  - A quote card carries the sentence, because a definition reduced to "10%"
  //    says nothing.
  const composition = beat.visual_intent;
  const statesAClaim = beat.on_screen_text.length > 0;
  const figures = statesAClaim && (composition === 'risk_card' || composition === 'statement') && claims.length > 0
    ? claimFigures(claims[0]!)
    : [];

  let headline: string;
  if (figures.length > 0) {
    headline = figures.slice(0, 3).join('   ·   ');
  } else if (composition === 'quote_card') {
    headline = trim(claims[0]?.claim_text || beat.on_screen_text || beat.chapter, 200);
  } else if (!statesAClaim && beat.narration) {
    headline = trim(firstSentence(beat.narration), 120);
  } else {
    headline = trim(beat.on_screen_text || beat.chapter, 110);
  }
  return { ...base, composition, headline };
}

function claimFigures(claim: Claim): string[] {
  const re = /(?:[$£€]\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:bn|billion|m|million|trillion))?)|(?:\d[\d,]*(?:\.\d+)?\s?(?:%|weeks|x|bps))/giu;
  const out: string[] = [];
  for (const m of claim.claim_text.matchAll(re)) {
    const v = m[0].replace(/\s+/gu, ' ').trim();
    if (!out.includes(v)) out.push(v);
  }
  return out;
}

function pickTransition(i: number): Scene['transition'] {
  const cycle: Scene['transition'][] = ['fade', 'rise', 'fade', 'push_left'];
  return cycle[i % cycle.length]!;
}

function citationFor(claim: Claim): string {
  return claim.as_of_date ? `${claim.claim_id} · as of ${claim.as_of_date}` : claim.claim_id;
}

function firstFigure(text: string): string {
  const m = text.match(/(?:[$£€]\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:bn|billion|m|million|trillion))?)|(?:\d[\d,]*(?:\.\d+)?\s?%)/iu);
  return m ? m[0].replace(/\s+/gu, ' ').trim() : '';
}

/** The opening sentence, which is where an explanatory beat states its point. */
function firstSentence(s: string): string {
  const m = s.match(/^[^.!?]+[.!?]/u);
  return (m?.[0] ?? s).trim();
}

function stripParenthetical(s: string): string {
  return s.replace(/\s*\([^)]*\)\s*$/u, '').trim();
}

function trim(s: string, n: number): string {
  return s.length <= n ? s : `${s.slice(0, n - 1).trimEnd()}…`;
}
