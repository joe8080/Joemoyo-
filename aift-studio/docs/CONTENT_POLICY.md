# Content policy

The channel's remit is research and education. This document is the standard the pipeline enforces,
not a statement of intent — each rule below maps to code that blocks a pack when it is broken.

---

## 1. The disclosure

Every pack carries this, verbatim, spoken in the narration and repeated in the description:

> **This video is for research and education only, not personalised financial advice. Always do your
> own research and consider professional advice where appropriate.**

Two separate gates check it. A pack missing it in either place cannot reach review. The wording lives
in Brand Studio; the compliance gate reads that value, so changing it there changes what is enforced.

---

## 2. Source hierarchy

1. **Primary filings** — 10-Q, 10-K, 20-F, 8-K, prospectus, exchange notice
2. **Primary company** — investor relations pages, press releases, earnings decks, transcripts
3. **Primary regulator** — SEC, FCA, central banks, national statistics agencies
4. **Specialist** — professional research, standards bodies, academic work
5. **Reputable financial journalism**

**Web search is discovery only.** A snippet is a pointer to a document; it is never a citation. The
pipeline fetches and stores the document before anything may cite it, and the mock research provider
reproduces that two-step shape so code that tries to shortcut fails in development too.

**Two-source rule.** A material claim resting only on non-primary evidence needs two independent
sources. A single specialist note is not enough to carry a market figure into a script.

---

## 3. Material claims

A claim is **material** if it is a price or performance figure, a market-cap figure, a
financial-statement figure, a forecast or guidance, a rating or recommendation, an insider or
ownership detail, a valuation, or a causal statement of the form "X caused Y".

A material claim reaches a script only with **all** of:

- at least one linked source document that was successfully **fetched and stored**
- a **verbatim excerpt** from that source
- the source's **publication date**
- an **as-of date** for the figure itself
- a **confidence** of 0.6 or higher
- an excerpt that **actually contains every figure the claim asserts**

Miss any one and the claim is marked `not_public_safe` with the specific reason, is withheld from
the writer entirely, and is listed on the Research Desk so you can see what was dropped and why.

**Definitional claims** — "customer-concentration disclosure exists because losing such a customer
could be material" — need no market evidence. They are the mechanism, and the mechanism is what
makes a video educational rather than a list of numbers.

---

## 4. What the script may not do

| Not permitted | Why | Enforced by |
|---|---|---|
| "You should buy / sell / add / trim / cut" | That is a personalised instruction, and this is not that product | `no_trade_instruction` |
| Banned phrases — "load up on", "guaranteed return", "risk-free", "to the moon", "my price target" | Instruction-shaped or certainty-shaped language | `no_banned_phrases` |
| "This will definitely re-rate" | Certainty about future performance | `no_performance_certainty` |
| A figure with no claim behind it | An unsourced number is the most common way an audience is misled | `no_unsourced_figures` |
| A price with no as-of date | An undated figure is not evidence | `material_claims_dated` |
| A title promising more than the evidence supports | The thumbnail and title are part of the claim | `title_not_overpromising` |
| Any mention of the owner's portfolio, holdings, account, broker or personal profit and loss | Private data does not become public content | `no_private_finance_in_public_copy` |
| A script with no counter-case | A one-sided read of a filing is not research | `counter_case_present` |

Note what *is* permitted: bull, base and bear cases; risks; financial concepts; what the evidence
suggests and what it does not; and disagreement with a company's own framing. The line is between
**describing evidence** and **instructing a viewer**.

---

## 5. The uncertainty style guide

Say what kind of statement you are making:

| Instead of | Say |
|---|---|
| "Revenue grew 60%" | "The company reported revenue of $4.61bn, against $2.88bn a year earlier, as of 27 June 2026" |
| "Margins will hold" | "Management guided to approximately 57.5%, below the 58.4% just reported" |
| "The stock is cheap" | "The filing states X; what that is worth depends on assumptions the filing does not make" |
| "This caused that" | "The company attributes the move to mix" |
| "It's going to keep growing" | "One quarter is a data point; a direction needs several" |

The distinction the pipeline works hardest to preserve is **reported versus guided**. A reported
figure has been through the company's controls and, at year end, an auditor's. A guided figure is
the company's own estimate of its own future, issued under a safe harbour and revised whenever
conditions change. Stat cards name which one they are showing, above the number, because that
distinction is the whole point of the card.

---

## 6. Visual accuracy

| Asset | Method | Rule |
|---|---|---|
| Charts, price series, allocation graphics, comparison tables | Code-generated SVG rendered into the video | Exact validated rows; source and as-of date visible in the frame |
| Headline cards, lower thirds, chapter cards, citations, subtitles | Editable HTML/React compositions | All on-screen text is source-controlled |
| Atmospheric B-roll | Generative provider adapter | Never a figure, a logo, a chart or a readable screen |
| Narration | Licensed TTS or a recorded voice | Transcript and voice settings preserved with the clip |
| Music and SFX | Licensed or user-supplied | Provenance stored; speech stays intelligible |
| Thumbnail | AI-assisted concept, editable final | No misleading performance claim, no fake screenshot, no unreadable text |

`MediaAsset.factualContentAllowed` is hard-coded `false`. The visual gate rejects a B-roll scene
carrying data, and rejects a B-roll prompt that asks for a chart, a percentage, a price, a ticker, a
logo or a dashboard. A test moves a real chart scene to a generated composition and asserts both
checks fail.

Every number a viewer reads on a stat card is compared, character for character, against the claim
ledger. Axis ticks are derived from the series rather than quoted individually, so those are
reported as a warning naming the series rather than a block — the distinction is deliberate, and the
report says which is which.

---

## 7. Private data

Portfolio data is **private context** and defaults to being excluded entirely. Where a theme is
allowed through, it is a bucket *label* and only where more than one bucket shares it, so a label
cannot identify a single position. No weight, no value, no count.

There is no configuration, flag or code path that puts a portfolio value into a model payload. See
`docs/SECURITY.md`.

---

## 8. Publication

The system does not publish. It produces a package and stops.

`approved_for_archive` means "this is complete and I stand behind it". `archived` means "stored, for
me to upload by hand". Both require an authenticated reviewer decision, in that order. Neither means
the video has been, or will be, uploaded by anything other than you.

Run the first real topic **one at a time**, and keep it in review until the output meets your
editorial standard consistently. The quality gates catch what can be checked mechanically. They
cannot tell you whether a video is worth watching — that judgement is the reason the review room
exists.
