import { describe, expect, it } from 'vitest';
import type { Claim } from '@/lib/schemas/content';
import type { SourceDocument } from '@/lib/domain';
import { evaluateClaim, excerptSupportsClaim, extractFigures } from '@/lib/qa/claim-safety';

const source = (over: Partial<SourceDocument> = {}): SourceDocument => ({
  id: 'src-1', research_job_id: 'rj-1', canonical_url: 'https://example.gov/filing',
  publisher: 'Regulator', published_at: '2026-07-30', accessed_at: '2026-08-14T00:00:00.000Z',
  source_tier: 'primary_filing', title: 'Filing', excerpt: '', content_hash: 'abc',
  licence_notes: '', retrieval_status: 'fetched', ...over,
});

const claim = (over: Partial<Claim> = {}): Claim => ({
  claim_id: 'C-001',
  claim_text: 'Revenue was $4.61 billion in the quarter.',
  claim_type: 'financial_statement',
  source_document_ids: ['src-1'],
  source_excerpt: 'Revenue for the third quarter of fiscal 2026 was $4.61 billion.',
  as_of_date: '2026-06-27',
  confidence: 0.9,
  uncertainty_note: '',
  ...over,
});

describe('figure extraction', () => {
  it('finds money, percentages and quantities but not bare years', () => {
    expect(extractFigures('Revenue was $4.61 billion, up 32% from 2025.')).toEqual(
      expect.arrayContaining(['$4.61 billion', '32%']),
    );
    expect(extractFigures('The 2026 filing was published in 2026.')).toEqual([]);
  });
});

describe('excerpt-supports-claim', () => {
  it('passes when every asserted figure is in the excerpt', () => {
    expect(excerptSupportsClaim(claim()).ok).toBe(true);
  });

  it('catches a real citation that does not say what the sentence says', () => {
    const c = claim({ claim_text: 'Revenue was $5.90 billion in the quarter.' });
    const r = excerptSupportsClaim(c);
    expect(r.ok).toBe(false);
    expect(r.missing.join(' ')).toContain('5.90');
  });

  it('normalises billion/bn and thousands separators before comparing', () => {
    const c = claim({
      claim_text: 'Commitments reached $6,100 million.',
      source_excerpt: 'Purchase commitments totalled $6,100m as of the period end.',
    });
    expect(excerptSupportsClaim(c).ok).toBe(true);
  });

  it('passes a claim with no figures at all', () => {
    expect(excerptSupportsClaim(claim({ claim_text: 'The company describes a supplier dependency.', source_excerpt: 'x' })).ok).toBe(true);
  });
});

describe('public-safety evaluation', () => {
  it('clears a fully evidenced material claim', () => {
    const v = evaluateClaim(claim(), [source()]);
    expect(v.isPublicSafe).toBe(true);
  });

  it('blocks a material claim with no source', () => {
    const v = evaluateClaim(claim({ source_document_ids: [] }), [source()]);
    expect(v.isPublicSafe).toBe(false);
    expect(v.reason).toMatch(/no linked source/u);
  });

  it('blocks a material claim with no as-of date', () => {
    const v = evaluateClaim(claim({ as_of_date: null }), [source()]);
    expect(v.isPublicSafe).toBe(false);
    expect(v.reason).toMatch(/as-of date/u);
  });

  it('blocks a material claim whose excerpt is missing', () => {
    const v = evaluateClaim(claim({ source_excerpt: '   ' }), [source()]);
    expect(v.isPublicSafe).toBe(false);
    expect(v.reason).toMatch(/excerpt/u);
  });

  it('blocks a material claim below the confidence threshold', () => {
    const v = evaluateClaim(claim({ confidence: 0.4 }), [source()]);
    expect(v.isPublicSafe).toBe(false);
    expect(v.reason).toMatch(/confidence/u);
  });

  it('blocks a claim citing a source that failed retrieval', () => {
    const v = evaluateClaim(claim(), [source({ retrieval_status: 'failed' })]);
    expect(v.isPublicSafe).toBe(false);
    expect(v.reason).toMatch(/not successfully retrieved/u);
  });

  it('blocks a claim citing a source that is not in the register', () => {
    const v = evaluateClaim(claim({ source_document_ids: ['ghost'] }), [source()]);
    expect(v.isPublicSafe).toBe(false);
    expect(v.reason).toMatch(/not in the stored source register/u);
  });

  it('blocks a material claim whose excerpt contradicts the figure', () => {
    const v = evaluateClaim(claim({ claim_text: 'Revenue was $9.99 billion.' }), [source()]);
    expect(v.isPublicSafe).toBe(false);
    expect(v.reason).toMatch(/does not contain the figure/u);
  });

  it('requires two sources for a material claim resting only on non-primary evidence', () => {
    const specialist = source({ source_tier: 'specialist' });
    const v = evaluateClaim(claim(), [specialist]);
    expect(v.isPublicSafe).toBe(false);
    expect(v.reason).toMatch(/two independent sources/u);

    const two = evaluateClaim(
      claim({ source_document_ids: ['src-1', 'src-2'] }),
      [specialist, source({ id: 'src-2', source_tier: 'journalism' })],
    );
    expect(two.isPublicSafe).toBe(true);
  });

  it('lets a definitional claim through without market evidence', () => {
    const v = evaluateClaim(
      claim({ claim_type: 'definitional', source_document_ids: [], source_excerpt: '', as_of_date: null, claim_text: 'A P/E ratio compares price to earnings.' }),
      [],
    );
    expect(v.isPublicSafe).toBe(true);
  });
});
