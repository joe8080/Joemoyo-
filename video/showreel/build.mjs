/**
 * Emits index.html for the JoeMoyo showreel.
 *
 * Everything that defines the film lives in SHOTS and CARDS below — edit those
 * and re-run `node build.mjs` rather than hand-editing index.html.
 */
import { writeFileSync } from "node:fs";

const W = 1920;
const H = 1080;
const DURATION = 240;
const FADE = 0.9; // crossfade length; shots overlap by exactly this much

const GOLD = "#C9A84C";
const DARK = "#1A1A2E";
const WHITE = "#FFFFFF";

/**
 * Ken Burns moves. Each shot names one. Directions alternate across cuts so the
 * film reads as one continuous camera move (motion-doctrine: how you exit
 * determines how you enter) rather than a stack of independent pushes.
 */
const MOVES = {
  pushIn: { from: { scale: 1.04, xPercent: 0, yPercent: 0 }, to: { scale: 1.2, xPercent: 0, yPercent: 0 } },
  pullOut: { from: { scale: 1.2, xPercent: 0, yPercent: 0 }, to: { scale: 1.04, xPercent: 0, yPercent: 0 } },
  driftLeft: { from: { scale: 1.14, xPercent: 2.5, yPercent: 0 }, to: { scale: 1.14, xPercent: -2.5, yPercent: 0 } },
  driftRight: { from: { scale: 1.14, xPercent: -2.5, yPercent: 0 }, to: { scale: 1.14, xPercent: 2.5, yPercent: 0 } },
  riseIn: { from: { scale: 1.06, xPercent: 0, yPercent: 2 }, to: { scale: 1.18, xPercent: 0, yPercent: -2 } },
  sinkOut: { from: { scale: 1.18, xPercent: 0, yPercent: -2 }, to: { scale: 1.06, xPercent: 0, yPercent: 2 } },
};

// [id, image key, start, end, move]
const SHOTS = [
  // Act 0 — cold open
  ["s01", "open-goldleaf", 0, 9.5, "pushIn"],
  ["s02", "close-converge", 8.6, 18.0, "pullOut"],

  // Act 1 — OrigineX Human Archives
  ["s03", "hist-monolith", 17.1, 26.0, "riseIn"],
  ["s04", "hist-relief-a", 25.1, 34.0, "driftLeft"],
  ["s05", "hist-papyrus", 33.1, 42.0, "pushIn"],
  ["s06", "hist-mask", 41.1, 51.0, "sinkOut"],
  ["s07", "hist-colonnade", 50.1, 59.0, "driftRight"],
  ["s08", "hist-relief-b", 58.1, 68.0, "pullOut"],

  // Act 2 — Finance channel + AI toolkit
  ["s09", "fin-chart-a", 67.1, 77.0, "riseIn"],
  ["s10", "fin-skyline", 76.1, 86.0, "driftLeft"],
  ["s11", "fin-ribbons-a", 85.1, 95.0, "pushIn"],
  ["s12", "fin-chart-b", 94.1, 105.0, "sinkOut"],
  ["s13", "fin-ribbons-b", 104.1, 115.0, "driftRight"],

  // Act 3 — music studio
  ["s14", "mus-console-a", 114.1, 123.0, "driftLeft"],
  ["s15", "mus-mic-a", 122.1, 131.0, "pushIn"],
  ["s16", "mus-wave-a", 130.1, 139.0, "pullOut"],
  ["s17", "mus-console-b", 138.1, 147.0, "driftRight"],
  ["s18", "mus-mic-b", 146.1, 155.0, "riseIn"],

  // Act 4 — commerce
  ["s19", "com-box-a", 154.1, 166.0, "pushIn"],
  ["s20", "com-warehouse", 165.1, 178.0, "driftLeft"],
  ["s21", "com-box-b", 177.1, 190.0, "sinkOut"],

  // Act 5 — agent systems
  ["s22", "sys-server", 189.1, 201.0, "pushIn"],
  ["s23", "sys-nodes", 200.1, 212.0, "driftRight"],
  ["s24", "fin-ribbons-b", 211.1, 222.0, "pullOut"],

  // Act 6 — close
  ["s25", "close-converge", 221.1, 232.0, "pushIn"],
  ["s26", "open-goldleaf", 231.1, 240.0, "pullOut"],
];

// [id, kind, start, end, label, hook, sub]
const CARDS = [
  ["c0", "opening", 2.0, 16.0, "PORTFOLIO · 2026", "JOEMOYO", "Media · Markets · Machines"],
  ["c1", "act", 21.0, 34.5, "ORIGINEX HUMAN ARCHIVES", "History, Restored", "Long-form documentary · YouTube"],
  ["c2", "act", 71.0, 84.5, "FINANCE CHANNEL &amp; AI TOOLKIT", "Money, Explained", "Education · Research · Tools"],
  ["c3", "act", 118.0, 131.5, "MUSIC STUDIO", "Sound, Built", "Recording · Production"],
  ["c4", "act", 158.0, 171.5, "COMMERCE", "Product, Shipped", "Shopify · Retail operations"],
  ["c5", "act", 193.0, 206.5, "AGENT SYSTEMS", "Work, Automated", "AI agents · Algorithmic trading"],
  ["c6", "closing", 225.0, 239.0, "FIVE VENTURES · ONE OPERATOR", "JOEMOYO", ""],
];

const shotMarkup = SHOTS.map(([id, key, start, end], i) => {
  const track = (i % 2) + 1; // alternate so neighbours can crossfade
  return `      <section id="${id}" class="clip shot" data-start="${start}" data-duration="${round(end - start)}" data-track-index="${track}">
        <div class="shot-fade" id="${id}-fade">
          <div class="plate" id="${id}-plate" style="background-image: url('assets/images/${key}.png')"></div>
        </div>
      </section>`;
}).join("\n");

const cardMarkup = CARDS.map(([id, kind, start, end, label, hook, sub]) => {
  const subLine = sub ? `\n          <p class="card-sub" id="${id}-sub">${sub}</p>` : "";
  return `      <section id="${id}" class="clip card card--${kind}" data-start="${start}" data-duration="${round(end - start)}" data-track-index="5">
        <div class="card-scrim" id="${id}-scrim"></div>
        <div class="card-inner">
          <p class="card-label" id="${id}-label">${label}</p>
          <h2 class="card-hook" id="${id}-hook">${hook}</h2>
          <span class="card-rule" id="${id}-rule"></span>${subLine}
        </div>
      </section>`;
}).join("\n");

const shotTweens = SHOTS.map(([id, , start, end, move]) => {
  const m = MOVES[move];
  const len = round(end - start);
  const lines = [
    `  tl.fromTo("#${id}-plate", ${json(m.from)}, { ...${json(m.to)}, duration: ${len}, ease: "none" }, ${start});`,
    `  tl.fromTo("#${id}-fade", { opacity: 0 }, { opacity: 1, duration: ${FADE}, ease: "power2.inOut" }, ${start});`,
  ];
  // The last shot holds to black; every other shot hands off to its successor.
  const fadeOutAt = round(end - FADE);
  lines.push(`  tl.to("#${id}-fade", { opacity: 0, duration: ${FADE}, ease: "power2.inOut" }, ${fadeOutAt});`);
  return lines.join("\n");
}).join("\n");

const cardTweens = CARDS.map(([id, kind, start, end, , , sub]) => {
  const len = round(end - start);
  const out = round(start + len - 1.1);
  const lines = [
    `  tl.fromTo("#${id}-scrim", { opacity: 0 }, { opacity: 1, duration: 0.9, ease: "power2.out" }, ${start});`,
    `  tl.fromTo("#${id}-label", { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: 0.7, ease: "power3.out" }, ${start});`,
    `  tl.fromTo("#${id}-hook", { opacity: 0, y: 34 }, { opacity: 1, y: 0, duration: 0.9, ease: "power3.out" }, ${round(start + 0.18)});`,
    `  tl.fromTo("#${id}-rule", { scaleX: 0 }, { scaleX: 1, duration: 0.8, ease: "power3.inOut" }, ${round(start + 0.42)});`,
  ];
  if (sub) {
    lines.push(`  tl.fromTo("#${id}-sub", { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.7, ease: "power3.out" }, ${round(start + 0.6)});`);
  }
  const outTargets = sub ? `"#${id}-label", "#${id}-hook", "#${id}-rule", "#${id}-sub"` : `"#${id}-label", "#${id}-hook", "#${id}-rule"`;
  lines.push(`  tl.to([${outTargets}], { opacity: 0, y: -12, duration: 0.8, ease: "power2.in" }, ${out});`);
  lines.push(`  tl.to("#${id}-scrim", { opacity: 0, duration: 0.9, ease: "power2.in" }, ${out});`);
  return lines.join("\n");
}).join("\n");

function round(n) {
  return Math.round(n * 1000) / 1000;
}
function json(o) {
  return JSON.stringify(o);
}

const html = `<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=${W}, height=${H}" />
    <title>JoeMoyo — Portfolio Showreel</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <style>
      @font-face {
        font-family: "Archivo Black";
        src: url("assets/fonts/archivo-black-latin-400-normal.woff2") format("woff2");
        font-weight: 400;
        font-display: block;
      }
      @font-face {
        font-family: "Inter";
        src: url("assets/fonts/inter-latin-400-normal.woff2") format("woff2");
        font-weight: 400;
        font-display: block;
      }
      @font-face {
        font-family: "Inter";
        src: url("assets/fonts/inter-latin-600-normal.woff2") format("woff2");
        font-weight: 600;
        font-display: block;
      }
      @font-face {
        font-family: "Inter";
        src: url("assets/fonts/inter-latin-700-normal.woff2") format("woff2");
        font-weight: 700;
        font-display: block;
      }

      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: ${W}px; height: ${H}px; overflow: hidden; background: #000; }
      body { font-family: "Inter", sans-serif; }

      #root { position: relative; width: ${W}px; height: ${H}px; overflow: hidden; }

      /* Opaque stage ground. Lives on a full-bleed child, never on #root itself —
         the producer can drop the root's own background and render black. */
      #stage-ground {
        position: absolute;
        inset: 0;
        background: ${DARK};
      }

      .shot { position: absolute; inset: 0; overflow: hidden; }
      .shot-fade { position: absolute; inset: 0; will-change: opacity; }
      .plate {
        position: absolute;
        inset: 0;
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        transform-origin: center center;
        will-change: transform;
      }

      /* Grade: crush toward the brand near-black and keep type legible over any plate. */
      #grade {
        position: absolute;
        inset: 0;
        background:
          radial-gradient(ellipse 78% 68% at 50% 46%, rgba(0,0,0,0) 0%, rgba(0,0,0,0.42) 72%, rgba(0,0,0,0.78) 100%),
          linear-gradient(180deg, rgba(26,26,46,0.30) 0%, rgba(26,26,46,0.06) 34%, rgba(26,26,46,0.42) 100%);
      }

      .card { position: absolute; inset: 0; display: grid; }

      /* Guarantees the gold label clears contrast over any plate, however bright.
         Fades with the card copy so it never pops at a clip boundary. */
      .card-scrim { position: absolute; inset: 0; will-change: opacity; }
      .card--act .card-scrim {
        background: linear-gradient(0deg, rgba(10,10,20,0.92) 0%, rgba(10,10,20,0.72) 22%, rgba(10,10,20,0.28) 44%, rgba(10,10,20,0) 62%);
      }
      .card--opening .card-scrim,
      .card--closing .card-scrim {
        background: radial-gradient(ellipse 62% 46% at 50% 50%, rgba(10,10,20,0.88) 0%, rgba(10,10,20,0.66) 46%, rgba(10,10,20,0) 78%);
      }
      .card-inner { align-self: end; justify-self: start; padding: 0 0 120px 132px; max-width: 1280px; }
      .card--opening .card-inner,
      .card--closing .card-inner { align-self: center; justify-self: center; text-align: center; padding: 0 132px; }

      .card-label {
        font-family: "Inter", sans-serif;
        font-weight: 600;
        font-size: 26px;
        letter-spacing: 0.34em;
        text-transform: uppercase;
        color: ${GOLD};
        margin-bottom: 22px;
        will-change: transform, opacity;
      }
      .card-hook {
        font-family: "Archivo Black", "Inter", sans-serif;
        font-weight: 400;
        font-size: 116px;
        line-height: 1.0;
        letter-spacing: -0.02em;
        color: ${WHITE};
        text-shadow: 0 6px 48px rgba(0,0,0,0.75);
        will-change: transform, opacity;
      }
      .card--opening .card-hook,
      .card--closing .card-hook { font-size: 168px; letter-spacing: 0.02em; }

      .card-rule {
        display: block;
        width: 232px;
        height: 3px;
        background: ${GOLD};
        margin: 34px 0 0;
        transform-origin: left center;
        will-change: transform;
      }
      .card--opening .card-rule,
      .card--closing .card-rule { margin: 34px auto 0; transform-origin: center center; }

      .card-sub {
        font-family: "Inter", sans-serif;
        font-weight: 400;
        font-size: 30px;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: rgba(255,255,255,0.74);
        margin-top: 30px;
        will-change: transform, opacity;
      }
    </style>
  </head>
  <body>
    <div
      id="root"
      data-composition-id="main"
      data-start="0"
      data-duration="${DURATION}"
      data-width="${W}"
      data-height="${H}"
    >
      <section id="ground" class="clip" data-start="0" data-duration="${DURATION}" data-track-index="0">
        <div id="stage-ground"></div>
      </section>

${shotMarkup}

      <section id="grade-clip" class="clip" data-start="0" data-duration="${DURATION}" data-track-index="4">
        <div id="grade"></div>
      </section>

${cardMarkup}
    </div>

    <script>
      window.__timelines = window.__timelines || {};
      const tl = gsap.timeline({ paused: true });

${shotTweens}

${cardTweens}

      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
`;

writeFileSync(new URL("./index.html", import.meta.url), html);
console.log(`index.html written — ${SHOTS.length} shots, ${CARDS.length} cards, ${DURATION}s`);
