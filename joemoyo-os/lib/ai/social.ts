import { runProvider } from "@/lib/ai/providers";
import { ProviderId } from "@/lib/ai/types";
import { Brand, brandContext } from "@/lib/brands";
import { VideoStat } from "@/lib/social/youtube";

const SOCIAL_SYSTEM =
  "You are the Social manager inside JoeMoyo OS. You write platform-native, on-brand posts and " +
  "give sharp, practical growth advice for a creator. Output clean Markdown.";

export const PLATFORMS = ["YouTube", "X", "Instagram", "TikTok", "LinkedIn", "Facebook"] as const;
export type Platform = (typeof PLATFORMS)[number];

/** Draft platform-tailored posts for a topic, in the brand voice. */
export async function draftPosts(
  topic: string,
  platforms: Platform[],
  brand: Brand,
  provider: ProviderId = "claude",
) {
  const prompt =
    `${brandContext(brand)}\n\n` +
    `Write posts about: "${topic}" for these platforms: ${platforms.join(", ")}.\n` +
    "For each platform: respect its norms (length, tone, hashtags, emoji), add a strong hook, " +
    "and a clear CTA. Use a Markdown heading per platform.";
  return runProvider(provider, [{ role: "user", content: prompt }], SOCIAL_SYSTEM);
}

/** Weekly growth report from channel + recent video stats. */
export async function weeklyInsights(
  channelTitle: string,
  subs: number,
  totalViews: number,
  videos: VideoStat[],
  provider: ProviderId = "claude",
) {
  const vids = videos
    .slice(0, 8)
    .map((v) => `- ${v.title}: ${v.views.toLocaleString()} views, ${v.likes} likes, ${v.comments} comments`)
    .join("\n");
  const prompt =
    `Channel: ${channelTitle} — ${subs.toLocaleString()} subscribers, ${totalViews.toLocaleString()} total views.\n` +
    `Recent uploads:\n${vids || "(none)"}\n\n` +
    "Give a tight weekly report:\n" +
    "## 📊 What's working — patterns in the top performers.\n" +
    "## 🔧 What to fix — weak spots (titles, topics, consistency).\n" +
    "## 🎯 Do next — 3 concrete actions for the coming week.";
  return runProvider(provider, [{ role: "user", content: prompt }], SOCIAL_SYSTEM);
}
