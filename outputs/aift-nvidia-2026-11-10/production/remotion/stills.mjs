import {renderStill, selectComposition} from '@remotion/renderer';
const serveUrl=process.env.BUNDLE||'bundle';
const browserExecutable='/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell';
const comp=await selectComposition({serveUrl,id:process.env.COMP||'Review',browserExecutable});
const frames=process.argv[2].split(',').map(Number);
for(const f of frames){await renderStill({composition:comp,serveUrl,frame:f,output:`${process.env.STILLS||'stills'}/f${String(f).padStart(5,'0')}.jpg`,imageFormat:'jpeg',jpegQuality:80,browserExecutable,scale:Number(process.env.SCALE||0.5)});console.log('ok',f);}
