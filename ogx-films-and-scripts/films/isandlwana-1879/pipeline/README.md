# Isandlwana 1879: editable project (v1.0)
This is the pipeline that built `OGX_Isandlwana_1879_v1.0`. It's the Adwa engine plus the Isandlwana content. Large media (voice WAVs, AI stills, Kling clips, maps as .npy, music, master MP4) is not in git. It lives in the build scratch folder and in the ElevenLabs flow and Higgsfield media (IDs in the session STATE notes).

Order:
1. `script_isa.py` → `split_isa.py`, which splits the act takes into lines using Scribe.
2. `timeline.py` → `timeline.json`.
3. `geo/fetch_tiles.py`, `geo/build_terrain.py`, `geo/pick_s2.py` + `geo/build_s2.py`. Set `FORCE_SCENE` to choose the scene.
4. `motion_prompts.py`, then Kling clips → `motion/split_chunk.py`.
5. `hyperframes/isa-*/index.html` → `npx hyperframes render --fps 24 --quality looks` → `motion/HF_title.mp4` and `motion/HF_question.mp4`. They need local fonts, `assets/gsap.min.js` (from `npm pack gsap@3.12.5`) and `assets/plate.jpg`.
6. `mix.py` → `mix_master.wav`; `captions.py` → SRT.
7. `render_all.sh` (32 resumable segments) → `finalize.sh`.
8. `thumbs.py` → the 2 thumbnail concepts.

The Natural Earth geojsons (10m/50m countries, rivers, lakes, land) aren't committed. Download them from naturalearthdata.com into `geo/`.
