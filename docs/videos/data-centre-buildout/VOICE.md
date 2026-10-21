# Voice
Chosen by Joe: "joe afrian british 1" (ElevenLabs voice_id FLcNu8oQgaYpRrmtMngB, generated voice, British narration). Same voice as Film 1.
Model: eleven_v4.
A 22.6 s test of an EARLIER cold open (different wording) was generated (381 credits, about 6p). The script has since been rewritten, so the test only proves the voice, not the final words.
Pace measured: 66 words in 22.6 s = 2.93 words/sec.
Full voiceover not generated yet. Next step: Joe approves the voice, then generate the full 782 words (about 4,900 characters, roughly 4,700 credits, about 77p; run estimate_only first).
Claude cannot hear audio. Joe must listen and approve before the render.
Other voices in the workspace: JOE+++ NEW VOICE (cloned) bvIvBjiaqkveYMoyPX3n; Joe (cloned) YzvaovVB78Ui2DlXEO6t; JoeAAA (cloned) orpTbR0qzZCLj7jr9tU9.

## Status 21 Oct 2026
Joe approved the voice. Full voiceover generated: audio/voiceover_v1.mp3, 268.5 s (4:28), 4,698 credits (about 77 cents). Flow: https://elevenlabs.io/app/flows/fxpm1Okfa52pCshiTUS8
Script at generation time = VOICEOVER.txt as committed. If the script changes, the audio must be regenerated.
End-to-end target 5:00 includes about 30 s of section cards and graphic holds.

## Film built 21 Oct 2026
Video v1: 1920x1080, 30 fps, 4:28, -14.3 LUFS (voice only, no music bed). Built from build/ in this folder. Rendered on the cloud machine (not the PC).

## v2 (21 Oct 2026, Remotion build)
- Voiceover v2 = v1 with the Question 1 paragraph re-recorded (same voice, +462 credits, about 8p) so it says "between one hundred and two hundred and twenty percent a year", matching the +221% bar. Spliced at the pause between paragraphs; audio/voiceover_v2.mp3 (4:29).
- Sound design is synthesised (audio/ stems not stored; remotion/audio/sound_design.py regenerates them): ambient bed that follows the colour script, UI sounds keyed to the visuals, ducked under the voice. Final mix -14.0 LUFS, peak -1.6 dBFS.
- Claude cannot hear audio. Listen to the bed and effects; if they are not to taste, the voice-only file is audio/voiceover_v2.mp3.
