import { NextRequest, NextResponse } from "next/server";
import { runMany } from "@/lib/ai/providers";
import { ChatMessage, ProviderId } from "@/lib/ai/types";

export const runtime = "nodejs";
export const maxDuration = 60;

interface ChatBody {
  providers?: ProviderId[];
  messages?: ChatMessage[];
  system?: string;
}

export async function POST(req: NextRequest) {
  let body: ChatBody;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const providers = body.providers?.length ? body.providers : (["claude"] as ProviderId[]);
  const messages = body.messages ?? [];
  if (!messages.length) {
    return NextResponse.json({ error: "messages[] is required" }, { status: 400 });
  }

  const results = await runMany(providers, messages, body.system);
  return NextResponse.json({ results });
}
