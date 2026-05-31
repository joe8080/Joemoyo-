"use client";

import { useEffect, useState } from "react";

interface Health {
  providers: Record<string, boolean>;
  vault: boolean;
}

function Pill({ label, ok }: { label: string; ok: boolean }) {
  return (
    <span className="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[11px]">
      <span className={`h-1.5 w-1.5 rounded-full ${ok ? "bg-emerald-400" : "bg-slate-600"}`} />
      {label}
    </span>
  );
}

export default function StatusBar() {
  const [health, setHealth] = useState<Health | null>(null);

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Pill label="Claude" ok={!!health?.providers?.claude} />
      <Pill label="ChatGPT" ok={!!health?.providers?.openai} />
      <Pill label="Perplexity" ok={!!health?.providers?.perplexity} />
      <Pill label="Vault" ok={!!health?.vault} />
    </div>
  );
}
