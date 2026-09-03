"""
Voice in and voice out.

Transcription: OpenAI Whisper when OPENAI_API_KEY is set, otherwise ElevenLabs
Scribe when ELEVENLABS_API_KEY is set. Speech: ElevenLabs text-to-speech when
both ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID are set. Without keys Jarvis
still works in text; voice notes get a polite "send text" reply.
"""
import requests

OPENAI_STT = "https://api.openai.com/v1/audio/transcriptions"
ELEVEN_STT = "https://api.elevenlabs.io/v1/speech-to-text"
ELEVEN_TTS = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

MAX_SPOKEN_CHARS = 1500


def transcribe(cfg, audio: bytes, filename: str = "voice.ogg", mime: str = "audio/ogg") -> str | None:
    """Return the transcript, or None if no transcription service is configured or it failed."""
    if not audio:
        return None
    if cfg.openai_api_key:
        try:
            r = requests.post(
                OPENAI_STT,
                headers={"Authorization": f"Bearer {cfg.openai_api_key}"},
                files={"file": (filename, audio, mime)},
                data={"model": "whisper-1", "language": "en"},
                timeout=90,
            )
            if r.ok:
                return (r.json().get("text") or "").strip()
            print(f"[voice] whisper failed {r.status_code}: {r.text[:200]}")
        except Exception as e:  # noqa: BLE001
            print(f"[voice] whisper error: {e}")
    if cfg.elevenlabs_api_key:
        try:
            r = requests.post(
                ELEVEN_STT,
                headers={"xi-api-key": cfg.elevenlabs_api_key},
                files={"file": (filename, audio, mime)},
                data={"model_id": "scribe_v1"},
                timeout=90,
            )
            if r.ok:
                return (r.json().get("text") or "").strip()
            print(f"[voice] scribe failed {r.status_code}: {r.text[:200]}")
        except Exception as e:  # noqa: BLE001
            print(f"[voice] scribe error: {e}")
    return None


def synthesize(cfg, text: str, max_chars: int = MAX_SPOKEN_CHARS) -> bytes | None:
    """Return MP3 bytes for `text`, or None when speech is not configured or failed."""
    if not cfg.can_speak or not (text or "").strip():
        return None
    spoken = text.strip()
    if len(spoken) > max_chars:
        spoken = spoken[:max_chars].rsplit(" ", 1)[0] + ". The rest is in the text above."
    try:
        r = requests.post(
            ELEVEN_TTS.format(voice_id=cfg.elevenlabs_voice_id),
            params={"output_format": "mp3_44100_128"},
            headers={
                "xi-api-key": cfg.elevenlabs_api_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },
            json={"text": spoken, "model_id": "eleven_flash_v2_5"},
            timeout=90,
        )
        if r.ok and r.content:
            return r.content
        print(f"[voice] tts failed {r.status_code}: {r.text[:200]}")
    except Exception as e:  # noqa: BLE001
        print(f"[voice] tts error: {e}")
    return None
