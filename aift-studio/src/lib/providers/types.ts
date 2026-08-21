import type { z } from 'zod';
import type { ContentContext } from '@/lib/domain';

/**
 * Every external dependency sits behind one of these interfaces, and every one
 * has a mock implementation. That is what makes the full pipeline runnable —
 * and testable — with no credentials and no spend.
 */

// ---------------------------------------------------------------------------

export type LlmRole = 'fast' | 'review';

export type LlmCall<T> = {
  role: LlmRole;
  promptVersion: string;
  system: string;
  user: string;
  /** Output-typed: inference must follow the parsed shape, not the input shape. */
  schema: z.ZodType<T, z.ZodTypeDef, unknown>;
  schemaName: string;
  maxAttempts?: number;
  /**
   * The same structured object that was serialised into `user`. Live providers
   * ignore it; the mock provider composes deterministically from it instead of
   * returning a canned blob. Keeping it typed here means a mock run exercises
   * the real stage inputs rather than a parallel fixture path.
   */
  payload: unknown;
};

export type LlmUsage = {
  provider: string;
  model: string;
  inputTokens: number | null;
  outputTokens: number | null;
  costUsd: number | null;
};

export type LlmResult<T> = { value: T; usage: LlmUsage; attempts: number };

export interface LLMProvider {
  readonly name: string;
  readonly isLive: boolean;
  complete<T>(call: LlmCall<T>): Promise<LlmResult<T>>;
}

// ---------------------------------------------------------------------------

export type DiscoveredResult = {
  url: string;
  title: string;
  snippet: string;
  publisher: string;
};

export type FetchedSource = {
  canonicalUrl: string;
  title: string;
  publisher: string;
  publishedAt: string | null;
  accessedAt: string;
  text: string;
  /** Verbatim slice actually used to back a claim. */
  excerpt: string;
  contentHash: string;
  licenceNotes: string;
  status: 'fetched' | 'failed' | 'blocked_by_policy';
  failureReason?: string;
};

export interface ResearchProvider {
  readonly name: string;
  readonly isLive: boolean;
  /** Discovery only. Snippets returned here may never be cited. */
  discover(query: string, limit: number): Promise<DiscoveredResult[]>;
  /** Retrieval. A claim may only cite a source that came back `fetched`. */
  fetchSource(url: string): Promise<FetchedSource>;
}

// ---------------------------------------------------------------------------

export type ChartSpec = {
  kind: 'line' | 'bar';
  width: number;
  height: number;
  series: Array<{ label: string; points: Array<{ x: string; y: number }>; unit: string }>;
  yLabel: string;
  xLabel: string;
  sourceLabel: string;
  asOfDate: string;
  highlightIndex: number | null;
  /** 0 → nothing drawn, 1 → fully drawn. Drives deterministic animation. */
  progress: number;
  palette: { ink: string; inkDim: string; accent: string; accent2: string; grid: string; surface: string };
};

export interface ChartRenderer {
  readonly name: string;
  /** Pure function of the spec — same spec in, byte-identical SVG out. */
  renderSvg(spec: ChartSpec): string;
  /** The exact numbers a viewer will read, for the visual-accuracy gate. */
  visibleValues(spec: ChartSpec): string[];
}

// ---------------------------------------------------------------------------

export type MediaRequest = {
  prompt: string;
  aspect: '16:9' | '9:16';
  seed: number;
  kind: 'image' | 'video';
};

export type MediaAsset = {
  bytes: Uint8Array;
  mimeType: string;
  generator: string;
  prompt: string;
  seed: number;
  /**
   * Provenance flag. `false` means the asset is not permitted to carry any
   * numeric or factual content and the visual gate will treat it as decorative.
   */
  factualContentAllowed: false;
};

export interface MediaProvider {
  readonly name: string;
  readonly isLive: boolean;
  generate(req: MediaRequest): Promise<MediaAsset>;
}

// ---------------------------------------------------------------------------

export type VoiceRequest = { text: string; voice: string; targetSeconds?: number };

export type VoiceClip = {
  /** 16-bit PCM WAV. */
  wav: Uint8Array;
  durationSeconds: number;
  generator: string;
  voice: string;
  /** Preserved verbatim so captions and QA can be checked against it. */
  transcript: string;
  settings: Record<string, string | number>;
};

/**
 * A music bed. Contract: mono 16-bit PCM WAV, and provenance for every second
 * of it — a track whose licence nobody can state is a track that cannot ship.
 */
export type MusicRequest = { durationSeconds: number; mood: 'analytical' | 'tense' | 'open'; seed: number };

export type MusicBed = {
  wav: Uint8Array;
  durationSeconds: number;
  generator: string;
  title: string;
  licence: string;
  provenance: string;
};

export interface MusicProvider {
  readonly name: string;
  readonly isLive: boolean;
  generate(req: MusicRequest): Promise<MusicBed>;
}

export interface VoiceProvider {
  readonly name: string;
  readonly isLive: boolean;
  speak(req: VoiceRequest): Promise<VoiceClip>;
}

// ---------------------------------------------------------------------------

export type StoredObject = { key: string; sha256: string; bytes: number; url: string };

export interface StorageProvider {
  readonly name: string;
  put(key: string, data: Uint8Array | string, contentType: string): Promise<StoredObject>;
  get(key: string): Promise<Uint8Array>;
  /** Never returns a public URL. Private bucket + short-lived signed access only. */
  signedUrl(key: string, ttlSeconds: number): Promise<string>;
  list(prefix: string): Promise<string[]>;
}

// ---------------------------------------------------------------------------

export type JobDefinition<TInput> = {
  jobType: string;
  /** Same key ⇒ same run. Re-running is a no-op, not a duplicate. */
  idempotencyKey: (input: TInput) => string;
  timeoutMs: number;
  maxAttempts: number;
  run: (input: TInput, ctx: JobContext) => Promise<void>;
};

export type JobContext = {
  runId: string;
  log: (level: 'info' | 'warn' | 'error', stage: string, message: string) => void;
  recordProviderCall: (usage: LlmUsage & { promptVersion: string }) => void;
  signal: AbortSignal;
};

export interface JobRunner {
  readonly name: string;
  register<T>(def: JobDefinition<T>): void;
  trigger<T>(jobType: string, input: T): Promise<{ runId: string; deduplicated: boolean }>;
}

// ---------------------------------------------------------------------------

export interface PrivateContextProvider {
  readonly name: string;
  /** Redaction happens server-side, before this returns. */
  load(referenceDate: string): Promise<ContentContext>;
}

// ---------------------------------------------------------------------------

export type Providers = {
  llm: LLMProvider;
  research: ResearchProvider;
  chart: ChartRenderer;
  media: MediaProvider;
  voice: VoiceProvider;
  music: MusicProvider;
  storage: StorageProvider;
  jobs: JobRunner;
  context: PrivateContextProvider;
};
