import { NextRequest, NextResponse } from "next/server";
import { authUrl, googleConfigured } from "@/lib/social/youtube";

export const runtime = "nodejs";

function redirectUri(req: NextRequest) {
  const base = process.env.NEXT_PUBLIC_BASE_URL ?? req.nextUrl.origin;
  return `${base}/api/social/youtube/callback`;
}

export async function GET(req: NextRequest) {
  if (!googleConfigured()) {
    return NextResponse.redirect(`${req.nextUrl.origin}/social?error=google_not_configured`);
  }
  return NextResponse.redirect(authUrl(redirectUri(req)));
}
