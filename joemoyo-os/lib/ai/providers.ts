import Anthropic from "@anthropic-ai/sdk";
import OpenAI from "openai";
import { ChatMessage, ChatResult, PROVIDERS, ProviderId } from "./types";

const SYSTEM_DEFAULT =
  "You are a module inside JoeMoyo OS, a personal command center for a multi-brand " +
  "creator/investor. Be concise, practical, and action-oriented.";

/** Is a given provider configured (has an API key)? */
export function providerReady(id: ProviderId): boolean {
  return Boolean(process.env[PROVIDERS[id].envKey]);
}

async function callClaude(messages: ChatMessage[], system: string): Promise<ChatResult> {
  const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY! });
  const model = PROVIDERS.claude.model;
  const res = await client.messages.create({
    model,
    max_tokens: 1500,
    system,
    messages: messages
      .filter((m) => m.role !== "system")
      .map((m) => ({ role: m.role as "user" | "assistant", content: m.content })),
  });
  const text = res.content
    .filter((b): b is Anthropic.TextBlock => b.type === "text")
    .map((b) => b.text)
    .join("\n");
  return { provider: "claude", model, text };
}

/** OpenAI + Perplexity share the OpenAI-compatible chat completions shape. */
async function callOpenAICompatible(
  id: "openai" | "perplexity",
  messages: ChatMessage[],
  system: string,
): Promise<ChatResult> {
  const meta = PROVIDERS[id];
  const client = new OpenAI({
    apiKey: process.env[meta.envKey]!,
    baseURL: id === "perplexity" ? "https://api.perplexity.ai" : undefined,
  });
  const res = await client.chat.completions.create({
    model: meta.model,
    max_tokens: 1500,
    messages: [{ role: "system", content: system }, ...messages.filter((m) => m.role !== "system")],
  });
  const text = res.choices[0]?.message?.content ?? "";
  // Perplexity returns citations alongside the choice.
  const citations = (res as unknown as { citations?: string[] }).citations;
  return { provider: id, model: meta.model, text, citations };
}

/** Run a single provider, never throwing — errors are returned in the result. */
export async function runProvider(
  id: ProviderId,
  messages: ChatMessage[],
  system: string = SYSTEM_DEFAULT,
): Promise<ChatResult> {
  if (!providerReady(id)) {
    return {
      provider: id,
      model: PROVIDERS[id].model,
      text: "",
      error: `Not configured — add ${PROVIDERS[id].envKey} to your environment.`,
    };
  }
  try {
    if (id === "claude") return await callClaude(messages, system);
    return await callOpenAICompatible(id, messages, system);
  } catch (err) {
    return {
      provider: id,
      model: PROVIDERS[id].model,
      text: "",
      error: err instanceof Error ? err.message : "Unknown provider error",
    };
  }
}

/** Fan out to several providers at once for side-by-side comparison. */
export async function runMany(
  ids: ProviderId[],
  messages: ChatMessage[],
  system?: string,
): Promise<ChatResult[]> {
  return Promise.all(ids.map((id) => runProvider(id, messages, system)));
}
