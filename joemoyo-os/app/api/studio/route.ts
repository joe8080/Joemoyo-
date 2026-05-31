import { NextRequest, NextResponse } from "next/server";
import { getBrand } from "@/lib/brands";
import { runStudioTask, StudioTask } from "@/lib/ai/studio";
import { ProviderId } from "@/lib/ai/types";
import { vaultClient } from "@/lib/supabase/server";

export const runtime = "nodejs";
export const maxDuration = 60;

interface StudioBody {
  task?: StudioTask;
  brandId?: string;
  topic?: string;
  provider?: ProviderId;
  save?: boolean;
}

export async function POST(req: NextRequest) {
  let body: StudioBody;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const { task, brandId, topic = "", provider = "claude", save } = body;
  if (!task) return NextResponse.json({ error: "task is required" }, { status: 400 });

  const brand = getBrand(brandId ?? "");
  if (!brand) return NextResponse.json({ error: "Unknown brandId" }, { status: 400 });
  if (task !== "calendar" && !topic.trim()) {
    return NextResponse.json({ error: "topic is required for this task" }, { status: 400 });
  }

  const result = await runStudioTask(task, brand, topic, provider);

  // Optionally persist to the vault (best-effort — never blocks the response).
  let saved = false;
  if (save && !result.error) {
    const db = vaultClient();
    if (db) {
      const { error } = await db.from("studio_content").insert({
        task,
        brand: brand.id,
        topic,
        provider,
        markdown: result.markdown,
      });
      saved = !error;
    }
  }

  return NextResponse.json({ ...result, saved });
}
