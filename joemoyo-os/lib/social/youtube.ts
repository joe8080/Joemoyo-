import { vaultClient, vaultReady } from "@/lib/supabase/server";

const GOOGLE_AUTH = "https://accounts.google.com/o/oauth2/v2/auth";
const GOOGLE_TOKEN = "https://oauth2.googleapis.com/token";
const SCOPES = [
  "https://www.googleapis.com/auth/youtube.readonly",
  "https://www.googleapis.com/auth/yt-analytics.readonly",
];

export interface YouTubeAccount {
  provider: "youtube";
  channel_id: string;
  channel_title: string;
  access_token: string;
  refresh_token: string;
  expires_at: string; // ISO
}

export function googleConfigured(): boolean {
  return Boolean(process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET);
}

export function authUrl(redirectUri: string): string {
  const p = new URLSearchParams({
    client_id: process.env.GOOGLE_CLIENT_ID!,
    redirect_uri: redirectUri,
    response_type: "code",
    access_type: "offline",
    prompt: "consent",
    include_granted_scopes: "true",
    scope: SCOPES.join(" "),
  });
  return `${GOOGLE_AUTH}?${p.toString()}`;
}

export async function exchangeCode(code: string, redirectUri: string) {
  const res = await fetch(GOOGLE_TOKEN, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      code,
      client_id: process.env.GOOGLE_CLIENT_ID!,
      client_secret: process.env.GOOGLE_CLIENT_SECRET!,
      redirect_uri: redirectUri,
      grant_type: "authorization_code",
    }),
  });
  if (!res.ok) throw new Error(`Token exchange failed: ${res.status}`);
  return (await res.json()) as { access_token: string; refresh_token?: string; expires_in: number };
}

async function refreshToken(refresh_token: string) {
  const res = await fetch(GOOGLE_TOKEN, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      refresh_token,
      client_id: process.env.GOOGLE_CLIENT_ID!,
      client_secret: process.env.GOOGLE_CLIENT_SECRET!,
      grant_type: "refresh_token",
    }),
  });
  if (!res.ok) throw new Error(`Token refresh failed: ${res.status}`);
  return (await res.json()) as { access_token: string; expires_in: number };
}

/** Fetch a YouTube channel's snippet+statistics with a bearer token. */
export async function fetchChannel(accessToken: string) {
  const res = await fetch(
    "https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics,contentDetails&mine=true",
    { headers: { Authorization: `Bearer ${accessToken}` } },
  );
  if (!res.ok) throw new Error(`channels.list ${res.status}`);
  const data = await res.json();
  return data.items?.[0];
}

export interface VideoStat {
  id: string;
  title: string;
  publishedAt: string;
  views: number;
  likes: number;
  comments: number;
}

/** Recent uploads with per-video stats. */
export async function fetchRecentVideos(accessToken: string, uploadsPlaylist: string): Promise<VideoStat[]> {
  const pl = await fetch(
    `https://www.googleapis.com/youtube/v3/playlistItems?part=contentDetails&maxResults=10&playlistId=${uploadsPlaylist}`,
    { headers: { Authorization: `Bearer ${accessToken}` } },
  );
  if (!pl.ok) return [];
  const ids = ((await pl.json()).items ?? [])
    .map((i: { contentDetails: { videoId: string } }) => i.contentDetails.videoId)
    .join(",");
  if (!ids) return [];
  const v = await fetch(
    `https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&id=${ids}`,
    { headers: { Authorization: `Bearer ${accessToken}` } },
  );
  if (!v.ok) return [];
  return ((await v.json()).items ?? []).map(
    (it: {
      id: string;
      snippet: { title: string; publishedAt: string };
      statistics: { viewCount?: string; likeCount?: string; commentCount?: string };
    }) => ({
      id: it.id,
      title: it.snippet.title,
      publishedAt: it.snippet.publishedAt,
      views: Number(it.statistics.viewCount ?? 0),
      likes: Number(it.statistics.likeCount ?? 0),
      comments: Number(it.statistics.commentCount ?? 0),
    }),
  );
}

/** Load the stored YouTube account from the vault, refreshing the token if expired. */
export async function getAccount(): Promise<{ account: YouTubeAccount | null; configured: boolean }> {
  if (!vaultReady()) return { account: null, configured: false };
  const db = vaultClient();
  if (!db) return { account: null, configured: false };
  const { data } = await db
    .from("social_accounts")
    .select("*")
    .eq("provider", "youtube")
    .limit(1)
    .maybeSingle();
  if (!data) return { account: null, configured: true };

  let acc = data as YouTubeAccount;
  if (new Date(acc.expires_at).getTime() < Date.now() + 60_000) {
    try {
      const refreshed = await refreshToken(acc.refresh_token);
      const expires_at = new Date(Date.now() + refreshed.expires_in * 1000).toISOString();
      await db
        .from("social_accounts")
        .update({ access_token: refreshed.access_token, expires_at })
        .eq("provider", "youtube");
      acc = { ...acc, access_token: refreshed.access_token, expires_at };
    } catch {
      /* fall through with stale token */
    }
  }
  return { account: acc, configured: true };
}

export async function saveAccount(acc: YouTubeAccount) {
  const db = vaultClient();
  if (!db) return false;
  const { error } = await db.from("social_accounts").upsert(acc, { onConflict: "provider" });
  return !error;
}
