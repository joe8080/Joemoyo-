"""
OGXPackagingAgent: thumbnail brief, title set, and the YouTube posting pack.

Scope boundary worth knowing: this agent produces the paste-ready thumbnail
generation prompt and the ranked title candidates. It does not call vidIQ —
image generation and title scoring live behind the vidIQ MCP tools, which the
`ogx-thumbnail-engine` skill drives interactively. The handoff is deliberate:
the pipeline gets you a complete, brand-locked brief for free, and you spend
vidIQ credits only on the concept you have already decided to ship.
"""

from agents.ogx_base import OGXAgent
from prompts.ogx_prompts import (
    OGX_EVIDENCE_RULES,
    OGX_HOUSE_STYLE,
    OGX_PACKAGING_SYSTEM_PROMPT,
)


class OGXPackagingAgent(OGXAgent):

    @property
    def system_prompt(self) -> str:
        palette = self.brand["palette"]
        return OGX_PACKAGING_SYSTEM_PROMPT.format(
            channel_name=self.brand["name"],
            evidence_rules=OGX_EVIDENCE_RULES,
            house_style=OGX_HOUSE_STYLE,
            gold=palette["gold"],
            dark=palette["dark"],
            crimson=palette["crimson"],
            amber=palette["amber"],
            teal=palette["teal"],
            white=palette["white"],
        )

    def _define_tools(self) -> list:
        # Titles and hooks carry the boldest claims in the whole package —
        # they need the tightest verification, not the loosest.
        return [self._verify_tool()]

    def package(self, topic: str, script_or_research: str = "",
                style: str = "archives") -> str:
        """Produce the full packaging pack for a topic."""
        references = "\n".join(f"  - {u}" for u in self.brand["thumbnail_references"])
        source = f"\n---\n{script_or_research}\n---\n" if script_or_research else ""

        stamp_note = (
            "\nThis is a DECLASSIFIED-style episode: the thumbnail carries a red "
            "rubber DECLASSIFIED stamp rotated ~12 degrees. Keep the stamp off "
            "the key words.\n"
            if style == "declassified" else ""
        )

        prompt = f"""
Package this {self.brand['name']} episode for publication.

TOPIC: {topic}
{source}
Deliver, in order:

1. THUMBNAIL BRIEF — a paste-ready generation prompt following the locked spec.
   State the dominant subject, the two-tier text (small gold SUBJECT · ERA
   label, plus a hook of four words or fewer), the single colour-pop and why
   that one, and the date badge. Pass these brand-anchor reference images with
   the generation:
{references}
   Then an art-pass checklist: anachronism risks in the props, whether this
   subject requires an archival photo rather than an AI face, and where the
   bottom-right logo space is protected.{stamp_note}
2. TITLES — three candidates, each with a concrete number or specific detail
   plus a reversal payoff, ~80 characters, hook front-loaded. Rank them with
   your reasoning. Name the winner and the A/B alternate. Flag that final
   scoring runs through vidIQ before publishing.

3. POSTING PACK — chaptered description with timestamps, 15 tags, hashtags,
   and the pinned first comment carrying the full source list with the database
   status of each source.

4. PUBLISH SLOT — apply the cadence: {self.brand['cadence']}.

5. VERIFICATION TABLE — every factual claim used in a title, hook, or
   description line, with its database status and source.
{self._evidence_reminder()}
"""
        pack = self.run(prompt)
        self._save(pack, topic, "posting_pack")
        return pack
