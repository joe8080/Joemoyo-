#!/usr/bin/env bash
# Generate stand-in plates so the composition can be checked and rendered
# without the real Higgsfield images. Each plate is a brand-palette radial
# gradient labelled with its key, at the same 2752x1536 as the real plates.
#
# These are for verification only — run ./fetch-images.sh to replace them with
# the real photography before rendering a deliverable.
set -euo pipefail

cd "$(dirname "$0")/assets/images"
FONT=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf

# Near-black ground #1A1A2E
BR=26; BG=26; BB=46

# key:R:G:B — accent matches the act's controlled colour-pop
PLATES=(
  "open-goldleaf:201:168:76"     # gold   #C9A84C
  "close-converge:201:168:76"
  "hist-monolith:255:243:205"    # amber  #FFF3CD
  "hist-papyrus:255:243:205"
  "hist-mask:255:243:205"
  "hist-colonnade:255:243:205"
  "hist-relief-a:255:243:205"
  "hist-relief-b:255:243:205"
  "fin-chart-a:15:76:117"        # teal   #0F4C75
  "fin-chart-b:15:76:117"
  "fin-skyline:15:76:117"
  "fin-ribbons-a:15:76:117"
  "fin-ribbons-b:15:76:117"
  "mus-console-a:255:243:205"
  "mus-console-b:255:243:205"
  "mus-mic-a:255:243:205"
  "mus-mic-b:255:243:205"
  "mus-wave-a:255:243:205"
  "com-box-a:139:26:26"          # crimson #8B1A1A
  "com-box-b:139:26:26"
  "com-warehouse:139:26:26"
  "sys-server:15:76:117"
  "sys-nodes:15:76:117"
)

# Radial falloff, brightest just left of centre so the Ken Burns move has
# somewhere to travel.
T="clip(1-hypot((X-W*0.42)/(W*0.62),(Y-H*0.45)/(H*0.62)),0,1)"

for entry in "${PLATES[@]}"; do
  IFS=':' read -r key ar ag ab <<< "$entry"
  ffmpeg -y -loglevel error \
    -f lavfi -i "color=c=black:s=2752x1536" \
    -vf "geq=r='${BR}+(${T})*(${ar}-${BR})':g='${BG}+(${T})*(${ag}-${BG})':b='${BB}+(${T})*(${ab}-${BB})',drawtext=fontfile=${FONT}:text='${key}':fontcolor=white@0.6:fontsize=96:x=(w-text_w)/2:y=(h-text_h)/2,drawtext=fontfile=${FONT}:text='PLACEHOLDER':fontcolor=white@0.3:fontsize=44:x=(w-text_w)/2:y=(h/2)+96" \
    -frames:v 1 "${key}.png"
  echo "  ✓ ${key}.png"
done

echo
echo "Placeholder plates written. Replace with ./fetch-images.sh before a real render."
