"""
OGXVideoBuildAgent: turns a script into a shot-by-shot production build sheet.

Output is scene-numbered and paste-ready for an editor or an n8n/Invideo
pipeline: VO, image brief, motion direction, on-screen text, audio cues, and
the beat type for every scene.
"""

from agents.ogx_base import OGXAgent
from prompts.ogx_prompts import (
    OGX_EVIDENCE_RULES,
    OGX_HOUSE_STYLE,
    OGX_VIDEO_BUILD_SYSTEM_PROMPT,
)


class OGXVideoBuildAgent(OGXAgent):

    @property
    def system_prompt(self) -> str:
        return OGX_VIDEO_BUILD_SYSTEM_PROMPT.format(
            channel_name=self.brand["name"],
            evidence_rules=OGX_EVIDENCE_RULES,
            house_style=OGX_HOUSE_STYLE,
        )

    def _define_tools(self) -> list:
        # On-screen text and date badges carry claims too, so the build stage
        # keeps the verify tool rather than trusting the script blindly.
        return [self._verify_tool()]

    def build_sheet(self, script_or_topic: str, target_minutes: int = 18,
                    subject: str = "") -> str:
        """Produce the scene-by-scene build sheet."""
        palette = self.brand["palette"]

        prompt = f"""
Turn the material below into a production build sheet for {self.brand['name']}.

---
{script_or_topic}
---

Runtime target: {target_minutes} minutes.

Number every scene. For each: VO, IMAGE brief, MOTION, TEXT, AUDIO, BEAT — in
the exact format from your instructions. Image briefs must be paste-ready into
an image generator: subject, setting, lighting, palette, emotion.

Hold the visual identity: gold {palette['gold']} on near-black {palette['dark']},
one controlled colour-pop per sequence, archival texture over saturation.

Mark clearly:
- the ONE image held through the entire cold open
- every staccato run and its 1-1.5s flashes
- the identity reclamation scene number
- the 2-3 scenes that get an AI motion clip instead of a still
- any scene depicting a real modern person, which MUST use an archival image
  and never an AI-generated face
{self._evidence_reminder()}
End with EDIT NOTES: staccato beat timestamps, motion-clip placements, and the
archival-image shot list.
"""
        sheet = self.run(prompt)
        self._save(sheet, subject or script_or_topic.split("\n")[0][:60], "video_build")
        return sheet
