import { NextRequest, NextResponse } from "next/server";
import { getBrand } from "@/lib/brands";
import { draftPosts, Platform } from "@/lib/ai/social";
import { ProviderId } from "@/lib/ai/types";

export const runtime = "nodejs";
export const maxDuration = 60;

export async function POST(req: NextRequest) {
  let body: { topic?: string; platforms?: Platform[]; brandId?: string; provider?: ProviderId };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }
  if (!body.topic?.trim()) return NextResponse.json({ error: "topic required" }, { status: 400 });
  const brand = getBrand(body.brandId ?? "history_channel");
  if (!brand) return NextResponse.json({ error: "Unknown brandId" }, { status: 400 });
  const platforms = body.platforms?.length ? body.platforms : (["YouTube", "X", "Instagram"] as Platform[]);

  const res = await draftPosts(body.topic, platforms, brand, body.provider ?? "claude");
  return NextResponse.json({ markdown: res.text, error: res.error });
}
