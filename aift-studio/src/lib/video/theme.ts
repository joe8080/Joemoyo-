import type { BrandSettings } from '@/lib/domain';

export type Theme = BrandSettings['visual_style'];

/**
 * The stylesheet for every composition.
 *
 * Two decisions worth naming. First, all motion is expressed as inline style
 * written by the seek function rather than CSS keyframes: a frame must be a pure
 * function of time, or a re-render would not be byte-identical. Second, type is
 * sized in `cqw`-style units derived from the canvas width, so the same
 * composition code lays out correctly at 1920×1080 and at 1080×1920.
 */
export function stylesheet(t: Theme, width: number, height: number): string {
  const vertical = height > width;
  const u = width / 100; // 1 unit = 1% of canvas width

  return `
:root{
  --bg:${t.background}; --surface:${t.surface}; --ink:${t.ink}; --dim:${t.ink_dim};
  --accent:${t.accent}; --accent2:${t.accent_2}; --pos:${t.positive}; --neg:${t.negative};
  --display:${t.display_font}; --body:${t.body_font}; --mono:${t.mono_font};
  --u:${u.toFixed(4)}px;
}
*{margin:0;padding:0;box-sizing:border-box;}
html,body{width:${width}px;height:${height}px;overflow:hidden;background:var(--bg);}
body{font-family:var(--body);color:var(--ink);-webkit-font-smoothing:antialiased;text-rendering:geometricPrecision;}
#stage{position:relative;width:${width}px;height:${height}px;overflow:hidden;}

/* Ground: a slow radial wash so flat black never reads as a dead frame. */
#ground{position:absolute;inset:0;
  background:
    radial-gradient(120% 90% at 22% 8%, ${hexA(t.accent, 0.11)} 0%, transparent 58%),
    radial-gradient(110% 80% at 84% 96%, ${hexA(t.accent_2, 0.10)} 0%, transparent 60%),
    var(--bg);}
#vignette{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(78% 68% at 50% 46%, transparent 55%, rgba(0,0,0,.62) 100%);}
#grain{position:absolute;inset:0;pointer-events:none;opacity:${t.grain};mix-blend-mode:overlay;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.82' numOctaves='3'/%3E%3C/filter%3E%3Crect width='220' height='220' filter='url(%23n)'/%3E%3C/svg%3E");}

#layers{position:absolute;inset:0;}
.scene{position:absolute;inset:0;display:none;}
.scene.on{display:block;}
.pad{position:absolute;inset:${vertical ? '14% 8% 20% 8%' : '13% 9% 16% 9%'};display:flex;flex-direction:column;justify-content:center;}
/* Data scenes need the lower third kept clear: captions live there and a chart
   sliding under a caption is the fastest way to make a frame unreadable. */
.scene[data-comp="line_chart"] .pad,.scene[data-comp="bar_chart"] .pad{
  inset:${vertical ? '13% 5% 31% 5%' : '13% 7% 24% 7%'};justify-content:flex-start;}
.scene[data-comp="title_card"] .pad,.scene[data-comp="outro"] .pad{
  inset:${vertical ? '20% 8% 26% 8%' : '15% 9% 20% 9%'};}
.scene[data-comp="comparison_table"] .pad{inset:${vertical ? '13% 6% 28% 6%' : '12% 7% 22% 7%'};}
.scene[data-comp="stat_reveal"] .pad{inset:${vertical ? '18% 8% 30% 8%' : '15% 9% 26% 9%'};}
.scene[data-comp="risk_card"] .pad,.scene[data-comp="statement"] .pad{
  inset:${vertical ? '16% 8% 28% 8%' : '14% 9% 24% 9%'};}
.scene[data-comp="quote_card"] .pad,.scene[data-comp="disclosure"] .pad,
.scene[data-comp="chapter_card"] .pad{inset:${vertical ? '17% 8% 28% 8%' : '15% 10% 25% 10%'};}
/* Captions step down a size on data scenes: there, the number is the subject. */
#caption.small{font-size:calc(var(--u)*${vertical ? 2.9 : 1.5});}
#caption.off{display:none;}

/* --- persistent chrome --- */
#chrome{position:absolute;inset:0;pointer-events:none;}
#mark{position:absolute;top:${vertical ? 4.6 : 5.4}%;left:${vertical ? 8 : 9}%;
  font-size:calc(var(--u)*${vertical ? 1.9 : 1.05});letter-spacing:.34em;color:var(--dim);
  text-transform:uppercase;font-weight:600;display:flex;align-items:center;gap:calc(var(--u)*1.1);}
#mark .dot{width:calc(var(--u)*.85);height:calc(var(--u)*.85);border-radius:50%;background:var(--accent);
  box-shadow:0 0 calc(var(--u)*1.6) var(--accent);}
#refdate{position:absolute;top:${vertical ? 4.6 : 5.4}%;right:${vertical ? 8 : 9}%;
  font-family:var(--mono);font-size:calc(var(--u)*${vertical ? 1.7 : .95});letter-spacing:.16em;color:var(--dim);}
#chapterTag{position:absolute;bottom:${vertical ? 9.6 : 8.2}%;left:${vertical ? 8 : 9}%;
  font-size:calc(var(--u)*${vertical ? 1.7 : .95});letter-spacing:.26em;text-transform:uppercase;color:var(--dim);font-weight:600;}
#cite{position:absolute;bottom:${vertical ? 9.6 : 8.2}%;right:${vertical ? 8 : 9}%;
  font-family:var(--mono);font-size:calc(var(--u)*${vertical ? 1.6 : .92});letter-spacing:.1em;color:var(--dim);
  border:1px solid ${hexA(t.ink_dim, 0.28)};border-radius:999px;padding:calc(var(--u)*.5) calc(var(--u)*1.2);}
#progress{position:absolute;left:0;right:0;bottom:0;height:calc(var(--u)*.34);background:${hexA(t.ink_dim, 0.16)};}
#bar{position:absolute;left:0;top:0;bottom:0;width:0;background:linear-gradient(90deg,var(--accent),var(--accent2));}
#ticks{position:absolute;left:0;right:0;bottom:0;height:calc(var(--u)*.34);}
#ticks i{position:absolute;top:0;bottom:0;width:2px;background:${hexA(t.background, 0.9)};}

/* --- captions --- */
#caption{position:absolute;left:${vertical ? 7 : 16}%;right:${vertical ? 7 : 16}%;
  bottom:${vertical ? 15 : 12.5}%;text-align:center;
  font-size:calc(var(--u)*${vertical ? 3.5 : 1.72});line-height:1.42;font-weight:600;
  text-shadow:0 calc(var(--u)*.25) calc(var(--u)*1.6) rgba(0,0,0,.8);}
#caption .w{color:${hexA(t.ink, 0.5)};transition:none;}
#caption .w.said{color:var(--ink);}
#caption .w.now{color:var(--accent);}

/* --- typography --- */
.kicker{font-size:calc(var(--u)*${vertical ? 1.9 : 1.05});letter-spacing:.32em;text-transform:uppercase;
  color:var(--accent);font-weight:700;margin-bottom:calc(var(--u)*2.2);}
.display{font-family:var(--display);font-weight:700;line-height:1.06;letter-spacing:-.015em;
  font-size:calc(var(--u)*${vertical ? 7.4 : 5.0});}
.h1{font-size:calc(var(--u)*${vertical ? 6.0 : 3.5});font-weight:700;line-height:1.14;letter-spacing:-.01em;}
.h2{font-size:calc(var(--u)*${vertical ? 4.4 : 2.5});font-weight:600;line-height:1.24;}
.body{font-size:calc(var(--u)*${vertical ? 3.4 : 1.85});line-height:1.5;color:${hexA(t.ink, 0.9)};font-weight:450;}
.dimtext{color:var(--dim);}
.rule{height:calc(var(--u)*.42);border-radius:999px;background:linear-gradient(90deg,var(--accent),var(--accent2));}

/* --- panels --- */
.card{background:${hexA(t.surface, 0.86)};border:1px solid ${hexA(t.ink_dim, 0.2)};
  border-radius:calc(var(--u)*1.5);padding:calc(var(--u)*3) calc(var(--u)*3.4);
  backdrop-filter:blur(calc(var(--u)*1.2));}
.stat{font-family:var(--mono);font-weight:800;letter-spacing:-.03em;line-height:.94;
  font-size:calc(var(--u)*${vertical ? 17 : 13});
  background:linear-gradient(180deg,var(--ink) 0%,${hexA(t.accent, 0.92)} 120%);
  -webkit-background-clip:text;background-clip:text;color:transparent;}
.source{font-family:var(--mono);font-size:calc(var(--u)*${vertical ? 1.6 : .92});letter-spacing:.08em;color:var(--dim);}
/* The chart is fitted by the box, not by its intrinsic size. Letting the SVG
   viewBox scale to meet inside a flex child is what keeps the source stamp
   clear of the captions at both aspect ratios, with no per-format height. */
.chartwrap{width:100%;flex:1 1 auto;min-height:0;display:flex;align-items:center;justify-content:center;}
.chartwrap svg{width:100%;height:100%;max-height:100%;}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:calc(var(--u)*2.4);}
.col h4{font-size:calc(var(--u)*${vertical ? 2.3 : 1.25});letter-spacing:.2em;text-transform:uppercase;
  color:var(--dim);margin-bottom:calc(var(--u)*1.4);font-weight:700;}
.col.pos h4{color:var(--pos);} .col.neg h4{color:var(--neg);}
.col{display:flex;flex-direction:column;}
.col p{font-size:calc(var(--u)*${vertical ? 2.7 : 1.42});line-height:1.46;margin-bottom:calc(var(--u)*1.1);
  padding-bottom:calc(var(--u)*1.1);border-bottom:1px solid ${hexA(t.ink_dim, 0.14)};}
.col p:last-child{margin-bottom:0;padding-bottom:0;border-bottom:none;}
.risk{border-left:calc(var(--u)*.6) solid var(--neg);padding-left:calc(var(--u)*2.4);}
.quote{font-family:var(--display);font-style:italic;font-size:calc(var(--u)*${vertical ? 5.2 : 3.0});line-height:1.28;}
.quote:before{content:'\\201C';display:block;font-size:calc(var(--u)*${vertical ? 12 : 8});color:var(--accent);
  line-height:.6;margin-bottom:calc(var(--u)*1.2);}
.disc{border:1px solid ${hexA(t.accent, 0.45)};border-radius:calc(var(--u)*1.4);
  padding:calc(var(--u)*3.2);background:${hexA(t.accent, 0.07)};}
.brollimg{position:absolute;inset:0;background-size:cover;background-position:center;}
.brollveil{position:absolute;inset:0;background:linear-gradient(180deg,${hexA(t.background, 0.35)},${hexA(t.background, 0.86)});}
`;
}

function hexA(hex: string, alpha: number): string {
  const h = hex.replace('#', '');
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

export { hexA };
