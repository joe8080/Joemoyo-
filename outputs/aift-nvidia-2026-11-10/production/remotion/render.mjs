import {renderMedia, selectComposition} from '@remotion/renderer';
const serveUrl=process.env.BUNDLE||'bundle';
const browserExecutable='/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell';
const comp=await selectComposition({serveUrl,id:'Review',browserExecutable});
let last=0;
await renderMedia({composition:comp,serveUrl,codec:'h264',crf:18,outputLocation:''+(process.env.OUT||'out/video_silent.mp4')+'',browserExecutable,concurrency:3,muted:true,
 onProgress:({progress})=>{const p=Math.floor(progress*100); if(p>=last+5){last=p;console.log(new Date().toISOString(),p+'%');}}});
console.log('DONE');
