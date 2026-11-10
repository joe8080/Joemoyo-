#!/usr/bin/env bash
# Trim ElevenLabs takes without clipping word endings, slow slightly (Joe: default pace too fast), mono 48k.
# Usage: put raw takes as raw/<ID>.mp3 (P01..P11) then: bash process_vo.sh
cd "$(dirname "$0")"; mkdir -p proc
for f in raw/*.mp3; do b=$(basename "$f" .mp3)
  ffmpeg -v error -y -i "$f" -af "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.05,areverse,silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.12,areverse,atempo=0.90,aresample=48000" -ac 1 "proc/$b.wav"
done; python3 measure_pauses.py
