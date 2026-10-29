// node images/sun/sheet.mjs t1 t2 ... -> images/sun/qa/sheet_beats.png (0.5x stills in a grid)
import {renderStill, selectComposition, openBrowser} from '@remotion/renderer';
import {execFileSync} from 'node:child_process';
import path from 'node:path';
const serveUrl = path.resolve('build');
const times = process.argv.slice(2).map(Number);
const browser = await openBrowser('chrome', {browserExecutable: '/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell', chromiumOptions: {gl: 'swangle'}});
const composition = await selectComposition({serveUrl, id: 'SunShort', puppeteerInstance: browser});
const files = [];
for (const t of times) {
  const frame = Math.min(composition.durationInFrames - 1, Math.round(t * 60));
  const out = `images/sun/qa/stills/s_${String(frame).padStart(4, '0')}.png`;
  await renderStill({composition, serveUrl, output: out, frame, scale: 0.25, puppeteerInstance: browser, overwrite: true});
  files.push([out, t]);
}
await browser.close({silent: true});
const py = `
import sys; from PIL import Image, ImageDraw
fs=${JSON.stringify(files)}
cols=6; w,h=270,480; rows=(len(fs)+cols-1)//cols
S=Image.new('RGB',(cols*w,rows*(h+18)),(255,255,255)); d=ImageDraw.Draw(S)
for i,(f,t) in enumerate(fs):
    im=Image.open(f).convert('RGB').resize((w,h)); x=(i%cols)*w; y=(i//cols)*(h+18)
    S.paste(im,(x,y+18)); d.text((x+4,y+3),f"{t:.2f}s",fill=(0,0,0))
S.save('images/sun/qa/sheet_beats.png')`;
execFileSync('python3', ['-c', py], {stdio: 'inherit'});
console.log('done', files.length);
