import { NextRequest, NextResponse } from "next/server";
import { vaultClient, vaultReady } from "@/lib/supabase/server";

export const runtime = "nodejs";

/** List queued posts. */
export async function GET() {
  if (!vaultReady()) return NextResponse.json({ posts: [], configured: false });
  const db = vaultClient();
  if (!db) return NextResponse.json({ posts: [], configured: false });
  const { data } = await db
    .from("scheduled_posts")
    .select("*")
    .order("scheduled_for", { ascending: true });
  return NextResponse.json({ posts: data ?? [], configured: true });
}

/** Queue a post (status=scheduled). Auto-publishing is handled by a worker later. */
export async function POST(req: NextRequest) {
  let body: { platform?: string; content?: string; scheduled_for?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }
  if (!body.platform || !body.content) {
    return NextResponse.json({ error: "platform and content required" }, { status: 400 });
  }
  if (!vaultReady()) {
    return NextResponse.json({ error: "Connect your vault to queue posts" }, { status: 400 });
  }
  const db = vaultClient();
  if (!db) return NextResponse.json({ error: "Vault unavailable" }, { status: 500 });

  const { error } = await db.from("scheduled_posts").insert({
    platform: body.platform,
    content: body.content,
    scheduled_for: body.scheduled_for ?? null,
    status: "scheduled",
  });
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ ok: true });
}
