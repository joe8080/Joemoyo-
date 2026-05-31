"use client";

import { useEffect, useState } from "react";
import PageHeader from "@/components/PageHeader";
import Markdown from "@/components/Markdown";
import { BRANDS } from "@/lib/brands";

const PLATFORMS = ["YouTube", "X", "Instagram", "TikTok", "LinkedIn", "Facebook"] as const;
type Platform = (typeof PLATFORMS)[number];

interface VideoStat { id: string; title: string; views: number; likes: number; comments: number }
interface Stats {
  connected: boolean;
  configured: boolean;
  channel?: { title: string; subs: number; views: number; videoCount: number };
  videos?: VideoStat[];
  error?: string;
}
interface QueuedPost { id: string; platform: string; content: string; scheduled_for: string | null; status: string }

const n = (x: number) => x.toLocaleString();

export default function Social() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [insights, setInsights] = useState<string | null>(null);
  const [insightsLoading, setInsightsLoading] = useState(false);

  const [brandId, setBrandId] = useState(BRANDS[0].id);
  const [topic, setTopic] = useState("");
  const [platforms, setPlatforms] = useState<Platform[]>(["YouTube", "X", "Instagram"]);
  const [draft, setDraft] = useState<string | null>(null);
  const [draftLoading, setDraftLoading] = useState(false);

  const [queue, setQueue] = useState<QueuedPost[]>([]);

  useEffect(() => {
    fetch("/api/social/youtube/stats").then((r) => r.json()).then(setStats).catch(() => setStats(null));
    fetch("/api/social/schedule").then((r) => r.json()).then((d) => setQueue(d.posts ?? [])).catch(() => {});
  }, []);

  function togglePlatform(p: Platform) {
    setPlatforms((s) => (s.includes(p) ? s.filter((x) => x !== p) : [...s, p]));
  }

  async function runInsights() {
    setInsightsLoading(true);
    setInsights(null);
    const r = await fetch("/api/social/insights", { method: "POST" });
    const d = await r.json();
    setInsights(d.error ? `⚠️ ${d.error}` : d.markdown);
    setInsightsLoading(false);
  }

  async function runDraft() {
    if (!topic.trim()) return;
    setDraftLoading(true);
    setDraft(null);
    const r = await fetch("/api/social/draft", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic, platforms, brandId }),
    });
    const d = await r.json();
    setDraft(d.error ? `⚠️ ${d.error}` : d.markdown);
    setDraftLoading(false);
  }

  return (
    <>
      <PageHeader title="Social" subtitle="YouTube analytics, AI post drafting & scheduling." />
      <div className="space-y-6 p-6">
        {/* YouTube connection */}
        <div className="glass p-5">
          <div className="mb-3 flex items-center justify-between">
            <span className="text-sm font-semibold text-white">📺 YouTube</span>
            {stats?.connected ? (
              <span className="rounded-full bg-emerald-400/15 px-2.5 py-0.5 text-[11px] text-emerald-300">
                Connected
              </span>
            ) : (
              <a
                href="/api/social/youtube/connect"
                className="rounded-xl bg-accent px-4 py-2 text-sm font-medium text-white shadow-glow transition hover:bg-accent-soft"
              >
                Connect YouTube
              </a>
            )}
          </div>

          {stats?.connected && stats.channel ? (
            <>
              <div className="grid gap-4 sm:grid-cols-3">
                <Stat label="Subscribers" value={n(stats.channel.subs)} />
                <Stat label="Total views" value={n(stats.channel.views)} />
                <Stat label="Videos" value={n(stats.channel.videoCount)} />
              </div>
              {stats.videos && stats.videos.length > 0 && (
                <div className="mt-4 overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="text-xs uppercase text-slate-500">
                      <tr>
                        <th className="py-2">Recent video</th>
                        <th className="py-2 text-right">Views</th>
                        <th className="py-2 text-right">Likes</th>
                        <th className="py-2 text-right">Comments</th>
                      </tr>
                    </thead>
                    <tbody>
                      {stats.videos.map((v) => (
                        <tr key={v.id} className="border-t border-white/5">
                          <td className="max-w-xs truncate py-2.5 text-slate-200">{v.title}</td>
                          <td className="py-2.5 text-right">{n(v.views)}</td>
                          <td className="py-2.5 text-right">{n(v.likes)}</td>
                          <td className="py-2.5 text-right">{n(v.comments)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          ) : (
            <p className="text-sm text-slate-500">
              {stats?.configured === false
                ? "Connect your Supabase vault and add Google OAuth keys to link YouTube."
                : "Link your channel to see subscribers, views and recent video performance."}
            </p>
          )}
        </div>

        {/* Weekly insights */}
        <div className="glass p-5">
          <div className="mb-3 flex items-center justify-between">
            <span className="text-sm font-semibold text-white">📈 AI weekly growth report</span>
            <button
              onClick={runInsights}
              disabled={insightsLoading}
              className="rounded-xl border border-white/10 px-4 py-2 text-sm text-white transition hover:bg-white/5 disabled:opacity-40"
            >
              {insightsLoading ? "Analyzing…" : "Generate report"}
            </button>
          </div>
          {insightsLoading && <div className="h-3 w-1/2 animate-pulse rounded bg-white/10" />}
          {insights ? <Markdown>{insights}</Markdown> : (
            !insightsLoading && <p className="text-sm text-slate-500">AI reviews your channel and tells you what to do next.</p>
          )}
        </div>

        {/* Post composer */}
        <div className="glass p-5">
          <div className="mb-3 text-sm font-semibold text-white">✍️ AI post composer</div>
          <div className="mb-3 flex flex-wrap gap-2">
            {BRANDS.map((b) => (
              <button
                key={b.id}
                onClick={() => setBrandId(b.id)}
                className={`rounded-xl border px-3 py-1.5 text-xs transition ${
                  brandId === b.id ? "border-accent/50 bg-accent/20 text-white" : "border-white/10 text-slate-400"
                }`}
              >
                {b.name}
              </button>
            ))}
          </div>
          <input
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && runDraft()}
            placeholder="What's the post about? e.g. New video: Fall of Rome"
            className="w-full rounded-lg bg-white/5 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none"
          />
          <div className="mt-3 flex flex-wrap items-center gap-2">
            {PLATFORMS.map((p) => (
              <button
                key={p}
                onClick={() => togglePlatform(p)}
                className={`rounded-full border px-2.5 py-1 text-xs transition ${
                  platforms.includes(p) ? "border-accent/50 text-white" : "border-white/10 text-slate-500"
                }`}
              >
                {p}
              </button>
            ))}
            <button
              onClick={runDraft}
              disabled={draftLoading || !topic.trim() || !platforms.length}
              className="ml-auto rounded-xl bg-accent px-4 py-2 text-sm font-medium text-white shadow-glow transition hover:bg-accent-soft disabled:opacity-40"
            >
              {draftLoading ? "Drafting…" : "Draft posts"}
            </button>
          </div>
          {draftLoading && <div className="mt-4 h-3 w-2/3 animate-pulse rounded bg-white/10" />}
          {draft && <div className="mt-4"><Markdown>{draft}</Markdown></div>}
        </div>

        {/* Queue */}
        <div className="glass p-5">
          <div className="mb-3 text-sm font-semibold text-white">🗓️ Scheduled queue</div>
          {queue.length > 0 ? (
            <ul className="space-y-2">
              {queue.map((p) => (
                <li key={p.id} className="flex items-center justify-between rounded-lg bg-white/5 px-3 py-2 text-sm">
                  <span className="truncate text-slate-300">
                    <span className="text-accent-soft">{p.platform}</span> · {p.content.slice(0, 60)}
                  </span>
                  <span className="ml-3 shrink-0 text-xs text-slate-500">
                    {p.scheduled_for ? new Date(p.scheduled_for).toLocaleDateString() : p.status}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-500">
              Queued posts appear here. Auto-publishing runs from a scheduled worker (added with platform write-access).
            </p>
          )}
        </div>
      </div>
    </>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-white/5 p-4">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-white">{value}</div>
    </div>
  );
}
