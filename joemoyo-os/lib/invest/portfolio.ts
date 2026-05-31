import { vaultClient, vaultReady } from "@/lib/supabase/server";
import { fetchQuotes, Quote } from "@/lib/market/quotes";

export interface Holding {
  symbol: string;
  shares: number;
  cost_basis: number; // per-share average cost
  account?: string;
}

export interface EnrichedHolding extends Holding {
  price: number;
  value: number;
  costValue: number;
  pnl: number;
  pnlPct: number;
  changePct: number;
  weight: number; // % of portfolio
}

export interface PortfolioSummary {
  holdings: EnrichedHolding[];
  totalValue: number;
  totalCost: number;
  totalPnl: number;
  totalPnlPct: number;
  dayChangeValue: number;
  configured: boolean;
  note?: string;
}

/** Load holdings from the vault `holdings` table. */
export async function loadHoldings(): Promise<{ holdings: Holding[]; configured: boolean }> {
  if (!vaultReady()) return { holdings: [], configured: false };
  const db = vaultClient();
  if (!db) return { holdings: [], configured: false };
  const { data, error } = await db.from("holdings").select("symbol, shares, cost_basis, account");
  if (error) return { holdings: [], configured: true };
  return { holdings: (data ?? []) as Holding[], configured: true };
}

export async function getPortfolio(): Promise<PortfolioSummary> {
  const { holdings, configured } = await loadHoldings();
  if (!holdings.length) {
    return {
      holdings: [],
      totalValue: 0,
      totalCost: 0,
      totalPnl: 0,
      totalPnlPct: 0,
      dayChangeValue: 0,
      configured,
      note: configured
        ? "No holdings yet — add rows to the `holdings` table in your vault."
        : "Connect your Supabase vault to load holdings.",
    };
  }

  const { quotes } = await fetchQuotes(holdings.map((h) => h.symbol));
  const bySym = new Map<string, Quote>(quotes.map((q) => [q.symbol.toUpperCase(), q]));

  const enriched: EnrichedHolding[] = holdings.map((h) => {
    const q = bySym.get(h.symbol.toUpperCase());
    const price = q?.price ?? h.cost_basis;
    const value = price * h.shares;
    const costValue = h.cost_basis * h.shares;
    const pnl = value - costValue;
    return {
      ...h,
      price,
      value,
      costValue,
      pnl,
      pnlPct: costValue ? (pnl / costValue) * 100 : 0,
      changePct: q?.changePct ?? 0,
      weight: 0,
    };
  });

  const totalValue = enriched.reduce((s, h) => s + h.value, 0);
  const totalCost = enriched.reduce((s, h) => s + h.costValue, 0);
  const dayChangeValue = enriched.reduce((s, h) => s + (h.value * h.changePct) / 100, 0);
  enriched.forEach((h) => (h.weight = totalValue ? (h.value / totalValue) * 100 : 0));
  enriched.sort((a, b) => b.value - a.value);

  return {
    holdings: enriched,
    totalValue,
    totalCost,
    totalPnl: totalValue - totalCost,
    totalPnlPct: totalCost ? ((totalValue - totalCost) / totalCost) * 100 : 0,
    dayChangeValue,
    configured,
  };
}
