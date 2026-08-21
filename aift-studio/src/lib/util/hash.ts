import { createHash } from 'node:crypto';

export function sha256(data: Uint8Array | string): string {
  return createHash('sha256').update(data as never).digest('hex');
}

/** Deterministic 32-bit hash, used for stable ids and seeded jitter. */
export function stableHash(input: string): number {
  let h = 2166136261;
  for (let i = 0; i < input.length; i += 1) {
    h ^= input.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

/** Deterministic UUID-shaped id derived from a namespace + key. */
export function stableId(namespace: string, key: string): string {
  const h = createHash('sha256').update(`${namespace}:${key}`).digest('hex');
  return [h.slice(0, 8), h.slice(8, 12), `4${h.slice(13, 16)}`, `8${h.slice(17, 20)}`, h.slice(20, 32)].join('-');
}

/** Seeded PRNG so "random" choices replay identically across runs. */
export function seededRandom(seed: number): () => number {
  let s = seed >>> 0 || 1;
  return () => {
    s ^= s << 13; s >>>= 0;
    s ^= s >> 17;
    s ^= s << 5; s >>>= 0;
    return s / 0xffffffff;
  };
}
