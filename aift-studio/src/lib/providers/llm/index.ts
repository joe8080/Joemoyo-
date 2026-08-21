import type { LLMProvider } from '@/lib/providers/types';
import { env } from '@/lib/env';
import { MockLLMProvider } from './mock';
import { HttpLLMProvider } from './http';

export function createLLMProvider(): LLMProvider {
  const e = env();
  if (!e.AIFT_LLM_API_KEY) return new MockLLMProvider();
  return new HttpLLMProvider();
}

export { MockLLMProvider, HttpLLMProvider };
