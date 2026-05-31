"use client";

import { useState } from "react";
import PageHeader from "@/components/PageHeader";
import Markdown from "@/components/Markdown";
import { BRANDS } from "@/lib/brands";
import { PROVIDERS, ProviderId } from "@/lib/ai/types";

type Task = "script" | "titles" | "thumbnails" | "repurpose" | "calendar";

const TASKS: { id: Task; label: string; icon: string; needsTopic: boolean; placeholder: string }[] = [
  { id: "script", label: "Script", icon: "📝", needsTopic: true, placeholder: "Video topic, e.g. The Fall of Constantinople" },
  { id: "titles", label: "Titles & Hooks", icon: "🎯", needsTopic: true, placeholder: "Video topic to brainstorm titles for" },
  { id: "thumbnails", label: "Thumbnails", icon: "🖼️", needsTopic: true, placeholder: "Video topic for thumbnail concepts" },
  { id: "repurpose", label: "Repurpose", icon: "♻️", needsTopic: true, placeholder: "Topic or paste a script to repurpose" },
  { id: "calendar", label: "Calendar", icon: "🗓️", needsTopic: false, placeholder: "Optional theme, e.g. summer growth push" },
];

export default function Studio() {
  const [brandId, setBrandId] = useState(BRANDS[0].id);
  const [task, setTask] = useState<Task>("script");
  const [topic, setTopic] = useState("");
  const [provider, setProvider] = useState<ProviderId>("claude");
  const [loading, setLoading] = useState(false);
  const [output, setOutput] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const activeTask = TASKS.find((t) => t.id === task)!;

  async function generate() {
    if (activeTask.needsTopic && !topic.trim()) return;
    setLoading(true);
    setError(null);
    setOutput(null);
    try {
      const res = await fetch("/api/studio", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task, brandId, topic, provider }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Request failed");
      if (data.error) throw new Error(data.error);
      setOutput(data.markdown);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  function copy() {
    if (!output) return;
    navigator.clipboard.writeText(output);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <>
      <PageHeader title="Content Studio" subtitle="Scripts, thumbnails & planning — in your brand voice." />
      <div className="p-6">
        {/* Brand picker */}
        <div className="mb-4 flex flex-wrap gap-2">
          {BRANDS.map((b) => (
            <button
              key={b.id}
              onClick={() => setBrandId(b.id)}
              className={`rounded-xl border px-3 py-1.5 text-xs transition ${
                brandId === b.id
                  ? "border-accent/50 bg-accent/20 text-white"
                  : "border-white/10 text-slate-400 hover:text-slate-200"
              }`}
            >
              {b.name}
            </button>
          ))}
        </div>

        {/* Task tabs */}
        <div className="mb-4 flex flex-wrap gap-2">
          {TASKS.map((t) => (
            <button
              key={t.id}
              onClick={() => {
                setTask(t.id);
                setOutput(null);
                setError(null);
              }}
              className={`flex items-center gap-1.5 rounded-xl px-3 py-2 text-sm transition ${
                task === t.id ? "bg-white/10 text-white shadow-glow" : "text-slate-400 hover:bg-white/5"
              }`}
            >
              <span>{t.icon}</span>
              {t.label}
            </button>
          ))}
        </div>

        {/* Composer */}
        <div className="glass p-4">
          <input
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && generate()}
            placeholder={activeTask.placeholder}
            className="w-full bg-transparent text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none"
          />
          <div className="mt-3 flex flex-wrap items-center justify-between gap-3 border-t border-white/10 pt-3">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500">Model</span>
              {(["claude", "openai", "perplexity"] as ProviderId[]).map((id) => (
                <button
                  key={id}
                  onClick={() => setProvider(id)}
                  className={`rounded-full border px-2.5 py-1 text-xs transition ${
                    provider === id ? "border-accent/50 text-white" : "border-white/10 text-slate-500"
                  }`}
                >
                  {PROVIDERS[id].label}
                </button>
              ))}
            </div>
            <button
              onClick={generate}
              disabled={loading || (activeTask.needsTopic && !topic.trim())}
              className="rounded-xl bg-accent px-4 py-2 text-sm font-medium text-white shadow-glow transition hover:bg-accent-soft disabled:cursor-not-allowed disabled:opacity-40"
            >
              {loading ? "Generating…" : `Generate ${activeTask.label}`}
            </button>
          </div>
        </div>

        {error && (
          <div className="mt-4 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
            {error}
          </div>
        )}

        {loading && (
          <div className="glass mt-6 space-y-3 p-6">
            <div className="h-4 w-1/3 animate-pulse rounded bg-white/10" />
            <div className="h-3 w-full animate-pulse rounded bg-white/10" />
            <div className="h-3 w-11/12 animate-pulse rounded bg-white/10" />
            <div className="h-3 w-4/5 animate-pulse rounded bg-white/10" />
          </div>
        )}

        {output && !loading && (
          <div className="glass animate-fade-up mt-6 p-6">
            <div className="mb-3 flex items-center justify-between">
              <span className="text-xs uppercase tracking-wide text-slate-500">
                {BRANDS.find((b) => b.id === brandId)?.name} · {activeTask.label}
              </span>
              <button
                onClick={copy}
                className="rounded-lg border border-white/10 px-3 py-1 text-xs text-slate-300 transition hover:bg-white/5"
              >
                {copied ? "Copied ✓" : "Copy"}
              </button>
            </div>
            <Markdown>{output}</Markdown>
          </div>
        )}
      </div>
    </>
  );
}
