"""
ScriptWriterAgent: Writes full YouTube scripts.

Takes a topic or research outline and produces a complete, production-ready
narration script with hooks, timestamps, B-roll cues, and CTAs.
Works for both the history channel and finance channel.
"""

from agents.base_agent import BaseAgent
from config.brand_profiles import BRAND_PROFILES
from prompts.script_prompts import SCRIPT_WRITER_SYSTEM_PROMPT


class ScriptWriterAgent(BaseAgent):

    def __init__(self, channel: str = "history_channel"):
        self.channel = channel
        self.brand = BRAND_PROFILES[channel]
        self.agent_id = "finance_script_writer" if channel == "finance_channel" else "history_script_writer"
        super().__init__()

    @property
    def system_prompt(self) -> str:
        return SCRIPT_WRITER_SYSTEM_PROMPT.format(
            channel_name=self.brand["name"],
            tone=self.brand["tone"],
            audience=self.brand["audience"],
            cta=self.brand["cta"],
        )

    def _define_tools(self) -> list:
        # Script writer works from provided research — no external tools needed
        return []

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return "No tools defined for this agent"

    def write_script(self, topic_or_research: str, target_minutes: int = 12) -> str:
        """
        Write a full YouTube script.

        Args:
            topic_or_research: Either a raw topic string or a detailed research outline
            target_minutes: Target video length in minutes (default 12)

        Returns: Complete script as a markdown string
        """
        target_words = target_minutes * 150  # ~150 words per minute of narration

        prompt = f"""
Write a complete YouTube script based on the following:

---
{topic_or_research}
---

Script requirements:
- Target length: {target_minutes} minutes (~{target_words} words of narration)
- Start with a STRONG hook in the first 15-30 seconds
- Use natural, spoken-word language — write for ears, not eyes
- Add [TIMESTAMP: XX:XX] markers every 2-3 minutes
- Include [B-ROLL: description] notes for visual suggestions
- Add [PAUSE] markers for dramatic effect at key moments
- Build narrative tension throughout
- End with emotional payoff + CTA: "{self.brand['cta']}"

Deliver the full script including:
TITLE: (SEO-optimized)
TAGS: (10 tags)
DESCRIPTION: (150-word YouTube description)
THUMBNAIL IDEA: (visual concept)
FULL SCRIPT: (complete word-for-word narration)
"""
        script = self.run(prompt)
        safe_channel = self.channel.replace("_", "-")
        self.save_output(script, "scripts", f"{safe_channel}_script_{self._timestamp()}.md")
        return script
