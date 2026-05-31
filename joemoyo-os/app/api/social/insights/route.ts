import { NextResponse } from "next/server";
import { getAccount, fetchChannel, fetchRecentVideos } from "@/lib/social/youtube";
import { weeklyInsights } from "@/lib/ai/social";

export const runtime = "nodejs";
export const maxDuration = 60;

export async function POST() {
  const { account } = await getAccount();
  if (!account) {
    return NextResponse.json({ error: "Connect YouTube first to get insights." }, { status: 400 });
  }
  try {
    const channel = await fetchChannel(account.access_token);
    const uploads = channel?.contentDetails?.relatedPlaylists?.uploads;
    const videos = uploads ? await fetchRecentVideos(account.access_token, uploads) : [];
    const res = await weeklyInsights(
      channel?.snippet?.title ?? account.channel_title,
      Number(channel?.statistics?.subscriberCount ?? 0),
      Number(channel?.statistics?.viewCount ?? 0),
      videos,
    );
    return NextResponse.json({ markdown: res.text, error: res.error });
  } catch (e) {
    return NextResponse.json({ error: e instanceof Error ? e.message : "Insights failed" }, { status: 500 });
  }
}
