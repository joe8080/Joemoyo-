import { renderVideo } from '@/lib/video/render';
import { assembleNarration } from '@/lib/video/audio';
import { MockVoiceProvider } from '@/lib/providers/voice/mock';

const html = `<!doctype html><html><head><style>
html,body{margin:0;width:960px;height:540px;background:#07090d;color:#f2f5f9;font-family:sans-serif}
#t{position:absolute;top:200px;left:60px;font-size:64px;font-weight:800}
</style></head><body><div id="t">0</div>
<script>
window.__seek=function(t){document.getElementById('t').textContent=(t/1000).toFixed(2)+'s';
document.body.style.background='hsl('+(t/12%360)+' 40% 8%)';};
window.__ready=true;__seek(0);
</script></body></html>`;

const voice = new MockVoiceProvider();
const clip = await voice.speak({ text: 'one two three four five six seven eight', voice: 'en-gb' });
const audio = assembleNarration([{ wav: clip.wav, startMs: 200 }], 3000);

const t0 = Date.now();
const res = await renderVideo({
  html, width: 960, height: 540, fps: 30, totalMs: 3000,
  audioWav: audio, outPath: '.artifacts/smoke.mp4',
  onProgress: (f, n) => { if (f % 30 === 0) console.log(`frame ${f}/${n}`); },
});
console.log(res, 'elapsed ms', Date.now() - t0);
