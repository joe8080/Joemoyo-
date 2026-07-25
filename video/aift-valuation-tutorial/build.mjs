/**
 * Emits index.html for the AIFT Own-Price Valuation Engine tutorial.
 *
 *   node build-audio.mjs   # first — produces timing.json + final-mix.wav
 *   node build.mjs         # then — generates index.html against those timings
 *
 * SCENES below is the source of truth. Every number in it is traceable to a
 * cell in AIFT_Own_Price_Valuation_Engine.xlsx — see SCRIPT.md's trace table.
 */
import { readFileSync, writeFileSync } from "node:fs";

const timing = JSON.parse(readFileSync("timing.json", "utf8"));
const W = 1920;
const H = 1080;
const DURATION = Math.ceil(timing.total);

const C = {
  bg: "#070B14",
  panel: "#0E1626",
  panelEdge: "#1B2740",
  grid: "#16203a",
  gold: "#C9A84C",
  cyan: "#38BDF8",
  red: "#F0553F",
  green: "#4ADE80",
  text: "#E8EDF5",
  dim: "#8A9AB5",
};

/* ── scene table ───────────────────────────────────────────────────────────
   [start, end, type, payload]  — times are absolute seconds, matched to the
   voiceover in timing.json.                                                */
const SCENES = [
  [0, 5.0, "title", { kicker: "AI FINANCE TOOLKIT", title: "Build Your Own Price", sub: "The Own-Price Valuation Engine" }],

  [5.0, 22.5, "verdict", { own: "$2.09", mkt: "$1.25", up: "+67%", label: "OWN PRICE vs MARKET" }],
  [22.5, 38.0, "statement", { big: "Build it. Break it. Fix it.", sub: "How much of that 67% survives?" }],
  [38.0, 50.0, "title", { kicker: "CHAPTER 1", title: "What the engine does", sub: "Three estimates, weighted, then haircut" }],
  [50.0, 88.6, "flow", {}],

  [88.6, 132.0, "legs", { nav: "$1.25", peer: "$3.17", analyst: "$3.75", note: "Three reasonable methods. Wildly different answers." }],
  [132.0, 160.0, "sheet", {
    tab: "Inputs", title: "A · COMPANY & MARKET",
    rows: [["Share price ($)", "$1.25", "in"], ["Shares — basic (M)", "194.216", "in"], ["Cash & equivalents ($M)", "41.6", "in"],
           ["Marketable securities ($M)", "70.1", "in"], ["Debt — face value ($M)", "115.0", "in"], ["Net cash / (debt) ($M)", "(3.3)", "calc"]],
    formula: "B16  =B13+B14−B15", reveal: true }],
  [160.0, 191.7, "bug", { stage: "spot" }],

  [191.7, 232.0, "bug", { stage: "cascade" }],
  [232.0, 246.0, "bug", { stage: "fix" }],
  [246.0, 281.7, "sheet", {
    tab: "Inputs", title: "B · CAP-SIZE ENGINE",
    rows: [["Micro", "< $300M", "row"], ["Small", "$300M – $2B", "row"], ["Mid", "$2B – $10B", "row"], ["Large", "> $10B", "row"],
           ["SELECTED bucket", "Micro", "hl"], ["Size premium", "4.5%", "calc"]],
    formula: "B22  =INDEX($F$28:$F$31, MATCH($B$21,$E$28:$E$31,0))" }],

  [281.7, 322.0, "sheet", {
    tab: "Inputs", title: "LIQUIDITY DISCOUNT",
    rows: [["Micro-cap default", "25.0%", "row"], ["Override (optional)", "10.0%", "in"], ["Discount USED", "10.0%", "hl"]],
    formula: "B25  =IF(ISNUMBER(B24), B24, B23)",
    note: "enCore trades on NASDAQ daily. A private-company haircut would be wrong." }],
  [322.0, 363.7, "build", {
    title: "C · DISCOUNT RATE BUILD",
    steps: [["Risk-free rate (US 10Y)", "4.55%"], ["Equity risk premium", "5.00%"], ["Beta", "1.30"], ["Base cost of equity", "11.05%"]] }],

  [363.7, 400.0, "bignum", { value: "15.55%", label: "DISCOUNT RATE USED", sub: "11.05% base + 4.50% size premium", cell: "Inputs!B40" }],
  [400.0, 440.0, "dcf", { highlight: null }],
  [440.0, 461.6, "dcf", { highlight: "fcf" }],

  [461.6, 495.0, "bignum", { value: "−$53.5M", label: "SUM OF PV OF FREE CASH FLOW", sub: "Five years of operations, discounted", cell: "DCF!B25", tone: "red" }],
  [495.0, 520.0, "statement", { big: "All of it is terminal value.", sub: "You're not buying five years of cash flow." }],
  [520.0, 559.2, "compare", {
    title: "TERMINAL VALUE — TWO METHODS",
    left: { name: "Gordon growth", value: "$350.0M", sub: "Normalised FCF, grown at 2% forever", cell: "DCF!B21" },
    right: { name: "Exit multiple", value: "$618.0M", sub: "$12/lb × 51.5M lbs of resource", cell: "DCF!B22" },
    delta: "76% higher — one dropdown apart" }],

  [559.2, 592.0, "statement", { big: "One dropdown.", sub: "That gap is a method choice, not a fact about the business." }],
  [592.0, 630.0, "peers", {}],
  [630.0, 654.6, "trap", { stage: "reveal" }],

  [654.6, 684.0, "trap", { stage: "explain" }],
  [684.0, 720.0, "blend", {}],
  [720.0, 735.9, "statement", { big: "On your assumptions.", sub: "The model never claims to know. It shows you what you assumed." }],

  [735.9, 768.0, "assumptions", {}],
  [768.0, 800.0, "sensitivity", {}],
  [800.0, 827.2, "versionlog", {}],

  [827.2, 850.0, "actions", {}],
  [850.0, DURATION, "outro", { title: "Build your own price.", sub: "AI Finance Toolkit · Own-Price Valuation Engine" }],
];

/* ── renderers ─────────────────────────────────────────────────────────── */
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
const R = {};

R.title = (id, p) => `
  <div class="stack center">
    <p class="kicker" id="${id}-a">${esc(p.kicker)}</p>
    <h1 class="h1" id="${id}-b">${esc(p.title)}</h1>
    <span class="rule" id="${id}-c"></span>
    <p class="sub" id="${id}-d">${esc(p.sub)}</p>
  </div>`;

R.statement = (id, p) => `
  <div class="stack center">
    <h1 class="h1 tight" id="${id}-b">${esc(p.big)}</h1>
    <p class="sub wide" id="${id}-d">${esc(p.sub)}</p>
  </div>`;

R.outro = (id, p) => `
  <div class="stack center">
    <h1 class="h1" id="${id}-b">${esc(p.title)}</h1>
    <span class="rule" id="${id}-c"></span>
    <p class="sub" id="${id}-d">${esc(p.sub)}</p>
  </div>`;

R.verdict = (id, p) => `
  <div class="stack center">
    <p class="kicker" id="${id}-a">${esc(p.label)}</p>
    <div class="vrow">
      <div class="vcell" id="${id}-own"><span class="vnum gold">${esc(p.own)}</span><span class="vlab">OWN PRICE</span></div>
      <div class="vsep" id="${id}-sep">vs</div>
      <div class="vcell" id="${id}-mkt"><span class="vnum">${esc(p.mkt)}</span><span class="vlab">MARKET</span></div>
    </div>
    <p class="updelta" id="${id}-up">${esc(p.up)}</p>
  </div>`;

R.flow = (id) => `
  <div class="stack center">
    <div class="flowrow">
      ${[["DCF", "$1.25", "NAV per share"], ["PEERS", "$3.17", "EV per lb applied"], ["ANALYST", "$3.75", "Sanity check"]]
        .map((l, i) => `<div class="fnode" id="${id}-n${i}"><span class="fname">${l[0]}</span><span class="fval">${l[1]}</span><span class="fsub">${l[2]}</span></div>`).join("")}
    </div>
    <div class="farrow" id="${id}-ar">↓ &nbsp; weighted 50 / 30 / 20 &nbsp; ↓</div>
    <div class="fblend" id="${id}-bl"><span class="fname">BLENDED</span><span class="fval">$2.33</span></div>
    <div class="farrow" id="${id}-ar2">↓ &nbsp; less 10% liquidity haircut &nbsp; ↓</div>
    <div class="fown" id="${id}-ow"><span class="fname">YOUR OWN PRICE</span><span class="fval gold">$2.09</span></div>
  </div>`;

R.legs = (id, p) => `
  <div class="stack center">
    <div class="flowrow">
      ${[["DCF / NAV", p.nav], ["PEER-IMPLIED", p.peer], ["ANALYST TARGET", p.analyst]]
        .map((l, i) => `<div class="fnode tall" id="${id}-n${i}"><span class="fname">${l[0]}</span><span class="fval big">${l[1]}</span></div>`).join("")}
    </div>
    <p class="sub wide" id="${id}-note">${esc(p.note)}</p>
  </div>`;

R.sheet = (id, p) => `
  <div class="stack">
    <div class="tabbar" id="${id}-tab"><span class="tab on">${esc(p.tab)}</span><span class="tab">Sensitivity</span><span class="tab">DCF</span><span class="tab">Peers</span><span class="tab">OwnPrice</span></div>
    <div class="panel">
      <p class="ptitle" id="${id}-pt">${esc(p.title)}</p>
      <table class="grid">
        ${p.rows.map((r, i) => `<tr class="grow ${r[2]}" id="${id}-r${i}"><td class="lab">${esc(r[0])}</td><td class="val ${r[2]}">${esc(r[1])}</td></tr>`).join("")}
      </table>
      ${p.formula ? `<p class="fbar" id="${id}-fx"><span class="fx">fx</span>${esc(p.formula)}</p>` : ""}
      ${p.note ? `<p class="pnote" id="${id}-nt">${esc(p.note)}</p>` : ""}
    </div>
  </div>`;

R.bug = (id, p) => {
  if (p.stage === "spot")
    return `<div class="stack center">
      <div class="cellbox" id="${id}-cb"><span class="cellref">Inputs!B8</span><span class="cellval">$1.25</span></div>
      <p class="bugline" id="${id}-l1">It looks like a number.</p>
      <p class="bugline" id="${id}-l2">It's formatted like a number.</p>
      <p class="bugline red" id="${id}-l3">It's text.</p>
    </div>`;
  if (p.stage === "cascade")
    return `<div class="stack center">
      <p class="kicker" id="${id}-k">WHAT ONE TEXT CELL BREAKS</p>
      <div class="cascade">
        ${[["Inputs!B12", "Market cap"], ["Inputs!B20", "Cap-size bucket"], ["Peers!C12", "Peer row"], ["OwnPrice!B12", "Upside / downside"], ["OwnPrice!B13", "Verdict"]]
          .map((r, i) => `<div class="crow" id="${id}-c${i}"><span class="cref">${r[0]}</span><span class="cname">${r[1]}</span><span class="cerr">#VALUE!</span></div>`).join("")}
      </div>
      <p class="sub wide" id="${id}-w">No warning. Every other number still calculates perfectly.</p>
    </div>`;
  return `<div class="stack center">
    <div class="fixrow">
      <div class="fixbox bad" id="${id}-b1"><span class="fixlab">STORED</span><span class="fixval">"$1.25"</span><span class="fixtype">text</span></div>
      <div class="fixarrow" id="${id}-ar">→</div>
      <div class="fixbox good" id="${id}-b2"><span class="fixlab">SHOULD BE</span><span class="fixval">1.25</span><span class="fixtype">number</span></div>
    </div>
    <p class="sub wide" id="${id}-t">Type the number. Let the cell's format add the dollar sign.</p>
  </div>`;
};

R.build = (id, p) => `
  <div class="stack center">
    <p class="kicker" id="${id}-k">${esc(p.title)}</p>
    <div class="buildcol">
      ${p.steps.map((s, i) => `<div class="brow ${i === p.steps.length - 1 ? "last" : ""}" id="${id}-s${i}"><span class="blab">${esc(s[0])}</span><span class="bval">${esc(s[1])}</span></div>`).join("")}
    </div>
  </div>`;

R.bignum = (id, p) => `
  <div class="stack center">
    <p class="kicker" id="${id}-k">${esc(p.label)}</p>
    <p class="huge ${p.tone === "red" ? "red" : "gold"}" id="${id}-v">${esc(p.value)}</p>
    <p class="sub" id="${id}-s">${esc(p.sub)}</p>
    <p class="cellref dim" id="${id}-c">${esc(p.cell)}</p>
  </div>`;

const DCF_ROWS = [
  ["Production (M lbs)", "0.7", "1.0", "1.5", "2.0", "2.5"],
  ["Realized price ($/lb)", "68", "72", "78", "84", "88"],
  ["Revenue ($M)", "47.6", "72.0", "117.0", "168.0", "220.0"],
  ["Operating cost ($M)", "(32.2)", "(44.0)", "(63.0)", "(82.0)", "(100.0)"],
  ["Overhead ($M)", "(8.3)", "(12.6)", "(20.5)", "(29.4)", "(38.5)"],
  ["EBITDA ($M)", "7.1", "15.4", "33.5", "56.6", "81.5"],
  ["Capex ($M)", "(25.0)", "(30.0)", "(40.0)", "(90.0)", "(90.0)"],
  ["Free cash flow ($M)", "(17.9)", "(14.6)", "(6.5)", "(33.4)", "(8.5)"],
];
R.dcf = (id, p) => `
  <div class="stack">
    <div class="tabbar"><span class="tab">Inputs</span><span class="tab">Sensitivity</span><span class="tab on">DCF</span><span class="tab">Peers</span><span class="tab">OwnPrice</span></div>
    <div class="panel wide">
      <p class="ptitle">5-YEAR DCF — 2026 to 2030</p>
      <table class="grid dcf">
        <tr class="hdr"><td></td><td>2026</td><td>2027</td><td>2028</td><td>2029</td><td>2030</td></tr>
        ${DCF_ROWS.map((r, i) => `<tr class="grow ${p.highlight === "fcf" && i === 7 ? "hl-red" : ""}" id="${id}-r${i}">
          <td class="lab">${esc(r[0])}</td>${r.slice(1).map((v) => `<td class="num ${v.startsWith("(") ? "neg" : ""}">${esc(v)}</td>`).join("")}</tr>`).join("")}
      </table>
      ${p.highlight === "fcf" ? `<p class="pnote red" id="${id}-nt">Negative every single year.</p>` : ""}
    </div>
  </div>`;

R.compare = (id, p) => `
  <div class="stack center">
    <p class="kicker" id="${id}-k">${esc(p.title)}</p>
    <div class="cmprow">
      ${[p.left, p.right].map((s, i) => `<div class="cmpbox" id="${id}-b${i}">
        <span class="cmpname">${esc(s.name)}</span><span class="cmpval">${esc(s.value)}</span>
        <span class="cmpsub">${esc(s.sub)}</span><span class="cellref dim">${esc(s.cell)}</span></div>`).join("")}
    </div>
    <p class="updelta" id="${id}-d">${esc(p.delta)}</p>
  </div>`;

const PEERS = [
  ["Cameco", "CCJ", "$64,500M", "Producer"],
  ["Kazatomprom", "KAP", "$13,500M", "Producer"],
  ["NexGen Energy", "NXE", "$10,950M", "Developer"],
  ["Uranium Energy", "UEC", "$6,200M", "Producer (ramp)"],
  ["Denison Mines", "DNN", "$4,710M", "Developer"],
  ["Energy Fuels", "UUUU", "$4,510M", "Producer"],
  ["Ur-Energy", "URG", "$602M", "Producer"],
  ["enCore Energy", "EU", "$243M", "Producer (ramp)"],
];
R.peers = (id) => `
  <div class="stack">
    <div class="tabbar"><span class="tab">Inputs</span><span class="tab">Sensitivity</span><span class="tab">DCF</span><span class="tab on">Peers</span><span class="tab">OwnPrice</span></div>
    <div class="panel wide">
      <p class="ptitle">PEER CROSS-CHECK — URANIUM UNIVERSE</p>
      <table class="grid peers">
        <tr class="hdr"><td>Company</td><td>Ticker</td><td>Market cap</td><td>Status</td></tr>
        ${PEERS.map((r, i) => `<tr class="grow ${i === 7 ? "hl" : ""}" id="${id}-r${i}">
          <td class="lab">${esc(r[0])}</td><td class="tick">${esc(r[1])}</td><td class="num">${esc(r[2])}</td><td class="stat">${esc(r[3])}</td></tr>`).join("")}
      </table>
      <p class="pnote" id="${id}-nt">NexGen is worth $10.9B with zero pounds coming out of the ground.</p>
    </div>
  </div>`;

R.trap = (id, p) =>
  p.stage === "reveal"
    ? `<div class="stack center">
        <div class="trapcell" id="${id}-tc"><span class="cellref">Inputs!B45</span><span class="cellval gold">$12.00 / lb</span></div>
        <div class="traparms">
          <div class="traparm" id="${id}-a1">drives <b>DCF terminal value</b></div>
          <div class="traparm" id="${id}-a2">drives <b>peer-implied price</b></div>
        </div>
      </div>`
    : `<div class="stack center">
        <h1 class="h1 tight" id="${id}-b">One opinion, two hats.</h1>
        <p class="sub wide" id="${id}-d">When the legs agree they aren't confirming each other. They're repeating one assumption you made once.</p>
      </div>`;

R.blend = (id) => `
  <div class="stack">
    <div class="tabbar"><span class="tab">Inputs</span><span class="tab">Sensitivity</span><span class="tab">DCF</span><span class="tab">Peers</span><span class="tab on">OwnPrice</span></div>
    <div class="panel">
      <p class="ptitle">YOUR OWN PRICE — THE ANSWER SHEET</p>
      <table class="grid">
        ${[["NAV per share (DCF)", "$1.25", ""], ["Peer-implied price", "$3.17", ""], ["Analyst target", "$3.75", ""],
           ["Weights (NAV / Peer / Analyst)", "50% / 30% / 20%", ""], ["Blended, pre-discount", "$2.33", "calc"],
           ["Liquidity discount", "10.0%", ""], ["OWN PRICE", "$2.09", "hl"], ["Current market price", "$1.25", ""],
           ["Upside", "+67.4%", "good"], ["Verdict", "UNDERVALUED", "good"]]
          .map((r, i) => `<tr class="grow ${r[2]}" id="${id}-r${i}"><td class="lab">${esc(r[0])}</td><td class="val ${r[2]}">${esc(r[1])}</td></tr>`).join("")}
      </table>
    </div>
  </div>`;

R.assumptions = (id) => `
  <div class="stack center">
    <p class="kicker" id="${id}-k">$2.09 HOLDS ONLY IF</p>
    <div class="iflist">
      ${["uranium holds up", "production ramps as modelled", "$12 per pound is fair", "the terminal year arrives roughly as sketched"]
        .map((s, i) => `<div class="ifrow" id="${id}-i${i}"><span class="ifn">${i + 1}</span><span>${esc(s)}</span></div>`).join("")}
    </div>
  </div>`;

R.sensitivity = (id) => `
  <div class="stack">
    <div class="tabbar"><span class="tab">Inputs</span><span class="tab on">Sensitivity</span><span class="tab">DCF</span><span class="tab">Peers</span><span class="tab">OwnPrice</span></div>
    <div class="panel wide">
      <p class="ptitle">URANIUM PRICE SENSITIVITY — YEAR-1 ECONOMICS</p>
      <table class="grid peers">
        <tr class="hdr"><td>Scenario</td><td>Spot ($/lb)</td><td>Realized</td><td>All-in margin</td><td>Gross profit ($M)</td></tr>
        ${[["Bear", "50", "55", "$9", "6.3"], ["Base", "70", "68", "$22", "15.4"], ["Term-price world", "90", "87", "$41", "28.7"], ["Bull", "110", "105", "$59", "41.3"]]
          .map((r, i) => `<tr class="grow ${i === 3 ? "hl" : ""}" id="${id}-r${i}">
            <td class="lab">${esc(r[0])}</td><td class="num">${esc(r[1])}</td><td class="num">${esc(r[2])}</td><td class="num">${esc(r[3])}</td><td class="num strong">${esc(r[4])}</td></tr>`).join("")}
      </table>
      <p class="pnote" id="${id}-nt">6.5× swing in gross profit — from a price range uranium has genuinely traded through.</p>
    </div>
  </div>`;

R.versionlog = (id) => `
  <div class="stack center">
    <p class="kicker" id="${id}-k">VERSION LOG — STAMP EVERY RUN</p>
    <div class="panel wide">
      <table class="grid peers">
        <tr class="hdr"><td>Date</td><td>Bucket</td><td>Disc. rate</td><td>Own price</td><td>Mkt price</td></tr>
        ${[["21-Jul-26", "Micro", "15.55%", "$2.09", "$1.25"]].map((r, i) => `<tr class="grow hl" id="${id}-r${i}">${r.map((v) => `<td class="num">${esc(v)}</td>`).join("")}</tr>`).join("")}
      </table>
    </div>
    <p class="sub wide" id="${id}-s">Do this for a year and you find out whether your prices were any good. Most people never do.</p>
  </div>`;

R.actions = (id) => `
  <div class="stack center">
    <p class="kicker" id="${id}-k">DO THIS NEXT</p>
    <div class="iflist">
      ${["Fix the text cell", "Split the shared $/lb lever", "Flip the terminal value method", "Log every run"]
        .map((s, i) => `<div class="ifrow" id="${id}-i${i}"><span class="ifn gold">${i + 1}</span><span>${esc(s)}</span></div>`).join("")}
    </div>
  </div>`;

/* ── markup + timeline ─────────────────────────────────────────────────── */
let markup = "";
let tweens = "";
SCENES.forEach(([start, end, type, payload], i) => {
  const id = `sc${String(i).padStart(2, "0")}`;
  const track = (i % 2) + 1;
  const d = Math.round((end - start) * 1000) / 1000;
  markup += `      <section id="${id}" class="clip scene" data-start="${start}" data-duration="${d}" data-track-index="${track}">
        <div class="fade" id="${id}-fade">${R[type](id, payload)}</div>
      </section>\n`;

  const FADE = 0.55;
  tweens += `  tl.fromTo("#${id}-fade", { opacity: 0 }, { opacity: 1, duration: ${FADE}, ease: "power2.out" }, ${start});\n`;
  tweens += `  tl.to("#${id}-fade", { opacity: 0, duration: ${FADE}, ease: "power2.in" }, ${Math.round((end - FADE) * 1000) / 1000});\n`;
  // Hard kill on the clip boundary so a non-linear seek can't land past the
  // fade and leave the scene visible over its successor.
  tweens += `  tl.set("#${id}-fade", { opacity: 0 }, ${Math.round(end * 1000) / 1000});\n`;

  // staggered reveal of whatever rows/nodes this scene type has
  const sel = {
    sheet: `#${id} .grow`, dcf: `#${id} .grow`, peers: `#${id} .grow`, blend: `#${id} .grow`,
    sensitivity: `#${id} .grow`, versionlog: `#${id} .grow`, flow: `#${id} .fnode`, legs: `#${id} .fnode`,
    build: `#${id} .brow`, assumptions: `#${id} .ifrow`, actions: `#${id} .ifrow`,
  }[type];
  if (sel) {
    tweens += `  tl.fromTo("${sel}", { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.5, stagger: 0.13, ease: "power3.out" }, ${start + 0.35});\n`;
  }
  if (type === "bug" && payload.stage === "cascade") {
    tweens += `  tl.fromTo("#${id} .crow", { opacity: 0, x: -26 }, { opacity: 1, x: 0, duration: 0.45, stagger: 0.55, ease: "power3.out" }, ${start + 0.6});\n`;
    tweens += `  tl.fromTo("#${id} .cerr", { opacity: 0, scale: 0.86 }, { opacity: 1, scale: 1, duration: 0.3, stagger: 0.55, ease: "back.out(2)" }, ${start + 0.95});\n`;
  }
  if (type === "bug" && payload.stage === "spot") {
    tweens += `  tl.fromTo(["#${id}-l1", "#${id}-l2", "#${id}-l3"], { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: 0.45, stagger: 1.5, ease: "power3.out" }, ${start + 1.6});\n`;
  }
  if (type === "verdict") {
    tweens += `  tl.fromTo(["#${id}-own", "#${id}-sep", "#${id}-mkt"], { opacity: 0, y: 22 }, { opacity: 1, y: 0, duration: 0.6, stagger: 0.4, ease: "power3.out" }, ${start + 0.5});\n`;
    tweens += `  tl.fromTo("#${id}-up", { opacity: 0, scale: 0.9 }, { opacity: 1, scale: 1, duration: 0.5, ease: "back.out(1.8)" }, ${start + 2.2});\n`;
  }
  if (type === "compare") {
    tweens += `  tl.fromTo("#${id} .cmpbox", { opacity: 0, y: 26 }, { opacity: 1, y: 0, duration: 0.6, stagger: 0.6, ease: "power3.out" }, ${start + 0.5});\n`;
    tweens += `  tl.fromTo("#${id}-d", { opacity: 0 }, { opacity: 1, duration: 0.5, ease: "power2.out" }, ${start + 2.4});\n`;
  }
  if (type === "trap" && payload.stage === "reveal") {
    tweens += `  tl.fromTo("#${id} .traparm", { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: 0.5, stagger: 0.7, ease: "power3.out" }, ${start + 1.0});\n`;
  }
  if (["title", "statement", "outro", "bignum"].includes(type)) {
    tweens += `  tl.fromTo("#${id} .stack > *", { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.55, stagger: 0.16, ease: "power3.out" }, ${start + 0.3});\n`;
  }
});

const html = `<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=${W}, height=${H}" />
    <title>AIFT — Own-Price Valuation Engine Tutorial</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <style>
      @font-face { font-family:"Archivo Black"; src:url("assets/fonts/archivo-black-latin-400-normal.woff2") format("woff2"); font-weight:400; font-display:block; }
      @font-face { font-family:"Inter"; src:url("assets/fonts/inter-latin-400-normal.woff2") format("woff2"); font-weight:400; font-display:block; }
      @font-face { font-family:"Inter"; src:url("assets/fonts/inter-latin-600-normal.woff2") format("woff2"); font-weight:600; font-display:block; }
      @font-face { font-family:"Inter"; src:url("assets/fonts/inter-latin-700-normal.woff2") format("woff2"); font-weight:700; font-display:block; }
      @font-face { font-family:"JBMono"; src:url("assets/fonts/jetbrains-mono-latin-400-normal.woff2") format("woff2"); font-weight:400; font-display:block; }

      * { margin:0; padding:0; box-sizing:border-box; }
      html, body { width:${W}px; height:${H}px; overflow:hidden; background:#000; }
      body { font-family:"Inter",sans-serif; color:${C.text}; }
      #root { position:relative; width:${W}px; height:${H}px; overflow:hidden; }

      #ground { position:absolute; inset:0; background:
        radial-gradient(ellipse 62% 52% at 50% 0%, #101B33 0%, ${C.bg} 62%),
        ${C.bg}; }
      #vign { position:absolute; inset:0; background:
        radial-gradient(ellipse 78% 70% at 50% 48%, rgba(0,0,0,0) 40%, rgba(0,0,0,.55) 100%); }

      .scene { position:absolute; inset:0; display:grid; place-items:center; }
      .fade { position:absolute; inset:0; display:grid; place-items:center; padding:96px 120px; will-change:opacity; }
      .stack { display:flex; flex-direction:column; gap:26px; width:100%; align-items:center; }
      .stack.center { text-align:center; }
      /* Tab bar tracks its panel's width so the tabs sit flush to the panel's
         left edge while the pair stays centred in frame. */
      .stack:has(.panel) .tabbar { width:1420px; }
      .stack:has(.panel.wide) .tabbar { width:1620px; }

      .kicker { font-size:24px; font-weight:600; letter-spacing:.32em; text-transform:uppercase; color:${C.cyan}; }
      .h1 { font-family:"Archivo Black",sans-serif; font-weight:400; font-size:104px; line-height:1.04; letter-spacing:-.02em; }
      .h1.tight { font-size:92px; }
      .rule { display:block; width:200px; height:3px; background:${C.gold}; transform-origin:center; }
      .sub { font-size:30px; color:${C.dim}; letter-spacing:.02em; }
      .sub.wide { max-width:1180px; line-height:1.45; }
      .huge { font-family:"Archivo Black",sans-serif; font-size:186px; line-height:1; letter-spacing:-.03em; }
      .gold { color:${C.gold}; } .red { color:${C.red}; } .good, .green { color:${C.green}; }
      .dim { color:${C.dim}; }

      .vrow { display:flex; align-items:center; gap:64px; }
      .vcell { display:flex; flex-direction:column; gap:10px; }
      .vnum { font-family:"Archivo Black",sans-serif; font-size:150px; line-height:1; }
      .vlab { font-size:22px; letter-spacing:.28em; color:${C.dim}; }
      .vsep { font-size:34px; color:${C.dim}; }
      .updelta { font-size:44px; font-weight:700; color:${C.green}; letter-spacing:.02em; }

      .flowrow { display:flex; gap:38px; justify-content:center; }
      .fnode { display:flex; flex-direction:column; gap:10px; padding:30px 42px; min-width:352px;
               background:${C.panel}; border:1px solid ${C.panelEdge}; border-radius:14px; }
      .fnode.tall { padding:46px 52px; }
      .fname { font-size:20px; letter-spacing:.26em; color:${C.cyan}; }
      .fval { font-family:"Archivo Black",sans-serif; font-size:58px; }
      .fval.big { font-size:82px; }
      .fsub { font-size:19px; color:${C.dim}; }
      .farrow { font-size:22px; letter-spacing:.16em; color:${C.dim}; }
      .fblend, .fown { display:flex; flex-direction:column; gap:8px; padding:26px 60px;
                       background:${C.panel}; border:1px solid ${C.panelEdge}; border-radius:14px; }
      .fown { border-color:${C.gold}; }

      .tabbar { display:flex; gap:6px; margin-bottom:-1px; }
      .tab { font-size:19px; padding:11px 26px; color:${C.dim}; background:#0B1322;
             border:1px solid ${C.panelEdge}; border-bottom:none; border-radius:9px 9px 0 0; }
      .tab.on { color:${C.text}; background:${C.panel}; border-color:${C.cyan}; }
      .panel { background:${C.panel}; border:1px solid ${C.panelEdge}; border-radius:0 14px 14px 14px;
               padding:38px 46px; width:1420px; }
      .panel.wide { width:1620px; }
      .ptitle { font-size:21px; letter-spacing:.26em; color:${C.cyan}; margin-bottom:24px; }
      .grid { width:100%; border-collapse:collapse; }
      .grid td { padding:15px 12px; border-bottom:1px solid ${C.grid}; font-size:29px; will-change:transform,opacity; }
      .grid .lab { color:${C.dim}; text-align:left; }
      .grid .val { text-align:right; font-family:"JBMono","Inter",monospace; }
      .grid .val.in { color:${C.cyan}; }
      .grid .val.calc { color:${C.text}; }
      .grid tr.hl td { background:rgba(201,168,76,.11); }
      .grid tr.hl .val { color:${C.gold}; font-weight:700; }
      .grid tr.good .val { color:${C.green}; font-weight:700; }
      .grid tr.hl-red td { background:rgba(240,85,63,.13); }
      .grid tr.hl-red .num { color:${C.red}; }
      .grid .hdr td { font-size:21px; letter-spacing:.16em; color:${C.dim}; border-bottom:1px solid ${C.panelEdge}; }
      .grid .num { text-align:right; font-family:"JBMono","Inter",monospace; font-size:27px; }
      .grid .num.neg { color:#C98A80; }
      .grid .num.strong { color:${C.gold}; font-weight:700; }
      .grid .tick, .grid .stat { font-size:24px; color:${C.dim}; }
      .grid.dcf .lab, .grid.peers .lab { font-size:26px; }
      .fbar { margin-top:24px; font-family:"JBMono","Inter",monospace; font-size:24px; color:${C.dim};
              background:#0A1120; border:1px solid ${C.grid}; border-radius:9px; padding:14px 18px; }
      .fbar .fx { color:${C.cyan}; margin-right:16px; font-style:italic; }
      .pnote { margin-top:20px; font-size:24px; color:${C.dim}; }
      .pnote.red { color:${C.red}; font-weight:600; }

      .cellbox, .trapcell { display:flex; flex-direction:column; gap:12px; padding:44px 76px;
                background:${C.panel}; border:2px solid ${C.cyan}; border-radius:14px; }
      .cellref { font-family:"JBMono","Inter",monospace; font-size:24px; color:${C.cyan}; letter-spacing:.08em; }
      .cellval { font-family:"Archivo Black",sans-serif; font-size:92px; }
      .bugline { font-size:42px; color:${C.dim}; }
      .bugline.red { color:${C.red}; font-weight:700; font-size:56px; }

      .cascade { display:flex; flex-direction:column; gap:12px; width:1180px; }
      .crow { display:grid; grid-template-columns:300px 1fr 190px; align-items:center; gap:20px;
              padding:19px 26px; background:${C.panel}; border:1px solid ${C.panelEdge}; border-radius:11px; }
      .cref { font-family:"JBMono","Inter",monospace; font-size:25px; color:${C.cyan}; text-align:left; }
      .cname { font-size:27px; color:${C.text}; text-align:left; }
      .cerr { font-family:"JBMono","Inter",monospace; font-size:26px; color:${C.red}; font-weight:700; text-align:right; }

      .fixrow { display:flex; align-items:center; gap:52px; }
      .fixbox { display:flex; flex-direction:column; gap:10px; padding:38px 58px; border-radius:14px;
                background:${C.panel}; border:2px solid ${C.panelEdge}; }
      .fixbox.bad { border-color:${C.red}; } .fixbox.good { border-color:${C.green}; }
      .fixlab { font-size:19px; letter-spacing:.24em; color:${C.dim}; }
      .fixval { font-family:"Archivo Black",sans-serif; font-size:74px; }
      .fixtype { font-family:"JBMono","Inter",monospace; font-size:22px; color:${C.dim}; }
      .fixarrow { font-size:56px; color:${C.dim}; }

      .buildcol { display:flex; flex-direction:column; gap:12px; width:1120px; }
      .brow { display:flex; justify-content:space-between; align-items:center; padding:24px 34px;
              background:${C.panel}; border:1px solid ${C.panelEdge}; border-radius:12px; }
      .brow.last { border-color:${C.gold}; }
      .blab { font-size:29px; color:${C.dim}; }
      .bval { font-family:"JBMono","Inter",monospace; font-size:38px; }
      .brow.last .bval { color:${C.gold}; font-weight:700; }

      .cmprow { display:flex; gap:56px; }
      .cmpbox { display:flex; flex-direction:column; gap:14px; padding:46px 58px; width:640px;
                background:${C.panel}; border:1px solid ${C.panelEdge}; border-radius:14px; }
      .cmpname { font-size:21px; letter-spacing:.24em; color:${C.cyan}; }
      .cmpval { font-family:"Archivo Black",sans-serif; font-size:88px; }
      .cmpsub { font-size:23px; color:${C.dim}; }

      .traparms { display:flex; gap:44px; }
      .traparm { font-size:29px; color:${C.dim}; padding:22px 34px; background:${C.panel};
                 border:1px solid ${C.panelEdge}; border-radius:12px; }
      .traparm b { color:${C.gold}; }

      .iflist { display:flex; flex-direction:column; gap:15px; width:1120px; }
      .ifrow { display:flex; align-items:center; gap:26px; padding:23px 34px; font-size:33px;
               background:${C.panel}; border:1px solid ${C.panelEdge}; border-radius:12px; text-align:left; }
      .ifn { display:grid; place-items:center; width:48px; height:48px; flex:0 0 48px; border-radius:50%;
             background:#0A1120; border:1px solid ${C.cyan}; color:${C.cyan}; font-size:23px; font-weight:700; }
      .ifn.gold { border-color:${C.gold}; color:${C.gold}; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="${DURATION}" data-width="${W}" data-height="${H}">
      <section id="bg" class="clip" data-start="0" data-duration="${DURATION}" data-track-index="0">
        <div id="ground"></div>
      </section>

${markup}
      <section id="vg" class="clip" data-start="0" data-duration="${DURATION}" data-track-index="8">
        <div id="vign"></div>
      </section>

      <audio id="mix" class="clip" src="assets/audio/final-mix.wav" data-start="0" data-duration="${DURATION}" data-track-index="9"></audio>
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

writeFileSync("index.html", html);
console.log(`index.html — ${SCENES.length} scenes, ${DURATION}s (${Math.floor(DURATION / 60)}m ${DURATION % 60}s)`);
