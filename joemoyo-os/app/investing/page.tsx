import ModuleScaffold from "@/components/ModuleScaffold";

export default function Investing() {
  return (
    <ModuleScaffold
      title="Investing"
      subtitle="Portfolio, market data, and AI alerts & suggestions."
      phase="Phase 3"
      icon="📈"
      features={[
        { title: "Portfolio dashboard", desc: "Holdings, allocation, P&L and progress toward your goals — synced from your vault." },
        { title: "Live market data", desc: "Quotes, charts and fundamentals via a free market-data API." },
        { title: "AI alerts", desc: "Daily scan that flags moves, news and risks on what you hold or watch." },
        { title: "Buy/sell suggestions", desc: "AI-reasoned ideas with rationale — you stay in control, nothing auto-trades." },
        { title: "Research briefs", desc: "One-tap deep-dive on any ticker, blending Perplexity's live web with Claude's analysis." },
      ]}
      wiring={[
        "Supabase vault: invest/ agents (sync_portfolio, goal_progress, uc_monitor)",
        "Market data API (FMP / Alpha Vantage) — keys in .env",
        "AI Hub for analysis, alerts and research briefs",
      ]}
    />
  );
}
