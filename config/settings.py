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

    # Supabase — source of truth (ORIGINEX HUMAN ARCHIVES)
    supabase_url: str = ""
    supabase_service_key: str = ""
    supabase_project_id: str = ""
    supabase_storage_bucket: str = "video-assets"

    # Media generation
    image_provider: str = "openai"      # openai | gemini | higgsfield | firefly
    openai_api_key: str = ""
    gemini_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"   # 1536-dim, matches the archive
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""        # Joe's cloned voice

    # Video output
    video_output_dir: str = "./outputs/videos"

    # Model config
    model: str = "claude-sonnet-4-6"
    max_tokens: int = 8096


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
        # Supabase (ORIGINEX HUMAN ARCHIVES is project qvlllknedilztozxwscj)
        supabase_url=os.environ.get("SUPABASE_URL", ""),
        supabase_service_key=os.environ.get("SUPABASE_SERVICE_KEY", ""),
        supabase_project_id=os.environ.get("SUPABASE_PROJECT_ID", ""),
        supabase_storage_bucket=os.environ.get("SUPABASE_STORAGE_BUCKET", "video-assets"),
        # Media generation
        image_provider=os.environ.get("IMAGE_PROVIDER", "openai"),
        openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
        gemini_api_key=os.environ.get("GEMINI_API_KEY", ""),
        embedding_model=os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small"),
        elevenlabs_api_key=os.environ.get("ELEVENLABS_API_KEY", ""),
        elevenlabs_voice_id=os.environ.get("ELEVENLABS_VOICE_ID", ""),
        video_output_dir=os.environ.get("VIDEO_OUTPUT_DIR", "./outputs/videos"),
    )


settings = get_settings()
