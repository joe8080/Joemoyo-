# Joe — personal site

One page, no build step, no tracking. Fonts are self-hosted, the YouTube player only loads when someone taps play (via the privacy-enhanced youtube-nocookie domain).

## Update the page (one file)

1. Open `site/content.js`.
2. Replace each `[PLACEHOLDER]` with the real value. Keep the quotes.
3. Save. Anything still showing a placeholder, or left empty, stays hidden from visitors.

| What | Key in `content.js` |
|---|---|
| YouTube channel | `youtubeChannelUrl` |
| Intro video | `introVideoUrl` |
| Collaboration email | `publicContactEmail` |
| Social links (optional) | `socials` |
| Photos (optional) | `photos.portrait`, `photos.studio` |
| Current project (optional) | `currentProject` — appears once `title` and `description` are filled in |

## See what's missing

Open the page with `?edit` on the end, e.g. `index.html?edit`.
Unfinished pieces show with orange dashed outlines and a checklist sits in the corner. Visitors never see this.

## Add photos

1. Put the files in `site/assets/photos/` (JPG or WebP, under about 250 KB each).
2. Portrait: about 1200 × 1500 px. Studio / project: about 1600 × 1000 px.
3. Write the path in `content.js`, e.g. `portrait: "assets/photos/joe-portrait.jpg"`.

Use real photos only. Until one is added, the hero shows the typography panel.

## Preview locally

```bash
cd site && python3 -m http.server 8080
# then open http://localhost:8080  (or http://localhost:8080/?edit)
```

## Launch checklist (only once approved)

1. Fill in the three essentials: channel, intro video, email.
2. In `index.html`, delete the `<meta name="robots" content="noindex, nofollow">` line.
3. Change `og:image` and `twitter:image` to the full address, e.g. `https://yourdomain.com/assets/og-image.png`.
4. Host the `site/` folder on any static host (GitHub Pages, Netlify, Cloudflare Pages all have free tiers).
5. If photos or thumbnails come from another website, add that host to `img-src` in the Content-Security-Policy line in `index.html`.

## Files

- `index.html` — page structure and the copy
- `content.js` — links, video, email, photos, project (edit this)
- `styles.css` — design
- `site.js` — behaviour (show/hide, video, menu, editor view)
- `noscript.css` — menu fallback when JavaScript is off
- `assets/` — fonts (SIL Open Font License), icons, share image
