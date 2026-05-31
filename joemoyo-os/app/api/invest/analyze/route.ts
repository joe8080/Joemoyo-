import { NextRequest, NextResponse } from "next/server";
import { getPortfolio } from "@/lib/invest/portfolio";
import { fetchQuotes } from "@/lib/market/quotes";
import { runScan, researchTicker } from "@/lib/ai/invest";
import { ProviderId } from "@/lib/ai/types";

export const runtime = "nodejs";
export const maxDuration = 60;

interface AnalyzeBody {
  mode?: "scan" | "research";
  symbol?: string;
  watchlist?: string[];
  provider?: ProviderId;
}

export async function POST(req: NextRequest) {
  let body: AnalyzeBody;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  if (body.mode === "research") {
    if (!body.symbol) return NextResponse.json({ error: "symbol required" }, { status: 400 });
    const res = await researchTicker(body.symbol, body.provider ?? "perplexity");
    return NextResponse.json({ markdown: res.text, error: res.error });
  }

  // default: daily scan over portfolio + watchlist
  const portfolio = await getPortfolio();
  const { quotes: watch } = body.watchlist?.length
    ? await fetchQuotes(body.watchlist)
    : { quotes: [] };
  const res = await runScan(portfolio, watch, body.provider ?? "claude");
  return NextResponse.json({ markdown: res.text, error: res.error });
}
