#!/bin/bash
# Render the film in chunks with retries, then join. Usage: ./render_chunks.sh <total_frames> [chunk]
set -u; TOTAL=$1; CH=${2:-1200}; mkdir -p out/chunks; : > out/chunks/list.txt; i=0; a=0
while [ $a -lt $TOTAL ]; do b=$((a+CH-1)); [ $b -ge $TOTAL ] && b=$((TOTAL-1)); f=out/chunks/c$(printf %03d $i).mp4; ok=0
  for try in 1 2 3; do FROM=$a TO=$b OUT=$f CONC=${CONC:-3} node render.mjs > out/chunks/log_$i.txt 2>&1 && ok=1 && break; echo "chunk $i try $try failed"; done
  [ $ok -eq 1 ] || { echo "CHUNK $i FAILED"; exit 1; }
  echo "file 'c$(printf %03d $i).mp4'" >> out/chunks/list.txt; echo "$(date -u +%T) chunk $i done ($a-$b)"; a=$((b+1)); i=$((i+1)); done
ffmpeg -v error -y -f concat -safe 0 -i out/chunks/list.txt -c copy out/dahomey_silent.mp4 && echo JOINED
