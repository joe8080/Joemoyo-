# Trick or Trade 2024 — Collection Board

A shareable, single-page board for the Pokémon TCG *Trick or Trade BOOster Bundle
2024* set. Catalogue every card, mark each one **keep** or **sell**, record real
prices, and get running totals for both piles.

Static, self-contained, zero dependencies. No build step, no backend, no runtime
network calls. Open `index.html` or push it to GitHub Pages.

## The one thing to understand about prices

**Every price on this board is one you entered. Nothing is estimated, modelled,
or AI-generated.**

I could not look up a single value while building this — the machine's network
policy blocks TCGplayer, Cardmarket, PriceCharting, eBay and the Pokémon TCG API
(all 403 at the gateway). Rather than fill the page with invented numbers you
might price real cards against, unpriced cards render as **"No price"** and are
excluded from every total.

The board is built so a missing price is visibly missing:

- the headline value shows `—`, never `£0.00`, when the sell pile is unpriced
- the valuation section stays hidden until at least one real price exists
- totals say how many cards are still unpriced, so you read them as a floor
- any price older than 30 days is flagged **stale**

## Using it

1. Open the page and click **Add cards**.
2. Paste your checklist, one card per line. The parser accepts:
   - `012 Gengar Rare`
   - `012, Gengar, Rare`
   - `Gengar`
3. Tap **KEEP** or **SELL** on each card.
4. Tap **£** to enter a price — it asks where the figure came from and stamps
   the date.
5. Click **Export** to download `cards.json`, then drop it in `data/` and commit
   so the board is the same for anyone you share the link with.

Edits live in `localStorage` until you export, so the page works offline and from
a plain `file://` open.

### Pricing them properly

- **eBay sold listings**, not active. Asking prices are fiction; sold is what
  someone actually paid.
- **Cardmarket trend** is the better read for UK/EU. Use trend, not the lowest
  listing — the lowest is usually damaged or shipping from abroad.
- **Price the exact variant.** Trick or Trade cards carry a Halloween stamp. A
  stamped card and its base-set twin are different products and can diverge a lot.
- **Condition moves the number** — NM to LP is often 20–40% on modern cards.

## Deploying

GitHub Pages, from this folder:

```bash
# Settings → Pages → Source: Deploy from a branch
# Branch: <your branch> · Folder: /web/tcg-collection
```

Or anything that serves static files — Netlify, Vercel, Cloudflare Pages. There
is nothing to build.

## Files

| Path | What |
|---|---|
| `index.html` | page structure and both dialogs |
| `assets/styles.css` | all styling — dark AI theme, holo card effect, motion |
| `assets/app.js` | data load, filter/sort, keep-sell state, valuation, import/export |
| `data/cards.json` | your collection — the file the page reads on load |

## What's in the build

- **Holographic card treatment** on rares — an animated conic border plus a
  pointer-tracked specular sheen, with a subtle 3D tilt on hover. Pure CSS and a
  few lines of JS; no library, no images.
- **Scroll-reveal** staggering as cards enter, and count-up animation on the stats.
- **Filters** by keep / sell / undecided / unpriced, live search, and five sort
  orders. Unpriced cards sort last in both value directions — absence isn't zero.
- **Respects `prefers-reduced-motion`** — all animation collapses to instant.
- **Responsive** to 390px.

## Verified

Driven in a real browser with Playwright, not just eyeballed:

- all four paste formats parse correctly
- keep/sell toggles, filters and search return the right counts
- unpriced sell pile shows `—`, and the valuation section stays hidden
- entering a price reveals the valuation and totals correctly
- state survives a page reload
- **zero console errors, zero failed requests**

## Still to do

- **Confirm the set.** `data/cards.json` names it *Trick or Trade BOOster Bundle
  2024* with `cardCount: null`. Fill in the real count before the page claims a
  complete set — I did not want to assert a checklist I could not verify.
- **Card images.** Each card has an `image` field the UI doesn't render yet.
  Wire it up once you have local scans or an image source that isn't blocked.
- **Prices.** All of them.

## Legal

Card names and imagery are property of The Pokémon Company. This is a personal,
non-commercial catalogue. The figures are the owner's own research — not a market
quote, an appraisal, or a valuation service.
