#!/bin/bash
# Render the film in chunks with retries; each chunk is re-encoded smaller as soon as it is done (keeps disk use low),
# and finished chunks are skipped on a re-run. Then join. Usage: ./render_chunks.sh <total_frames> [chunk]
set -u; TOTAL=$1; CH=${2:-1200}; mkdir -p out/chunks; : > out/chunks/list.txt; i=0; a=0
while [ $a -lt $TOTAL ]; do b=$((a+CH-1)); [ $b -ge $TOTAL ] && b=$((TOTAL-1)); n=$(printf %03d $i); f=out/chunks/c$n.mp4; t=out/chunks/t$n.mp4
  if [ ! -s $t ]; then
    if [ ! -s $f ]; then ok=0
      for try in 1 2 3; do FROM=$a TO=$b OUT=$f CONC=${CONC:-3} node render.mjs > out/chunks/log_$i.txt 2>&1 && ok=1 && break; echo "chunk $i try $try failed"; rm -f $f; done
      [ $ok -eq 1 ] || { echo "CHUNK $i FAILED"; exit 1; }
    fi
    ffmpeg -v error -y -i $f -an -c:v libx264 -preset medium -crf ${CRF:-22} -pix_fmt yuv420p -g 60 $t.tmp.mp4 && mv $t.tmp.mp4 $t && rm -f $f || { echo "ENCODE $i FAILED"; exit 1; }
  fi
  echo "file 't$n.mp4'" >> out/chunks/list.txt; echo "$(date -u +%T) chunk $i done ($a-$b) $(du -m $t | cut -f1)MB"; a=$((b+1)); i=$((i+1)); done
echo CHUNKS_DONE
