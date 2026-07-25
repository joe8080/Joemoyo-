/* Trick or Trade 2024 — collection board
 *
 * Loads data/cards.json, merges any local edits from localStorage, and renders.
 * Keep/sell decisions and prices you type live in localStorage until you Export,
 * so the page works from a file:// open or GitHub Pages with no backend.
 *
 * PRICING RULE: this file never invents, infers, or estimates a price. A card
 * with priceGBP === null renders as "No price" and is excluded from every total.
 */
(() => {
  "use strict";

  const LS = "trt2024.collection.v1";
  const STALE_DAYS = 30;
  const RARITY_ORDER = ["Common", "Uncommon", "Rare", "Double Rare", "Ultra Rare", "Illustration Rare", "Special Illustration Rare", "Hyper Rare"];

  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  let SET = {};
  let CARDS = [];
  let filter = "all";
  let query = "";
  let sortBy = "number";

  const gbp = (n) =>
    new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP", minimumFractionDigits: 2 }).format(n);

  const daysSince = (iso) => {
    if (!iso) return null;
    const t = Date.parse(iso);
    if (Number.isNaN(t)) return null;
    return Math.floor((Date.now() - t) / 86400000);
  };

  /* ── data ───────────────────────────────────────────────────────────── */

  async function load() {
    let file = { set: {}, cards: [] };
    try {
      const r = await fetch("data/cards.json", { cache: "no-store" });
      if (r.ok) file = await r.json();
    } catch {
      /* file:// with no fetch permission — fall through to localStorage */
    }

    SET = file.set || {};
    const seeded = (file.cards || []).filter((c) => !/^EXAMPLE/i.test(c.name || ""));

    let local = null;
    try {
      local = JSON.parse(localStorage.getItem(LS) || "null");
    } catch { /* corrupt storage — ignore rather than crash the page */ }

    CARDS = local && Array.isArray(local.cards) && local.cards.length ? local.cards : seeded;
    CARDS = CARDS.map(normalise);
    if (SET.code) $("#set-code").textContent = SET.code;
  }

  function normalise(c, i) {
    return {
      number: String(c.number ?? i + 1).padStart(3, "0"),
      name: c.name || "Unknown",
      rarity: c.rarity || "",
      variant: c.variant || "",
      condition: c.condition || "NM",
      qty: Number(c.qty) || 1,
      status: ["keep", "sell", "undecided"].includes(c.status) ? c.status : "undecided",
      priceGBP: c.priceGBP === null || c.priceGBP === undefined || c.priceGBP === "" ? null : Number(c.priceGBP),
      priceSource: c.priceSource || "",
      priceChecked: c.priceChecked || "",
      image: c.image || "",
      notes: c.notes || "",
    };
  }

  const save = () => localStorage.setItem(LS, JSON.stringify({ set: SET, cards: CARDS }));

  /* ── render ─────────────────────────────────────────────────────────── */

  function visible() {
    const q = query.trim().toLowerCase();
    return CARDS.filter((c) => {
      if (filter === "unpriced" && c.priceGBP !== null) return false;
      if (["keep", "sell", "undecided"].includes(filter) && c.status !== filter) return false;
      if (q && !(`${c.number} ${c.name} ${c.rarity}`.toLowerCase().includes(q))) return false;
      return true;
    }).sort(cmp);
  }

  function cmp(a, b) {
    switch (sortBy) {
      case "name": return a.name.localeCompare(b.name);
      case "rarity": return RARITY_ORDER.indexOf(a.rarity) - RARITY_ORDER.indexOf(b.rarity) || a.number.localeCompare(b.number);
      case "value-desc": return (b.priceGBP ?? -1) - (a.priceGBP ?? -1);
      case "value-asc": {
        // unpriced sorts last in both directions — it is absence, not zero
        if (a.priceGBP === null) return 1;
        if (b.priceGBP === null) return -1;
        return a.priceGBP - b.priceGBP;
      }
      default: return a.number.localeCompare(b.number, undefined, { numeric: true });
    }
  }

  function cardEl(c) {
    const el = document.createElement("article");
    const holo = /rare|illustration|hyper/i.test(c.rarity);
    el.className = "card" + (holo ? " holo" : "");
    el.dataset.n = c.number;

    const stale = daysSince(c.priceChecked);
    const isStale = stale !== null && stale > STALE_DAYS;

    const priceHtml =
      c.priceGBP === null
        ? `<span class="amt none">No price</span>
           <span class="src">not yet<br>researched</span>`
        : `<span class="amt">${gbp(c.priceGBP * c.qty)}</span>
           <span class="src${isStale ? " stale" : ""}">${c.priceSource ? esc(c.priceSource) : "source?"}${
             stale !== null ? `<br>${stale}d ago${isStale ? " · stale" : ""}` : ""
           }</span>`;

    el.innerHTML = `
      <div class="c-top">
        <span class="c-num">#${esc(c.number)}</span>
        <span class="badge ${c.status}">${c.status}</span>
      </div>
      <h3 class="c-name">${esc(c.name)}</h3>
      <p class="c-meta">
        ${c.rarity ? `<span>${esc(c.rarity)}</span>` : ""}
        <span>${esc(c.condition)}</span>
        ${c.qty > 1 ? `<span>×${c.qty}</span>` : ""}
        ${c.variant ? `<span>${esc(c.variant)}</span>` : ""}
      </p>
      <div class="c-price">${priceHtml}</div>
      <div class="c-actions">
        <button class="tog ${c.status === "keep" ? "on" : ""}" data-s="keep">KEEP</button>
        <button class="tog ${c.status === "sell" ? "on" : ""}" data-s="sell">SELL</button>
        <button class="tog" data-s="price">£</button>
      </div>`;

    el.addEventListener("click", (e) => {
      const b = e.target.closest(".tog");
      if (!b) return;
      if (b.dataset.s === "price") return editPrice(c);
      c.status = c.status === b.dataset.s ? "undecided" : b.dataset.s;
      save();
      render();
    });

    // pointer-tracked sheen + subtle 3D tilt
    el.addEventListener("pointermove", (e) => {
      const r = el.getBoundingClientRect();
      const px = (e.clientX - r.left) / r.width;
      const py = (e.clientY - r.top) / r.height;
      el.style.setProperty("--mx", `${px * 100}%`);
      el.style.setProperty("--my", `${py * 100}%`);
      el.classList.add("tilt");
      el.style.transform = `perspective(880px) rotateY(${(px - .5) * 9}deg) rotateX(${(.5 - py) * 9}deg) translateY(-4px)`;
    });
    el.addEventListener("pointerleave", () => {
      el.classList.remove("tilt");
      el.style.transform = "";
    });

    return el;
  }

  function editPrice(c) {
    const raw = prompt(
      `Price for #${c.number} ${c.name} (GBP, per card).\n\n` +
      `Use a real source — eBay SOLD listings or Cardmarket trend.\n` +
      `Leave blank to clear.`,
      c.priceGBP ?? "",
    );
    if (raw === null) return;
    if (raw.trim() === "") {
      c.priceGBP = null; c.priceSource = ""; c.priceChecked = "";
    } else {
      const n = Number(raw.replace(/[£,\s]/g, ""));
      if (!Number.isFinite(n) || n < 0) return alert("That is not a number.");
      c.priceGBP = n;
      c.priceSource = (prompt("Where did that come from? (e.g. eBay sold, Cardmarket trend)", c.priceSource || "") || "").slice(0, 40);
      c.priceChecked = new Date().toISOString().slice(0, 10);
    }
    save();
    render();
  }

  function render() {
    const list = visible();
    const board = $("#board");
    board.innerHTML = "";
    list.forEach((c) => board.appendChild(cardEl(c)));

    $("#empty").hidden = CARDS.length > 0;
    $("#count").textContent = CARDS.length
      ? `Showing ${list.length} of ${CARDS.length} cards`
      : "";

    stats();
    valuation();
    observeCards();
  }

  function stats() {
    const keep = CARDS.filter((c) => c.status === "keep");
    const sell = CARDS.filter((c) => c.status === "sell");
    const priced = sell.filter((c) => c.priceGBP !== null);

    countTo($("#s-total"), CARDS.reduce((s, c) => s + c.qty, 0));
    countTo($("#s-keep"), keep.reduce((s, c) => s + c.qty, 0));
    countTo($("#s-sell"), sell.reduce((s, c) => s + c.qty, 0));

    const anyPriced = CARDS.some((c) => c.priceGBP !== null);
    $("#price-banner").hidden = anyPriced || CARDS.length === 0;

    const el = $("#s-value");
    if (!sell.length || !priced.length) {
      el.textContent = "—";
      $("#s-value-lab").textContent = sell.length ? "Sell pile unpriced" : "Sell value";
    } else {
      const total = priced.reduce((s, c) => s + c.priceGBP * c.qty, 0);
      el.textContent = gbp(total);
      const missing = sell.length - priced.length;
      $("#s-value-lab").textContent = missing ? `Sell value · ${missing} unpriced` : "Sell value";
    }
  }

  function valuation() {
    const priced = CARDS.filter((c) => c.priceGBP !== null);
    const sec = $("#valuation");
    if (!priced.length) { sec.hidden = true; return; }
    sec.hidden = false;

    const tot = (arr) => arr.reduce((s, c) => s + c.priceGBP * c.qty, 0);
    const all = tot(priced);
    const keep = tot(priced.filter((c) => c.status === "keep"));
    const sell = tot(priced.filter((c) => c.status === "sell"));
    const top = [...priced].sort((a, b) => b.priceGBP - a.priceGBP)[0];
    const unpriced = CARDS.length - priced.length;

    $("#vgrid").innerHTML = [
      ["Priced cards", `${priced.length} / ${CARDS.length}`],
      ["Collection total", gbp(all)],
      ["Keep pile", gbp(keep)],
      ["Sell pile", gbp(sell)],
      ["Most valuable", top ? `${gbp(top.priceGBP)}<span class="vsub">${esc(top.name)}</span>` : "—"],
      ["Median card", gbp(median(priced.map((c) => c.priceGBP)))],
    ].map(([k, v]) => `<div class="vcell"><div class="k">${k}</div><div class="v">${v}</div></div>`).join("");

    const staleCards = priced.filter((c) => (daysSince(c.priceChecked) ?? 0) > STALE_DAYS);
    const notes = [];
    if (unpriced) notes.push(`${unpriced} card${unpriced > 1 ? "s have" : " has"} no price, so these totals are a floor, not the full value.`);
    if (staleCards.length) notes.push(`${staleCards.length} price${staleCards.length > 1 ? "s are" : " is"} over ${STALE_DAYS} days old — re-check before you list.`);
    $("#stale").hidden = !notes.length;
    $("#stale").textContent = notes.join(" ");
  }

  const median = (a) => {
    if (!a.length) return 0;
    const s = [...a].sort((x, y) => x - y);
    const m = s.length >> 1;
    return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
  };

  /* ── import / export ────────────────────────────────────────────────── */

  function parsePaste(text) {
    const out = [];
    text.split(/\r?\n/).forEach((line) => {
      const t = line.trim();
      if (!t) return;
      let number = "", name = t, rarity = "";

      if (t.includes(",")) {
        const p = t.split(",").map((x) => x.trim());
        if (/^\d+$/.test(p[0])) { number = p[0]; name = p[1] || ""; rarity = p[2] || ""; }
        else { name = p[0]; rarity = p[1] || ""; }
      } else {
        const m = t.match(/^(\d{1,3})[\s.\-/]+(.+)$/);
        if (m) { number = m[1]; name = m[2]; }
        const r = name.match(/\s+(Common|Uncommon|Double Rare|Ultra Rare|Illustration Rare|Special Illustration Rare|Hyper Rare|Rare)$/i);
        if (r) { rarity = r[1]; name = name.slice(0, r.index).trim(); }
      }
      if (!name) return;
      out.push({ number: number || String(out.length + 1), name, rarity });
    });
    return out;
  }

  function doImport() {
    const rows = parsePaste($("#paste").value);
    if (!rows.length) return;
    const replace = $("#replace").checked;
    const base = replace ? [] : CARDS;
    CARDS = [...base, ...rows.map(normalise)].map((c, i) => normalise(c, i));
    save();
    $("#paste").value = "";
    render();
  }

  function doExport() {
    const blob = new Blob(
      [JSON.stringify({ set: SET, cards: CARDS }, null, 2)],
      { type: "application/json" },
    );
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "cards.json";
    a.click();
    URL.revokeObjectURL(a.href);
  }

  /* ── motion ─────────────────────────────────────────────────────────── */

  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;

  function countTo(el, target) {
    const from = Number(el.dataset.count || 0);
    el.dataset.count = target;
    if (reduce || from === target) { el.textContent = target; return; }
    const t0 = performance.now(), dur = 620;
    const step = (t) => {
      const k = Math.min(1, (t - t0) / dur);
      el.textContent = Math.round(from + (target - from) * (1 - Math.pow(1 - k, 3)));
      if (k < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }

  let io;
  function observeCards() {
    io?.disconnect();
    io = new IntersectionObserver(
      (es) => es.forEach((e, i) => {
        if (!e.isIntersecting) return;
        setTimeout(() => e.target.classList.add("in"), Math.min(i * 26, 320));
        io.unobserve(e.target);
      }),
      { rootMargin: "0px 0px -8% 0px" },
    );
    $$(".card").forEach((c) => io.observe(c));
  }

  function esc(s) {
    return String(s).replace(/[&<>"]/g, (m) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[m]));
  }

  /* ── wire up ────────────────────────────────────────────────────────── */

  async function init() {
    await load();

    $("#q").addEventListener("input", (e) => { query = e.target.value; render(); });
    $("#sort").addEventListener("change", (e) => { sortBy = e.target.value; render(); });
    $$(".chip").forEach((b) =>
      b.addEventListener("click", () => {
        $$(".chip").forEach((x) => x.classList.remove("on"));
        b.classList.add("on");
        filter = b.dataset.filter;
        render();
      }));

    const dlg = $("#dlg-import");
    $("#btn-import").addEventListener("click", () => dlg.showModal());
    $("#btn-import-2").addEventListener("click", () => dlg.showModal());
    dlg.addEventListener("close", () => { if (dlg.returnValue === "ok") doImport(); });
    $("#btn-export").addEventListener("click", doExport);
    $("#open-help").addEventListener("click", () => $("#dlg-help").showModal());

    const tb = $("#toolbar");
    addEventListener("scroll", () => tb.classList.toggle("stuck", scrollY > 10), { passive: true });

    $$(".reveal").forEach((el, i) => setTimeout(() => el.classList.add("in"), 90 * i));
    $("#built").textContent = `Board generated ${new Date().toISOString().slice(0, 10)} · prices are owner-entered, never estimated`;

    render();
  }

  init();
})();
