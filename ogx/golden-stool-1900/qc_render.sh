#!/usr/bin/env bash
# Automated technical QC for a rendered master and its 720p review copy.
#   ./qc_render.sh master.mp4 review_720p.mp4 [captions.srt] > qc_auto.md
# This covers integrity, loudness, clipping, black/frozen frames and silence
# only. It is NOT a watch-and-listen pass: pronunciation, caption accuracy,
# visual claims, map labels, credits and readability still need a human
# full playback, logged separately in the QC report with timecodes.
set -euo pipefail
MASTER="$1"; REVIEW="$2"; SRT="${3:-}"

probe() { ffprobe -v error -show_entries "$2" -of default=nw=1:nk=1 "$1"; }

echo "# Automated QC — $(date -u '+%Y-%m-%d %H:%M UTC')"
for f in "$MASTER" "$REVIEW"; do
  echo; echo "## $(basename "$f")"
  echo "- sha256: \`$(sha256sum "$f" | cut -d' ' -f1)\`  md5: \`$(md5sum "$f" | cut -d' ' -f1)\`"
  echo "- duration: $(probe "$f" format=duration) s"
  echo "- video: $(ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,width,height,r_frame_rate,pix_fmt -of csv=p=0 "$f")"
  echo "- audio: $(ffprobe -v error -select_streams a:0 -show_entries stream=codec_name,sample_rate,channels -of csv=p=0 "$f")"
  errs=$(ffmpeg -v error -i "$f" -f null - 2>&1 | wc -l)
  echo "- full decode errors: $errs"
done

echo; echo "## Master audio"
loud=$(ffmpeg -hide_banner -nostats -i "$MASTER" -af ebur128=peak=true -f null - 2>&1 \
  | awk '/Summary:/{s=1} s&&/I:|LRA:|Peak:/{gsub(/^ +/,""); print}')
echo "$loud" | sed 's/^/- /'
peak=$(ffmpeg -hide_banner -nostats -i "$MASTER" -af astats=metadata=0 -f null - 2>&1 \
  | awk '/Overall/{o=1} o&&/Peak level dB/{print $NF; exit}')
echo "- sample peak: ${peak} dBFS"
python3 - "$loud" "$peak" <<'PY'
import re, sys
loud, peak = sys.argv[1], float(sys.argv[2])
i = float(re.search(r"I:\s+(-?[\d.]+)", loud).group(1))
tp = float(re.search(r"Peak:\s+(-?[\d.]+)", loud).group(1))
print(f"- loudness {i:.1f} LUFS vs -14 ±1 reference: {'OK' if abs(i + 14) <= 1 else 'CHECK'}")
print(f"- true peak {tp:.1f} dBTP vs <= -1.0: {'OK' if tp <= -1.0 else 'FAIL (clipping risk)'}")
print(f"- sample peak {peak:.1f} dBFS: {'OK' if peak < -0.1 else 'FAIL (at or over full scale)'}")
PY
echo "- silences > 2.0 s:"
ffmpeg -hide_banner -nostats -i "$MASTER" -af silencedetect=noise=-50dB:d=2 -f null - 2>&1 \
  | grep -o 'silence_start: [0-9.]*\|silence_duration: [0-9.]*' | paste - - | sed 's/^/  - /' || true

echo; echo "## Master picture"
echo "- black segments > 0.5 s:"
ffmpeg -hide_banner -nostats -i "$MASTER" -vf blackdetect=d=0.5:pix_th=0.10 -an -f null - 2>&1 \
  | grep -o 'black_start:[0-9.]* black_end:[0-9.]*' | sed 's/^/  - /' || true
echo "- frozen segments > 8 s (stills with no motion; expected for held cards, check each):"
ffmpeg -hide_banner -nostats -i "$MASTER" -vf freezedetect=n=0.001:d=8 -an -f null - 2>&1 \
  | grep -o 'freeze_start: [0-9.]*\|freeze_end: [0-9.]*' | paste - - | sed 's/^/  - /' || true

m=$(probe "$MASTER" format=duration); r=$(probe "$REVIEW" format=duration)
echo; echo "## Copies match"
python3 -c "import sys; d=abs($m-$r); print(f'- duration difference master vs 720p: {d:.3f} s', '(OK)' if d<0.1 else '(CHECK)')"

if [ -n "$SRT" ]; then
  echo; echo "## Captions"
  last=$(grep -E '^[0-9:,]+ --> ' "$SRT" | tail -1 | awk '{print $3}')
  echo "- cues: $(grep -cE '^[0-9:,]+ --> ' "$SRT"); last cue ends $last (master ends ${m} s)"
fi
