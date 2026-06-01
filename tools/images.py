"""Image generation — provider-pluggable, key-gated.

Generates a still from a text prompt and writes it to disk. Providers:
  - openai  : gpt-image-1 (https://platform.openai.com/docs/api-reference/images)
  - gemini  : Imagen / gemini image (Google AI Studio)

Returns None (without raising) when the selected provider has no API key, so
the crew falls back to specs-only mode (prompts saved, no pixels).
"""

from __future__ import annotations

import base64
import os

import requests

from config.settings import settings


def is_configured(provider: str | None = None) -> bool:
    provider = provider or settings.image_provider
    if provider == "openai":
        return bool(settings.openai_api_key)
    if provider == "gemini":
        return bool(settings.gemini_api_key)
    return False


def generate_image(
    prompt: str,
    out_path: str,
    *,
    size: str = "1536x1024",       # 16:9-ish for video stills
    provider: str | None = None,
) -> str | None:
    """Generate one image and save to out_path. Returns the path, or None."""
    provider = provider or settings.image_provider
    if not is_configured(provider):
        return None
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    if provider == "openai":
        return _openai_image(prompt, out_path, size)
    if provider == "gemini":
        return _gemini_image(prompt, out_path)
    return None


def _openai_image(prompt: str, out_path: str, size: str) -> str | None:
    resp = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        },
        json={"model": "gpt-image-1", "prompt": prompt, "size": size, "n": 1},
        timeout=180,
    )
    resp.raise_for_status()
    b64 = resp.json()["data"][0]["b64_json"]
    with open(out_path, "wb") as f:
        f.write(base64.b64decode(b64))
    return out_path


def _gemini_image(prompt: str, out_path: str) -> str | None:
    model = "imagen-3.0-generate-002"
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:predict"
        f"?key={settings.gemini_api_key}"
    )
    resp = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        json={"instances": [{"prompt": prompt}], "parameters": {"sampleCount": 1}},
        timeout=180,
    )
    resp.raise_for_status()
    preds = resp.json().get("predictions", [])
    if not preds:
        return None
    b64 = preds[0].get("bytesBase64Encoded")
    if not b64:
        return None
    with open(out_path, "wb") as f:
        f.write(base64.b64decode(b64))
    return out_path
