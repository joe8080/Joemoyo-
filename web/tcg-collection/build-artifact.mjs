/**
 * Assembles the shareable single-file build from the tested source files.
 *
 *   node build-artifact.mjs
 *
 * Inlines styles.css and app.js and bakes data/cards.json in as a constant, so
 * the page needs no fetch and no network — required by the Artifact CSP, and it
 * also means the published board shows YOUR cards to everyone you send it to
 * (localStorage is per-viewer, so anything not baked in is invisible to them).
 *
 * Re-run this and republish whenever you change data/cards.json.
 */
import { readFileSync, writeFileSync } from "node:fs";

const html = readFileSync("index.html", "utf8");
const css = readFileSync("assets/styles.css", "utf8");
const js = readFileSync("assets/app.js", "utf8");
const data = JSON.parse(readFileSync("data/cards.json", "utf8"));

// Drop the template row so a fresh board opens on the empty state.
data.cards = (data.cards || []).filter((c) => !/^EXAMPLE/i.test(c.name || ""));

// Body content only — the host wraps this in doctype/head/body at publish time.
const body = html
  .slice(html.indexOf("<body>") + 6, html.lastIndexOf("</body>"))
  .replace(/\s*<script src="assets\/app\.js"><\/script>/, "")
  .trim();

// Serve the baked data instead of fetching a file that will not exist.
const patched = js.replace(
  /const r = await fetch\("data\/cards\.json", \{ cache: "no-store" \}\);\s*if \(r\.ok\) file = await r\.json\(\);/,
  "file = window.__CARDS__ || file;",
);
if (patched === js) throw new Error("fetch shim did not apply — app.js changed; update the replace target");

const out = `<title>Trick or Trade 2024 — Collection Board</title>
<style>
/* The board commits to a single dark visual world on purpose: the holographic
   card treatment is a specular effect that only reads against a dark ground.
   Declared rather than omitted. */
:root { color-scheme: dark; }
${css}
</style>

${body}

<script>
window.__CARDS__ = ${JSON.stringify(data)};
</script>
<script>
${patched}
</script>
`;

writeFileSync("artifact.html", out);
console.log(`artifact.html — ${(out.length / 1024).toFixed(1)} KB, ${data.cards.length} cards baked in`);
