import { runProvider } from "@/lib/ai/providers";
import { ProviderId } from "@/lib/ai/types";
import { PortfolioSummary } from "@/lib/invest/portfolio";
import { Quote } from "@/lib/market/quotes";

const ANALYST_SYSTEM =
  "You are the Investing analyst inside JoeMoyo OS. You give clear, balanced, plain-English " +
  "analysis for a retail investor. You NEVER place trades — you only surface alerts and " +
  "suggestions the user decides on. Always include risk and a one-line 'not financial advice' " +
  "footer. Be specific and concise. Output Markdown.";

function fmt(n: number) {
  return n.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

/** Daily scan: alerts + buy/sell suggestions for the held + watched names. */
export async function runScan(
  portfolio: PortfolioSummary,
  watch: Quote[],
  provider: ProviderId = "claude",
) {
  const holdingsText = portfolio.holdings.length
    ? portfolio.holdings
        .map(
          (h) =>
            `${h.symbol}: ${h.shares} sh @ avg ${fmt(h.cost_basis)}, now ${fmt(h.price)} ` +
            `(day ${h.changePct.toFixed(2)}%, P&L ${h.pnlPct.toFixed(1)}%, weight ${h.weight.toFixed(1)}%)`,
        )
        .join("\n")
    : "No holdings provided.";
  const watchText = watch.length
    ? watch.map((w) => `${w.symbol}: ${fmt(w.price)} (day ${w.changePct.toFixed(2)}%)`).join("\n")
    : "No watchlist provided.";

  const prompt =
    `Portfolio (total value ${fmt(portfolio.totalValue)}, P&L ${portfolio.totalPnlPct.toFixed(1)}%, ` +
    `today ${portfolio.dayChangeValue >= 0 ? "+" : ""}${fmt(portfolio.dayChangeValue)}):\n${holdingsText}\n\n` +
    `Watchlist:\n${watchText}\n\n` +
    "Produce:\n" +
    "## ⚠️ Alerts — anything notable today (big moves, concentration risk, names to watch).\n" +
    "## 💡 Suggestions — 2-4 specific, reasoned buy/trim/hold ideas with a one-line rationale each.\n" +
    "Keep it tight. Flag concentration if any single weight > 25%.";

  return runProvider(provider, [{ role: "user", content: prompt }], ANALYST_SYSTEM);
}

/** Deep-dive research brief on one ticker. Perplexity is best (live web + citations). */
export async function researchTicker(symbol: string, provider: ProviderId = "perplexity") {
  const prompt =
    `Write a concise research brief on ${symbol.toUpperCase()}. Cover: what it does, recent ` +
    "price action and news, the bull case, the bear case, key risks, and a balanced bottom line. " +
    "Use Markdown headings. End with 'Not financial advice.'";
  return runProvider(provider, [{ role: "user", content: prompt }], ANALYST_SYSTEM);
}
