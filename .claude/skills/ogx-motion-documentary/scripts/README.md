# Reference implementation (Adwa 1896, v1.4)
This is working code from the Adwa build. It is Adwa-specific in places: the archive keys, the CREDITS table, the map boxes and battle arrows in render.py/geomap.py, the question/title lines in mix.py and timeline.py, and N-keys in motion_prompts.py. Copy the code into a new project folder and swap those bits for the new film.

| File | Role |
|---|---|
| script_v06.py | Script format: ACTS (line, vis, on-screen text), V2 second pictures, VOICE_SUBS |
| timeline.py | Script + split voice clips -> timeline.json (one shot per line, gaps, holds, second-picture cut) |
| geomap.py | Real relief/satellite map plates (AWS Terrain Tiles, Sentinel-2, Natural Earth) |
| render.py | timeline.json -> frames. Modes: `still t1 t2 ...` (preview JPEGs) and `range f0 f1 out.mp4` (segment) |
| render_all.sh | Resumable 32-segment render, 4 in parallel, `.ok` markers. Set N = total frames |
| mix.py | Voice bus + per-act score, ducking, two-pass master -14 LUFS |
| captions.py | EN-GB SRT from timeline words (rename the output per version) |
| finalize.sh | Concat + mux + 720p review + QC (rename versions inside first) |
| motion_prompts.py | Per-still motion lines + STYLE lock for Kling |
| put_batch.py | PUT stills to Higgsfield presigned URLs (only where the upload host is reachable) |
| split_patch.py | Split a multi-line patch take into per-line clips (Scribe words), uniform level match |
| patch_timeline.py | Patch timeline.json by shot: new VO lines, cuts, caption/picture swaps, map holds, renumber |
| split_chunk.py | Split a downloaded motion pack back into frame-exact per-still clips |

Expected project layout: `fonts/` (Cinzel, Lora, Lora-Italic), `archive/`, `ai/`, `geo/`, `music12/C00..C11.mp3`, `clips12/` (voice per line), `motion/clips/N*.mp4`, `parts/`, `preview/`.
