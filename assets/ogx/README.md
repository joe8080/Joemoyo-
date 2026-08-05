# OGX Video Assets — where to drop audio and images

Working area for OrigineX (OGX) "declassified receipts" documentaries built with
the HeyGen / HyperFrames pipeline.

## One folder per video

Copy `_TEMPLATE/` to a slug named after the video, e.g.:

```
assets/ogx/west-sabotage/
assets/ogx/congo-lumumba/
```

Slug rule: lowercase, hyphens, no dates. The folder name is what gets referenced
from the build sheet and the HyperFrames composition.

## Layout

```
assets/ogx/<video-slug>/
├── audio/
│   ├── narration/     master VO, one file per act — 01_cold_open.wav, 02_act_one.wav …
│   ├── music/         score beds — bed_main.wav, bed_tension.wav, bed_outro.wav
│   └── sfx/           stamps, paper, static — stamp_declassified.wav, page_turn.wav
├── images/
│   ├── archival/      the actual "receipts": doc scans, cables, seals, maps
│   ├── cards/         rendered fact cards (2560×1440)
│   ├── title/         title card (2560×1440)
│   └── thumbnail/     1280×720 only
└── build/             build sheet, narration script, MANIFEST.md
```

## File specs (locked to the house style)

| Asset | Format | Size / rate |
| --- | --- | --- |
| Narration | WAV 48 kHz 24-bit mono (MP3 320 kbps acceptable) | −16 LUFS target |
| Music beds | WAV 48 kHz stereo | −26 LUFS under VO |
| SFX | WAV 48 kHz | short, trimmed, no lead silence |
| Fact / title cards | PNG | 2560×1440, exported to a 1920×1080 timeline |
| Archival receipts | PNG or JPG | ≥2000 px on the long edge |
| Thumbnail | PNG | 1280×720 |

Brand colours are fixed: background `#0A0A0A`, gold `#C9A24B`, alert red
`#B0231F`, body `#F2EDE4`. Pop-up fact boxes use the **brighter** border — that
is the locked default, not the original.

## Naming

Prefix everything with a two-digit scene number so the build sheet and the
composition sort identically:

```
audio/narration/03_the_cable.wav
images/cards/03_the_cable_card.png
images/archival/03_cable_scan.png
```

## Before you commit

- Keep any single file under ~50 MB. Full-length narration masters and video
  renders do **not** belong in git — put those in Drive and record the link in
  `build/MANIFEST.md`.
- Nothing ships unverified: every date, figure, document ID, and quote goes
  through the OGX Supabase DB (`qvlllknedilztozxwscj`) first.

## HyperFrames note

HyperFrames compositions fetch media over HTTPS, so assets referenced by a
hosted HeyGen project need a public URL — a raw GitHub URL on this branch works,
or upload to Drive/CDN and record the link in the manifest. Local paths only
work for local HTML compositions authored with the HyperFrames skills.
