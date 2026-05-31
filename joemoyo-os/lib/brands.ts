export interface Brand {
  id: string;
  name: string;
  kind: "youtube" | "service" | "store";
  tone: string;
  audience: string;
  style: string;
  cta: string;
  niches?: string[];
}

/** Mirrors config/brand_profiles.py from the Python agent system. */
export const BRANDS: Brand[] = [
  {
    id: "history_channel",
    name: "Chronicles of Time",
    kind: "youtube",
    tone: "authoritative, engaging, narrative-driven, research-backed, cinematic",
    audience: "history enthusiasts, students, curious learners aged 25-55",
    style: "documentary-style storytelling with academic rigor",
    cta: "Like and subscribe so you never miss a story from history",
    niches: ["ancient civilizations", "wars", "empires", "biographies", "revolutions"],
  },
  {
    id: "finance_channel",
    name: "Capital Edge",
    kind: "youtube",
    tone: "analytical, confident, balanced, plain-English, actionable",
    audience: "retail investors, working professionals, ages 28-50",
    style: "data-driven insights with clear takeaways, no fluff",
    cta: "Subscribe for weekly market analysis — hit the bell so you never miss a video",
    niches: ["stocks", "crypto", "real estate", "ETFs", "personal finance", "economy"],
  },
  {
    id: "music_studio",
    name: "JoeMoyo Studios",
    kind: "service",
    tone: "creative, professional, collaborative, warm, passionate",
    audience: "independent artists, bands, content creators, podcasters",
    style: "creative partnership focused on world-class sound quality",
    cta: "Book a free consultation — let's create something amazing together",
  },
  {
    id: "shopify_store",
    name: "JoeMoyo Store",
    kind: "store",
    tone: "friendly, enthusiastic, benefit-focused, trustworthy",
    audience: "general online shoppers looking for quality and value",
    style: "clear, benefit-driven product copy with strong social proof",
    cta: "Shop now — free shipping on all orders",
  },
];

export function getBrand(id: string): Brand | undefined {
  return BRANDS.find((b) => b.id === id);
}

export function brandContext(b: Brand): string {
  return [
    `Brand: ${b.name}`,
    `Tone: ${b.tone}`,
    `Audience: ${b.audience}`,
    `Style: ${b.style}`,
    `Call to action: ${b.cta}`,
    b.niches ? `Niches: ${b.niches.join(", ")}` : "",
  ]
    .filter(Boolean)
    .join("\n");
}
