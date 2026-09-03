"""
Jarvis configuration. Everything is read from environment variables (or a
local .env file) so the same code runs on a laptop, in Docker, or on Railway.

Required: ANTHROPIC_API_KEY, TELEGRAM_BOT_TOKEN, SUPABASE_URL and
SUPABASE_SERVICE_KEY (the Vault). Every other integration switches itself on
when its key is present and degrades gracefully when it is not.
"""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip().strip('"').strip("'")


def _flag(name: str, default: bool) -> bool:
    raw = _env(name)
    if not raw:
        return default
    return raw.lower() not in ("0", "false", "no", "off")


@dataclass
class JarvisConfig:
    # Claude
    anthropic_api_key: str
    model: str
    effort: str
    max_tokens: int
    fallbacks: bool
    # The Vault (finance-chief Supabase project): identity, rules, holdings, decisions
    vault_url: str
    vault_key: str
    # OrigineX Human Archives Supabase project: citations, people, ideas, debates
    ogx_url: str
    ogx_key: str
    # Telegram front door
    telegram_token: str
    telegram_chat_id: str
    poll_timeout: int
    # Identity
    owner_key: str
    assistant_name: str
    # Voice
    openai_api_key: str
    elevenlabs_api_key: str
    elevenlabs_voice_id: str
    voice_replies: bool
    # Memory
    history_turns: int
    context_ttl_seconds: int

    @property
    def vault_enabled(self) -> bool:
        return bool(self.vault_url and self.vault_key)

    @property
    def ogx_enabled(self) -> bool:
        return bool(self.ogx_url and self.ogx_key)

    @property
    def can_transcribe(self) -> bool:
        return bool(self.openai_api_key or self.elevenlabs_api_key)

    @property
    def can_speak(self) -> bool:
        return bool(self.elevenlabs_api_key and self.elevenlabs_voice_id)


def load_config() -> JarvisConfig:
    return JarvisConfig(
        anthropic_api_key=_env("ANTHROPIC_API_KEY"),
        model=_env("JARVIS_MODEL", "claude-opus-5"),
        effort=_env("JARVIS_EFFORT", "high"),
        max_tokens=int(_env("JARVIS_MAX_TOKENS", "16000")),
        fallbacks=_flag("JARVIS_FALLBACKS", True),
        vault_url=_env("SUPABASE_URL").rstrip("/"),
        vault_key=_env("SUPABASE_SERVICE_KEY") or _env("SUPABASE_KEY"),
        ogx_url=_env("OGX_SUPABASE_URL").rstrip("/"),
        ogx_key=_env("OGX_SUPABASE_SERVICE_KEY") or _env("OGX_SUPABASE_KEY"),
        telegram_token=_env("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=_env("TELEGRAM_CHAT_ID"),
        poll_timeout=int(_env("TELEGRAM_POLL_TIMEOUT", "30")),
        owner_key=_env("JARVIS_OWNER_KEY"),
        assistant_name=_env("JARVIS_NAME", "Jarvis"),
        openai_api_key=_env("OPENAI_API_KEY"),
        elevenlabs_api_key=_env("ELEVENLABS_API_KEY"),
        elevenlabs_voice_id=_env("ELEVENLABS_VOICE_ID"),
        voice_replies=_flag("JARVIS_VOICE_REPLIES", True),
        history_turns=int(_env("JARVIS_HISTORY_TURNS", "20")),
        context_ttl_seconds=int(_env("JARVIS_CONTEXT_TTL", "600")),
    )
