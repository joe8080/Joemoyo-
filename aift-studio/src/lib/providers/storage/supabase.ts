import 'server-only';
import type { StorageProvider, StoredObject } from '@/lib/providers/types';
import { sha256 } from '@/lib/util/hash';
import { adminClient } from '@/lib/supabase/admin';
import { env } from '@/lib/env';

/**
 * Private-bucket storage.
 *
 * There is no public-URL method on this class by design. Assets are reachable
 * only through short-lived signed URLs minted server-side, so a leaked storage
 * key on its own grants nothing.
 */
export class SupabaseStorageProvider implements StorageProvider {
  readonly name = 'supabase-private-bucket@1';
  private readonly bucket: string;

  constructor(bucket = env().AIFT_STORAGE_BUCKET) {
    this.bucket = bucket;
  }

  async put(key: string, data: Uint8Array | string, contentType: string): Promise<StoredObject> {
    const bytes = typeof data === 'string' ? new TextEncoder().encode(data) : data;
    const { error } = await adminClient().storage.from(this.bucket).upload(key, bytes, { contentType, upsert: true });
    if (error) throw new Error(`storage upload failed for ${key}: ${error.message}`);
    return { key, sha256: sha256(bytes), bytes: bytes.byteLength, url: `supabase://${this.bucket}/${key}` };
  }

  async get(key: string): Promise<Uint8Array> {
    const { data, error } = await adminClient().storage.from(this.bucket).download(key);
    if (error || !data) throw new Error(`storage download failed for ${key}: ${error?.message ?? 'no data'}`);
    return new Uint8Array(await data.arrayBuffer());
  }

  async signedUrl(key: string, ttlSeconds: number): Promise<string> {
    const { data, error } = await adminClient().storage.from(this.bucket).createSignedUrl(key, ttlSeconds);
    if (error || !data) throw new Error(`could not sign ${key}: ${error?.message ?? 'no data'}`);
    return data.signedUrl;
  }

  async list(prefix: string): Promise<string[]> {
    const { data, error } = await adminClient().storage.from(this.bucket).list(prefix, { limit: 1000 });
    if (error) throw new Error(`storage list failed for ${prefix}: ${error.message}`);
    return (data ?? []).map((o) => `${prefix}/${o.name}`);
  }
}
