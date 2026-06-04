"""Image generation — provider-pluggable, key-gated.

Generates a still from a text prompt and writes it to disk. Providers:
  - openai     : gpt-image-1 (https://platform.openai.com/docs/api-reference/images)
  - gemini     : Imagen / gemini image (Google AI Studio)
  - higgsfield : nano_banana_pro etc. (https://platform.higgsfield.ai) — async
                 submit/poll/download; the funded, proven path for this project.

Returns None (without raising) when the selected provider has no API key, so
the crew falls back to specs-only mode (prompts saved, no pixels).
"""

from __future__ import annotations

import base64
import os
import time

import requests

from config.settings import settings


def is_configured(provider: str | None = None) -> bool:
    provider = provider or settings.image_provider
    if provider == "openai":
        return bool(settings.openai_api_key)
    if provider == "gemini":
        return bool(settings.gemini_api_key)
    if provider == "higgsfield":
        return bool(settings.higgsfield_api_key and settings.higgsfield_secret)
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
    if provider == "higgsfield":
        return _higgsfield_image(prompt, out_path, size)
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


def _hf_headers() -> dict:
    return {
        "hf-api-key": settings.higgsfield_api_key,
        "hf-secret": settings.higgsfield_secret,
        "Content-Type": "application/json",
    }


def _higgsfield_image(prompt: str, out_path: str, size: str) -> str | None:
    """Higgsfield text-to-image: submit a job, poll the job-set, download the result.

    Mirrors the async contract of the Higgsfield platform API (submit returns a
    job-set whose status moves pending -> in_progress -> completed, at which point
    each result carries a CDN url). Endpoint host, model, and auth header names are
    all driven by config/env (HIGGSFIELD_*), so they can be corrected to match the
    exact account/API revision without touching code.
    """
    base = settings.higgsfield_base_url.rstrip("/")
    model = settings.higgsfield_model
    width, height = _parse_size(size)

    submit = requests.post(
        f"{base}/v1/text2image/{model}",
        headers=_hf_headers(),
        json={
            "params": {
                "prompt": prompt,
                "width_and_height": f"{width}x{height}",
                "aspect_ratio": _aspect_ratio(width, height),
                "quality": "1080p",
            }
        },
        timeout=60,
    )
    submit.raise_for_status()
    job_set_id = (submit.json() or {}).get("id")
    if not job_set_id:
        return None

    # Poll until the job-set completes (cap ~3 min).
    url = None
    for _ in range(60):
        time.sleep(3)
        poll = requests.get(
            f"{base}/v1/job-sets/{job_set_id}", headers=_hf_headers(), timeout=30
        )
        poll.raise_for_status()
        jobs = (poll.json() or {}).get("jobs", [])
        statuses = [j.get("status") for j in jobs]
        if jobs and all(s == "completed" for s in statuses):
            results = jobs[0].get("results") or {}
            url = results.get("raw", {}).get("url") or results.get("url")
            break
        if any(s in ("failed", "nsfw", "canceled") for s in statuses):
            return None
    if not url:
        return None

    img = requests.get(url, timeout=120)
    img.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(img.content)
    return out_path


def _parse_size(size: str) -> tuple[int, int]:
    try:
        w, h = size.lower().split("x")
        return int(w), int(h)
    except Exception:
        return 1536, 1024


def _aspect_ratio(width: int, height: int) -> str:
    ratios = {(16, 9): "16:9", (9, 16): "9:16", (1, 1): "1:1", (4, 3): "4:3", (3, 2): "3:2"}
    if height == 0:
        return "16:9"
    target = width / height
    best = min(ratios, key=lambda r: abs(r[0] / r[1] - target))
    return ratios[best]
