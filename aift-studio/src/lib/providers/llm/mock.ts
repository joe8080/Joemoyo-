import { z } from 'zod';
import type { LLMProvider, LlmCall, LlmResult } from '@/lib/providers/types';
import type {
  AnalystBriefPayload, CritiquePayload, EditorialPayload, ScriptPayload,
  SearchPlanPayload, SourceAssessmentPayload, StagePayload,
} from '@/lib/workflow/payloads';
import type {
  AnalystBrief, Claim, EditorialPlan, ReviewerCritique, Script, ScriptBeat, SearchPlan, SourceAssessment,
} from '@/lib/schemas/content';
import { isMaterial } from '@/lib/schemas/content';
import { seededRandom, stableHash } from '@/lib/util/hash';

/**
 * Deterministic composer standing in for a language model.
 *
 * It is a genuine transformation of the stage input, not a canned response: the
 * same brief always produces the same script, and a different brief produces a
 * different one. That makes the whole workflow — including QA, rendering and the
 * review room — exercisable and testable with no credentials and no spend.
 *
 * Provenance is recorded as `mock-composer@1` on every asset it touches so a
 * mock run can never be mistaken for a model run.
 */
export class MockLLMProvider implements LLMProvider {
  readonly name = 'mock-composer@1';
  readonly isLive = false;

  async complete<T>(call: LlmCall<T>): Promise<LlmResult<T>> {
    const payload = call.payload as StagePayload;
    const raw = this.compose(payload, call.schemaName);
    const parsed = call.schema.safeParse(raw);
    if (!parsed.success) {
      throw new Error(
        `mock composer produced output that failed ${call.schemaName}: ${parsed.error.issues
          .map((i) => `${i.path.join('.')}: ${i.message}`)
          .join('; ')}`,
      );
    }
    return {
      value: parsed.data,
      usage: { provider: this.name, model: `mock-${call.role}`, inputTokens: null, outputTokens: null, costUsd: 0 },
      attempts: 1,
    };
  }

  private compose(payload: StagePayload, schemaName: string): unknown {
    switch (payload.kind) {
      case 'search_plan': return searchPlan(payload);
      case 'source_assessment': return sourceAssessment(payload);
      case 'analyst_brief': return analystBrief(payload);
      case 'editorial_plan': return editorialPlan(payload);
      case 'script': return script(payload);
      case 'reviewer_critique': return critique(payload);
      default: throw new Error(`mock composer has no route for schema "${schemaName}"`);
    }
  }
}

// ---------------------------------------------------------------------------
// Stage 2 — search plan
// ---------------------------------------------------------------------------

function searchPlan(p: SearchPlanPayload): SearchPlan {
  const subject = p.ticker ? `${p.ticker}` : p.topic.split(/[:—-]/u)[0]!.trim();
  return {
    reference_date: p.reference_date,
    rationale:
      `Primary disclosure first: the most recent periodic filing and the matching earnings call carry the ` +
      `figures and the company's own risk language. Specialist industry work is used only for context that a ` +
      `filing cannot supply. Discovery results are treated as pointers; nothing is cited until the document ` +
      `itself has been fetched and stored.`,
    queries: [
      { query: `${subject} latest quarterly report filing`, intent: 'Locate the most recent periodic filing', preferred_tiers: ['primary_filing'] },
      { query: `${subject} earnings call transcript`, intent: 'Management commentary and forward guidance in their own words', preferred_tiers: ['primary_company'] },
      { query: `${subject} risk factors supply concentration`, intent: 'Disclosed dependencies and their stated consequences', preferred_tiers: ['primary_filing'] },
      { query: `${subject} segment revenue mix`, intent: 'Segment split behind the headline number', preferred_tiers: ['primary_filing', 'primary_company'] },
      { query: `${p.topic} industry capacity lead times`, intent: 'Independent context on the supply side', preferred_tiers: ['specialist'] },
      { query: `customer concentration disclosure threshold explained`, intent: 'Educational grounding for the concept, not a company claim', preferred_tiers: ['specialist'] },
    ],
    required_primary_documents: [
      'Most recent periodic filing (10-Q / 10-K equivalent)',
      'Matching earnings call transcript or press release',
    ],
    out_of_scope: [
      'Social media posts and forum commentary',
      'Price targets and analyst ratings presented as fact',
      'Any private portfolio, account or holdings data',
    ],
  };
}

// ---------------------------------------------------------------------------
// Stage 3 — relevance assessment
// ---------------------------------------------------------------------------

function sourceAssessment(p: SourceAssessmentPayload): SourceAssessment {
  const terms = p.topic.toLowerCase().split(/\W+/u).filter((t) => t.length > 3);
  return {
    assessments: p.discovered.map((d) => {
      const hay = `${d.title} ${d.snippet} ${d.publisher}`.toLowerCase();
      const hits = terms.filter((t) => hay.includes(t));
      const relevance = hits.length >= 3 ? 'high' : hits.length >= 1 ? 'medium' : 'low';
      return {
        canonical_url: d.url,
        relevance: relevance as 'high' | 'medium' | 'low',
        supports_topics: hits.slice(0, 8),
        caution_notes: /synthetic|fixture/iu.test(d.publisher)
          ? 'Synthetic fixture corpus. Every figure is invented and is labelled as such on screen.'
          : '',
      };
    }),
  };
}

// ---------------------------------------------------------------------------
// Stage 4 — analyst brief
// ---------------------------------------------------------------------------

function analystBrief(p: AnalystBriefPayload): AnalystBrief {
  const facts = p.evidence.flatMap((e) =>
    e.candidate_facts.map((f) => ({ ...f, doc: e.source_document_id, publisher: e.publisher })),
  );

  const claims: Claim[] = facts.map((f, i) => ({
    claim_id: `C-${String(i + 1).padStart(3, '0')}`,
    claim_text: f.text,
    claim_type: f.type as Claim['claim_type'],
    source_document_ids: [f.doc],
    source_excerpt: f.excerpt,
    as_of_date: isMaterial(f.type as Claim['claim_type']) ? f.as_of : f.as_of,
    confidence: f.confidence,
    uncertainty_note: f.uncertainty,
  }));

  const byDirection = (d: 'bull' | 'bear') =>
    facts.map((f, i) => ({ f, id: `C-${String(i + 1).padStart(3, '0')}` })).filter((x) => x.f.direction === d);

  const bull = byDirection('bull');
  const bear = byDirection('bear');
  const subject = p.ticker ?? p.topic.split(/[:—-]/u)[0]!.trim();

  return {
    reference_date: p.reference_date,
    headline: truncate(p.topic, 160),
    summary:
      `As of ${p.reference_date}, the evidence set for ${subject} comprises ${p.evidence.length} fetched and stored ` +
      `documents yielding ${claims.length} discrete claims. The strongest material claims come from primary ` +
      `disclosure rather than commentary. ` +
      (bull.length > 0
        ? `The supportive side of the evidence rests on: ${bull.slice(0, 3).map((x) => lower(x.f.text)).join(' ')} `
        : '') +
      (bear.length > 0
        ? `The cautionary side rests on: ${bear.slice(0, 3).map((x) => lower(x.f.text)).join(' ')} `
        : '') +
      `Every figure below carries an as-of date because a number without one is not evidence. Where the source is ` +
      `an estimate or a company characterisation rather than a reported result, the claim is labelled accordingly.`,
    bull_case: (bull.length > 0 ? bull : facts.slice(0, 2).map((f, i) => ({ f, id: `C-${i}` })))
      .slice(0, 5)
      .map((x) => `${x.f.text}${x.f.uncertainty ? ` (${lower(x.f.uncertainty)})` : ''}`),
    bear_case: (bear.length > 0 ? bear : facts.slice(-2).map((f, i) => ({ f, id: `C-${i}` })))
      .slice(0, 5)
      .map((x) => `${x.f.text}${x.f.uncertainty ? ` (${lower(x.f.uncertainty)})` : ''}`),
    key_risks: [
      ...bear.slice(0, 3).map((x) => `${x.f.text} The filing discloses the dependency; it does not quantify the probability.`),
      'Guidance is an estimate produced by the company and is revised as conditions change.',
      'A single quarter is a data point. Extrapolating a trend from it is the most common error in this kind of analysis.',
    ].slice(0, 6),
    open_questions: [
      'What proportion of committed volume is cancellable, and on what notice?',
      'How much of the margin improvement is mix and how much is durable pricing?',
      'Does order visibility reflect genuine end demand or inventory being positioned ahead of it?',
    ],
    claims,
  };
}

// ---------------------------------------------------------------------------
// Stage 5 — editorial plan
// ---------------------------------------------------------------------------

function editorialPlan(p: EditorialPayload): EditorialPlan {
  const subject = p.ticker ?? p.brief.headline.split(/[:—-]/u)[0]!.trim();
  const short = p.format === 'short';
  const material = p.brief.claims.filter((c) => isMaterial(c.claim_type));
  const bearIds = p.brief.claims.filter((c) => /concentration|single supplier|below|cancellable/iu.test(c.claim_text)).map((c) => c.claim_id);

  const outline = short
    ? [
        { chapter: 'Hook', purpose: 'One number, stated with its date', claim_ids: material.slice(0, 1).map((c) => c.claim_id), target_seconds: 20 },
        { chapter: 'The catch', purpose: 'The disclosed dependency behind the number', claim_ids: bearIds.slice(0, 1), target_seconds: 22 },
        { chapter: 'What to watch', purpose: 'The one thing that would change the reading', claim_ids: [], target_seconds: 20 },
        { chapter: 'Disclosure', purpose: 'Educational disclosure', claim_ids: [], target_seconds: 20 },
      ]
    : [
        { chapter: 'The number everyone quotes', purpose: 'Open on the headline figure, dated and sourced', claim_ids: material.slice(0, 1).map((c) => c.claim_id), target_seconds: 65 },
        { chapter: 'Where the growth actually came from', purpose: 'Decompose the headline into its mix', claim_ids: material.slice(1, 3).map((c) => c.claim_id), target_seconds: 95 },
        { chapter: 'What the margin line is telling you', purpose: 'Separate reported margin from guided margin', claim_ids: material.slice(2, 5).map((c) => c.claim_id), target_seconds: 100 },
        { chapter: 'The commitment the company has made', purpose: 'Read commitments as both signal and obligation', claim_ids: material.slice(3, 5).map((c) => c.claim_id), target_seconds: 90 },
        { chapter: 'The dependency in the risk factors', purpose: 'Concentration and supply, in the company’s own words', claim_ids: bearIds.slice(0, 3), target_seconds: 105 },
        { chapter: 'The bull case and the bear case', purpose: 'Both sides, evidence-linked, no verdict', claim_ids: material.slice(0, 4).map((c) => c.claim_id), target_seconds: 95 },
        { chapter: 'What would change the picture', purpose: 'Falsifiable things to watch next', claim_ids: [], target_seconds: 70 },
        { chapter: 'Disclosure and close', purpose: 'Educational disclosure and call to action', claim_ids: [], target_seconds: 45 },
      ];

  return {
    angle:
      `Take one quarter of primary disclosure and read it the way an analyst would: separate what was reported ` +
      `from what was guided, name the dates on every figure, and give the disclosed dependencies the same airtime ` +
      `as the growth. No verdict, no price target, no instruction.`,
    audience_promise:
      `By the end you will be able to read this kind of filing yourself and know which three lines actually matter.`,
    title_options: [
      { title: truncate(`${subject}: What The Filing Actually Says`, 90), why_it_works: 'Concrete, promises the primary source rather than an opinion', overpromise_risk: 'low' },
      { title: truncate(`The Three Lines That Matter In ${subject}'s Quarter`, 90), why_it_works: 'Numbered promise with a bounded scope the video delivers', overpromise_risk: 'low' },
      { title: truncate(`${subject}: The Growth Number And The Dependency Behind It`, 90), why_it_works: 'Signals balance up front; both halves appear in the video', overpromise_risk: 'low' },
      { title: truncate(`How To Read A Quarter Like This One (${subject} Case Study)`, 90), why_it_works: 'Educational framing that matches the channel’s remit', overpromise_risk: 'low' },
    ],
    hook:
      `One line in this quarter did most of the work — and one line in the risk factors explains why that first ` +
      `line is worth reading twice.`,
    outline,
    call_to_action:
      `If you want the next one of these, the filing links and the full claim list are in the description. ` +
      `Tell me which line you would have led with.`,
  };
}

// ---------------------------------------------------------------------------
// Stage 6 — script
// ---------------------------------------------------------------------------

const OPENERS = [
  'Start with what the filing states.',
  'Here is what the document actually says.',
  'The disclosure is specific on this point.',
  'Read the line itself rather than the summary of it.',
  'The primary source puts it plainly.',
];

const PIVOTS = [
  'That is the reported figure. What it does not tell you is the shape underneath it.',
  'So far, so straightforward. The interesting part is what sits behind it.',
  'That is one line. It is worth asking what has to be true for it to hold.',
  'Take that as given and the next question follows immediately.',
];

const CAUTIONS = [
  'The evidence supports the statement. It does not support extending the statement into next year.',
  'One quarter is a data point. A direction needs several.',
  'This is what was disclosed, not what will happen.',
  'The number is precise. The conclusion drawn from it should not be.',
];

const VISUAL_FOR_TYPE: Record<string, ScriptBeat['visual_intent']> = {
  financial_statement: 'stat_reveal',
  forecast_or_guidance: 'stat_reveal',
  market_cap: 'stat_reveal',
  price_or_performance: 'line_chart',
  valuation: 'bar_chart',
  causal: 'risk_card',
  insider_or_ownership: 'risk_card',
  rating_or_recommendation: 'statement',
  definitional: 'quote_card',
  contextual: 'statement',
};

function script(p: ScriptPayload): Script {
  const rnd = seededRandom(stableHash(p.editorial.angle + p.brief.reference_date));
  const pick = <T,>(arr: readonly T[]): T => arr[Math.floor(rnd() * arr.length) % arr.length]!;
  const claimById = new Map(p.approved_claims.map((c) => [c.claim_id, c]));

  const beats: ScriptBeat[] = [];
  let n = 0;
  const nextId = () => `B-${String(++n).padStart(3, '0')}`;

  const title = p.editorial.title_options[0]!.title;

  // --- Cold open -----------------------------------------------------------
  beats.push({
    beat_id: nextId(), chapter: p.editorial.outline[0]!.chapter,
    narration: `${p.editorial.hook}`,
    on_screen_text: title, claim_ids: [], visual_intent: 'title_card',
  });

  for (const [ci, chapter] of p.editorial.outline.entries()) {
    const isDisclosureChapter = /disclosure/iu.test(chapter.chapter);
    if (isDisclosureChapter) continue;

    if (ci > 0) {
      beats.push({
        beat_id: nextId(), chapter: chapter.chapter,
        narration: `${chapter.chapter}.`,
        on_screen_text: chapter.chapter, claim_ids: [], visual_intent: 'chapter_card',
      });
    }

    const claims = chapter.claim_ids.map((id) => claimById.get(id)).filter((c): c is Claim => Boolean(c));

    if (claims.length === 0) {
      // Analytical chapter with no direct claim — e.g. "what would change the picture".
      const qs = p.brief.open_questions.slice(0, 3);
      beats.push({
        beat_id: nextId(), chapter: chapter.chapter,
        narration:
          `${pick(PIVOTS)} There are three things that would genuinely change the reading here, and all three are ` +
          `checkable rather than a matter of opinion.`,
        on_screen_text: 'What would change the picture', claim_ids: [], visual_intent: 'statement',
      });
      for (const q of qs) {
        beats.push({
          beat_id: nextId(), chapter: chapter.chapter,
          narration: q, on_screen_text: truncate(q, 120), claim_ids: [], visual_intent: 'risk_card',
        });
      }
      continue;
    }

    if (/bull case and the bear case/iu.test(chapter.chapter)) {
      beats.push({
        beat_id: nextId(), chapter: chapter.chapter,
        narration:
          `Set the two readings side by side. The supportive case and the cautionary case draw on the same ` +
          `document; they differ in which lines they weight.`,
        on_screen_text: 'Same filing, two readings',
        claim_ids: claims.map((c) => c.claim_id), visual_intent: 'comparison_table',
      });
      const pairs = Math.max(p.brief.bull_case.length, p.brief.bear_case.length);
      for (let i = 0; i < Math.min(pairs, 3); i += 1) {
        const bullLine = p.brief.bull_case[i];
        const bearLine = p.brief.bear_case[i];
        beats.push({
          beat_id: nextId(), chapter: chapter.chapter,
          narration:
            (bullLine ? `The supportive reading: ${lower(stripParens(bullLine))} ` : '') +
            (bearLine ? `The cautionary reading: ${lower(stripParens(bearLine))}` : ''),
          on_screen_text: '', claim_ids: claims.map((c) => c.claim_id), visual_intent: 'statement',
        });
      }
      continue;
    }

    for (const [i, claim] of claims.entries()) {
      const lead = i === 0 ? pick(OPENERS) : pick(PIVOTS);
      const asOf = claim.as_of_date ? ` As of ${formatDate(claim.as_of_date)}.` : '';
      const hedge = claim.uncertainty_note ? ` ${capitalise(claim.uncertainty_note)}` : ` ${pick(CAUTIONS)}`;
      beats.push({
        beat_id: nextId(), chapter: chapter.chapter,
        narration: `${lead} ${claim.claim_text}${asOf}${hedge}`,
        on_screen_text: truncate(claim.claim_text, 150),
        claim_ids: [claim.claim_id],
        visual_intent: VISUAL_FOR_TYPE[claim.claim_type] ?? 'statement',
      });
    }
  }

  // --- Disclosure and outro ------------------------------------------------
  beats.push({
    beat_id: nextId(), chapter: 'Disclosure',
    narration: p.disclosure_text,
    on_screen_text: 'Research and education only — not financial advice',
    claim_ids: [], visual_intent: 'disclosure',
  });
  beats.push({
    beat_id: nextId(), chapter: 'Disclosure',
    narration: p.editorial.call_to_action,
    on_screen_text: p.channel_name, claim_ids: [], visual_intent: 'outro',
  });

  const chapters = dedupeChapters(beats);

  return {
    working_title: truncate(title, 100),
    reference_date: p.reference_date,
    beats,
    chapters,
    description_markdown: buildDescription(p, chapters),
    tags: buildTags(p),
    disclosure_text: p.disclosure_text,
  };
}

function dedupeChapters(beats: ScriptBeat[]): Script['chapters'] {
  const out: Script['chapters'] = [];
  const seen = new Set<string>();
  for (const b of beats) {
    if (seen.has(b.chapter)) continue;
    seen.add(b.chapter);
    out.push({ title: truncate(b.chapter, 80), start_beat: b.beat_id });
  }
  return out;
}

function buildDescription(p: ScriptPayload, chapters: Script['chapters']): string {
  const claimLines = p.approved_claims
    .map((c) => `- \`${c.claim_id}\` — ${c.claim_text} _(as of ${c.as_of_date ?? 'n/a'}, confidence ${c.confidence.toFixed(2)})_`)
    .join('\n');
  return [
    `## ${p.editorial.title_options[0]!.title}`,
    '',
    p.editorial.audience_promise,
    '',
    `**Reference date:** ${p.reference_date}`,
    '',
    '### Chapters',
    chapters.map((c, i) => `- ${i === 0 ? '00:00' : '—'} ${c.title}`).join('\n'),
    '',
    '### Every claim in this video',
    claimLines,
    '',
    '### Sources',
    'Full source register with URLs, publishers, publication dates, access dates and content hashes is attached to this content pack as `source_manifest.json`.',
    '',
    '### Disclosure',
    p.disclosure_text,
  ].join('\n');
}

function buildTags(p: ScriptPayload): string[] {
  const base = ['investing education', 'how to read a 10-Q', 'financial statements', 'equity research', 'fundamental analysis',
    'earnings explained', 'risk factors', 'customer concentration', 'gross margin', 'guidance vs results'];
  const fromTitle = p.editorial.title_options[0]!.title.toLowerCase().split(/\W+/u).filter((t) => t.length > 4).slice(0, 5);
  return Array.from(new Set([...base, ...fromTitle])).slice(0, 20);
}

// ---------------------------------------------------------------------------
// Stage 9 — independent reviewer critique
// ---------------------------------------------------------------------------

/**
 * Deliberately implemented as an *independent* pass: it re-derives its findings
 * from the script text alone and never sees the writer's reasoning. In live mode
 * this call is routed to the `review` model, which must differ from `fast`.
 */
function critique(p: CritiquePayload): ReviewerCritique {
  const findings: ReviewerCritique['findings'] = [];
  const approved = new Set(p.approved_claim_ids);
  const fullText = p.script.beats.map((b) => b.narration).join(' ');

  for (const beat of p.script.beats) {
    for (const id of beat.claim_ids) {
      if (!approved.has(id)) {
        findings.push({
          severity: 'blocking', area: 'evidence', beat_id: beat.beat_id,
          detail: `Beat ${beat.beat_id} cites claim ${id}, which is not in the approved claim set.`,
          remediation: 'Remove the citation or return the claim to the evidence stage for verification.',
        });
      }
    }
    const bareNumber = /(?<![A-Za-z$€£%\d.])\d{1,3}(?:[.,]\d+)?\s?(?:%|per cent|billion|million|bn|m\b)/iu;
    if (bareNumber.test(beat.narration) && beat.claim_ids.length === 0) {
      findings.push({
        severity: 'blocking', area: 'evidence', beat_id: beat.beat_id,
        detail: `Beat ${beat.beat_id} states a figure with no claim reference.`,
        remediation: 'Attach the claim id that carries the figure, its source and its as-of date.',
      });
    }
    for (const phrase of p.banned_phrases) {
      if (phrase && beat.narration.toLowerCase().includes(phrase.toLowerCase())) {
        findings.push({
          severity: 'blocking', area: 'compliance', beat_id: beat.beat_id,
          detail: `Beat ${beat.beat_id} uses the banned phrase "${phrase}".`,
          remediation: 'Rewrite without the phrase. Describe evidence rather than instructing the viewer.',
        });
      }
    }
  }

  if (!fullText.includes(p.disclosure_text.slice(0, 40))) {
    findings.push({
      severity: 'blocking', area: 'compliance', beat_id: '',
      detail: 'The required educational disclosure does not appear in the narration.',
      remediation: 'Add the disclosure beat verbatim before the outro.',
    });
  }

  const hasCounterCase = /cautionary|risk|dependency|however|does not/iu.test(fullText);
  if (!hasCounterCase) {
    findings.push({
      severity: 'blocking', area: 'balance', beat_id: '',
      detail: 'The script presents no counter-case or risk discussion.',
      remediation: 'Add at least one evidence-linked risk or bear-case segment.',
    });
  }

  const blocking = findings.filter((f) => f.severity === 'blocking').length;
  return {
    verdict: blocking > 0 ? 'rework' : 'pass',
    findings,
    strengths: blocking > 0 ? [] : [
      'Every figure in the narration is bound to a stored claim with an as-of date.',
      'The counter-case is given its own chapter rather than a closing caveat.',
      'No instruction-shaped language: the script describes evidence and stops there.',
    ],
  };
}

// ---------------------------------------------------------------------------

function truncate(s: string, n: number): string {
  return s.length <= n ? s : `${s.slice(0, n - 1).trimEnd()}…`;
}
function lower(s: string): string {
  return s.length > 0 ? s[0]!.toLowerCase() + s.slice(1) : s;
}
function capitalise(s: string): string {
  return s.length > 0 ? s[0]!.toUpperCase() + s.slice(1) : s;
}
function stripParens(s: string): string {
  return s.replace(/\s*\([^)]*\)\s*$/u, '').trim();
}
function formatDate(iso: string): string {
  const [y, m, d] = iso.split('-');
  const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  return `${Number(d)} ${months[Number(m) - 1] ?? m} ${y}`;
}

export const __testables = { searchPlan, analystBrief, editorialPlan, script, critique };
export const zodPassthrough = z;
