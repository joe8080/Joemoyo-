import { mkdir, readFile, readdir, writeFile } from 'node:fs/promises';
import { dirname, join, relative, resolve, sep } from 'node:path';
import type { StorageProvider, StoredObject } from '@/lib/providers/types';
import { sha256 } from '@/lib/util/hash';

/**
 * Filesystem storage for local development and for producing a content pack you
 * can open directly. The root is git-ignored, and every key is resolved and
 * checked against the root so a crafted key cannot escape it.
 */
export class LocalStorageProvider implements StorageProvider {
  readonly name = 'local-fs@1';
  private readonly root: string;

  constructor(root = join(process.cwd(), '.artifacts')) {
    this.root = resolve(root);
  }

  private resolveKey(key: string): string {
    const target = resolve(this.root, key);
    const rel = relative(this.root, target);
    if (rel.startsWith('..') || rel.startsWith(`..${sep}`) || resolve(rel) === rel) {
      throw new Error(`storage key escapes the artifact root: ${key}`);
    }
    return target;
  }

  async put(key: string, data: Uint8Array | string, _contentType: string): Promise<StoredObject> {
    const path = this.resolveKey(key);
    const bytes = typeof data === 'string' ? new TextEncoder().encode(data) : data;
    await mkdir(dirname(path), { recursive: true });
    await writeFile(path, bytes);
    return { key, sha256: sha256(bytes), bytes: bytes.byteLength, url: `file://${path}` };
  }

  async get(key: string): Promise<Uint8Array> {
    return new Uint8Array(await readFile(this.resolveKey(key)));
  }

  async signedUrl(key: string, _ttlSeconds: number): Promise<string> {
    return `file://${this.resolveKey(key)}`;
  }

  async list(prefix: string): Promise<string[]> {
    const base = this.resolveKey(prefix);
    const out: string[] = [];
    const walk = async (dir: string): Promise<void> => {
      let entries;
      try {
        entries = await readdir(dir, { withFileTypes: true });
      } catch {
        return;
      }
      for (const e of entries) {
        const full = join(dir, e.name);
        if (e.isDirectory()) await walk(full);
        else out.push(relative(this.root, full).split(sep).join('/'));
      }
    };
    await walk(base);
    return out.sort();
  }

  get rootPath(): string {
    return this.root;
  }
}
