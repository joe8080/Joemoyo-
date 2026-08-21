import { zodToJsonSchema } from 'zod-to-json-schema';
import type { LLMProvider, LlmCall, LlmResult } from '@/lib/providers/types';
import { env } from '@/lib/env';

/**
 * OpenAI-compatible chat-completions adapter with strict structured output.
 *
 * Two rules are enforced here rather than left to the prompt:
 *  - The response is parsed against the caller's zod schema. A response that
 *    fails validation is retried with the validation error appended, and after
 *    `maxAttempts` the stage fails. Nothing is coerced or partially accepted.
 *  - `fast` and `review` must resolve to different models. A writer is never
 *    allowed to grade its own draft.
 */
export class HttpLLMProvider implements LLMProvider {
  readonly name = 'http-openai-compatible@1';
  readonly isLive = true;

  private readonly apiKey: string;
  private readonly baseUrl: string;
  private readonly modelFast: string;
  private readonly modelReview: string;

  constructor(opts?: { apiKey?: string; baseUrl?: string; modelFast?: string; modelReview?: string }) {
    const e = env();
    const apiKey = opts?.apiKey ?? e.AIFT_LLM_API_KEY;
    if (!apiKey) throw new Error('HttpLLMProvider requires AIFT_LLM_API_KEY');
    this.apiKey = apiKey;
    this.baseUrl = (opts?.baseUrl ?? e.AIFT_LLM_BASE_URL ?? 'https://api.openai.com/v1').replace(/\/$/u, '');
    this.modelFast = opts?.modelFast ?? e.AIFT_LLM_MODEL_FAST ?? '';
    this.modelReview = opts?.modelReview ?? e.AIFT_LLM_MODEL_REVIEW ?? '';
    if (!this.modelFast || !this.modelReview) {
      throw new Error('Both AIFT_LLM_MODEL_FAST and AIFT_LLM_MODEL_REVIEW must be set');
    }
    if (this.modelFast === this.modelReview) {
      throw new Error(
        'AIFT_LLM_MODEL_FAST and AIFT_LLM_MODEL_REVIEW must differ: the drafting model may not grade its own output',
      );
    }
  }

  async complete<T>(call: LlmCall<T>): Promise<LlmResult<T>> {
    const model = call.role === 'review' ? this.modelReview : this.modelFast;
    const maxAttempts = call.maxAttempts ?? 3;
    const jsonSchema = zodToJsonSchema(call.schema, { name: call.schemaName, target: 'openApi3' });

    let lastError = '';
    for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
      const messages = [
        { role: 'system', content: call.system },
        {
          role: 'user',
          content: lastError
            ? `${call.user}\n\nYour previous response failed schema validation: ${lastError}\nReturn corrected JSON only.`
            : call.user,
        },
      ];

      const res = await fetch(`${this.baseUrl}/chat/completions`, {
        method: 'POST',
        headers: { 'content-type': 'application/json', authorization: `Bearer ${this.apiKey}` },
        body: JSON.stringify({
          model,
          temperature: call.role === 'review' ? 0 : 0.4,
          messages,
          response_format: {
            type: 'json_schema',
            json_schema: { name: call.schemaName, strict: false, schema: jsonSchema },
          },
        }),
      });

      if (!res.ok) {
        // Never echo the body: a provider error page can contain the request,
        // and the request contains the redacted-but-private research context.
        throw new Error(`LLM request failed with HTTP ${res.status} (${call.schemaName}, role=${call.role})`);
      }

      const body = (await res.json()) as {
        choices?: Array<{ message?: { content?: string } }>;
        usage?: { prompt_tokens?: number; completion_tokens?: number };
      };
      const content = body.choices?.[0]?.message?.content ?? '';

      let candidate: unknown;
      try {
        candidate = JSON.parse(content);
      } catch {
        lastError = 'response was not valid JSON';
        continue;
      }

      const parsed = call.schema.safeParse(candidate);
      if (!parsed.success) {
        lastError = parsed.error.issues.map((i) => `${i.path.join('.')}: ${i.message}`).join('; ');
        continue;
      }

      return {
        value: parsed.data,
        usage: {
          provider: this.name,
          model,
          inputTokens: body.usage?.prompt_tokens ?? null,
          outputTokens: body.usage?.completion_tokens ?? null,
          costUsd: null,
        },
        attempts: attempt,
      };
    }

    throw new Error(`LLM output failed ${call.schemaName} validation after ${maxAttempts} attempts: ${lastError}`);
  }
}
