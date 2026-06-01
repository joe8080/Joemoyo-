"""ThumbnailAgent: owns the thumbnail concept and image-generation prompt."""

from __future__ import annotations

from agents.base_agent import BaseAgent
from agents.video._utils import extract_json
from config.brand_profiles import BRAND_PROFILES
from prompts.video.crew_prompts import THUMBNAIL_SYSTEM_PROMPT


class ThumbnailAgent(BaseAgent):

    def __init__(self, channel: str = "history_channel"):
        self.channel = channel
        self.brand = BRAND_PROFILES[channel]
        super().__init__()

    @property
    def system_prompt(self) -> str:
        return THUMBNAIL_SYSTEM_PROMPT.format(
            channel_name=self.brand["name"],
            tone=self.brand["tone"],
            audience=self.brand["audience"],
            style=self.brand.get("style", "cinematic documentary"),
        )

    def _define_tools(self) -> list:
        return []

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return "No tools defined for this agent"

    def design(self, topic: str, script_excerpt: str = "") -> dict:
        """Return a thumbnail design dict including an image-gen prompt."""
        prompt = (
            f"Design the thumbnail for a video titled around: {topic}\n\n"
            "Use this script context for the visual concept:\n"
            f"---\n{script_excerpt[:2000]}\n---"
        )
        return extract_json(self.run(prompt))
