import { NextResponse } from "next/server";
import { providerReady } from "@/lib/ai/providers";
import { vaultReady } from "@/lib/supabase/server";
import { ProviderId } from "@/lib/ai/types";

export const runtime = "nodejs";

/** Lightweight status endpoint the dashboard polls to show what's wired up. */
export async function GET() {
  const ids: ProviderId[] = ["claude", "openai", "perplexity"];
  return NextResponse.json({
    providers: Object.fromEntries(ids.map((id) => [id, providerReady(id)])),
    vault: vaultReady(),
    time: new Date().toISOString(),
  });
}
