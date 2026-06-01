"""VoiceoverAgent: owns narration — clean spoken text + ElevenLabs synthesis."""

from __future__ import annotations

from agents.base_agent import BaseAgent
from config.brand_profiles import BRAND_PROFILES
from prompts.video.crew_prompts import VOICEOVER_SYSTEM_PROMPT


class VoiceoverAgent(BaseAgent):

    def __init__(self, channel: str = "history_channel"):
        self.channel = channel
        self.brand = BRAND_PROFILES[channel]
        super().__init__()

    @property
    def system_prompt(self) -> str:
        return VOICEOVER_SYSTEM_PROMPT.format(channel_name=self.brand["name"])

    def _define_tools(self) -> list:
        return []

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return "No tools defined for this agent"

    def prepare_narration(self, script: str) -> str:
        """Strip all non-spoken cues; return clean narration ready for TTS."""
        return self.run(f"Clean this script into spoken narration:\n\n---\n{script}\n---").strip()

    def synthesize(self, narration_text: str, out_path: str) -> str | None:
        """Render narration to an mp3 in Joe's ElevenLabs voice. Returns path or None."""
        from tools.elevenlabs import synthesize
        return synthesize(narration_text, out_path)
