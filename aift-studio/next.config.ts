import type { NextConfig } from 'next';

/**
 * Hard architectural guarantees expressed in build config:
 *  - `serverExternalPackages` keeps render-engine binaries out of any client bundle.
 *  - No `env` block: secrets are read at runtime, server-side only (see src/lib/env.ts).
 *  - No image/remote domains: the studio never fetches third-party media into the browser.
 */
const nextConfig: NextConfig = {
  reactStrictMode: true,
  serverExternalPackages: ['playwright-core', 'ffmpeg-static'],
  typedRoutes: false,
  experimental: {
    // Only server code may import these; violations fail the build.
    typedEnv: false,
  },
};

export default nextConfig;
