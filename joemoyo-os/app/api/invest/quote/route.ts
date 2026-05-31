import { NextRequest, NextResponse } from "next/server";
import { fetchQuotes } from "@/lib/market/quotes";

export const runtime = "nodejs";

export async function GET(req: NextRequest) {
  const symbols = (req.nextUrl.searchParams.get("symbols") ?? "")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
  if (!symbols.length) {
    return NextResponse.json({ error: "symbols query param required" }, { status: 400 });
  }
  const result = await fetchQuotes(symbols);
  return NextResponse.json(result);
}
