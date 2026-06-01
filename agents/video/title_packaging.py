"""TitlePackagingAgent: owns titles, tags, description, chapters, thumbnail headline."""

from __future__ import annotations

from agents.base_agent import BaseAgent
from agents.video._utils import extract_json
from config.brand_profiles import BRAND_PROFILES
from prompts.video.crew_prompts import TITLE_PACKAGING_SYSTEM_PROMPT


class TitlePackagingAgent(BaseAgent):

    def __init__(self, channel: str = "history_channel"):
        self.channel = channel
        self.brand = BRAND_PROFILES[channel]
        super().__init__()

    @property
    def system_prompt(self) -> str:
        return TITLE_PACKAGING_SYSTEM_PROMPT.format(
            channel_name=self.brand["name"],
            tone=self.brand["tone"],
            audience=self.brand["audience"],
            cta=self.brand["cta"],
        )

    def _define_tools(self) -> list:
        return []

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return "No tools defined for this agent"

    def create_packaging(self, script_or_research: str) -> dict:
        """Return a structured packaging dict (titles/tags/description/chapters)."""
        prompt = (
            "Create the full packaging for this video. Base the chapters on the "
            "script's structure and timing.\n\n---\n"
            f"{script_or_research}\n---"
        )
        data = extract_json(self.run(prompt))
        return data
