import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition, openBrowser} from '@remotion/renderer';
import path from 'path'; import fs from 'fs';
const [,, comp, outdir, ...frames] = process.argv;
const B='/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell';
const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts'), onProgress:()=>{}});
const browser = await openBrowser('chrome', {browserExecutable: B, chromiumOptions:{gl:'angle'}});
const c = await selectComposition({serveUrl, id: comp, puppeteerInstance: browser});
fs.mkdirSync(outdir,{recursive:true});
for (const fr of frames) {
  const t0=Date.now();
  await renderStill({composition:c, serveUrl, frame: parseInt(fr), output: `${outdir}/${comp}_${String(fr).padStart(5,'0')}.png`, puppeteerInstance: browser, imageFormat:'png', chromiumOptions:{gl:'angle'}});
  console.log(comp, fr, ((Date.now()-t0)/1000).toFixed(1)+'s');
}
await browser.close({silent:true});
