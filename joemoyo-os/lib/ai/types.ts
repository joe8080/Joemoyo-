export type ProviderId = "claude" | "openai" | "perplexity";

export interface ProviderMeta {
  id: ProviderId;
  label: string;
  model: string;
  accent: string;
  blurb: string;
  envKey: string;
}

export const PROVIDERS: Record<ProviderId, ProviderMeta> = {
  claude: {
    id: "claude",
    label: "Claude",
    model: "claude-sonnet-4-6",
    accent: "#d97757",
    blurb: "Anthropic — deep reasoning & writing",
    envKey: "ANTHROPIC_API_KEY",
  },
  openai: {
    id: "openai",
    label: "ChatGPT",
    model: "gpt-4o",
    accent: "#10a37f",
    blurb: "OpenAI — versatile generalist",
    envKey: "OPENAI_API_KEY",
  },
  perplexity: {
    id: "perplexity",
    label: "Perplexity",
    model: "sonar-pro",
    accent: "#20b8cd",
    blurb: "Live web search with citations",
    envKey: "PERPLEXITY_API_KEY",
  },
};

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface ChatResult {
  provider: ProviderId;
  model: string;
  text: string;
  error?: string;
  citations?: string[];
}
