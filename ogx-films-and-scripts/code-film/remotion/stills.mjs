// Usage: STILLS=stills1 node stills.mjs 120,480,900
import {renderStill, selectComposition} from '@remotion/renderer';
const serveUrl = process.env.BUNDLE || 'bundle';
const browserExecutable = '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell';
const comp = await selectComposition({serveUrl, id: process.env.EP || 'dahomey', browserExecutable});
for (const f of process.argv[2].split(',').map(Number)) { await renderStill({composition: comp, serveUrl, frame: f, output: `${process.env.STILLS || 'stills'}/f${String(f).padStart(5, '0')}.jpg`, imageFormat: 'jpeg', jpegQuality: 80, browserExecutable, scale: 0.5}); }
console.log('ok');
