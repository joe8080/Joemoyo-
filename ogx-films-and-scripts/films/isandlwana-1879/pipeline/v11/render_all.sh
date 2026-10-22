#!/bin/bash
# Resumable picture render: 32 segments, 4 at a time; a segment is redone unless its .ok marker exists.
cd "$(dirname "$0")"
N=8231; S=32; Q=$(( (N + S - 1) / S ))
for i in $(seq 0 $((S-1))); do
  a=$((i*Q)); b=$(( (i+1)*Q )); [ $b -gt $N ] && b=$N
  echo "$i $a $b"
done | xargs -P 4 -n 3 sh -c '[ -f parts/s$0.ok ] || { python3 render.py range $1 $2 parts/s$0.mp4 && touch parts/s$0.ok; }'
ls parts/*.ok | wc -l
