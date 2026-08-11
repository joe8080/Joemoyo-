# OGX Render Kit

Reusable Ken Burns render for the OrigineX `_OGX_BATCH` pipeline — one command per
video, same locked house spec every time. This is the generalized version of the
per-video `build_*_kenburns.py` scripts (Aksum / Severus / Carthage / Meroe …).

## Setup (once)

- Machine needs **ffmpeg** and **ffprobe** on PATH, plus **Python 3**.
- Copy `render_ogx.py` and `run_render.bat` into your batch folder
  `C:\Users\Joe\Downloads\ORIGINEX CONTENT\_OGX_BATCH` (next to the
  `01_audio_inbox` / `02_images_inbox` / `03_finished_packs` folders).

## Render a video

```
python render_ogx.py 23_Kingdom_of_Meroe
```
or double-click / run:
```
run_render.bat 23_Kingdom_of_Meroe
```

Output → `03_finished_packs\23_Kingdom_of_Meroe\FINAL.mp4` (~40–60 min for a ~55-min
audio). **Resumable** — if it stops, re-run the same command; finished `.ts` chunks are
skipped. After a successful render it auto-updates `_pipeline_state.json` for that slug
(`render_status`, `final_video`, `render_completed_at`, `duration_seconds`).

## What it does automatically

- **Auto-discovers the audio** — the single `.m4a`/`.mp3`/`.wav` in
  `01_audio_inbox\<slug>\` (no hard-coded filename to edit per video).
- **Guards (refuses to render otherwise):** ≥ 15 numbered scene PNGs present, audio
  present. `THUMBNAIL.png` is excluded automatically (scene files must start with two
  digits, e.g. `01_scene.png`).
- **Verifies on finish:** ffprobe duration vs audio (warns if drift > 2s) + size report
  (flags if outside the usual ~400–600 MB band).

## Folder convention (every video)

```
_OGX_BATCH\
  01_audio_inbox\NN_Slug\        <- one .m4a (NotebookLM export)
  02_images_inbox\NN_Slug\       <- 01_scene.png ... 20_scene.png + THUMBNAIL.png
  03_finished_packs\NN_Slug\     <- FINAL.mp4 written here
  _TEMPLATES\OGX_BATCH_NN_Slug.pdf   <- audio prompt + the 20 image prompts
  _pipeline_state.json           <- canonical per-video status
  render_ogx.py  run_render.bat  <- this kit
```

## Locked render spec (do not change without a reason)

- 1920×1080, 30 fps, libx264, preset veryfast, CRF 28, maxrate 1500k, bufsize 3000k.
- Per-image duration = audio duration ÷ number of scene images.
- Ken Burns slow zoom-in: `zoompan=z='min(zoom+0.0008,1.15)'`.
- Audio AAC 192k, `-shortest`, `-movflags +faststart`.
- Per-scene `.ts` chunks, then **concat demuxer** (`-f concat -safe 0`) + mux — keeps it
  resumable and is path-safe for spaces and Windows drive letters.

## PRO / broadcast render (`render_ogx_pro.py`)

Broadcast-standard version (ogx-motion-sections spec). Same folders + audio, but:
- **Fast pacing** — each still becomes several **7–14s shots** with **A-to-B multi-move**
  framings (wide / detail / opposite-corner), not one slow 33s hold.
- **Unified cinematic grade** on every shot (contrast + colour-balance + vignette + film
  grain) so the AI stills read as one graded film.
- **Broadcast lower-third chyrons** — drop transparent 1920×1080 chyron PNGs in
  `02_images_inbox/<slug>/lowerthirds/` with a `cards.json`
  (`[{"file":"lt1.png","at":0.06,"dur":7}, ...]`, `at` = fraction of audio or seconds).
- **Sound-design sting** (58Hz sub + pink noise) under each chyron entry.

```
python render_ogx_pro.py 23_Kingdom_of_Meroe
```
Output → `03_finished_packs\<slug>\FINAL_PRO.mp4` (1080p, no music). Resumable per-shot `.ts`.
The 5 Meroë chyrons + `cards.json` are ready in the repo at `outputs/meroe/lowerthirds/` —
copy that folder to `02_images_inbox\23_Kingdom_of_Meroe\lowerthirds\`. Make chyrons for
other videos with `broadcast/make_lowerthirds.py` (needs Python `playwright` + a Chromium;
edit the `CARDS` list). No `lowerthirds/` folder → a clean graded film with no chyrons.

## Cadence

- **Tuesday = a PERSON, Thursday = a CIVILISATION**, both **15:00 UK**.

## After a successful render

1. `ffprobe FINAL.mp4` — duration within ~2s of the source audio.
2. Scrub a few points — image moving (slow zoom), audio in sync. Size ~400–600 MB.
3. Upload to YouTube with the metadata in the video's PUBLISH PACK (locked title +
   thumbnail `02_images_inbox\<slug>\THUMBNAIL.png`), set the schedule.
4. In Supabase (`content_ideas`, project `qvlllknedilztozxwscj`) set that video's row to
   `status = 'ready_to_publish'`.
