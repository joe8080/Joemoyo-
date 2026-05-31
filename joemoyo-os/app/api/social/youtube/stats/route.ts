import { NextResponse } from "next/server";
import { getAccount, fetchChannel, fetchRecentVideos } from "@/lib/social/youtube";

export const runtime = "nodejs";

export async function GET() {
  const { account, configured } = await getAccount();
  if (!account) {
    return NextResponse.json({ connected: false, configured });
  }
  try {
    const channel = await fetchChannel(account.access_token);
    const uploads = channel?.contentDetails?.relatedPlaylists?.uploads;
    const videos = uploads ? await fetchRecentVideos(account.access_token, uploads) : [];
    return NextResponse.json({
      connected: true,
      configured,
      channel: {
        id: account.channel_id,
        title: channel?.snippet?.title ?? account.channel_title,
        subs: Number(channel?.statistics?.subscriberCount ?? 0),
        views: Number(channel?.statistics?.viewCount ?? 0),
        videoCount: Number(channel?.statistics?.videoCount ?? 0),
        thumbnail: channel?.snippet?.thumbnails?.default?.url ?? null,
      },
      videos,
    });
  } catch (e) {
    return NextResponse.json({
      connected: true,
      configured,
      error: e instanceof Error ? e.message : "YouTube API error",
    });
  }
}
