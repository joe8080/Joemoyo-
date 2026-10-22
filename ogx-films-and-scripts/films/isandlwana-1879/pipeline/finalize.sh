#!/bin/bash
# Concat picture parts, mux the master mix, QC, and make a 720p review copy.
set -e
cd "$(dirname "$0")"
for i in $(seq 0 31); do echo "file 's$i.mp4'"; done > parts/concat.txt
ffmpeg -v error -y -f concat -safe 0 -i parts/concat.txt -c copy picture.mp4
ffmpeg -v error -y -i picture.mp4 -i mix_master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -ar 48000 \
  -shortest -movflags +faststart OGX_Isandlwana_1879_v1.0.mp4
ffmpeg -v error -y -i OGX_Isandlwana_1879_v1.0.mp4 -vf scale=1280:720 -c:v libx264 -preset medium -crf 25 \
  -c:a aac -b:a 160k -movflags +faststart OGX_Isandlwana_1879_v1.0_720p_review.mp4
echo "--- streams"
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,sample_rate:format=duration,size -of compact OGX_Isandlwana_1879_v1.0.mp4
echo "--- black frames (>0.5 s)"
ffmpeg -i OGX_Isandlwana_1879_v1.0.mp4 -vf blackdetect=d=0.5:pix_th=0.06 -an -f null - 2>&1 | grep blackdetect || echo none
echo "--- loudness"
ffmpeg -i OGX_Isandlwana_1879_v1.0.mp4 -af ebur128=peak=true -vn -f null - 2>&1 | grep -A14 Summary | grep -E "I:|LRA:|Peak:"
md5sum OGX_Isandlwana_1879_v1.0.mp4 OGX_Isandlwana_1879_v1.0_720p_review.mp4
ls -la OGX_Isandlwana_1879_v1.0*.mp4
