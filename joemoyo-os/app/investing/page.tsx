"use client";

import { useEffect, useState } from "react";
import PageHeader from "@/components/PageHeader";
import Markdown from "@/components/Markdown";

interface EnrichedHolding {
  symbol: string;
  shares: number;
  price: number;
  value: number;
  pnl: number;
  pnlPct: number;
  changePct: number;
  weight: number;
}
interface Portfolio {
  holdings: EnrichedHolding[];
  totalValue: number;
  totalPnl: number;
  totalPnlPct: number;
  dayChangeValue: number;
  configured: boolean;
  note?: string;
}
interface Quote {
  symbol: string;
  price: number;
  changePct: number;
}

const money = (n: number) => "$" + n.toLocaleString(undefined, { maximumFractionDigits: 2 });
const pct = (n: number) => `${n >= 0 ? "+" : ""}${n.toFixed(2)}%`;
const tone = (n: number) => (n >= 0 ? "text-emerald-400" : "text-red-400");

export default function Investing() {
  const [pf, setPf] = useState<Portfolio | null>(null);
  const [watchInput, setWatchInput] = useState("");
  const [watch, setWatch] = useState<Quote[]>([]);
  const [scan, setScan] = useState<string | null>(null);
  const [scanLoading, setScanLoading] = useState(false);
  const [research, setResearch] = useState<string | null>(null);
  const [researchSym, setResearchSym] = useState("");
  const [researchLoading, setResearchLoading] = useState(false);

  useEffect(() => {
    fetch("/api/invest/portfolio").then((r) => r.json()).then(setPf).catch(() => setPf(null));
    const saved = localStorage.getItem("watchlist");
    if (saved) {
      setWatchInput(saved);
      refreshWatch(saved);
    }
  }, []);

  async function refreshWatch(symbols: string) {
    const list = symbols.split(",").map((s) => s.trim()).filter(Boolean);
    if (!list.length) return setWatch([]);
    localStorage.setItem("watchlist", symbols);
    const r = await fetch(`/api/invest/quote?symbols=${encodeURIComponent(list.join(","))}`);
    const d = await r.json();
    setWatch(d.quotes ?? []);
  }

  async function runScan() {
    setScanLoading(true);
    setScan(null);
    const list = watchInput.split(",").map((s) => s.trim()).filter(Boolean);
    const r = await fetch("/api/invest/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: "scan", watchlist: list }),
    });
    const d = await r.json();
    setScan(d.error ? `⚠️ ${d.error}` : d.markdown);
    setScanLoading(false);
  }

  async function runResearch() {
    if (!researchSym.trim()) return;
    setResearchLoading(true);
    setResearch(null);
    const r = await fetch("/api/invest/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: "research", symbol: researchSym.trim() }),
    });
    const d = await r.json();
    setResearch(d.error ? `⚠️ ${d.error}` : d.markdown);
    setResearchLoading(false);
  }

  return (
    <>
      <PageHeader title="Investing" subtitle="Portfolio, market data & AI alerts — never auto-trades." />
      <div className="space-y-6 p-6">
        {/* Summary */}
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="glass animate-fade-up p-5">
            <div className="text-xs uppercase tracking-wide text-slate-500">Portfolio value</div>
            <div className="mt-1 text-2xl font-semibold text-white">{pf ? money(pf.totalValue) : "—"}</div>
          </div>
          <div className="glass animate-fade-up p-5" style={{ animationDelay: "60ms" }}>
            <div className="text-xs uppercase tracking-wide text-slate-500">Total P&amp;L</div>
            <div className={`mt-1 text-2xl font-semibold ${pf ? tone(pf.totalPnl) : ""}`}>
              {pf ? `${money(pf.totalPnl)} (${pct(pf.totalPnlPct)})` : "—"}
            </div>
          </div>
          <div className="glass animate-fade-up p-5" style={{ animationDelay: "120ms" }}>
            <div className="text-xs uppercase tracking-wide text-slate-500">Today</div>
            <div className={`mt-1 text-2xl font-semibold ${pf ? tone(pf.dayChangeValue) : ""}`}>
              {pf ? money(pf.dayChangeValue) : "—"}
            </div>
          </div>
        </div>

        {/* Holdings */}
        <div className="glass p-5">
          <div className="mb-3 text-sm font-semibold text-white">Holdings</div>
          {pf && pf.holdings.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs uppercase text-slate-500">
                  <tr>
                    <th className="py-2">Symbol</th>
                    <th className="py-2 text-right">Price</th>
                    <th className="py-2 text-right">Day</th>
                    <th className="py-2 text-right">Value</th>
                    <th className="py-2 text-right">P&amp;L</th>
                    <th className="py-2 text-right">Weight</th>
                  </tr>
                </thead>
                <tbody>
                  {pf.holdings.map((h) => (
                    <tr key={h.symbol} className="border-t border-white/5">
                      <td className="py-2.5 font-medium text-white">{h.symbol}</td>
                      <td className="py-2.5 text-right">{money(h.price)}</td>
                      <td className={`py-2.5 text-right ${tone(h.changePct)}`}>{pct(h.changePct)}</td>
                      <td className="py-2.5 text-right">{money(h.value)}</td>
                      <td className={`py-2.5 text-right ${tone(h.pnl)}`}>{pct(h.pnlPct)}</td>
                      <td className="py-2.5 text-right text-slate-400">{h.weight.toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-sm text-slate-500">{pf?.note ?? "Loading…"}</p>
          )}
        </div>

        {/* Watchlist */}
        <div className="glass p-5">
          <div className="mb-3 flex items-center justify-between">
            <span className="text-sm font-semibold text-white">Watchlist</span>
            <button onClick={() => refreshWatch(watchInput)} className="text-xs text-accent-soft hover:underline">
              Refresh
            </button>
          </div>
          <input
            value={watchInput}
            onChange={(e) => setWatchInput(e.target.value)}
            onBlur={() => refreshWatch(watchInput)}
            onKeyDown={(e) => e.key === "Enter" && refreshWatch(watchInput)}
            placeholder="Symbols, comma-separated — e.g. AAPL, NVDA, BTCUSD"
            className="w-full rounded-lg bg-white/5 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none"
          />
          {watch.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {watch.map((q) => (
                <div key={q.symbol} className="rounded-xl border border-white/10 px-3 py-2 text-sm">
                  <span className="font-medium text-white">{q.symbol}</span>{" "}
                  <span className="text-slate-300">{money(q.price)}</span>{" "}
                  <span className={tone(q.changePct)}>{pct(q.changePct)}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* AI scan */}
        <div className="glass p-5">
          <div className="mb-3 flex items-center justify-between">
            <span className="text-sm font-semibold text-white">🔎 AI scan — alerts &amp; suggestions</span>
            <button
              onClick={runScan}
              disabled={scanLoading}
              className="rounded-xl bg-accent px-4 py-2 text-sm font-medium text-white shadow-glow transition hover:bg-accent-soft disabled:opacity-40"
            >
              {scanLoading ? "Scanning…" : "Run scan"}
            </button>
          </div>
          {scanLoading && <div className="h-3 w-2/3 animate-pulse rounded bg-white/10" />}
          {scan && <Markdown>{scan}</Markdown>}
          {!scan && !scanLoading && (
            <p className="text-sm text-slate-500">
              Scans your holdings + watchlist for moves, concentration risk, and reasoned ideas. Never trades.
            </p>
          )}
        </div>

        {/* Research */}
        <div className="glass p-5">
          <div className="mb-3 text-sm font-semibold text-white">📑 Ticker research brief</div>
          <div className="flex gap-2">
            <input
              value={researchSym}
              onChange={(e) => setResearchSym(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && runResearch()}
              placeholder="e.g. NVDA"
              className="flex-1 rounded-lg bg-white/5 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none"
            />
            <button
              onClick={runResearch}
              disabled={researchLoading || !researchSym.trim()}
              className="rounded-xl border border-white/10 px-4 py-2 text-sm text-white transition hover:bg-white/5 disabled:opacity-40"
            >
              {researchLoading ? "Researching…" : "Research"}
            </button>
          </div>
          {researchLoading && <div className="mt-3 h-3 w-1/2 animate-pulse rounded bg-white/10" />}
          {research && (
            <div className="mt-4">
              <Markdown>{research}</Markdown>
            </div>
          )}
        </div>

        <p className="text-center text-xs text-slate-600">Not financial advice. JoeMoyo OS never places trades.</p>
      </div>
    </>
  );
}
