# PROOF_NOTES — OGX_Ishango_v1.2_PROOF.mp4 (ogx-ishango-1)

Built 31 Oct 2026 (UK) for Chief's REQUEST CHANGES on the v1.0 review (Follow-up 09). This is a PROOF clip, not a new cut. Nothing is published. v1.0 and v1.1 are frozen and untouched (hashes re-checked after the build, all unchanged).

## The file

| | |
|---|---|
| File | `work_proof/OGX_Ishango_v1.2_PROOF.mp4` (stays in this session; not in git) |
| Runtime | 87.32 s (1:27.3) |
| Picture | 1920×1080, 25 fps, H.264 |
| Audio | AAC 192k; −14.0 LUFS integrated, −1.3 dBTP |
| Size | 149,687,240 bytes |
| sha256 | `129b1575b9338ec9c2b0ab971ceca166d8b9f66a71aa1095555a4abbf7603ea3` |
| md5 | `b8a15ff28b3a696ff86f5639daba92b3` |
| Source | v1.1 natural cut, **33.66 s → 121.00 s** (lines L08–L24) |
| Credits used | 0 everywhere: OpenArt 0, ElevenLabs 0, Higgsfield 0, Canva 0, Eden 0 |

**Sound.** The proof reuses the v1.1 voice, music and ambience stems with no re-voicing and no word changes. The voice is cut at 119.62 s. That falls between L24's last word (119.50 s) and L25's first word (119.65 s), so it is a line boundary. Music and ambience run on to 121.0 s, then fade out over 1.6 s. The duck and the two-pass loudness settings are the same as v1.1.

**Picture.** L08 and L16–L24 were re-rendered; their changes are fixes (a), (b), (c) and (e) below. L09–L15 come from the same stills and settings as v1.1. The shot list is in `work_proof/shots.json` and the builder is `engine/proof.py`.

## Fix (a): the real photo is the object of record

- In v1.1, L16–L19 used AI bone stills (16, 17, 18, 19), which could pass for the real object. All four are removed from the proof. Those lines now show the real photo (Ishango_bone_(cropped).jpg):
  - **L16:** the whole object.
  - **L17:** the worn lower shaft.
  - **L18:** the quartz end.
  - **L19:** the notched middle of the shaft.
- The count shots (L20–L24) show the real photo beside the drawing. Their background is the same real photo, blurred. No generated imagery appears on any shot that shows or describes the bone.
- Every frame with the photo carries its credit line: "Joeykentin · Wikimedia Commons · CC BY-SA 4.0". **⚠ BY-SA is a review-only exception.** It is still pending Ernest, and the author name is still to be confirmed (Joeykentin vs "JhowieNitnek").
- AI stills remain only on the site, people and landscape lines (L09–L11, L13–L15). Each is labelled "Reconstruction (AI)" for the whole shot.
- The crops of the 891×1230 photo are enlarged about 2.5×. They are softer than the full view, but no detail is invented.

## Fix (b): animated map with labels (L08)

- The NASA Landsat image pushes in with a site marker. "DR Congo" fades in at 0.8 s, "Lake Edward" at 1.6 s and "Ishango" next to the marker at 2.6 s.
- The credit "NASA Landsat · Wikimedia Commons · Public domain" stays on screen throughout.
- The marker position is approximate, as in v1.0. Map labels were off in v1.0 (no map tags); Chief's fix (b) asks for these three, so these three only.

## Fix (c): guided notch count (L20–L24)

- **Layout.** The real photo sits on the left with a warm bracket along its notched shaft. The open-licence drawing of the columns sits on the right (Albert1ls · Wikimedia Commons · CC BY 2.5).
- **Timing.** The groups light up one at a time, each on the narrator's word. The number appears above its group and stays on screen, dimmed, once the next group lights. The sum appears on the spoken total.
- **Counts on screen.** Only the counts in the locked v0.3 script and the evidence pack:
  - L20: 168.
  - Side one: 11, 13, 17, 19 = 60.
  - Middle: 3, 6, 4, 8, 10, 5, 5, 7 = 48.
  - Other side: 11, 21, 19, 9 = 60.
  - L24: the middle "10" changes to "10 or 9?" on "could be a nine" (C09).
- **Order.** The groups light right to left, to match the narration order already used in v1.0/v1.1.
- **⚠ Deviation from the ruling.** Chief asked for the count on the real bone photo, one group at a time. The groups are counted on the drawing next to the photo instead. The bracket on the photo marks the notched shaft as a whole, not individual groups.
  - Reason: the pack (§5) says no open high-resolution image exists for counting the marks independently. It is also unknown which column faces the camera in this photo. Putting group boxes on the photo would invent positions we cannot support.
  - If Ernest can supply a licensed high-resolution image of all three faces (the museum's own, for example), the count can move onto the photo.

## Fix (d): repetition in the intro and the ending (proposal only, NOT applied)

Times are given for v1.1 natural, with the v1.0 time in brackets. Chief's 00:26–00:35 is the v1.0 L06–L07.

- **Intro/agenda.**
  - L06 "This is OrigineX, and this is the Ishango bone." runs 0:23.8–0:27.0 [v1.0 0:25.8–0:29.4].
  - L07 "Three questions. What is it… really tell us?" runs 0:27.0–0:33.7 [v1.0 0:29.4–0:37.5].
  - L07 restates the hook's questions (L04–L05).
  - **Proposed cut I-1 (recommended):** drop L07. The hook cuts from L06 straight to the map (L08). This saves 6.7 s and keeps the brand line.
  - **Alternative I-2:** drop L06 and L07 together, so the hook goes straight to the map. This saves 9.8 s and loses the spoken channel ident.
- **Ending recap.**
  - L41 "So, our three questions." runs 3:32.2–3:34.0 [v1.0 3:54.2–3:56.4].
  - L42 runs 3:34.0–3:42.9 [3:56.4–4:05.7].
  - L43 runs 3:42.9–3:51.8 [4:05.7–4:15.0].
  - L44 runs 3:51.8–4:02.2 [4:15.0–4:25.8].
  - L42 repeats the setup in L08–L16. L43 repeats L20–L24 and is the third time "168" is said (after L03 and L20).
  - **Proposed cut R-1 (recommended):** drop L41–L43, 3:32.2–3:51.8. This saves 19.6 s. The film goes from L40 (the Brooks & Smith dating) to L44 "And how much can they tell us? Less than we'd like… none is proven", then L45–L46.
  - **Alternative R-2:** drop L41–L44, 3:32.2–4:02.2. This saves 30.0 s, and L40 runs straight into L45 "What we do know is this."
- All of these cuts fall at line boundaries, so no re-voicing is needed.
- **Conflicts for Ernest/Chief to rule on:**
  1. Cutting L07 or L41 drops the house-standard "three questions" frame and its recap.
  2. With I-1 and R-1, v1.1 would run about 3:53.9, below the 4:30–5:30 target. v1.1 natural is already 4:20.

## Fix (e): excavation scenes (L09, L10)

**Option chosen: the name subtitles are removed.**
- "Hubert Damas" (L09) and "Jean de Heinzelin" (L10) no longer appear on the generated excavation stills. The narrator still says the names, as the locked script requires.
- Both shots keep "Reconstruction (AI)" for the whole shot.
- No name appears on any generated image anywhere in the proof.

## QA from rendered frames

| Check | Result |
|---|---|
| Runtime | 87.32 s (target 60–90 s): PASS |
| Loudness | −14.0 LUFS / −1.3 dBTP: PASS |
| Frozen frames (freezedetect, −50 dB, 2 s) | 0 |
| Credit read-back (OCR vs credits.md) | 15 of 16 PASS |

- **Credit read-back.** The single FAIL is the L08 NASA line. I checked the grab by eye and the text is exact: the OCR crop sits on map texture and clips the final letter. This is the same false fail found and cleared in v1.0. The count shots were checked on both credit lines.
- **Text inventory.** Two "unexpected" words were found, and both are OCR misreads of the credit lines ("dia", "loeykentin"). No other text appears.
- **Motion** (rendered matte, optical flow):
  - L09–L24: 16/16 PASS (FG travel ≥ 3%, FG/BG ≥ 2). The lowest is L10, at 3.09% and 3.1×.
  - L08: the flat map, logged as the documented MAP override, as in v1.0.
- **Reports:**
  - `qc/QA_REPORT_OGX_Ishango_v1.2_PROOF.md`
  - `qc/parallax_stats_v1.2_PROOF.csv`

## Delivery

No upload and no transfer of any kind. The Google Drive connector cannot take files from disk, as Chief stated. The file stays in this session.
