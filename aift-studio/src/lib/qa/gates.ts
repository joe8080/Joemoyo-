import type { BrandSettings, ClaimRecord, ContentAsset, QualityCheck, SourceDocument, Uuid } from '@/lib/domain';
import type { ReviewerCritique, ScenePlan, Script } from '@/lib/schemas/content';
import { isMaterial } from '@/lib/schemas/content';
import { extractFigures } from './claim-safety';
import { stableId } from '@/lib/util/hash';

/**
 * The quality gates.
 *
 * A job cannot reach `needs_review` while any blocking check fails. Warnings are
 * recorded and shown but do not hold the job. Each check states what failed, who
 * or what caused it, and what to do about it — a gate that only says "failed"
 * gets ignored, and an ignored gate is not a gate.
 */

export type GateContext = {
  contentJobId: Uuid;
  format: 'deep_dive' | 'short';
  brand: BrandSettings;
  script: Script;
  plan: ScenePlan;
  claims: ClaimRecord[];
  sources: SourceDocument[];
  assets: ContentAsset[];
  critique: ReviewerCritique | null;
  /** Exact strings the chart renderer will draw, keyed by scene id. */
  renderedChartValues: Map<string, string[]>;
  audioPeakDbfs: number;
  /** Measured programme loudness of the delivered mix. */
  loudness: { integratedLufs: number; truePeakDbtp: number; loudnessRange: number };
  targetLufs: number;
  musicEnabled: boolean;
  duckDb: number;
  /** beat_id → measured narration seconds, for the scene-coverage check. */
  narrationByBeat: Map<string, number>;
  /** Cue start times from the produced SRT, in order of appearance. */
  captionCueStartsMs: number[];
  videoBytes: number;
  videoAspect: string;
  narrationSeconds: number;
  runAt: string;
};

type Draft = Omit<QualityCheck, 'id' | 'content_job_id' | 'run_at' | 'resolved_at'>;

const ok = (gate: string, check_name: string, message: string): Draft => ({
  gate, check_name, severity: 'blocking', result: 'pass',
  details: { message, offenders: [], remediation: '' },
});

const fail = (gate: string, check_name: string, message: string, offenders: string[], remediation: string, severity: QualityCheck['severity'] = 'blocking'): Draft => ({
  gate, check_name, severity, result: 'fail', details: { message, offenders, remediation },
});

const warn = (gate: string, check_name: string, message: string, offenders: string[], remediation: string): Draft =>
  fail(gate, check_name, message, offenders, remediation, 'warning');

// ---------------------------------------------------------------------------

export function runAllGates(ctx: GateContext): QualityCheck[] {
  const drafts = [
    ...evidenceGate(ctx),
    ...financialSafetyGate(ctx),
    ...complianceGate(ctx),
    ...scriptGate(ctx),
    ...visualAccuracyGate(ctx),
    ...technicalGate(ctx),
    ...brandGate(ctx),
    ...publishingGate(ctx),
    ...reviewerGate(ctx),
  ];
  return drafts.map((d) => ({
    ...d,
    id: stableId('aift_quality_check', `${ctx.contentJobId}:${d.gate}:${d.check_name}`),
    content_job_id: ctx.contentJobId,
    run_at: ctx.runAt,
    resolved_at: null,
  }));
}

export function isBlocked(checks: QualityCheck[]): boolean {
  return checks.some((c) => c.result === 'fail' && c.severity === 'blocking');
}

// ---------------------------------------------------------------------------

function evidenceGate(ctx: GateContext): Draft[] {
  const out: Draft[] = [];
  const byId = new Map(ctx.claims.map((c) => [c.claim_id, c]));
  const cited = new Set(ctx.script.beats.flatMap((b) => b.claim_ids));

  const unknown = [...cited].filter((id) => !byId.has(id));
  out.push(unknown.length === 0
    ? ok('evidence', 'cited_claims_exist', 'Every claim id in the script resolves to a stored claim record.')
    : fail('evidence', 'cited_claims_exist', 'The script cites claim ids that do not exist in the claim ledger.', unknown,
        'Remove the citation, or re-run the evidence stage so the claim is created and verified.'));

  const unsafe = [...cited].map((id) => byId.get(id)).filter((c): c is ClaimRecord => Boolean(c) && !c!.is_public_safe);
  out.push(unsafe.length === 0
    ? ok('evidence', 'cited_claims_public_safe', 'Every cited claim passed the public-safety evaluation.')
    : fail('evidence', 'cited_claims_public_safe', 'The script cites claims that were not cleared as public-safe.',
        unsafe.map((c) => `${c.claim_id}: ${c.public_safe_reason}`),
        'Supply the missing evidence for the claim, or rewrite the beat without it.'));

  const undated = ctx.claims.filter((c) => isMaterial(c.claim_type) && cited.has(c.claim_id) && !c.as_of_date);
  out.push(undated.length === 0
    ? ok('evidence', 'material_claims_dated', 'Every material claim used on screen carries an as-of date.')
    : fail('evidence', 'material_claims_dated', 'A material claim used in the script has no as-of date.',
        undated.map((c) => c.claim_id), 'Add the as-of date from the source, or drop the claim.'));

  const badSources = ctx.sources.filter((s) => s.retrieval_status !== 'fetched');
  out.push(badSources.length === 0
    ? ok('evidence', 'sources_retrieved', 'Every source in the register was fetched and stored.')
    : warn('evidence', 'sources_retrieved', 'Some sources in the register were not retrieved.',
        badSources.map((s) => `${s.canonical_url} (${s.retrieval_status})`),
        'Retry retrieval or remove the source. Claims depending on it are already blocked.'));

  // Figures spoken with no claim attached — the classic way an unsourced number
  // reaches an audience.
  const orphanFigures: string[] = [];
  for (const beat of ctx.script.beats) {
    if (beat.claim_ids.length > 0) continue;
    const figures = extractFigures(beat.narration);
    if (figures.length > 0) orphanFigures.push(`${beat.beat_id}: ${figures.join(', ')}`);
  }
  out.push(orphanFigures.length === 0
    ? ok('evidence', 'no_unsourced_figures', 'No spoken figure appears without a linked claim.')
    : fail('evidence', 'no_unsourced_figures', 'The narration states figures that are not linked to any claim.',
        orphanFigures, 'Attach the claim id carrying the figure, its source and its as-of date, or remove the figure.'));

  return out;
}

// ---------------------------------------------------------------------------

/**
 * Private-finance leakage. This is the gate that matters most: it scans the
 * public-facing copy, not the private context, because that is where an
 * accident actually reaches an audience.
 */
const PRIVATE_PATTERNS: Array<{ label: string; re: RegExp }> = [
  { label: 'portfolio value', re: /\b(my|our|the owner'?s)\s+(portfolio|holdings?|account|position)\b/iu },
  { label: 'personal holding statement', re: /\bI (own|hold|bought|sold|added|trimmed)\b/iu },
  { label: 'account identifier', re: /\b(account|acct)\.?\s*(number|no\.?|#)\s*[:#]?\s*[\w-]{4,}/iu },
  { label: 'broker name reference', re: /\b(my|our)\s+(broker|brokerage|isa|sipp|401k|ira)\b/iu },
  { label: 'personal position size', re: /\b\d+(\.\d+)?\s*(shares|units)\s+(of|in)\s+(my|our)\b/iu },
  { label: 'personal p&l', re: /\b(my|our)\s+(profit|loss|p\/?l|pnl|return)\b/iu },
  { label: 'statement reference', re: /\b(broker|account)\s+statement\b/iu },
];

function financialSafetyGate(ctx: GateContext): Draft[] {
  const surfaces = publicSurfaces(ctx);
  const offenders: string[] = [];
  for (const { where, text } of surfaces) {
    for (const p of PRIVATE_PATTERNS) {
      const m = text.match(p.re);
      if (m) offenders.push(`${where}: ${p.label} — "${m[0]}"`);
    }
  }
  return [offenders.length === 0
    ? ok('financial_safety', 'no_private_finance_in_public_copy',
        'No portfolio, holdings, account, broker or personal p&l reference appears in any public-facing surface.')
    : fail('financial_safety', 'no_private_finance_in_public_copy',
        'Public-facing copy contains what reads as private financial information.', offenders,
        'Remove it. Private portfolio data is context for the owner only and must never become public content.')];
}

// ---------------------------------------------------------------------------

function complianceGate(ctx: GateContext): Draft[] {
  const out: Draft[] = [];
  const surfaces = publicSurfaces(ctx);
  const narration = ctx.script.beats.map((b) => b.narration).join(' ');

  const disclosureKey = ctx.brand.disclosure_text.slice(0, 48).toLowerCase();
  const hasDisclosure = narration.toLowerCase().includes(disclosureKey);
  out.push(hasDisclosure
    ? ok('compliance', 'disclosure_present', 'The educational disclosure is spoken in the narration.')
    : fail('compliance', 'disclosure_present', 'The required educational disclosure is missing from the narration.',
        [], 'Add the disclosure beat verbatim from brand settings before the outro.'));

  const inDescription = ctx.script.description_markdown.toLowerCase().includes(disclosureKey);
  out.push(inDescription
    ? ok('compliance', 'disclosure_in_description', 'The disclosure also appears in the video description.')
    : fail('compliance', 'disclosure_in_description', 'The disclosure does not appear in the description.',
        [], 'Append the disclosure to the description markdown.'));

  const bannedHits: string[] = [];
  for (const { where, text } of surfaces) {
    const lower = text.toLowerCase();
    for (const phrase of ctx.brand.banned_phrases) {
      if (phrase && lower.includes(phrase.toLowerCase())) bannedHits.push(`${where}: "${phrase}"`);
    }
  }
  out.push(bannedHits.length === 0
    ? ok('compliance', 'no_banned_phrases', 'No banned or instruction-shaped phrase appears in public copy.')
    : fail('compliance', 'no_banned_phrases', 'Public copy contains banned instruction-shaped language.', bannedHits,
        'Rewrite to describe evidence rather than instruct the viewer.'));

  // Direct second-person instructions to trade.
  const instructionRe = /\b(you should|you must|you need to|make sure you|i(?:'| a)m telling you to)\s+(buy|sell|short|add|trim|cut|dump|accumulate|exit)\b/iu;
  const instructionHits = surfaces.filter((s) => instructionRe.test(s.text)).map((s) => s.where);
  out.push(instructionHits.length === 0
    ? ok('compliance', 'no_trade_instruction', 'No copy instructs the viewer to buy, sell or adjust a position.')
    : fail('compliance', 'no_trade_instruction', 'Copy instructs the viewer to take a trading action.', instructionHits,
        'Replace the instruction with an evidence statement and a stated uncertainty.'));

  const certaintyRe = /\b(will (?:definitely|certainly|surely)|is guaranteed to|cannot (?:fail|lose)|is going to (?:double|triple|soar|crash))\b/iu;
  const certaintyHits = surfaces.filter((s) => certaintyRe.test(s.text)).map((s) => s.where);
  out.push(certaintyHits.length === 0
    ? ok('compliance', 'no_performance_certainty', 'No copy asserts certainty about future performance.')
    : fail('compliance', 'no_performance_certainty', 'Copy asserts certainty about future performance.', certaintyHits,
        'State the evidence and label the projection as an estimate.'));

  return out;
}

// ---------------------------------------------------------------------------

function scriptGate(ctx: GateContext): Draft[] {
  const out: Draft[] = [];
  const target = ctx.format === 'short'
    ? { minSec: 30, maxSec: 90, label: '45–75s (tolerance 30–90s)' }
    : { minSec: 7 * 60, maxSec: 14 * 60, label: '8–12 min (tolerance 7–14 min)' };

  const dur = ctx.plan.total_ms / 1000;
  out.push(dur >= target.minSec && dur <= target.maxSec
    ? ok('script', 'duration_in_band', `Runtime ${fmt(dur)} sits inside the ${target.label} band.`)
    : fail('script', 'duration_in_band', `Runtime ${fmt(dur)} is outside the ${target.label} band.`, [],
        'Add or cut beats. Duration is measured from narration, so trimming words is what moves it.'));

  const risky = ctx.script.beats.some((b) => /risk|however|cautionary|does not|dependency|open question/iu.test(b.narration));
  out.push(risky
    ? ok('script', 'counter_case_present', 'The script contains an explicit risk or counter-case segment.')
    : fail('script', 'counter_case_present', 'The script presents no counter-case or risk discussion.', [],
        'Add an evidence-linked risk or bear-case chapter.'));

  const title = ctx.script.working_title;
  const overpromise = /\b(secret|nobody is telling you|will make you rich|10x|guaranteed|shocking truth|before it'?s too late)\b/iu;
  out.push(!overpromise.test(title)
    ? ok('script', 'title_not_overpromising', 'The working title does not overpromise.')
    : fail('script', 'title_not_overpromising', 'The working title uses overpromising language.', [title],
        'Choose a title option whose overpromise risk is rated low.'));

  const wpm = wordsPerMinute(ctx.script, ctx.narrationSeconds);
  out.push(wpm >= 120 && wpm <= 200
    ? ok('script', 'reading_pace_reasonable', `Reading pace is ${Math.round(wpm)} words per minute.`)
    : warn('script', 'reading_pace_reasonable', `Reading pace of ${Math.round(wpm)} wpm is outside the comfortable 120–200 band.`,
        [], 'Adjust the voice rate or rebalance narration across beats.'));

  return out;
}

// ---------------------------------------------------------------------------

function visualAccuracyGate(ctx: GateContext): Draft[] {
  const out: Draft[] = [];

  // 1. No generated image may be used where a number is displayed.
  const generatedAssets = ctx.assets.filter((a) => a.generator.includes('broll') || a.asset_type === 'broll_prompt');
  const numericCompositions = new Set(['line_chart', 'bar_chart', 'stat_reveal', 'comparison_table']);
  const brollScenes = ctx.plan.scenes.filter((s) => s.composition === 'broll');
  const brollWithData = brollScenes.filter((s) => s.data !== null || s.stat !== null);
  out.push(brollWithData.length === 0
    ? ok('visual', 'no_generated_image_as_chart',
        `${generatedAssets.length} generated asset(s) present, none carrying numeric data. Every numeric composition is code-rendered.`)
    : fail('visual', 'no_generated_image_as_chart', 'A generated B-roll scene carries numeric data.',
        brollWithData.map((s) => s.scene_id),
        'Move the figures to a code-rendered chart or stat composition. Generated imagery is decorative only.'));

  // 2. Every number on screen must exist in the claim ledger.
  const ledger = new Set(ctx.claims.flatMap((c) => extractFigures(c.claim_text).map(norm)));
  for (const s of ctx.plan.scenes) {
    if (!numericCompositions.has(s.composition)) continue;
    const rendered = ctx.renderedChartValues.get(s.scene_id) ?? [];
    const statValue = s.stat ? [s.stat.value] : [];
    const shown = [...rendered, ...statValue].map(norm);
    const unmatched = shown.filter((v) => !ledger.has(v));
    // Chart axis ticks are derived from the series, not claimed individually, so
    // only the highlighted/stat values are required to match the ledger.
    const mustMatch = statValue.map(norm).filter((v) => !ledger.has(v));
    if (mustMatch.length > 0) {
      out.push(fail('visual', `scene_values_match_claims:${s.scene_id}`,
        `Scene ${s.scene_id} displays a headline figure that does not appear in any stored claim.`,
        mustMatch, 'Correct the figure, or add the claim with its source and as-of date.'));
    }
    if (unmatched.length > 0 && mustMatch.length === 0) {
      out.push(warn('visual', `scene_axis_values_derived:${s.scene_id}`,
        `Scene ${s.scene_id} shows ${unmatched.length} axis/series value(s) derived from the registry series rather than quoted in a claim.`,
        unmatched.slice(0, 8), 'This is expected for axis ticks. Confirm the series is the one the claim refers to.'));
    }
  }
  if (!out.some((d) => d.gate === 'visual' && d.check_name.startsWith('scene_values_match_claims'))) {
    out.push(ok('visual', 'scene_values_match_claims', 'Every headline figure on screen resolves to a stored claim.'));
  }

  // 3. Every data scene must display its source and as-of date.
  const missingStamp = ctx.plan.scenes.filter(
    (s) => (s.data !== null && (!s.data.source_label || !s.data.as_of_date)) || (s.stat !== null && (!s.stat.source_label || !s.stat.as_of_date)),
  );
  out.push(missingStamp.length === 0
    ? ok('visual', 'data_scenes_stamped', 'Every data scene carries a visible source label and as-of date.')
    : fail('visual', 'data_scenes_stamped', 'A data scene is missing its source label or as-of date.',
        missingStamp.map((s) => s.scene_id), 'Attach the source and as-of date from the claim to the scene.'));

  // 4. B-roll prompts may not request factual content.
  const promptRe = /\b(chart|graph|percent|%|price|revenue|earnings|ticker|logo|screenshot|dashboard|number|figure)\b/iu;
  const badPrompts = ctx.plan.scenes.filter((s) => s.broll_prompt && promptRe.test(s.broll_prompt) && !/no (charts|numbers|logos)/iu.test(s.broll_prompt));
  out.push(badPrompts.length === 0
    ? ok('visual', 'broll_prompts_non_factual', 'No B-roll prompt requests charts, figures, logos or screens.')
    : fail('visual', 'broll_prompts_non_factual', 'A B-roll prompt asks for factual or brand content.',
        badPrompts.map((s) => s.scene_id), 'Rewrite the prompt as pure atmosphere with an explicit no-text, no-chart constraint.'));

  return out;
}

// ---------------------------------------------------------------------------

function technicalGate(ctx: GateContext): Draft[] {
  const out: Draft[] = [];
  const expectedAspect = ctx.format === 'short' ? '9:16' : '16:9';

  out.push(ctx.videoAspect === expectedAspect
    ? ok('technical', 'aspect_ratio', `Video is ${expectedAspect} as required for the ${ctx.format} format.`)
    : fail('technical', 'aspect_ratio', `Video aspect ${ctx.videoAspect} does not match the required ${expectedAspect}.`,
        [ctx.videoAspect], 'Re-render with the format’s canvas dimensions.'));

  out.push(ctx.videoBytes > 10_000
    ? ok('technical', 'video_present', `Rendered video is ${(ctx.videoBytes / 1_048_576).toFixed(1)} MB.`)
    : fail('technical', 'video_present', 'The rendered video file is missing or implausibly small.', [String(ctx.videoBytes)],
        'Re-run the render stage and check the encoder log.'));

  const hasCaptions = ctx.assets.some((a) => a.asset_type === 'captions_srt' && a.bytes > 100);
  out.push(hasCaptions
    ? ok('technical', 'captions_present', 'An SRT caption file was produced.')
    : fail('technical', 'captions_present', 'No caption file was produced.', [], 'Re-run caption generation.'));

  // Loudness, not peak. YouTube normalises playback to about -14 LUFS, so a
  // track that peaks politely can still arrive quiet or crushed — and a peak
  // check would pass both.
  const { integratedLufs, truePeakDbtp, loudnessRange } = ctx.loudness;
  if (!Number.isFinite(integratedLufs)) {
    out.push(warn('technical', 'programme_loudness', 'The programme is silent: no narration and no music bed.', [],
      'Expected with no TTS credential and music disabled. Configure AIFT_TTS_PROVIDER before publishing from this pack.'));
  } else {
    const drift = Math.abs(integratedLufs - ctx.targetLufs);
    out.push(drift <= 2
      ? ok('technical', 'programme_loudness',
          `Programme is ${integratedLufs.toFixed(1)} LUFS against a ${ctx.targetLufs} LUFS target, range ${loudnessRange.toFixed(1)} LU.`)
      : fail('technical', 'programme_loudness',
          `Programme is ${integratedLufs.toFixed(1)} LUFS, ${drift.toFixed(1)} LU from the ${ctx.targetLufs} LUFS target.`,
          [`${integratedLufs.toFixed(1)} LUFS`],
          'Re-normalise the mix. A pack this far off target will be re-levelled on playback, undoing the balance you approved.'));

    out.push(truePeakDbtp <= -1.0
      ? ok('technical', 'true_peak', `True peak is ${truePeakDbtp.toFixed(1)} dBTP, below the -1.0 dBTP ceiling.`)
      : fail('technical', 'true_peak', `True peak is ${truePeakDbtp.toFixed(1)} dBTP, above the -1.0 dBTP ceiling.`,
          [`${truePeakDbtp.toFixed(1)} dBTP`],
          'Lower the mix gain. Above the ceiling, lossy encoding for playback will clip.'));
  }

  // Speech has to survive the bed. This is the "maintain speech intelligibility"
  // rule from the brief, expressed as a number rather than a note.
  if (ctx.musicEnabled) {
    const music = ctx.assets.find((a) => a.asset_type === 'music_wav');
    out.push(music && music.licence_notes.length > 10
      ? ok('technical', 'music_licensed', `Music bed carries its licence and provenance: ${music.generator}.`)
      : fail('technical', 'music_licensed', 'A music bed is present with no licence or provenance recorded.',
          [music?.storage_key ?? 'music_wav missing'],
          'Record the licence on the asset. A track whose rights nobody can state cannot ship.'));

    const duckDb = Math.abs(ctx.duckDb);
    out.push(duckDb >= 6
      ? ok('technical', 'speech_priority', `The bed ducks ${duckDb.toFixed(0)} dB under narration.`)
      : fail('technical', 'speech_priority', `The bed only ducks ${duckDb.toFixed(0)} dB under narration.`,
          [`${duckDb.toFixed(0)} dB`], 'Increase the duck depth to at least 6 dB or the narration will fight the bed.'));
  }

  // The quality report and package manifest are this gate's own downstream
  // outputs, so they are not listed: a gate cannot require its own result.
  const requiredAssets: Array<ContentAsset['asset_type']> = [
    'script_markdown', 'script_json', 'scene_plan', 'narration_text', 'captions_srt',
    'chapters_json', 'description_markdown', 'source_manifest', 'thumbnail_brief',
    'composition_html', 'video_mp4',
  ];
  const missing = requiredAssets.filter((t) => !ctx.assets.some((a) => a.asset_type === t));
  out.push(missing.length === 0
    ? ok('technical', 'pack_complete', 'Every required asset is present in the content pack.')
    : fail('technical', 'pack_complete', 'The content pack is missing required assets.', missing,
        'Re-run the render stage; each missing asset names the producing step.'));

  // Overlapping narration is the failure this catches: a scene shorter than the
  // speech it carries bleeds into the next one, and the captions go with it.
  const overrun = ctx.plan.scenes.filter((s) => {
    const spoken = (ctx.narrationByBeat.get(s.beat_ids[0] ?? '') ?? 0) * 1000;
    return spoken > 0 && spoken + 200 > s.duration_ms;
  });
  out.push(overrun.length === 0
    ? ok('technical', 'scenes_cover_narration', 'Every scene is long enough for the narration it carries.')
    : fail('technical', 'scenes_cover_narration',
        'A scene is shorter than its narration, so speech and captions overlap the next scene.',
        overrun.map((s) => `${s.scene_id}: ${(s.duration_ms / 1000).toFixed(1)}s scene, ${((ctx.narrationByBeat.get(s.beat_ids[0] ?? '') ?? 0)).toFixed(1)}s spoken`),
        'Lengthen the scene to at least the narration duration, or split the beat.'));

  // Cues must advance. A backwards SRT is rejected by most players outright.
  const srtAsset = ctx.assets.find((a) => a.asset_type === 'captions_srt');
  const cueOrder = ctx.captionCueStartsMs;
  const ordered = cueOrder.every((v, i) => i === 0 || v >= cueOrder[i - 1]!);
  out.push(ordered
    ? ok('technical', 'caption_cues_ordered', `${cueOrder.length} caption cues, all in ascending order.`)
    : fail('technical', 'caption_cues_ordered', 'Caption cues are not in ascending order.',
        [srtAsset?.storage_key ?? 'captions.srt'], 'Fix the scene timings; a cue cannot start before the previous one.'));

  const badHash = ctx.assets.filter((a) => a.bytes > 0 && !/^[0-9a-f]{64}$/u.test(a.sha256));
  out.push(badHash.length === 0
    ? ok('technical', 'asset_hashes', 'Every stored asset carries a SHA-256 content hash.')
    : fail('technical', 'asset_hashes', 'Assets are missing content hashes.', badHash.map((a) => a.storage_key),
        'Re-store the asset through the storage provider so the hash is recorded.'));

  return out;
}

// ---------------------------------------------------------------------------

function brandGate(ctx: GateContext): Draft[] {
  const out: Draft[] = [];
  const style = ctx.brand.visual_style;

  const hexes = [style.background, style.surface, style.ink, style.ink_dim, style.accent, style.accent_2];
  const badHex = hexes.filter((h) => !/^#[0-9a-fA-F]{6}$/u.test(h));
  out.push(badHex.length === 0
    ? ok('brand', 'palette_valid', 'The brand palette is complete and well-formed.')
    : fail('brand', 'palette_valid', 'The brand palette contains malformed colours.', badHex,
        'Fix the values in Brand Studio; the renderer writes them straight into the stylesheet.'));

  const hasChannel = ctx.script.description_markdown.includes(ctx.brand.channel_name)
    || ctx.script.beats.some((b) => b.on_screen_text.includes(ctx.brand.channel_name));
  out.push(hasChannel
    ? ok('brand', 'channel_named', 'The channel name appears in the pack.')
    : warn('brand', 'channel_named', 'The channel name does not appear in the description or on screen.', [],
        'Add the channel name to the outro card or the description.'));

  out.push(ctx.script.tags.length >= 5
    ? ok('brand', 'tags_present', `${ctx.script.tags.length} tags supplied.`)
    : warn('brand', 'tags_present', 'Fewer than five tags were supplied.', [], 'Add tags in the editorial stage.'));

  return out;
}

// ---------------------------------------------------------------------------

/**
 * The publishing gate is a runtime restatement of a property the build already
 * enforces (`scripts/guard-no-publish.ts`). It exists so that the impossibility
 * is visible in the review room, not only in CI.
 */
function publishingGate(ctx: GateContext): Draft[] {
  const uploadish = ctx.assets.filter((a) => /youtube|upload|publish|videos\.insert/iu.test(a.storage_key + a.generator));
  return [
    uploadish.length === 0
      ? ok('publishing', 'no_upload_path',
          'No upload, scheduling or publication step exists. This build has no YouTube credentials, no upload scope and no call to videos.insert.')
      : fail('publishing', 'no_upload_path', 'An asset or generator references a publishing path.',
          uploadish.map((a) => a.storage_key), 'Remove it. Version one produces packages for manual upload only.'),
  ];
}

// ---------------------------------------------------------------------------

function reviewerGate(ctx: GateContext): Draft[] {
  if (!ctx.critique) {
    return [warn('reviewer', 'independent_critique', 'No independent reviewer critique was produced.', [],
      'Run the QA stage with a review-role model configured.')];
  }
  const blocking = ctx.critique.findings.filter((f) => f.severity === 'blocking');
  return [
    blocking.length === 0
      ? ok('reviewer', 'independent_critique',
          `Independent reviewer verdict: ${ctx.critique.verdict}. ${ctx.critique.findings.length} finding(s), none blocking.`)
      : fail('reviewer', 'independent_critique',
          `Independent reviewer returned "${ctx.critique.verdict}" with ${blocking.length} blocking finding(s).`,
          blocking.map((f) => `${f.area}${f.beat_id ? ` @${f.beat_id}` : ''}: ${f.detail}`),
          'Address each finding, then re-run QA. The reviewer runs on a separate model and prompt from the writer.'),
  ];
}

// ---------------------------------------------------------------------------

function publicSurfaces(ctx: GateContext): Array<{ where: string; text: string }> {
  return [
    ...ctx.script.beats.map((b) => ({ where: `narration:${b.beat_id}`, text: b.narration })),
    ...ctx.script.beats.filter((b) => b.on_screen_text).map((b) => ({ where: `on_screen:${b.beat_id}`, text: b.on_screen_text })),
    { where: 'title', text: ctx.script.working_title },
    { where: 'description', text: ctx.script.description_markdown },
    { where: 'tags', text: ctx.script.tags.join(', ') },
    ...ctx.plan.scenes.filter((s) => s.headline).map((s) => ({ where: `scene:${s.scene_id}`, text: `${s.headline} ${s.subhead}` })),
  ];
}

function norm(s: string): string {
  return s.toLowerCase().replace(/\s+/gu, '').replace(/,/gu, '')
    .replace(/percent|per cent/gu, '%').replace(/billion/gu, 'bn').replace(/million/gu, 'm');
}

function wordsPerMinute(script: Script, narrationSeconds: number): number {
  const words = script.beats.reduce((n, b) => n + b.narration.trim().split(/\s+/u).filter(Boolean).length, 0);
  return narrationSeconds > 0 ? (words / narrationSeconds) * 60 : 0;
}

function fmt(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m}m ${String(s).padStart(2, '0')}s`;
}
