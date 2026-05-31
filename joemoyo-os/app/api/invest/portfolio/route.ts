import { NextResponse } from "next/server";
import { getPortfolio } from "@/lib/invest/portfolio";
import { marketSource } from "@/lib/market/quotes";

export const runtime = "nodejs";

export async function GET() {
  const portfolio = await getPortfolio();
  return NextResponse.json({ ...portfolio, marketSource: marketSource() });
}
