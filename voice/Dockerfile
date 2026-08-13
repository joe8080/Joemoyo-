# Portable GPU image for the voice generator.
# Works on RunPod, Vast.ai, Lambda, or any host with an NVIDIA GPU + container toolkit.
#
#   docker build -t joemoyo-voice voice/
#   docker run --gpus all -v "$PWD/voice/voices:/app/voice/voices" \
#     -v "$PWD/voice/scripts:/app/voice/scripts" \
#     -v "$PWD/voice/outputs:/app/voice/outputs" \
#     -v hf-cache:/root/.cache/huggingface \
#     joemoyo-voice --script voice/scripts/example_2p.txt --voices Joe Maya
FROM pytorch/pytorch:2.4.0-cuda12.1-cudnn9-runtime

ENV PYTHONUNBUFFERED=1 \
    HF_HOME=/root/.cache/huggingface

RUN apt-get update && apt-get install -y --no-install-recommends \
        git ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Vendor VibeVoice in its own layer so application edits don't invalidate it.
RUN git clone --depth 1 https://github.com/vibevoice-community/VibeVoice.git \
        /app/voice/vendor/VibeVoice \
    && pip install --no-cache-dir -e /app/voice/vendor/VibeVoice

# Optional speedup. Build failures must not break the image.
RUN pip install --no-cache-dir flash-attn --no-build-isolation || \
    echo "flash-attn unavailable; falling back to sdpa attention"

COPY generate.py prepare_voice.py /app/voice/
COPY scripts /app/voice/scripts

# Model weights are ~3 GB (1.5B) and download on first run into the mounted
# HF cache, keeping the image itself small.
ENTRYPOINT ["python", "/app/voice/generate.py"]
CMD ["--help"]
