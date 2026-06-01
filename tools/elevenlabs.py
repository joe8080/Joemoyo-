"""ElevenLabs text-to-speech — Joe's cloned voice for narration.

There is no ElevenLabs MCP connector, so we call the REST API directly.
Degrades gracefully (returns None) when ELEVENLABS_API_KEY / voice id are
unset, so the crew still runs in specs-only mode.

Docs: https://elevenlabs.io/docs/api-reference/text-to-speech
"""

from __future__ import annotations

import os

import requests

from config.settings import settings

_BASE = "https://api.elevenlabs.io/v1/text-to-speech"
_DEFAULT_MODEL = "eleven_multilingual_v2"


def is_configured() -> bool:
    return bool(settings.elevenlabs_api_key and settings.elevenlabs_voice_id)


def synthesize(
    text: str,
    out_path: str,
    *,
    voice_id: str | None = None,
    model_id: str = _DEFAULT_MODEL,
    stability: float = 0.5,
    similarity_boost: float = 0.75,
) -> str | None:
    """Synthesize narration to an mp3 at out_path. Returns the path, or None.

    Returns None (without raising) when ElevenLabs is not configured so the
    pipeline can continue and produce narration.txt only.
    """
    if not is_configured():
        return None

    vid = voice_id or settings.elevenlabs_voice_id
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    resp = requests.post(
        f"{_BASE}/{vid}",
        headers={
            "xi-api-key": settings.elevenlabs_api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        json={
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
            },
        },
        timeout=120,
    )
    resp.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(resp.content)
    return out_path
