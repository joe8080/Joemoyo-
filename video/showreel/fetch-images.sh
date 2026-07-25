#!/usr/bin/env bash
# Download the Higgsfield plates for the showreel.
#
# The authoring session ran behind an egress policy that blocks the Higgsfield
# CDN, so the plates were generated but never downloaded. Run this once on a
# machine with open network access, then `npm run render`.
#
#   ./fetch-images.sh
#
set -euo pipefail

cd "$(dirname "$0")/assets/images"

BASE=$(node -e "console.log(require('./manifest.json').base)")
KEYS=$(node -e "console.log(Object.keys(require('./manifest.json').images).join(' '))")

missing=0
for key in $KEYS; do
  file=$(node -e "console.log(require('./manifest.json').images['$key'])")
  if [ -f "$key.png" ]; then
    echo "  ✓ $key.png (already present)"
    continue
  fi
  echo "  → $key.png"
  if ! curl -fsS -o "$key.png" "$BASE$file"; then
    echo "    ✗ failed: $BASE$file"
    rm -f "$key.png"
    missing=$((missing + 1))
  fi
done

if [ "$missing" -gt 0 ]; then
  echo
  echo "$missing image(s) failed to download."
  echo "Higgsfield CDN links can expire — regenerate from the prompts in STORYBOARD.md,"
  echo "or pull them from your Higgsfield generation history."
  exit 1
fi

echo
echo "All plates downloaded. Next: npm run check && npm run render"
