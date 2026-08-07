// Generates index.html for the OGX "Chilling Receipts" build.
//
// Timings live in SCENES below. When the narration VO lands, retime the film by
// editing `hold` values here and re-running `node build-composition.mjs` — the
// seam maths, track assignment and GSAP timeline all recompute from them.

import { existsSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const W = 1920;
const H = 1080;

// Seam overlap: outgoing and incoming scenes share this window so the cut lands
// mid-motion on both sides (motion-doctrine, the Vector Law).
const SEAM = 0.6;

// Partial travel — cut-the-curve puts the velocity-matched hand-off at ~12% of frame.
const TRAVEL = Math.round(W * 0.12);

// The film's current. House default is LEFT: every ordinary seam runs -x.
// Reserved vectors are declared per scene via `vector`.
// Paths are root-relative to the project — compositions are served with the
// project root as base URL, so "../" traversal 404s in preview. assets/cards
// and assets/broll are symlinks out to the video's shared asset folders.
const CARD = (n) => `assets/cards/s${String(n).padStart(2, "0")}_generated.webp`;
const BROLL = (name) => `assets/broll/${name}.mp4`;

const SCENES = [
  { id: "s01", kind: "card", src: CARD(1), hold: 7, push: 1.06, label: "Title — Chilling Receipts" },
  { id: "s02", kind: "card", src: CARD(2), hold: 6, push: 1.05, label: "The Unbreakable Rule — 39 citations" },
  { id: "b01", kind: "broll", src: BROLL("01_stasi_corridor"), hold: 4, label: "B-roll — Stasi filing corridor" },
  { id: "s03", kind: "card", src: CARD(3), hold: 13, push: 1.07, label: "The Stasi — Europe", correction: "stasi" },
  { id: "s04", kind: "card", src: CARD(4), hold: 10, push: 1.05, label: "The 1991 Reckoning" },
  { id: "b02", kind: "broll", src: BROLL("02_birch_forest"), hold: 4, label: "B-roll — birch forest (Katyn)" },
  { id: "s05", kind: "card", src: CARD(5), hold: 14, push: 1.06, label: "Katyn — the 50-year lie" },
  { id: "s06", kind: "card", src: CARD(6), hold: 12, push: 1.05, label: "Nazi criminals, Western payroll" },
  { id: "b03", kind: "broll", src: BROLL("03_weapons_cache"), hold: 4, label: "B-roll — buried weapons cache" },
  { id: "s07", kind: "card", src: CARD(7), hold: 12, push: 1.06, label: "Operation Gladio" },
  { id: "b04", kind: "broll", src: BROLL("04_radar_scope"), hold: 4, label: "B-roll — naval radar scope" },
  { id: "s08", kind: "card", src: CARD(8), hold: 12, push: 1.05, label: "Gulf of Tonkin — Asia" },
  { id: "b05", kind: "broll", src: BROLL("05_oil_derrick"), hold: 4, label: "B-roll — oil derrick at dusk" },
  { id: "s09", kind: "card", src: CARD(9), hold: 12, push: 1.06, label: "Iran 1953 — Operation TPAJAX" },
  { id: "s10", kind: "card", src: CARD(10), hold: 13, push: 1.05, label: "The Americas — regime change blueprint" },
  { id: "s11", kind: "card", src: CARD(11), hold: 12, push: 1.06, label: "The Barr Doctrine" },
  { id: "s12", kind: "card", src: CARD(12), hold: 11, push: 1.05, label: "CIA Family Jewels" },
  { id: "s13", kind: "card", src: CARD(13), hold: 13, push: 1.06, label: "MLK & COINTELPRO" },
  // Reserved vector: Z forward — pushing deeper into the same thought.
  { id: "s14", kind: "card", src: CARD(14), hold: 16, push: 1.08, vector: "z-in", label: "The Synthesis" },
  { id: "b06", kind: "broll", src: BROLL("06_server_vault"), hold: 4, label: "B-roll — server vault" },
  // Reserved vector: Z backward — ARRIVAL, something bigger lands.
  { id: "s15", kind: "card", src: CARD(15), hold: 11, push: 1.04, vector: "z-out", label: "The Digital Vault — closing" },
];

// ------------------------------------------------------- b-roll availability
//
// The Highfield motion plates are downloaded separately (see MANIFEST.md — the
// render CDN is not reachable from every environment). A b-roll scene is only
// composited when its file is actually on disk, so the film builds and renders
// either way; drop the MP4s into video/broll/ and re-run to fold them in.

const present = (s) =>
  s.kind !== "broll" || existsSync(fileURLToPath(new URL(s.src, import.meta.url)));

const missing = SCENES.filter((s) => !present(s));
const ACTIVE = SCENES.filter(present);

// ---------------------------------------------------------------- layout pass

let cursor = 0;
const timed = ACTIVE.map((s, i) => {
  const start = cursor;
  // Every scene but the last runs SEAM seconds long so it overlaps its successor.
  const isLast = i === ACTIVE.length - 1;
  const duration = s.hold + (isLast ? 0 : SEAM);
  cursor += s.hold;
  return {
    ...s,
    start: +start.toFixed(3),
    duration: +duration.toFixed(3),
    // Alternate tracks so consecutive scenes can overlap without same-track collision.
    track: (i % 2) + 1,
    isLast,
    isFirst: i === 0,
  };
});

const TOTAL = +cursor.toFixed(3);

// ------------------------------------------------------------------ html pass

const scenesHtml = timed
  .map((s) => {
    const inner =
      s.kind === "broll"
        ? `            <video id="${s.id}-media" class="plate" src="${s.src}" muted playsinline></video>`
        : `            <img id="${s.id}-media" class="plate" src="${s.src}" alt="" />`;

    // The correction sits INSIDE the push wrapper so it scales and travels with
    // the card underneath it, instead of drifting off its target as the frame moves.
    const correction =
      s.correction === "stasi"
        ? `
            <div id="${s.id}-fix" class="stat-fix">
              <div class="stat-fix-line">CITIZENS WAS AN INFORMANT</div>
              <div class="stat-fix-line">OR COLLABORATOR</div>
            </div>`
        : "";

    return `      <section
        id="${s.id}"
        class="clip scene"
        data-start="${s.start}"
        data-duration="${s.duration}"
        data-track-index="${s.track}"
        data-label="${s.label}"
      >
        <div id="${s.id}-frame" class="frame">
          <div id="${s.id}-kb" class="push" data-layout-allow-overflow>
${inner}${correction}
          </div>
        </div>
      </section>`;
  })
  .join("\n");

// ------------------------------------------------------------- timeline pass
//
// Each scene: a slow push held across the hold, then a velocity-matched exit.
// Exit uses power4.in and the next entry uses power4.out over the same distance
// and duration, so the cut lands mid-motion on both sides with matched speed.

const tweens = timed
  .map((s, i) => {
    const prev = i > 0 ? timed[i - 1] : null;
    const lines = [];
    const frame = `#${s.id}-frame`;
    const media = `#${s.id}-kb`;

    // --- entry -------------------------------------------------------------
    if (s.isFirst) {
      lines.push(
        `  tl.fromTo("${frame}", { opacity: 0 }, { opacity: 1, duration: 0.9, ease: "power2.out" }, ${s.start});`
      );
    } else if (s.vector === "z-in") {
      // Answering a Z-forward exit: keep growing. Same axis, same sign.
      lines.push(
        `  tl.fromTo("${frame}", { scale: 1.14, opacity: 0 }, { scale: 1, opacity: 1, duration: ${SEAM}, ease: "power4.out" }, ${s.start});`
      );
    } else if (s.vector === "z-out") {
      // ARRIVAL — camera pulls back, something bigger lands.
      lines.push(
        `  tl.fromTo("${frame}", { scale: 0.9, opacity: 0 }, { scale: 1, opacity: 1, duration: ${SEAM}, ease: "power4.out" }, ${s.start});`
      );
    } else {
      // The current: enter from the right, already travelling left.
      lines.push(
        `  tl.fromTo("${frame}", { x: ${TRAVEL}, opacity: 0 }, { x: 0, opacity: 1, duration: ${SEAM}, ease: "power4.out" }, ${s.start});`
      );
    }

    // --- the hold: a slow push, so the frame is never at rest --------------
    const pushTo = s.kind === "broll" ? 1.04 : s.push;
    lines.push(
      `  tl.fromTo("${media}", { scale: 1 }, { scale: ${pushTo}, duration: ${s.hold}, ease: "none" }, ${s.start});`
    );

    // --- exit --------------------------------------------------------------
    if (!s.isLast) {
      const next = timed[i + 1];
      const exitAt = +(s.start + s.hold).toFixed(3);
      if (next.vector === "z-in") {
        lines.push(
          `  tl.to("${frame}", { scale: 1.14, opacity: 0, duration: ${SEAM}, ease: "power4.in" }, ${exitAt});`
        );
      } else if (next.vector === "z-out") {
        lines.push(
          `  tl.to("${frame}", { scale: 0.9, opacity: 0, duration: ${SEAM}, ease: "power4.in" }, ${exitAt});`
        );
      } else {
        lines.push(
          `  tl.to("${frame}", { x: ${-TRAVEL}, opacity: 0, duration: ${SEAM}, ease: "power4.in" }, ${exitAt});`
        );
      }
    }

    // The corrected Stasi label rides its card exactly — no independent motion.
    return `  // ${s.label}\n${lines.join("\n")}`;
  })
  .join("\n\n");

// ------------------------------------------------------------------- emit

const html = `<!doctype html>
<html lang="en" data-resolution="landscape">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=${W}, height=${H}" />
    <title>OGX — Chilling Receipts of Declassified Global Statecraft</title>
    <script src="vendor/gsap.min.js"></script>
    <style>
      * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }
      html,
      body {
        width: ${W}px;
        height: ${H}px;
        overflow: hidden;
        background: #000;
        /* Inter is what the renderer substitutes for system sans anyway —
           naming it directly keeps preview and render identical. */
        font-family: Inter, sans-serif;
      }
      /* Opaque stage ground — guards against the white flash at crossfade seams
         (seam-craft). Full-bleed child, never the composition root itself. */
      #stage {
        position: absolute;
        inset: 0;
        background: #0a0a0a;
      }
      .scene {
        position: absolute;
        inset: 0;
        overflow: hidden;
      }
      /* Every scene frame starts hidden. A full-frame overlay that starts
         visible covers all earlier frames in the render, even though preview
         looks correct — each scene's entry tween is what reveals it. */
      .frame {
        position: absolute;
        inset: 0;
        overflow: hidden;
        opacity: 0;
        background: #0a0a0a;
      }
      /* The slow push rides this wrapper, so anything composited on the card
         (e.g. the corrected statistic) scales and travels with it. */
      .push {
        position: absolute;
        inset: 0;
        width: ${W}px;
        height: ${H}px;
        transform-origin: 50% 50%;
      }
      .plate {
        position: absolute;
        inset: 0;
        width: ${W}px;
        height: ${H}px;
        object-fit: cover;
      }
      /* Correction plate over the Stasi card's bottom-left statistic label.
         The original read "CITIZENS WAS A FULL-TIME STASI OFFICER", which is
         wrong: ~91,000 full-time officers against ~16.4M population is roughly
         1 in 180. The 1-in-63 figure is Koehler's ratio for informants and
         collaborators, which is what this label now says. */
      .stat-fix {
        position: absolute;
        left: 11%;
        top: 81%;
        width: 40%;
        height: 15%;
        /* Feathered rather than a flat rectangle — a hard-edged fill reads as a
           patch against the archival folder art at the card's left edge. The
           opaque core still fully covers the original label. */
        background: radial-gradient(
          ellipse at center,
          #060707 0%,
          #060707 82%,
          rgba(6, 7, 7, 0) 100%
        );
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 4px;
      }
      .stat-fix-line {
        color: #f2ede4;
        font-size: 23px;
        font-weight: 700;
        letter-spacing: 1.1px;
        text-align: center;
        line-height: 1.15;
      }
    </style>
  </head>
  <body>
    <div
      id="root"
      data-composition-id="main"
      data-start="0"
      data-duration="${TOTAL}"
      data-width="${W}"
      data-height="${H}"
    >
      <div id="stage"></div>

${scenesHtml}
    </div>

    <script>
      window.__timelines = window.__timelines || {};
      const tl = gsap.timeline({ paused: true });

${tweens}

      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
`;

writeFileSync(new URL("./index.html", import.meta.url), html);

const mins = Math.floor(TOTAL / 60);
const secs = String(Math.round(TOTAL % 60)).padStart(2, "0");
console.log(`wrote index.html — ${timed.length} scenes, ${TOTAL}s (${mins}:${secs})`);
if (missing.length) {
  console.log(
    `  ${missing.length} b-roll plate(s) not on disk, omitted: ${missing.map((s) => s.id).join(", ")}`
  );
  console.log("  drop the MP4s listed in MANIFEST.md into video/broll/ and re-run to fold them in");
}
