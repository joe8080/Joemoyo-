# AI Finance Toolkit — Faceless Video Project Kickoff Kit

**Take this file to a NEW Claude Code project.** It contains everything needed to spin up a
faceless, modern-fintech video pipeline for your existing **AI Finance Toolkit** channel and
make the first video. Copy the kickoff prompt, connect the tools, drop in the skill.

---

## 0) The channel (real numbers)

- **AI Finance Toolkit** — `@aifinancetoolkit` · channel ID `UCjnWDpf_JbGUVp7man8_ZFw`
- GB / English · category Knowledge · niche Investing (AI Investing, Stock Analysis, Strategies)
- **1,140 subs · 69 videos · ~108 avg views · long-form ~6 min · last upload Jan 2026 (dormant).**
- Positioning (from your own description): *"Daily market recaps & weekly AI-driven investing
  deep dives; transparent, data-backed… building wealth, mastering automation, navigating the
  new financial era with AI."*
- Diagnosis: same as OrigineX — good positioning, too many low-effort uploads, weak packaging.
  **Fix = fewer, sharper, data-driven videos with strong titles/thumbnails and a clean look.**

---

## 1) Kickoff prompt (paste as your FIRST message in the new project)

> Set up a faceless finance-video pipeline for my YouTube channel **AI Finance Toolkit**
> (`@aifinancetoolkit`, `UCjnWDpf_JbGUVp7man8_ZFw`, GB/English). Style = **modern fintech**
> (charts, tickers, big-number stat cards, clean UI — NOT cinematic history). Narrator =
> **my cloned voice** (vidIQ custom voice **"Joe OGX"**, voiceId `JKDjSisy3uHa5eqQYalW`).
> Three content pillars: my portfolio journey, investment education, and market breakdowns —
> all UK-compliant (educational, not financial advice).
> First: build the `youtube-finance-video` skill from the spec I'm pasting, then make video #1
> on **"<pick a starter idea from §4>"** — research → scored title+thumbnail → script →
> my-voice VO → motion-graphic charts/cards + a little b-roll → assemble → show me before upload.

**Connect these MCP connectors in the new project** (same accounts as this one):
vidIQ for Claude · Highfield (Higgsfield) · Gmail · Google Drive · GitHub. The Joe OGX voice
already lives in the vidIQ voice library, so it's available to any session on this vidIQ account.

---

## 2) Reuse what already works

Copy the proven skill as your base and fork it:

```
cp -r <origineX repo>/.claude/skills/youtube-animated-doc  .claude/skills/youtube-finance-video
```

Keep the **mechanics** (they're identical and already cost-tuned):
- `vidiq_motion_graphics` → animated charts, tickers, count-up stat cards, comparison cards
  (**this is the backbone of finance video and it's cheap**).
- `vidiq_voiceover_generate` with voiceId `JKDjSisy3uHa5eqQYalW` (Joe OGX), chunk ≤5,000 chars.
- Highfield `generate_image` / `generate_video` for **rationed** b-roll (skylines, trading
  floors, data centers, AI/robot-advisor motifs) — preflight with `get_cost: true`.
- `vidiq_compose` for Ken Burns + text/logo/chart overlays; **stitch the final locally** with
  ffmpeg (`pip install imageio-ffmpeg`, concat `-c copy`) — Higgsfield import caps at 50 MB.
- vidIQ `generate_titles` / `score_title` / `generate_thumbnail` / `score_thumbnail`.
- Review-before-upload; nothing publishes without your OK.

Then **swap the house style** (below) — that's the only real change from the history skill.

---

## 3) Modern-fintech house style (LOCK THIS)

- **Palette:** near-black charcoal `#0b0e14` / deep-navy background; **electric-green `#00e08a`**
  (up / positive / brand) + **electric-blue `#3b82f6`** (neutral / accent); **red `#ff4d4d`**
  for down-moves; off-white `#e8edf5` text; muted grey `#7a8598` labels.
- **Type:** clean geometric sans (Inter / Söhne feel), heavy weights for big numbers.
- **Motion vocabulary:** animated line charts, bar races, count-up big numbers (`countUp`),
  progress bars (`barFill`), ticker strips, glassmorphism cards, subtle dot-grid background.
- **B-roll (rationed, ≤4–6 clips/video):** trading floors, London/NY skylines at dusk, server
  rooms, abstract data/AI motifs. Prompt suffix: *"sleek modern fintech, dark UI aesthetic,
  electric green and blue accents, clean, high-tech, 16:9."*
- **Pace:** a new data point or visual beat every **3–6 seconds**. Lower-third **source
  citations** on every stat (builds the "transparent, data-backed" trust the channel promises).
- **Intro/outro:** 3s branded logo sting; outro = subscribe card + "next video" nudge.

---

## 4) Content plan — 3 pillars + 12 starter ideas

Pick 1–2/week. Lead with the **journey** pillar (most bingeable), season with education & breakdowns.

**Pillar A — Portfolio journey (your real numbers):**
1. "I Let AI Pick My Portfolio for 30 Days — Here's the Real P&L"
2. "My Road to £1M: Month 1 (Real Trading 212 Numbers)"
3. "£500/Month Into an AI-Ranked Portfolio — Update #1"

**Pillar B — Education (evergreen, high search):**
4. "Index Funds vs AI-Managed: What UK Investors Should Actually Know"
5. "The ISA Mistake Quietly Costing You Thousands"
6. "Compounding, Explained in 6 Minutes (With Real Numbers)"
7. "5 AI Tools That Do Your Investment Research For You"

**Pillar C — Market breakdowns (timely, use sparingly):**
8. "What the Fed Just Did — and What It Means for Your Portfolio"
9. "Nvidia's Earnings, Decoded by AI"
10. "Is the S&P Overvalued? What the Data Says"
11. "Gold vs Bitcoin vs Stocks 2026: The Numbers"
12. "Weekly Market Recap — AI Deep Dive"

**Real portfolio data:** for Pillar A, pull your actual figures with the existing
`portfolio-command-centre` skill (Trading 212 CSV export). **Verify every number before it
goes on a card** — accuracy is the whole brand.

**Recommended first video:** #1 or #2 — the journey hook is the strongest way to relaunch a
dormant channel and it shows off the animated-chart look immediately.

---

## 5) UK compliance (MANDATORY — bake into the skill and every video)

- On-screen (early), in the description, and in a pinned comment:
  **"Educational only — not financial advice. Your capital is at risk. Past performance does
  not guarantee future results."**
- No guaranteed-return claims. No "buy this now" / personal recommendations — keep it
  **general and educational**. Frame opinions as opinions.
- Cite sources on-screen for every stat/claim. Prefer primary data (company filings, central
  banks, index providers).
- When showing your own portfolio, make clear it's *your* journey, not advice to copy.

---

## 6) Cost & cadence

- Finance leans on **cheap motion-graphics/charts** and little AI video → est.
  **~120–250 credits/video** (cheaper than the history builds). Keep the `get_cost` preflight
  gates and the "stop if a step quotes >150 credits" rule.
- **6–9 min** long-form, **1–2/week** to relaunch, + optional **1 Short/week** cut from each
  long-form (hook + one stat). Always score title+thumbnail before building.

---

## 7) First-session checklist (in the new project)

1. Connect vidIQ, Highfield, Gmail, Drive, GitHub.
2. `cp` the skill → fork to `youtube-finance-video`; paste §3 house style + §5 compliance in.
3. Confirm Joe OGX voice is visible: `vidiq_voiceover_list_voices` → look for `isCustom: true`.
4. Pull channel context: `vidiq_channel_stats` / `vidiq_channel_videos` for `@aifinancetoolkit`.
5. Make video #1 (§4) end-to-end; review; upload unlisted; go public on approval.

_— Generated for Joe (OrigineX / AI Finance Toolkit). Voice: Joe OGX (`JKDjSisy3uHa5eqQYalW`)._
