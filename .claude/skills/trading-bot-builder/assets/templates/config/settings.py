"""
Configuration for the trading bot — loads credentials from the environment
(.env locally, or platform secrets in CI/Streamlit Cloud). No secrets live in
code. Paper trading is the default and the bot refuses live trading.
"""

import os
import re
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _alpaca_env(name: str) -> str:
    """
    Read a credential, tolerating common paste accidents: surrounding quotes or
    an entire `KEY = "value"` block (e.g. a Streamlit secrets blob) pasted into
    one variable. Prevents a malformed secret from being sent as an API header.
    """
    raw = os.environ.get(name, "").strip()
    if "ALPACA_API" in raw and "=" in raw:
        m = re.search(rf'{name}\s*=\s*["\']?([A-Za-z0-9]+)["\']?', raw)
        return m.group(1) if m else ""
    return raw.strip('"').strip("'").strip()


@dataclass
class Settings:
    alpaca_api_key_id: str
    alpaca_api_secret_key: str
    alpaca_paper: bool
    anthropic_api_key: str
    output_dir: str
    model: str = "claude-sonnet-4-6"
    max_tokens: int = 4096


def get_settings() -> Settings:
    return Settings(
        alpaca_api_key_id=_alpaca_env("ALPACA_API_KEY_ID"),
        alpaca_api_secret_key=_alpaca_env("ALPACA_API_SECRET_KEY"),
        # Paper is the safe default; set ALPACA_PAPER=false to go live (the bot
        # still hard-refuses live trading in this template).
        alpaca_paper=os.environ.get("ALPACA_PAPER", "true").lower() != "false",
        # Coach narrative is optional; "unused..." disables the LLM call cleanly.
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", "unused-no-coach"),
        output_dir=os.environ.get("OUTPUT_DIR", "./outputs"),
    )


settings = get_settings()
