import type { Scene, ScenePlan, Script } from '@/lib/schemas/content';
import type { BrandSettings } from '@/lib/domain';
import { stylesheet } from './theme';

/**
 * Builds the single self-contained HTML document the renderer screenshots.
 *
 * The whole film is one page. `__seek(tMs)` is a pure function of time: it picks
 * the active scene, computes local time and writes inline styles. Nothing
 * depends on wall-clock, CSS keyframes, requestAnimationFrame or transitions, so
 * frame 4,197 is identical on every run and on every machine — which is what
 * makes the rendered numbers auditable rather than merely plausible.
 */

export type CaptionWord = { w: string; start: number; end: number };
export type CaptionLine = { beatId: string; start: number; end: number; words: CaptionWord[] };

export type PreparedScene = {
  scene: Scene;
  /** Pre-rendered chart SVG, one entry per animation step. Produced by the Node chart renderer. */
  chartFrames?: string[];
  chartStepMs?: number;
  brollDataUri?: string;
};

export type ComposeInput = {
  plan: ScenePlan;
  script: Script;
  brand: BrandSettings;
  prepared: PreparedScene[];
  captions: CaptionLine[];
  formatLabel: string;
};

const ENTER_MS = 620;
const EXIT_MS = 380;

export function buildDocument(input: ComposeInput): string {
  const { plan, brand, prepared, captions } = input;
  const vertical = plan.height > plan.width;

  const chartBank: string[][] = [];
  const chartSteps: number[] = [];

  const sections = prepared.map((p, i) => {
    let chartIndex = -1;
    if (p.chartFrames && p.chartFrames.length > 0) {
      chartIndex = chartBank.length;
      chartBank.push(p.chartFrames);
      chartSteps.push(p.chartStepMs ?? 40);
    }
    return sceneHtml(p, i, chartIndex, vertical, input.formatLabel);
  });

  const chapterTicks = input.script.chapters
    .map((c) => {
      const beat = input.script.beats.findIndex((b) => b.beat_id === c.start_beat);
      const scene = plan.scenes[Math.max(0, beat)];
      return scene ? (scene.start_ms / plan.total_ms) * 100 : 0;
    })
    .map((pct) => `<i style="left:${pct.toFixed(3)}%"></i>`)
    .join('');

  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>${escapeHtml(input.script.working_title)}</title>
<style>${stylesheet(brand.visual_style, plan.width, plan.height)}</style></head>
<body><div id="stage">
  <div id="ground"></div>
  <div id="layers">${sections.join('\n')}</div>
  <div id="vignette"></div><div id="grain"></div>
  <div id="chrome">
    <div id="mark"><span class="dot"></span>${escapeHtml(brand.channel_name)}</div>
    <div id="refdate">${escapeHtml(input.formatLabel)} · ${escapeHtml(input.script.reference_date)}</div>
    <div id="chapterTag"></div>
    <div id="cite"></div>
    <div id="progress"><div id="bar"></div><div id="ticks">${chapterTicks}</div></div>
  </div>
  <div id="caption"></div>
</div>
<script>
const TOTAL=${plan.total_ms};
const SCENES=${JSON.stringify(plan.scenes.map((s, i) => ({
    i, s: s.start_ms, d: s.duration_ms, ch: chapterOf(input.script, s), cite: s.citation, c: s.composition,
  })))};
const CHARTS=${JSON.stringify(chartBank)};
const CHART_STEP=${JSON.stringify(chartSteps)};
const CAPS=${JSON.stringify(captions)};

const els=[...document.querySelectorAll('.scene')];
const bar=document.getElementById('bar');
const chapterTag=document.getElementById('chapterTag');
const cite=document.getElementById('cite');
const caption=document.getElementById('caption');

function ease(t){t=t<0?0:t>1?1:t;return 1-Math.pow(1-t,3);}
function easeInOut(t){t=t<0?0:t>1?1:t;return t<0.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2;}

const ANIM={
  rise:(p)=>({opacity:p,transform:'translate3d(0,'+((1-p)*34).toFixed(2)+'px,0)'}),
  fade:(p)=>({opacity:p,transform:'none'}),
  left:(p)=>({opacity:p,transform:'translate3d('+((1-p)*-52).toFixed(2)+'px,0,0)'}),
  pop:(p)=>({opacity:p,transform:'scale('+(0.94+0.06*p).toFixed(4)+')'}),
  wipe:(p)=>({opacity:1,clipPath:'inset(0 '+((1-p)*100).toFixed(2)+'% 0 0)'}),
};

let lastActive=-1;
function __seek(t){
  t=Math.max(0,Math.min(TOTAL-1,t));
  let active=0;
  for(let i=0;i<SCENES.length;i++){ if(t>=SCENES[i].s) active=i; else break; }
  const S=SCENES[active];
  const local=t-S.s;

  if(active!==lastActive){
    for(let i=0;i<els.length;i++) els[i].classList.toggle('on', i===active);
    chapterTag.textContent=S.ch||'';
    cite.textContent=S.cite||'';
    cite.style.opacity=S.cite?'1':'0';
    caption.classList.toggle('small', S.c==='line_chart'||S.c==='bar_chart'||S.c==='comparison_table');
    // A chapter card's narration is the chapter name, which is already the
    // largest thing on screen. Captioning it too would print the same words
    // three times in one frame.
    const isChapter = S.c==='chapter_card';
    caption.classList.toggle('off', isChapter);
    chapterTag.style.opacity = isChapter ? '0' : '1';
    lastActive=active;
  }

  // Scene-level enter/exit envelope.
  const enter=ease(local/${ENTER_MS});
  const outT=(S.d-local)/${EXIT_MS};
  const exit=ease(outT);
  const env=Math.min(enter,exit);
  const el=els[active];
  el.style.opacity=String(env);

  // Element-level staggered motion.
  const nodes=el.querySelectorAll('[data-a]');
  for(const n of nodes){
    const delay=+n.dataset.d||0, dur=+n.dataset.t||620;
    const p=ease((local-delay)/dur);
    const st=ANIM[n.dataset.a]?ANIM[n.dataset.a](p):ANIM.fade(p);
    for(const k in st) n.style[k]=st[k];
  }

  // Count-ups.
  for(const n of el.querySelectorAll('[data-count]')){
    const to=parseFloat(n.dataset.count), dec=+n.dataset.dec||0;
    const delay=+n.dataset.cd||220, dur=+n.dataset.ct||1100;
    const p=easeInOut((local-delay)/dur);
    n.textContent=(n.dataset.pre||'')+ (to*p).toFixed(dec) + (n.dataset.suf||'');
  }

  // Charts: pick the pre-rendered draw step for this instant.
  for(const n of el.querySelectorAll('[data-chart]')){
    const bank=CHARTS[+n.dataset.chart];
    if(!bank) continue;
    const step=CHART_STEP[+n.dataset.chart]||40;
    const delay=+n.dataset.cdelay||260;
    let idx=Math.floor((local-delay)/step);
    idx=idx<0?0:idx>=bank.length?bank.length-1:idx;
    if(n.dataset.cur!==String(idx)){ n.innerHTML=bank[idx]; n.dataset.cur=String(idx); }
  }

  bar.style.width=((t/TOTAL)*100).toFixed(4)+'%';

  // Captions.
  let line=null;
  for(const c of CAPS){ if(t>=c.start&&t<c.end){line=c;break;} }
  if(!line){ caption.innerHTML=''; caption.dataset.cur=''; }
  else {
    if(caption.dataset.cur!==line.beatId){
      caption.innerHTML=line.words.map((w,i)=>'<span class="w" data-i="'+i+'">'+w.w+'</span>').join(' ');
      caption.dataset.cur=line.beatId;
    }
    const spans=caption.children;
    for(let i=0;i<spans.length;i++){
      const w=line.words[i]; if(!w) continue;
      const s=spans[i];
      const said=t>=w.end, now=t>=w.start&&t<w.end;
      s.className='w'+(said?' said':'')+(now?' now':'');
    }
    caption.style.opacity=String(Math.min(1,Math.max(0,Math.min((t-line.start)/180,(line.end-t)/180))));
  }
}
window.__seek=__seek;
window.__ready=true;
__seek(0);
</script></body></html>`;
}

// ---------------------------------------------------------------------------

function chapterOf(script: Script, scene: Scene): string {
  const beatId = scene.beat_ids[0];
  return script.beats.find((b) => b.beat_id === beatId)?.chapter ?? '';
}

function sceneHtml(p: PreparedScene, index: number, chartIndex: number, vertical: boolean, formatLabel: string): string {
  const s = p.scene;
  const inner = compositionHtml(s, chartIndex, p, vertical, formatLabel);
  return `<section class="scene" data-id="${s.scene_id}" data-i="${index}" data-comp="${s.composition}">${inner}</section>`;
}

function a(anim: string, delay: number, dur = ENTER_MS): string {
  return `data-a="${anim}" data-d="${delay}" data-t="${dur}"`;
}

function compositionHtml(s: Scene, chartIndex: number, p: PreparedScene, vertical: boolean, formatLabel: string): string {
  switch (s.composition) {
    case 'title_card':
      return `<div class="pad">
        <div class="kicker" ${a('rise', 60)}>${escapeHtml(formatLabel)}</div>
        <div class="display" ${a('rise', 200, 760)}>${escapeHtml(s.headline)}</div>
        <div class="rule" style="width:22%;margin-top:calc(var(--u)*3)" ${a('wipe', 620, 760)}></div>
        ${s.subhead ? `<div class="body dimtext" style="margin-top:calc(var(--u)*2.4);max-width:${vertical ? 100 : 70}%" ${a('rise', 760)}>${escapeHtml(s.subhead)}</div>` : ''}
      </div>`;

    case 'chapter_card':
      return `<div class="pad">
        <div class="rule" style="width:${vertical ? 26 : 14}%" ${a('wipe', 40, 520)}></div>
        <div class="h1" style="margin-top:calc(var(--u)*2.4)" ${a('left', 180, 720)}>${escapeHtml(s.headline)}</div>
      </div>`;

    case 'stat_reveal': {
      const raw = s.stat?.value ?? s.headline;
      const num = parseFloat(raw.replace(/[^0-9.]/gu, ''));
      const prefix = raw.match(/^[^0-9.]+/u)?.[0] ?? '';
      const suffix = raw.match(/[^0-9.]+$/u)?.[0] ?? '';
      const dec = (raw.split('.')[1]?.replace(/[^0-9]/gu, '').length) ?? 0;
      // Type scales with the length of the figure so "$4.61bn" and
      // "$5.05 billion" both fill the frame without either one wrapping.
      const unit = vertical ? 17 : 13;
      const size = (unit * Math.min(1, 9 / Math.max(6, raw.length))).toFixed(2);
      const style = `font-size:calc(var(--u)*${size});white-space:nowrap`;
      const counter = Number.isFinite(num)
        ? `<div class="stat" style="${style}" data-count="${num}" data-dec="${dec}" data-pre="${escapeHtml(prefix)}" data-suf="${escapeHtml(suffix)}" data-cd="200" data-ct="1200" ${a('pop', 80, 700)}>${escapeHtml(raw)}</div>`
        : `<div class="stat" style="${style}" ${a('pop', 80, 700)}>${escapeHtml(raw)}</div>`;
      return `<div class="pad">
        <div class="kicker" ${a('rise', 40)}>${escapeHtml(s.subhead || 'Stored claim')}</div>
        ${counter}
        ${s.stat ? `<div class="source" style="margin-top:calc(var(--u)*2.2)" ${a('fade', 900)}>${escapeHtml(s.stat.source_label)} · as of ${escapeHtml(s.stat.as_of_date)} · ${escapeHtml(s.stat.claim_ids.join(', '))}</div>` : ''}
      </div>`;
    }

    case 'line_chart':
    case 'bar_chart':
      return `<div class="pad">
        <div class="kicker" ${a('rise', 40)}>${escapeHtml(s.data?.y_label ?? s.headline)}</div>
        ${s.subhead ? `<div class="h2" style="margin-bottom:calc(var(--u)*1.4)" ${a('rise', 160)}>${escapeHtml(clamp(s.subhead, vertical ? 86 : 112))}</div>` : ''}
        <div class="chartwrap" data-chart="${chartIndex}" data-cdelay="240" ${a('fade', 200, 420)}></div>
      </div>`;

    case 'comparison_table': {
      const [c1, c2] = [s.columns[0] ?? 'Supportive reading', s.columns[1] ?? 'Cautionary reading'];
      const rows = s.rows.length > 0 ? s.rows : [];
      return `<div class="pad">
        <div class="h1" style="margin-bottom:calc(var(--u)*3)" ${a('rise', 40)}>${escapeHtml(s.headline)}</div>
        <div class="cols">
          <div class="col pos card" ${a('rise', 220)}><h4>${escapeHtml(c1)}</h4>${rows.map((r) => `<p>${escapeHtml(r.values[0] ?? r.label)}</p>`).join('')}</div>
          <div class="col neg card" ${a('rise', 380)}><h4>${escapeHtml(c2)}</h4>${rows.map((r) => `<p>${escapeHtml(r.values[1] ?? '')}</p>`).join('')}</div>
        </div>
      </div>`;
    }

    case 'quote_card':
      return `<div class="pad">
        <div class="quote" ${a('rise', 80, 780)}>${escapeHtml(s.headline)}</div>
        ${s.citation ? `<div class="source" style="margin-top:calc(var(--u)*2.6)" ${a('fade', 700)}>${escapeHtml(s.citation)}</div>` : ''}
      </div>`;

    case 'risk_card':
      return `<div class="pad">
        <div class="risk" ${a('left', 60, 700)}>
          <div class="kicker" style="color:var(--neg)">Risk / open question</div>
          <div class="h1">${escapeHtml(s.headline)}</div>
        </div>
      </div>`;

    case 'disclosure':
      return `<div class="pad">
        <div class="disc" ${a('pop', 60, 700)}>
          <div class="kicker">Disclosure</div>
          <div class="h2">${escapeHtml(s.headline)}</div>
        </div>
      </div>`;

    case 'outro':
      return `<div class="pad" style="align-items:center;text-align:center">
        <div class="display" ${a('pop', 60, 780)}>${escapeHtml(s.headline)}</div>
        <div class="rule" style="width:18%;margin-top:calc(var(--u)*3)" ${a('wipe', 520, 700)}></div>
      </div>`;

    case 'broll':
      return `<div class="brollimg" style="${p.brollDataUri ? `background-image:url('${p.brollDataUri}')` : ''}" ${a('fade', 0, 900)}></div>
        <div class="brollveil"></div>
        <div class="pad"><div class="h1" ${a('rise', 260, 760)}>${escapeHtml(s.headline)}</div></div>`;

    case 'statement':
    default:
      return `<div class="pad">
        <div class="h1" style="max-width:${vertical ? 100 : 82}%" ${a('rise', 60, 760)}>${escapeHtml(s.headline)}</div>
        ${s.bullets.length > 0
          ? `<div style="margin-top:calc(var(--u)*2.6)">${s.bullets
              .map((b, i) => `<div class="body" style="margin-bottom:calc(var(--u)*1.2)" ${a('rise', 320 + i * 140)}>— ${escapeHtml(b)}</div>`)
              .join('')}</div>`
          : ''}
      </div>`;
  }
}

/** Headline text that must not wrap past its allotted lines. */
function clamp(s: string, n: number): string {
  return s.length <= n ? s : `${s.slice(0, n - 1).trimEnd()}…`;
}

export function escapeHtml(s: string): string {
  return s
    .replace(/&/gu, '&amp;').replace(/</gu, '&lt;').replace(/>/gu, '&gt;')
    .replace(/"/gu, '&quot;').replace(/'/gu, '&#39;');
}
