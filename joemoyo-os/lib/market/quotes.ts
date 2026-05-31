export interface Quote {
  symbol: string;
  name?: string;
  price: number;
  change: number;
  changePct: number;
  currency?: string;
}

export type MarketSource = "fmp" | "alphavantage" | "none";

export function marketSource(): MarketSource {
  if (process.env.FMP_API_KEY) return "fmp";
  if (process.env.ALPHAVANTAGE_API_KEY) return "alphavantage";
  return "none";
}

/** Financial Modeling Prep — batch quotes in one call. */
async function fromFMP(symbols: string[]): Promise<Quote[]> {
  const key = process.env.FMP_API_KEY!;
  const url = `https://financialmodelingprep.com/api/v3/quote/${symbols.join(",")}?apikey=${key}`;
  const res = await fetch(url, { next: { revalidate: 60 } });
  if (!res.ok) throw new Error(`FMP ${res.status}`);
  const data = (await res.json()) as Array<{
    symbol: string;
    name?: string;
    price: number;
    change: number;
    changesPercentage: number;
  }>;
  return data.map((d) => ({
    symbol: d.symbol,
    name: d.name,
    price: d.price,
    change: d.change,
    changePct: d.changesPercentage,
  }));
}

/** Alpha Vantage — one symbol per request (free tier is rate-limited). */
async function fromAlphaVantage(symbols: string[]): Promise<Quote[]> {
  const key = process.env.ALPHAVANTAGE_API_KEY!;
  const out: Quote[] = [];
  for (const symbol of symbols) {
    const url = `https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=${symbol}&apikey=${key}`;
    const res = await fetch(url, { next: { revalidate: 60 } });
    if (!res.ok) continue;
    const q = (await res.json())["Global Quote"];
    if (!q || !q["05. price"]) continue;
    out.push({
      symbol: q["01. symbol"],
      price: Number(q["05. price"]),
      change: Number(q["09. change"]),
      changePct: Number(String(q["10. change percent"]).replace("%", "")),
    });
  }
  return out;
}

/** Fetch quotes from whichever provider is configured. Never throws on "no key". */
export async function fetchQuotes(symbols: string[]): Promise<{ quotes: Quote[]; source: MarketSource; error?: string }> {
  const clean = symbols.map((s) => s.trim().toUpperCase()).filter(Boolean);
  if (!clean.length) return { quotes: [], source: marketSource() };
  const source = marketSource();
  if (source === "none") {
    return { quotes: [], source, error: "No market-data key — add FMP_API_KEY or ALPHAVANTAGE_API_KEY." };
  }
  try {
    const quotes = source === "fmp" ? await fromFMP(clean) : await fromAlphaVantage(clean);
    return { quotes, source };
  } catch (e) {
    return { quotes: [], source, error: e instanceof Error ? e.message : "Market data error" };
  }
}
