"use client";

import { useState } from "react";
import PageHeader from "@/components/PageHeader";
import { PROVIDERS, ProviderId, ChatResult } from "@/lib/ai/types";

const ALL: ProviderId[] = ["claude", "openai", "perplexity"];

export default function AIHub() {
  const [prompt, setPrompt] = useState("");
  const [selected, setSelected] = useState<ProviderId[]>(["claude", "openai", "perplexity"]);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<ChatResult[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  function toggle(id: ProviderId) {
    setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));
  }

  async function ask() {
    if (!prompt.trim() || !selected.length) return;
    setLoading(true);
    setError(null);
    setResults(null);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          providers: selected,
          messages: [{ role: "user", content: prompt }],
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Request failed");
      setResults(data.results);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageHeader title="AI Hub" subtitle="One prompt — every model answers." />
      <div className="p-6">
        {/* Composer */}
        <div className="glass animate-fade-up p-4">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => {
              if ((e.metaKey || e.ctrlKey) && e.key === "Enter") ask();
            }}
            placeholder="Ask anything… (⌘/Ctrl + Enter to send)"
            rows={3}
            className="w-full resize-none bg-transparent text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none"
          />
          <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap gap-2">
              {ALL.map((id) => {
                const on = selected.includes(id);
                return (
                  <button
                    key={id}
                    onClick={() => toggle(id)}
                    style={on ? { borderColor: PROVIDERS[id].accent } : undefined}
                    className={`rounded-full border px-3 py-1 text-xs transition ${
                      on
                        ? "bg-white/10 text-white"
                        : "border-white/10 text-slate-500 hover:text-slate-300"
                    }`}
                  >
                    {PROVIDERS[id].label}
                  </button>
                );
              })}
            </div>
            <button
              onClick={ask}
              disabled={loading || !prompt.trim() || !selected.length}
              className="rounded-xl bg-accent px-4 py-2 text-sm font-medium text-white shadow-glow transition hover:bg-accent-soft disabled:cursor-not-allowed disabled:opacity-40"
            >
              {loading ? "Thinking…" : "Ask all"}
            </button>
          </div>
        </div>

        {error && (
          <div className="mt-4 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
            {error}
          </div>
        )}

        {/* Results grid */}
        <div className="mt-6 grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
          {(loading ? selected : results?.map((r) => r.provider) ?? []).map((id) => {
            const result = results?.find((r) => r.provider === id);
            const meta = PROVIDERS[id as ProviderId];
            return (
              <div key={id} className="glass animate-fade-up flex flex-col p-4">
                <div className="mb-3 flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: meta.accent }} />
                  <span className="text-sm font-semibold text-white">{meta.label}</span>
                  <span className="ml-auto text-[10px] text-slate-600">{meta.model}</span>
                </div>
                {loading && !result ? (
                  <div className="space-y-2">
                    <div className="h-3 w-3/4 animate-pulse rounded bg-white/10" />
                    <div className="h-3 w-full animate-pulse rounded bg-white/10" />
                    <div className="h-3 w-5/6 animate-pulse rounded bg-white/10" />
                  </div>
                ) : result?.error ? (
                  <p className="text-sm text-amber-400/80">{result.error}</p>
                ) : (
                  <>
                    <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-300">
                      {result?.text}
                    </p>
                    {result?.citations && result.citations.length > 0 && (
                      <div className="mt-3 border-t border-white/10 pt-2 text-[11px] text-slate-500">
                        {result.citations.slice(0, 4).map((c, i) => (
                          <a
                            key={i}
                            href={c}
                            target="_blank"
                            rel="noreferrer"
                            className="block truncate hover:text-accent-soft"
                          >
                            [{i + 1}] {c}
                          </a>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>
            );
          })}
        </div>

        {!results && !loading && !error && (
          <p className="mt-10 text-center text-sm text-slate-600">
            Pick your models and ask a question to see them compared.
          </p>
        )}
      </div>
    </>
  );
}
