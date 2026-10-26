# Pilot master: Arthur & Julian Ep 1–7 (9:16, 3:34)

`Arthur_and_Julian_Pilot_Ep1-7_master_9x16.mp4`: 720×1280, 24 fps, about -14.5 LUFS.

Order: Ep 1 → Ep 2 (lobby) → "48 Hours Later / The Truth" → Ep 2 (car) → Ep 3 → "The Next Day" → Ep 4 → Ep 5 → Ep 6 (reshot opening + original from the cut to Arthur at 9.67s) → "One Month Later" → Ep 7.

Fixes:
- Ep 6 phone: AI text "FUNDS FROIZEN" replaced with a tracked "FUNDS FROZEN" (frames 495–543, the thumb stays in front).
- Ep 7 phone: garbled notification replaced with a tracked "VICTOR — I can get you your empire back. Meet me." (frames 476–551).
- Music bed at 15% under everything. Sub-drop stings at 19.95s (Ep 1 blue eyes), 172.41s (FUNDS FROZEN) and 204.05s (Victor's message).

Rebuild: put the eight Higgsfield clips in `src/` (ep1, ep2, ep3, ep4, ep5, ep6, ep6fix, ep7 .mp4), then run
`python3 phone_fix.py ep6 src/ep6.mp4 ep6_fixed.mp4`, `python3 phone_fix.py ep7 src/ep7.mp4 ep7_fixed.mp4`, then `python3 build_master.py`.
