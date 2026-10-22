# Isandlwana v2 proof pipeline (zero credit)
1. `plate.py` builds the battlefield relief plate from AWS terrain tiles (z14) and Sentinel-2 (the v1.1 geo cache).
2. `flights.py O1 O11 B1` renders 3D terrain flights with `terrain3d.py`, a heightfield renderer.
3. `proof.py opening|battle` composites the picture (maps, archive, regraded Kling clips, testimony cards, transitions) and the mix (existing voice takes, existing cues, procedural SFX from `sfx.py`), loudness-normalised to −14 LUFS.

Paths point at the build machine's scratchpad. Media files aren't committed.
