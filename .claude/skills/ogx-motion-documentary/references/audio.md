# Voice, music and mix

## Narration
- Voice: ElevenLabs **"joe afrian british 1"**, model `eleven_multilingual_v2`.
- Style: Joe's voice bible. Conversational British storyteller ("Have a look at this picture…"), short sentences, numbers written as words in the voice text.
- Record **one continuous take per act**, so tone stays consistent; splitting lines gives choppy delivery.
- Transcribe with Scribe (`creative_transcribe_audio`) to get word timings.
- Split each line at the quietest point in the pause between lines.
- Match the words to the script. Accept spelling variants (Wolayta, centre/center, numerals); anything else is a re-take.
- Pronunciation: put respellings in `VOICE_SUBS`, used in the voice prompt only. Examples: Wuchale → "Wuchalé", Mekelle → "Mekellay", OrigineX → "Origin-ex" (said OR-ih-jin-EX). Screen and captions keep the real spelling.
- To re-voice one line, trim the old take, re-generate just that line, and re-align it. Example: the v1.4 close was trimmed by 3.30 s to start at "If you think…", using ffmpeg `atrim`, with the words list shifted by the same amount.

## Score
- One instrumental cue per act from `eleven_music_v2_5`, with the instrumental flag on. Each act's mood is matched to its content. Adwa's 12 cues:
  - washint flute mystery (cold open);
  - pizzicato intrigue (treaty);
  - krar and masenqo court music;
  - kebero war drums;
  - action, then siege tension;
  - suspense;
  - stealthy night march;
  - full battle;
  - lament;
  - hope;
  - legacy;
  - resolving finale.
- Joe wanted variety: "mixed music, not one loop".
- Crossfade 2.5 s at act boundaries.
- A cue shorter than its act is slowed with pitch kept, at most 0.8×, but ideally generate it long enough.

## Mix (`scripts/mix.py`)
- **Voice bus:** sum every shot's `vo_file` at `vo_at`. Then:
  - high-pass at 75 Hz;
  - EQ −1.5 dB at 250 Hz and +1.5 dB at 3.5 kHz;
  - compressor at 2.5:1;
  - loudnorm to −16 LUFS.
- **Music:** each cue normalised to −19 LUFS, then −5 dB.
  - Duck −11 dB under the voice. Speech activity comes from the word timings, bridged over 0.35 s gaps, with 120 ms attack and 450 ms release.
  - Fade to silence under the question card.
  - Swell +4 dB on the title.
- **Master:** two-pass loudnorm to −14 LUFS / −1.5 dBTP, LRA ≤ 11. QC should read about −14.0 LUFS, peak ≤ −1.4.
