"""MotionGraphicsAgent: designs Remotion dynamic cards and motion overlays."""

from __future__ import annotations

from agents.base_agent import BaseAgent
from agents.video._utils import extract_json
from config.brand_profiles import BRAND_PROFILES
from prompts.video.crew_prompts import MOTION_GRAPHICS_SYSTEM_PROMPT


class MotionGraphicsAgent(BaseAgent):

    def __init__(self, channel: str = "history_channel"):
        self.channel = channel
        self.brand = BRAND_PROFILES[channel]
        super().__init__()

    @property
    def system_prompt(self) -> str:
        return MOTION_GRAPHICS_SYSTEM_PROMPT.format(
            channel_name=self.brand["name"],
            style=self.brand.get("style", "cinematic documentary"),
            cta=self.brand["cta"],
        )

    def _define_tools(self) -> list:
        return []

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return "No tools defined for this agent"

    def build_props(self, script: str, packaging: dict | None = None) -> dict:
        """Return Remotion props: intro, lower_thirds, stat_cards, quote_cards, outro."""
        title = ""
        if packaging and packaging.get("titles"):
            title = packaging["titles"][0]
        prompt = (
            f"Working title: {title}\n\n"
            "Design the motion-graphics overlays for this script. Place lower-thirds "
            "when a new person/place is introduced, stat cards on striking numbers, and "
            "quote cards on sourced quotations.\n\n---\n"
            f"{script}\n---"
        )
        return extract_json(self.run(prompt))
