import type { Claim } from '@/lib/schemas/content';
import { isMaterial } from '@/lib/schemas/content';
import type { SourceDocument } from '@/lib/domain';

export type SafetyVerdict = { isPublicSafe: boolean; reason: string };

/**
 * Numbers a viewer would hear as a fact: percentages, money, plain quantities
 * and multiples. Deliberately excludes bare years, which are context rather
 * than measurements.
 */
export function extractFigures(text: string): string[] {
  const out: string[] = [];
  const re = /(?:[$£€]\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:bn|billion|m|million|k|trillion))?)|(?:\d[\d,]*(?:\.\d+)?\s?(?:%|per cent|percent|bn|billion|million|basis points|bps|weeks|x))/giu;
  for (const m of text.matchAll(re)) out.push(m[0].trim());
  return out;
}

function normaliseFigure(f: string): string {
  return f
    .toLowerCase()
    .replace(/\s+/gu, '')
    .replace(/,/gu, '')
    .replace(/percent|per cent/gu, '%')
    .replace(/billion/gu, 'bn')
    .replace(/million/gu, 'm')
    .replace(/basis points/gu, 'bps');
}

/**
 * Does the stored excerpt actually contain every figure the claim asserts?
 *
 * This is the check that catches the failure mode nobody notices: a citation
 * that exists, is real, and simply does not say what the sentence says.
 */
export function excerptSupportsClaim(claim: Claim): { ok: boolean; missing: string[] } {
  const claimFigures = extractFigures(claim.claim_text).map(normaliseFigure);
  if (claimFigures.length === 0) return { ok: true, missing: [] };
  const haystack = normaliseFigure(claim.source_excerpt);
  const missing = claimFigures.filter((f) => !haystack.includes(f));
  return { ok: missing.length === 0, missing };
}

export const MIN_MATERIAL_CONFIDENCE = 0.6;

/**
 * The gate a claim must pass before a writer is allowed to see it. A claim that
 * fails is not softened or footnoted — it is withheld from the script entirely.
 */
export function evaluateClaim(claim: Claim, sources: SourceDocument[]): SafetyVerdict {
  const material = isMaterial(claim.claim_type);

  if (!material) {
    if (claim.claim_type === 'definitional') return { isPublicSafe: true, reason: 'definitional/educational claim; no market evidence required' };
    if (claim.source_document_ids.length === 0) {
      return { isPublicSafe: true, reason: 'contextual claim carried without a figure' };
    }
  }

  if (material) {
    if (claim.source_document_ids.length === 0) {
      return { isPublicSafe: false, reason: 'material claim has no linked source document' };
    }
    if (!claim.source_excerpt.trim()) {
      return { isPublicSafe: false, reason: 'material claim has no stored source excerpt' };
    }
    if (!claim.as_of_date) {
      return { isPublicSafe: false, reason: 'material claim has no as-of date' };
    }
    if (claim.confidence < MIN_MATERIAL_CONFIDENCE) {
      return { isPublicSafe: false, reason: `confidence ${claim.confidence.toFixed(2)} is below the ${MIN_MATERIAL_CONFIDENCE} threshold for material claims` };
    }
  }

  const linked = claim.source_document_ids
    .map((id) => sources.find((s) => s.id === id))
    .filter((s): s is SourceDocument => Boolean(s));

  if (claim.source_document_ids.length > 0 && linked.length !== claim.source_document_ids.length) {
    return { isPublicSafe: false, reason: 'claim references a source document that is not in the stored source register' };
  }
  if (linked.some((s) => s.retrieval_status !== 'fetched')) {
    return { isPublicSafe: false, reason: 'claim cites a source that was not successfully retrieved and stored' };
  }
  if (material && linked.some((s) => !s.published_at)) {
    return { isPublicSafe: false, reason: 'material claim cites a source with no publication date' };
  }

  const support = excerptSupportsClaim(claim);
  if (!support.ok) {
    return { isPublicSafe: false, reason: `stored excerpt does not contain the figure(s) the claim asserts: ${support.missing.join(', ')}` };
  }

  // Two-source rule: a material claim resting on non-primary evidence alone
  // needs corroboration.
  const primaryTiers = new Set(['primary_filing', 'primary_company', 'primary_regulator']);
  if (material && linked.length > 0 && !linked.some((s) => primaryTiers.has(s.source_tier)) && linked.length < 2) {
    return { isPublicSafe: false, reason: 'material non-primary claim needs two independent sources' };
  }

  return { isPublicSafe: true, reason: 'evidence complete: linked source, stored excerpt containing the figure, publication date, as-of date and sufficient confidence' };
}
