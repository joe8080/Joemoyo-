#!/usr/bin/env bash
# Install VibeVoice and its dependencies into the current Python environment.
#
#   bash voice/setup.sh            # auto-detect hardware
#   bash voice/setup.sh --cpu      # force CPU-only torch (small download, slow inference)
#
# Safe to re-run: it updates the vendored checkout rather than recloning.
set -euo pipefail

VOICE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENDOR_DIR="$VOICE_DIR/vendor"
REPO_DIR="$VENDOR_DIR/VibeVoice"
# Microsoft withdrew the original repo in Sept 2025; this is the MIT-licensed
# community preservation fork of the same code.
REPO_URL="https://github.com/vibevoice-community/VibeVoice.git"

FORCE_CPU=0
[[ "${1:-}" == "--cpu" ]] && FORCE_CPU=1

echo "==> Checking hardware"
if [[ $FORCE_CPU -eq 0 ]] && command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true
    DEVICE="cuda"
elif [[ $FORCE_CPU -eq 0 ]] && [[ "$(uname -s)" == "Darwin" ]] && [[ "$(uname -m)" == "arm64" ]]; then
    echo "Apple Silicon detected — will use Metal (mps)"
    DEVICE="mps"
else
    echo "No NVIDIA GPU detected — installing for CPU."
    echo "WARNING: CPU inference is impractically slow for full episodes."
    echo "         Use voice/notebooks/VibeVoice_Colab.ipynb for a free GPU instead."
    DEVICE="cpu"
fi

echo
echo "==> Fetching VibeVoice source"
mkdir -p "$VENDOR_DIR"
if [[ -d "$REPO_DIR/.git" ]]; then
    git -C "$REPO_DIR" pull --ff-only
else
    git clone --depth 1 "$REPO_URL" "$REPO_DIR"
fi

echo
echo "==> Installing PyTorch"
if [[ "$DEVICE" == "cpu" ]]; then
    # The CPU-only wheels are a much smaller download, but some networks block
    # download.pytorch.org — fall back to the (larger) PyPI build if so.
    pip install --quiet torch torchaudio --index-url https://download.pytorch.org/whl/cpu \
        || pip install --quiet torch torchaudio
else
    pip install --quiet torch torchaudio
fi

echo
echo "==> Installing VibeVoice"
# transformers is pinned by upstream to 4.51.3; newer releases break the
# modelling code, so let pip resolve from the package metadata rather than
# forcing an upgrade here.
pip install --quiet -e "$REPO_DIR"

if [[ "$DEVICE" == "cuda" ]]; then
    echo
    echo "==> Installing flash-attn (optional speedup; failure is not fatal)"
    pip install --quiet flash-attn --no-build-isolation || \
        echo "flash-attn unavailable — generate.py will fall back to sdpa attention."
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
    echo
    echo "NOTE: ffmpeg is not installed. You need it for voice/prepare_voice.py."
    echo "      Ubuntu/Debian: sudo apt-get install -y ffmpeg"
    echo "      macOS:         brew install ffmpeg"
fi

cat <<EOF

==> Done. Device: $DEVICE

Next:
  1. Make your voice samples (15-25s of clean speech each):
       python voice/prepare_voice.py --input you.mp4  --name Joe  --gender man
       python voice/prepare_voice.py --input her.wav  --name Maya --gender woman

  2. Generate an episode:
       python voice/generate.py --script voice/scripts/example_2p.txt --voices Joe Maya

  3. Check a script's formatting without loading the model:
       python voice/generate.py --script yourscript.txt --voices Joe Maya --dry-run
EOF
