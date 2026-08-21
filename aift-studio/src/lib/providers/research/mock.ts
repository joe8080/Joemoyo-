import type { DiscoveredResult, FetchedSource, ResearchProvider } from '@/lib/providers/types';
import { FIXTURE_SOURCES } from '@/lib/fixtures/northwind';
import { sha256 } from '@/lib/util/hash';

/**
 * Fixture-backed research provider.
 *
 * It deliberately reproduces the two-step shape of the real thing: `discover`
 * returns snippets that may never be cited, and `fetchSource` returns the stored
 * document that may. Code that shortcuts from a snippet to a citation therefore
 * fails here exactly as it would in production.
 */
export class MockResearchProvider implements ResearchProvider {
  readonly name = 'mock-fixture-research@1';
  readonly isLive = false;

  private readonly now: string;

  constructor(now = '2026-08-14T09:00:00.000Z') {
    this.now = now;
  }

  async discover(query: string, limit: number): Promise<DiscoveredResult[]> {
    const terms = query.toLowerCase().split(/\W+/u).filter((t) => t.length > 3);
    const scored = FIXTURE_SOURCES.map((s) => {
      const hay = `${s.title} ${s.publisher} ${s.fullText}`.toLowerCase();
      const score = terms.reduce((acc, t) => acc + (hay.includes(t) ? 1 : 0), 0);
      return { s, score };
    })
      .filter((r) => r.score > 0)
      .sort((a, b) => b.score - a.score || a.s.url.localeCompare(b.s.url));

    return scored.slice(0, limit).map(({ s }) => ({
      url: s.url,
      title: s.title,
      // Snippet is intentionally lossy: it is not a usable excerpt.
      snippet: `${s.fullText.slice(0, 140).replace(/\s+/gu, ' ')}…`,
      publisher: s.publisher,
    }));
  }

  async fetchSource(url: string): Promise<FetchedSource> {
    const found = FIXTURE_SOURCES.find((s) => s.url === url);
    if (!found) {
      return {
        canonicalUrl: url, title: '', publisher: '', publishedAt: null,
        accessedAt: this.now, text: '', excerpt: '', contentHash: '',
        licenceNotes: '', status: 'failed', failureReason: 'not in fixture corpus',
      };
    }
    return {
      canonicalUrl: found.url,
      title: found.title,
      publisher: found.publisher,
      publishedAt: found.publishedAt,
      accessedAt: this.now,
      text: found.fullText,
      excerpt: found.fullText.slice(0, 600),
      contentHash: sha256(found.fullText),
      licenceNotes: found.licenceNotes,
      status: 'fetched',
    };
  }
}
