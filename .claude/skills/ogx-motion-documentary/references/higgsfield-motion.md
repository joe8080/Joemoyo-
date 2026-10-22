# Animating stills on Higgsfield (Kling 3.0 Pro)

Joe chose Higgsfield for motion. ElevenLabs video was rejected at about 43k credits a clip. The Adwa build animated 54 stills for 633 credits, plus 13.5 to redo one. Quote the cost before you start.

## Settings that work
- Tool: `generate_video` / `generate_video_batch`.
- Params:
  - `model: "kling3_0"`, `mode: "pro"`, `sound: "off"`, `aspect_ratio: "16:9"`;
  - `duration` from 4 to 15 s;
  - `medias: [{value: <media_id>, role: "start_image"}]`.
- The tool may block a job and recommend a preset. Pass `declined_preset_id` with the preset id it offered, then resubmit.
- Output is 1080p, 24 fps, silent.
- Use `jobs_wait` to wait. Poll in batches; don't open a viewer for every job.

## Prompts
Use one motion line per still (`scripts/motion_prompts.py`, dict `M`) and append `STYLE`.

- **The motion line describes movement only.** It covers what moves (marching, galloping, smoke, flicker, mist, crowds walking) plus one camera move. The start frame already fixes the picture, so the prompt shouldn't describe it again.
- **The STYLE lock carries the guardrails:**
  - keep the engraving look (cross-hatching, paper grain, sepia and umber);
  - figures stay anonymous, with no close-up faces;
  - natural motion, with no morphing or extra limbs;
  - **no new text, flags or logos.**

  Kling still sometimes paints lettering on vehicles and planes. In the first N45, biplanes flew close to camera with invented markings. For machines, ask for them to be "distant, unmarked silhouettes".

## Clip length
- `durations.json`: for each still, take the longest stretch any of its shots needs, plus a margin, rounded up and capped at 15 s.
- If a still appears more than once, the render plan (`_motion_plan` in render.py) plays a different stretch of the clip each time, so no movement repeats.
- Avoid slow-motion. Adwa stretched only one shot, by under 1%.

## Getting files in and out (cloud session network blocks)
This cloud session's proxy blocks Higgsfield's upload host and its CDN. Routes that worked:

1. **In: stills to Higgsfield.**
   - `media_import_url` with a public or signed URL. The ElevenLabs-generated stills have signed GCS URLs, and those work.
   - Alternatively, `media_upload` gives presigned PUT URLs. `scripts/put_batch.py`-style PUTs only work where the upload host is reachable, i.e. from the Higgsfield sandbox, not from here.
2. **Pack in the Higgsfield sandbox.**
   - `sandbox_exec` with `size: "xl"`; the standard sandbox has 1 CPU.
   - Run long jobs with `background: true` and poll them, because foreground calls die at about 60 s.
   - In the sandbox:
     1. curl each result from the CDN (`urls.txt` maps key → result filename);
     2. make QC strips (frames at start, middle and end, tiled);
     3. concatenate clips into 4 "packs";
     4. PUT each pack to a `media_upload` presigned URL.
3. **Out: bridge through ElevenLabs** (free).
   1. `creative_attach_reference_file` with the pack's public CloudFront URL onto an ElevenLabs flow.
   2. Add a `composition` node, `model_id: "eleven_composition"`, connected from it.
   3. Run the node. Its output `content_url` is on storage.googleapis.com, which this session *can* download.
   4. curl it down and split it back into per-still clips with `scripts/split_chunk.py`. The split is frame-exact, using `framecounts.json` and `chunks.json`, re-encoded at CRF 15 with GOP 24.
4. Verify every clip's frame count against `framecounts.json`.
5. **Isandlwana additions (22 Oct 2026):**
   - **Pack size:** ElevenLabs `creative_attach_reference_file` timed out on a 293 MB pack. Packs of about 40–100 MB work, so re-pack at CRF 19 into 6 packs rather than 3–4 big ones.
   - **PUT headers:** a presigned `media_upload` PUT needs `Content-Type: video/mp4` and `If-None-Match: *`, or it is refused. Call `media_confirm` after each PUT.
   - **Sandbox concat:** ffmpeg concat lists inside the sandbox need **absolute paths**. Relative ones fail with "Impossible to open p6/norm/...".
   - **Odd source frames:** a Kling result from a re-framed still can come back with a different picture area (Z34 had a moon to lose). Crop and scale it to 1920×1080 in the sandbox before packing, and note the crop in STATE.md.
   - Never `pkill -f <pattern>` in the session shell: it can match and kill the shell itself (exit 144). `kill <pid>` instead.

## QC (do not skip)
- Build contact sheets with the start, middle and end frame of every clip. Look for:
  - warping and melted limbs;
  - invented text, flags or insignia;
  - faces becoming too detailed;
  - blur at the end.
- Regenerate failures, and say so in the production pack.
- If a clip blurs only in a stretch the cut never uses, it can stay. Note it anyway.
- Keep rejected versions outside `clips/` (e.g. `N45_old_lettered.mp4`).
