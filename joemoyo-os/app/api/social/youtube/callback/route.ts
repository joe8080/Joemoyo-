import { NextRequest, NextResponse } from "next/server";
import { exchangeCode, fetchChannel, saveAccount } from "@/lib/social/youtube";

export const runtime = "nodejs";

export async function GET(req: NextRequest) {
  const origin = req.nextUrl.origin;
  const code = req.nextUrl.searchParams.get("code");
  if (!code) return NextResponse.redirect(`${origin}/social?error=no_code`);

  const base = process.env.NEXT_PUBLIC_BASE_URL ?? origin;
  const redirectUri = `${base}/api/social/youtube/callback`;

  try {
    const tokens = await exchangeCode(code, redirectUri);
    const channel = await fetchChannel(tokens.access_token);
    if (!channel) return NextResponse.redirect(`${origin}/social?error=no_channel`);

    const ok = await saveAccount({
      provider: "youtube",
      channel_id: channel.id,
      channel_title: channel.snippet?.title ?? "YouTube",
      access_token: tokens.access_token,
      refresh_token: tokens.refresh_token ?? "",
      expires_at: new Date(Date.now() + tokens.expires_in * 1000).toISOString(),
    });
    return NextResponse.redirect(`${origin}/social?connected=${ok ? "1" : "novault"}`);
  } catch {
    return NextResponse.redirect(`${origin}/social?error=oauth_failed`);
  }
}
