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

  // Group claims by what they are, then build chapters around the groups that
  // actually have evidence. A chapter with nothing behind it is padding, and
  // padding is what makes a ten-minute video feel like a four-minute one.
  const g = groupClaims(p.brief.claims);

  const outline: EditorialPlan['outline'] = [];
  const add = (chapter: string, purpose: string, claim_ids: string[], target_seconds: number) => {
    outline.push({ chapter, purpose, claim_ids, target_seconds });
  };

  if (short) {
    add('Hook', 'One reported figure, stated with its date', g.reported.slice(0, 1), 18);
    add('The catch', 'The disclosed dependency sitting behind it', g.dependency.slice(0, 1), 20);
    add('What to watch', 'The one checkable thing that would change the reading', [], 16);
    add('Disclosure', 'Educational disclosure and close', [], 14);
  } else {
    add('The number everyone quotes', 'Open on the headline reported figure, dated and sourced', g.reported.slice(0, 1), 70);
    if (g.reported.length > 1) {
      add('Where the growth actually came from', 'Decompose the headline into its mix', g.reported.slice(1, 3), 105);
    }
    if (g.guided.length > 0) {
      add('Reported versus guided', 'Separate what happened from what the company expects', [...g.reported.slice(3, 4), ...g.guided.slice(0, 2)], 115);
    }
    if (g.reported.length > 3) {
      add('The commitment on the balance sheet', 'Read commitments as signal and as obligation', g.reported.slice(3), 95);
    }
    if (g.dependency.length > 0) {
      add('The dependency in the risk factors', 'Concentration and supply, in the company\u2019s own words', [...g.dependency, ...g.definitional.slice(0, 1)], 120);
    }
    if (g.context.length > 0) {
      add('What the outside evidence adds', 'Independent context the filing cannot supply', g.context.slice(0, 3), 100);
    }
    add('The bull case and the bear case', 'Both readings of the same document, no verdict', g.reported.slice(0, 3), 95);
    add('What would change the picture', 'Falsifiable things to watch next', [], 75);
    add('Disclosure', 'Educational disclosure and call to action', [], 45);
  }

  return {
    angle:
      `Take one quarter of primary disclosure and read it the way an analyst would: separate what was reported ` +
      `from what was guided, name the dates on every figure, and give the disclosed dependencies the same airtime ` +
      `as the growth. No verdict, no price target, no instruction.`,
    audience_promise:
      `By the end you will be able to read this kind of filing yourself and know which three lines actually matter.`,
    title_options: [
      { title: truncate(`${subject}: What The Filing Actually Says`, 90), why_it_works: 'Concrete, promises the primary source rather than an opinion', overpromise_risk: 'low' },
      { title: truncate(`The Three Lines That Matter In ${subject}\u2019s Quarter`, 90), why_it_works: 'Numbered promise with a bounded scope the video delivers', overpromise_risk: 'low' },
      { title: truncate(`${subject}: The Growth Number And The Dependency Behind It`, 90), why_it_works: 'Signals balance up front; both halves appear in the video', overpromise_risk: 'low' },
      { title: truncate(`How To Read A Quarter Like This One (${subject} Case Study)`, 90), why_it_works: 'Educational framing that matches the channel\u2019s remit', overpromise_risk: 'low' },
    ],
    hook: short
      ? `One line in this quarter did most of the work. One line in the risk factors explains why it is worth reading twice.`
      : `One line in this quarter did most of the work \u2014 and one line in the risk factors explains why that first ` +
        `line is worth reading twice.`,
    outline,
    call_to_action: short
      ? `Full source list in the description.`
      : `The filing links and the full claim list are in the description. Tell me which line you would have led with.`,
  };
}

type ClaimGroups = {
  reported: string[]; guided: string[]; dependency: string[]; context: string[]; definitional: string[];
};

function groupClaims(claims: Claim[]): ClaimGroups {
  const g: ClaimGroups = { reported: [], guided: [], dependency: [], context: [], definitional: [] };
  for (const c of claims) {
    switch (c.claim_type) {
      case 'financial_statement': case 'market_cap': case 'valuation': case 'price_or_performance':
        g.reported.push(c.claim_id); break;
      case 'forecast_or_guidance': case 'rating_or_recommendation':
        g.guided.push(c.claim_id); break;
      case 'insider_or_ownership': case 'causal':
        g.dependency.push(c.claim_id); break;
      case 'definitional':
        g.definitional.push(c.claim_id); break;
      default:
        g.context.push(c.claim_id);
    }
  }
  return g;
}

// ---------------------------------------------------------------------------
// Stage 6 — script
// ---------------------------------------------------------------------------

const OPENERS = [
  'Start with what the filing states.',
  'Here is what the document actually says.',
  'The disclosure is specific on this point.',
  'Read the line itself rather than a summary of it.',
  'The primary source puts it plainly.',
  'Take the sentence as it is written.',
];

const PIVOTS = [
  'That is the reported figure. What it does not tell you is the shape underneath it.',
  'So far, so straightforward. The interesting part is what sits behind it.',
  'That is one line. It is worth asking what has to be true for it to hold.',
  'Take that as given and the next question follows immediately.',
  'Hold that number for a moment, because the next one changes how you read it.',
];

/**
 * Mechanism paragraphs, keyed by what kind of claim they follow.
 *
 * This is the part that turns a list of figures into something worth watching:
 * after every number, explain what that *kind* of number can and cannot tell
 * you. Two variants per type, chosen by a seeded index, so a long video does
 * not repeat the same framing four times.
 */
const MECHANISM: Record<string, string[]> = {
  financial_statement: [
    'A reported figure is the most solid thing in a filing. It has been through the company’s own controls and, at the year end, an auditor’s. What it does not carry is context. It tells you what happened in the period. It does not tell you whether the period was representative, and it does not tell you what the next one looks like.',
    'Reported figures are backward-looking by construction. That is a feature: it is the one part of the document that is not an opinion. The work is in deciding what the figure is evidence of — a durable change in the business, or a quarter that happened to fall a certain way.',
  ],
  forecast_or_guidance: [
    'Guidance sits in a different category entirely. It is the company’s own estimate of its own future, issued under a safe harbour and revised whenever conditions change. Treat it as information about management’s confidence rather than as a result that has already happened.',
    'A guided number is not a small version of a reported number. It is a statement of intent with a range attached. The useful question is not whether the midpoint is right; it is what the company would have to see to move it.',
  ],
  insider_or_ownership: [
    'Concentration disclosure exists because dependency is material. The threshold is not a judgement about whether the relationship is good or bad — a concentrated customer base can be extremely profitable for as long as it lasts. It is a statement that if the relationship ends, it matters.',
    'When a filing names a dependency, it is telling you where the business is fragile, not predicting that the fragility will be tested. Those are different claims, and conflating them is the most common mistake made with this line.',
  ],
  causal: [
    'This is the company’s own account of its own business, which makes it authoritative about the arrangement and not necessarily about the risk. A firm knows who its suppliers are. It does not know, and does not claim to know, the probability that one of them fails.',
    'A causal sentence in a filing is written by people with an interest in how it reads. That does not make it false. It does mean the sentence is evidence about the structure of the business rather than a forecast of what that structure will do.',
  ],
  contextual: [
    'This one comes from outside the company, which is exactly why it is worth having. A filing can only tell you about itself. An independent estimate can tell you whether what you are looking at is unusual — at the cost of being an estimate.',
    'Outside context earns its place by being independent, and pays for it by being less precise. Use it to size the question, not to settle it.',
  ],
  definitional: [
    'That is the mechanism, and it is worth holding on to, because it applies to every filing you will read after this one.',
    'This is the sort of thing worth learning once. The specific company changes; the way the disclosure works does not.',
  ],
  valuation: [
    'Valuation is a ratio, and a ratio has two ends. A change in it can come from the numerator, the denominator, or a change in what the market is willing to assume. The figure alone does not say which.',
  ],
  price_or_performance: [
    'Performance figures are the easiest to quote and the easiest to mislead with, because the answer depends almost entirely on the window you choose. The date attached to this one is not decoration.',
  ],
};

const CHAPTER_INTROS: Record<string, string> = {
  default: 'The evidence for this section comes from the stored source register, and every figure carries the date it refers to.',
};

const CLOSERS = [
  'That is what the evidence supports on this point, and no more than that.',
  'Note what has not been claimed here: nothing about what happens next.',
  'The figure is precise. The conclusion you draw from it should be held more loosely.',
  'One line, one source, one date. That is the standard the rest of this holds to as well.',
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
  const rnd = seededRandom(stableHash(p.editorial.angle + p.brief.reference_date + p.format));
  const pick = <T,>(arr: readonly T[]): T => arr[Math.floor(rnd() * arr.length) % arr.length]!;
  const claimById = new Map(p.approved_claims.map((c) => [c.claim_id, c]));
  const short = p.format === 'short';

  const beats: ScriptBeat[] = [];
  let n = 0;
  const nextId = () => `B-${String(++n).padStart(3, '0')}`;
  const push = (b: Omit<ScriptBeat, 'beat_id'>) => { beats.push({ beat_id: nextId(), ...b }); };

  const title = p.editorial.title_options[0]!.title;

  push({
    chapter: p.editorial.outline[0]!.chapter,
    narration: p.editorial.hook,
    on_screen_text: title, claim_ids: [], visual_intent: 'title_card',
  });

  for (const [ci, chapter] of p.editorial.outline.entries()) {
    if (/disclosure/iu.test(chapter.chapter)) continue;

    if (ci > 0 && !short) {
      push({
        chapter: chapter.chapter,
        narration: `${chapter.chapter}.`,
        on_screen_text: chapter.chapter, claim_ids: [], visual_intent: 'chapter_card',
      });
    }

    const claims = chapter.claim_ids.map((id) => claimById.get(id)).filter((c): c is Claim => Boolean(c));

    if (/bull case and the bear case/iu.test(chapter.chapter)) {
      push({
        chapter: chapter.chapter,
        narration:
          'Set the two readings side by side. This matters more than it sounds, because the supportive case and ' +
          'the cautionary case here are drawing on the same document. They do not disagree about the facts. They ' +
          'disagree about which lines carry the most weight.',
        on_screen_text: 'Same filing, two readings',
        claim_ids: claims.map((c) => c.claim_id), visual_intent: 'comparison_table',
      });
      const pairs = Math.min(3, Math.max(p.brief.bull_case.length, p.brief.bear_case.length));
      for (let i = 0; i < pairs; i += 1) {
        const bullLine = p.brief.bull_case[i];
        const bearLine = p.brief.bear_case[i];
        push({
          chapter: chapter.chapter,
          narration:
            (bullLine ? `The supportive reading takes this: ${lower(stripParens(bullLine))} ` : '') +
            (bearLine ? `The cautionary reading answers with this: ${lower(stripParens(bearLine))} ` : '') +
            'Both sentences are true. Which one you weight more heavily is a judgement, and it should be held as one.',
          on_screen_text: '', claim_ids: claims.map((c) => c.claim_id), visual_intent: 'statement',
        });
      }
      continue;
    }

    if (claims.length === 0) {
      push({
        chapter: chapter.chapter,
        narration: short
          ? 'So here is the thing worth checking in the next filing.'
          : `${pick(PIVOTS)} There are three things that would genuinely change the reading here. All three are ` +
            `checkable against a future document rather than a matter of opinion, which is what makes them worth ` +
            `writing down now.`,
        on_screen_text: 'What would change the picture', claim_ids: [], visual_intent: 'statement',
      });
      for (const q of p.brief.open_questions.slice(0, short ? 1 : 3)) {
        push({ chapter: chapter.chapter, narration: q, on_screen_text: truncate(q, 120), claim_ids: [], visual_intent: 'risk_card' });
      }
      continue;
    }

    for (const [i, claim] of claims.entries()) {
      const lead = i === 0 ? pick(OPENERS) : pick(PIVOTS);
      const asOf = claim.as_of_date ? ` As of ${formatDate(claim.as_of_date)}.` : '';
      push({
        chapter: chapter.chapter,
        narration: `${lead} ${claim.claim_text}${asOf}`,
        on_screen_text: truncate(claim.claim_text, 150),
        claim_ids: [claim.claim_id],
        visual_intent: VISUAL_FOR_TYPE[claim.claim_type] ?? 'statement',
      });

      if (short) continue;

      // The mechanism beat: why this kind of figure behaves the way it does.
      const bank = MECHANISM[claim.claim_type] ?? MECHANISM.contextual!;
      push({
        chapter: chapter.chapter,
        narration: `${pick(bank)}${claim.uncertainty_note ? ` ${capitalise(claim.uncertainty_note)}` : ''}`,
        on_screen_text: '',
        claim_ids: [claim.claim_id],
        visual_intent: claim.claim_type === 'definitional' ? 'quote_card' : 'statement',
      });
    }

    // A closing beat earns its place only where a chapter carried more than one
    // claim. Adding one everywhere is how an explainer starts to feel padded.
    if (!short && claims.length >= 2) {
      push({
        chapter: chapter.chapter,
        narration: `${pick(CLOSERS)} ${CHAPTER_INTROS.default}`,
        on_screen_text: '', claim_ids: [], visual_intent: 'statement',
      });
    }
  }

  push({
    chapter: 'Disclosure',
    narration: p.disclosure_text,
    on_screen_text: 'Research and education only — not financial advice',
    claim_ids: [], visual_intent: 'disclosure',
  });
  push({
    chapter: 'Disclosure',
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
