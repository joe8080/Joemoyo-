import { FIXTURE_SERIES, type FixtureSeries } from '@/lib/fixtures/northwind';

/**
 * The only place chart data may come from.
 *
 * A series is a set of validated rows with a source label, an as-of date and the
 * claim ids it belongs to. Nothing in the visual pipeline can invent a data
 * point: the planner asks this registry by key, and if the key is unknown the
 * scene is planned as a non-numeric composition instead.
 *
 * In production this is backed by `price_snapshots` / `macro_indicators` /
 * filing extracts. The fixture registry has exactly the same shape.
 */
export type DataSeries = FixtureSeries;

export interface DataRegistry {
  readonly name: string;
  get(key: string): DataSeries | null;
  findForClaims(claimIds: readonly string[]): DataSeries | null;
  all(): DataSeries[];
}

export class FixtureDataRegistry implements DataRegistry {
  readonly name = 'fixture-data-registry@1';
  private readonly byKey = new Map<string, DataSeries>(FIXTURE_SERIES.map((s) => [s.key, s]));

  get(key: string): DataSeries | null { return this.byKey.get(key) ?? null; }

  findForClaims(claimIds: readonly string[]): DataSeries | null {
    for (const s of this.byKey.values()) {
      if (s.claimIds.some((c) => claimIds.includes(c))) return s;
    }
    return null;
  }

  all(): DataSeries[] { return [...this.byKey.values()]; }
}
