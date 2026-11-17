// Usage: EP=dahomey [FROM=0 TO=899] OUT=out/x.mp4 node render.mjs   (bundle first: npx remotion bundle src/index.ts --out-dir bundle)
import {renderMedia, selectComposition} from '@remotion/renderer';
const serveUrl = process.env.BUNDLE || 'bundle';
const browserExecutable = '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell';
const comp = await selectComposition({serveUrl, id: process.env.EP || 'dahomey', browserExecutable});
const range = process.env.FROM ? [Number(process.env.FROM), Number(process.env.TO)] : undefined;
let last = -5;
await renderMedia({composition: comp, serveUrl, codec: 'h264', crf: 17, outputLocation: process.env.OUT || 'out/video_silent.mp4', browserExecutable, concurrency: Number(process.env.CONC || 4), muted: true, frameRange: range,
  onProgress: ({progress}) => { const p = Math.floor(progress * 100); if (p >= last + 5) { last = p; console.log(new Date().toISOString(), p + '%'); } }});
console.log('DONE');
