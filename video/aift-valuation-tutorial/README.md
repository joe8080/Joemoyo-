# AIFT Own-Price Valuation Engine — Tutorial

A 14:22, 1920×1080 tutorial walking through the AI Finance Toolkit Own-Price
Valuation Engine end to end, using enCore Energy (EU) as the worked example.

Narrated in Joe's own cloned voice, over an original music bed. Every visual is
a rendered recreation of the actual workbook — no AI-generated imagery, so all
type and numbers stay crisp and correct.

## Rebuild it

```bash
node build-audio.mjs   # VO parts + music → narration.wav, final-mix.wav, timing.json
node build.mjs         # timing.json + scene table → index.html
npm run check          # lint + runtime + layout + motion + contrast
npm run render         # → aift-valuation-tutorial.mp4
```

`build-audio.mjs` must run first — `build.mjs` reads `timing.json` to place every
scene against the real voiceover.

## Editing

**`build.mjs` is the source of truth.** `index.html` is generated; hand edits are
lost on rebuild.

- **Retime or change a visual** — edit the `SCENES` table. Each row is
  `[start, end, type, payload]` in absolute seconds.
- **Change a scene's look** — the renderers live in the `R` object, one function
  per scene type (`sheet`, `dcf`, `peers`, `bug`, `compare`, `blend`, …).
- **Change the palette** — the `C` object at the top.
- **Change pacing between chapters** — `GAP_AFTER` in `build-audio.mjs`, then
  re-run both scripts. Those gaps are deliberate reading beats, not padding.

## Re-recording the voiceover

Narration is split into `vo-01.txt` … `vo-10.txt` (~1,200 chars each — the vidIQ
tool times out above roughly 1,500). To regenerate:

1. `mcp__vidIQ_for_Claude__vidiq_voiceover_generate` with
   `voiceId: JKDjSisy3uHa5eqQYalW` (Joe OGX cloned voice)
2. Download each presigned S3 URL to `assets/audio/vo-NN.mp3` **immediately** —
   they expire in 12 hours
3. `node build-audio.mjs && node build.mjs`

Cost was ~151 credits for 10,818 characters at 14 credits per 1,000.

## Source data

`AIFT_Own_Price_Valuation_Engine.xlsx` — the workbook, **with the input bug
fixed**. Every figure on screen traces to a cell; the mapping is at the bottom of
`SCRIPT.md`.

### The bug this tutorial opens on

`Inputs!B8` held the string `"$1.25"` under a `\$0.00` currency format. It looked
like a number and wasn't, so five cells returned `#VALUE!`:

| Cell | What it should show |
|---|---|
| `Inputs!B12` | Market cap |
| `Inputs!B20` | Suggested cap bucket |
| `Peers!C12` | enCore's peer row |
| `OwnPrice!B12` | Upside / downside |
| `OwnPrice!B13` | Verdict |

Fixed to numeric `1.25`. The chain now resolves: market cap $242.77M → Micro
bucket (which independently confirms the manually-selected bucket) → Own Price
$2.09 → +67.4% → UNDERVALUED.

`DCF!B3:F3` also held year headers as text; those are now numeric.

> **Note on cached values.** openpyxl writes formulas without cached results, so
> tools that read cached values (pandas, `data_only=True`) will see `None` until
> the file is opened once in Excel or LibreOffice, which recalculates on open.
> The formulas themselves are correct — verified arithmetically.

## Two analytical points the tutorial makes

1. **Every projected year has negative free cash flow** (−17.9, −14.6, −6.5,
   −33.4, −8.5). Sum of PV is −$53.5M, so the entire NAV rests on terminal
   value. Legitimate for a pre-scale producer, but it changes what you're
   betting on.
2. **The DCF and Peers legs share a lever.** Both are driven by `Inputs!B45`
   ($12/lb). When they agree they aren't confirming each other. The workbook
   flags this itself in `Peers!C15` — give the peer leg its own $/lb if you want
   a genuine second opinion.

## Files

| Path | What |
|---|---|
| `SCRIPT.md` | narration + stage directions + cell trace table |
| `build-audio.mjs` | VO concat, chapter gaps, music duck → `timing.json` |
| `build.mjs` | scene table + renderers → `index.html` |
| `timing.json` | generated — per-part start/end against the real audio |
| `vo-NN.txt` | narration chunks, verbatim, as sent to TTS |
| `assets/audio/vo-NN.mp3` | generated voiceover (committed — costs credits) |
| `assets/audio/music-bed.wav` | source music track (committed) |
| `AIFT_Own_Price_Valuation_Engine.xlsx` | the workbook, bug fixed |
