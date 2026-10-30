#!/bin/sh
# v1.1: concat the v1.1 slices, mux the unchanged v1.0 master mix (same voice, same 4:46 timing), write the
# v1.1 REVIEW export and a 720p copy. Never overwrites; v1.0 files are not touched.
set -e
cd "$(dirname "$0")/.."
B=build/v1.1
OUT=deliverables/OGX_Nok_v1.1_REVIEW.mp4
[ -e "$OUT" ] && { echo "refusing to overwrite $OUT"; exit 1; }
mkdir -p $B/qa
ls $B/parts/slice_*.mp4 | sort | sed "s#^#file '$PWD/#; s#\$#'#" > $B/parts/concat.txt
ls $B/parts_qa/slice_*.mp4 | sort | sed "s#^#file '$PWD/#; s#\$#'#" > $B/parts_qa/concat.txt
ffmpeg -v error -y -f concat -safe 0 -i $B/parts/concat.txt -c copy $B/video_only.mp4
ffmpeg -v error -y -f concat -safe 0 -i $B/parts_qa/concat.txt -c copy $B/qa/proxy_overlays_off.mp4
ffmpeg -v error -i $B/video_only.mp4 -i audio/MASTER_mix.wav -map 0:v:0 -map 1:a:0 -c:v copy \
  -c:a aac -b:a 320k -ar 48000 -shortest -movflags +faststart "$OUT"
ffmpeg -v error -y -i "$OUT" -vf scale=1280:720 -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 160k \
  -movflags +faststart deliverables/OGX_Nok_v1.1_REVIEW_720p.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT"
