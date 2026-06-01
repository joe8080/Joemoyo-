"""VisualDirectorAgent: turns a script into an ordered shot list of image prompts."""

from __future__ import annotations

from agents.base_agent import BaseAgent
from agents.video._utils import extract_json
from config.brand_profiles import BRAND_PROFILES
from prompts.video.crew_prompts import VISUAL_DIRECTOR_SYSTEM_PROMPT


class VisualDirectorAgent(BaseAgent):

    def __init__(self, channel: str = "history_channel"):
        self.channel = channel
        self.brand = BRAND_PROFILES[channel]
        super().__init__()

    @property
    def system_prompt(self) -> str:
        return VISUAL_DIRECTOR_SYSTEM_PROMPT.format(
            channel_name=self.brand["name"],
            style=self.brand.get("style", "cinematic documentary"),
        )

    def _define_tools(self) -> list:
        return []

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return "No tools defined for this agent"

    def build_shotlist(self, script: str, target_minutes: float = 12) -> dict:
        """Return {'clips': [...]} — one image prompt per narration beat."""
        approx_shots = max(6, int(target_minutes * 60 / 9))  # ~1 shot / 9s
        prompt = (
            f"Build the shot list for this ~{target_minutes}-minute video. "
            f"Aim for about {approx_shots} shots.\n\n---\n{script}\n---"
        )
        data = extract_json(self.run(prompt))
        if isinstance(data, list):
            data = {"clips": data}
        # Normalise sequence numbering.
        for i, clip in enumerate(data.get("clips", []), start=1):
            clip.setdefault("sequence", i)
        return data
