import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    anthropic_api_key: str
    brave_api_key: str
    shopify_shop_name: str
    shopify_access_token: str
    output_dir: str

    # Brand names
    history_channel: str
    finance_channel: str
    music_studio: str
    shopify_store: str

    # Model config
    model: str = "claude-sonnet-4-6"
    max_tokens: int = 8096
    # Max tool-use iterations per agent run (Factor 8: own your control flow).
    # Prevents runaway tool-calling loops and unbounded API cost.
    max_tool_iterations: int = 10


def get_settings() -> Settings:
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not anthropic_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY is not set. "
            "Copy .env.example to .env and add your key."
        )
    return Settings(
        anthropic_api_key=anthropic_key,
        brave_api_key=os.environ.get("BRAVE_SEARCH_API_KEY", ""),
        shopify_shop_name=os.environ.get("SHOPIFY_SHOP_NAME", ""),
        shopify_access_token=os.environ.get("SHOPIFY_ACCESS_TOKEN", ""),
        output_dir=os.environ.get("OUTPUT_DIR", "./outputs"),
        history_channel=os.environ.get("YOUTUBE_HISTORY_CHANNEL_NAME", "Chronicles of Time"),
        finance_channel=os.environ.get("YOUTUBE_FINANCE_CHANNEL_NAME", "Capital Edge"),
        music_studio=os.environ.get("MUSIC_STUDIO_NAME", "JoeMoyo Studios"),
        shopify_store=os.environ.get("SHOPIFY_STORE_NAME", "JoeMoyo Store"),
        max_tool_iterations=int(os.environ.get("MAX_TOOL_ITERATIONS", "10")),
    )


settings = get_settings()
