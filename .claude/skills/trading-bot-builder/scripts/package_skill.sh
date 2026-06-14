#!/usr/bin/env bash
# Package the skill into a standalone, shareable/sellable zip.
# Usage: bash scripts/package_skill.sh  (run from the skill folder or repo root)
set -euo pipefail

# Resolve the skill root (the folder containing SKILL.md), regardless of cwd.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
NAME="trading-bot-builder-skill"
OUT_DIR="$SKILL_DIR/dist"
STAGE="$OUT_DIR/$NAME"

rm -rf "$STAGE" "$OUT_DIR/$NAME.zip"
mkdir -p "$STAGE"

# Copy everything except build output and caches.
cp -r "$SKILL_DIR/SKILL.md" "$SKILL_DIR/README.md" "$SKILL_DIR/LICENSE.md" \
      "$SKILL_DIR/NOTICE.md" "$SKILL_DIR/references" "$SKILL_DIR/assets" "$STAGE/"
find "$STAGE" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
find "$STAGE" -name '*.pyc' -delete 2>/dev/null || true

# Safety: refuse to package if any credential-looking VALUE slipped in.
# (Matches real Alpaca key ids, JWT/service keys, sb_secret_ keys, PEM blocks —
# NOT the legitimate Postgres role name "service_role" used in the migration.)
SECRET_RE='PK[A-Z0-9]{18,}|sb_secret_[A-Za-z0-9]|eyJ[A-Za-z0-9_-]{24,}|-----BEGIN'
if grep -rEq "$SECRET_RE" "$STAGE"; then
  echo "ERROR: possible secret found in staged files — aborting." >&2
  grep -rEin "$SECRET_RE" "$STAGE" >&2 || true
  exit 1
fi

( cd "$OUT_DIR" && zip -rq "$NAME.zip" "$NAME" )
echo "Packaged: $OUT_DIR/$NAME.zip"
echo "Contents:"
( cd "$STAGE" && find . -type f | sort | sed 's/^/  /' )
