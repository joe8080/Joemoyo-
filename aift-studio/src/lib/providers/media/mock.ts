import type { MediaAsset, MediaProvider, MediaRequest } from '@/lib/providers/types';
import { seededRandom, stableHash } from '@/lib/util/hash';

/**
 * Procedural stand-in for a generative image provider.
 *
 * It produces an abstract, deterministic field — never anything resembling a
 * chart, a figure, a logo or a screenshot. That is the same constraint the live
 * adapter operates under: generated media is atmosphere, and `factualContentAllowed`
 * is hard-coded `false` so the visual gate treats it as decorative wherever it appears.
 */
export class MockMediaProvider implements MediaProvider {
  readonly name = 'procedural-broll@1';
  readonly isLive = false;

  async generate(req: MediaRequest): Promise<MediaAsset> {
    const seed = stableHash(`${req.prompt}|${req.seed}|${req.aspect}`);
    const rnd = seededRandom(seed);
    const [w, h] = req.aspect === '16:9' ? [1920, 1080] : [1080, 1920];

    const hue = Math.floor(rnd() * 360);
    const nodes = Array.from({ length: 34 }, () => ({
      x: rnd() * w, y: rnd() * h, r: 40 + rnd() * 260, o: 0.05 + rnd() * 0.22,
      hue: (hue + (rnd() * 70 - 35) + 360) % 360,
    }));
    const lines = Array.from({ length: 22 }, () => ({
      x1: rnd() * w, y1: rnd() * h, x2: rnd() * w, y2: rnd() * h, o: 0.05 + rnd() * 0.12,
    }));

    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">
  <defs>
    <radialGradient id="bg" cx="50%" cy="40%" r="80%">
      <stop offset="0%" stop-color="hsl(${hue} 45% 16%)"/>
      <stop offset="100%" stop-color="hsl(${(hue + 210) % 360} 40% 5%)"/>
    </radialGradient>
    <filter id="soft"><feGaussianBlur stdDeviation="46"/></filter>
  </defs>
  <rect width="${w}" height="${h}" fill="url(#bg)"/>
  <g filter="url(#soft)">${nodes
    .map((n) => `<circle cx="${n.x.toFixed(1)}" cy="${n.y.toFixed(1)}" r="${n.r.toFixed(1)}" fill="hsl(${n.hue.toFixed(0)} 70% 55%)" opacity="${n.o.toFixed(3)}"/>`)
    .join('')}</g>
  <g stroke="hsl(${hue} 60% 70%)" stroke-width="1.2">${lines
    .map((l) => `<line x1="${l.x1.toFixed(1)}" y1="${l.y1.toFixed(1)}" x2="${l.x2.toFixed(1)}" y2="${l.y2.toFixed(1)}" opacity="${l.o.toFixed(3)}"/>`)
    .join('')}</g>
</svg>`;

    return {
      bytes: new TextEncoder().encode(svg),
      mimeType: 'image/svg+xml',
      generator: this.name,
      prompt: req.prompt,
      seed: req.seed,
      factualContentAllowed: false,
    };
  }
}
