import os
import re
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


def _alpaca_env(name: str) -> str:
    """
    Read an Alpaca credential, tolerating common paste accidents: surrounding
    quotes/whitespace, or an entire TOML block ('KEY = "value"' lines, as used
    in Streamlit secrets) pasted into a single variable.
    """
    raw = os.environ.get(name, "").strip()
    if "ALPACA_API" in raw and "=" in raw:
        m = re.search(rf'{name}\s*=\s*["\']?([A-Za-z0-9]+)["\']?', raw)
        if m:
            return m.group(1)
        return ""  # a blob that doesn't contain this key is not a credential
    return raw.strip('"').strip("'").strip()


@dataclass
class Settings:
    anthropic_api_key: str
    brave_api_key: str
    shopify_shop_name: str
    shopify_access_token: str
    alpaca_api_key_id: str
    alpaca_api_secret_key: str
    alpaca_paper: bool
    output_dir: str

    # Brand names
    history_channel: str
    finance_channel: str
    music_studio: str
    shopify_store: str

    # Model config
    model: str = "claude-sonnet-4-6"
    max_tokens: int = 8096

    # "sdk" calls the Anthropic API and needs ANTHROPIC_API_KEY.
    # "claude_cli" shells out to the Claude Code CLI and needs no key —
    # it reuses whatever session you are already signed into.
    agent_backend: str = "sdk"


def get_settings() -> Settings:
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    backend = os.environ.get("AGENT_BACKEND", "sdk").strip().lower()
    # The CLI backend authenticates through the Claude Code session, so a
    # missing API key is expected there rather than a setup error.
    if not anthropic_key and backend != "claude_cli":
        raise EnvironmentError(
            "ANTHROPIC_API_KEY is not set. "
            "Copy .env.example to .env and add your key — or set "
            "AGENT_BACKEND=claude_cli to run through the Claude Code CLI "
            "with no API key at all."
        )
    return Settings(
        agent_backend=backend,
        model=os.environ.get("AGENT_MODEL", "claude-sonnet-4-6"),
        anthropic_api_key=anthropic_key,
        brave_api_key=os.environ.get("BRAVE_SEARCH_API_KEY", ""),
        shopify_shop_name=os.environ.get("SHOPIFY_SHOP_NAME", ""),
        shopify_access_token=os.environ.get("SHOPIFY_ACCESS_TOKEN", ""),
        alpaca_api_key_id=_alpaca_env("ALPACA_API_KEY_ID"),
        alpaca_api_secret_key=_alpaca_env("ALPACA_API_SECRET_KEY"),
        # Paper trading is the safe default. Set ALPACA_PAPER=false to go live.
        alpaca_paper=os.environ.get("ALPACA_PAPER", "true").lower() != "false",
        output_dir=os.environ.get("OUTPUT_DIR", "./outputs"),
        history_channel=os.environ.get("YOUTUBE_HISTORY_CHANNEL_NAME", "Chronicles of Time"),
        finance_channel=os.environ.get("YOUTUBE_FINANCE_CHANNEL_NAME", "Capital Edge"),
        music_studio=os.environ.get("MUSIC_STUDIO_NAME", "JoeMoyo Studios"),
        shopify_store=os.environ.get("SHOPIFY_STORE_NAME", "JoeMoyo Store"),
    )


settings = get_settings()
