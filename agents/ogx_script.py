"""
OGXScriptWriterAgent: writes the OGX narration script.

Two locked styles:
  "archives"     — the default house style. Cinematic narrative arc, chapter
                   markup, SEO package. Used for biographies and civilisations.
  "declassified" — the receipts-documentary variant. Case-file cards built
                   around named declassified documents, the pattern card, and
                   the full timeline card.

Both keep the verify tool in hand while writing, so a claim that survives the
research stage but cannot be backed at sentence level still gets caught.
"""

from agents.ogx_base import OGXAgent
from prompts.ogx_prompts import (
    OGX_DECLASSIFIED_SYSTEM_PROMPT,
    OGX_EVIDENCE_RULES,
    OGX_HOUSE_STYLE,
    OGX_SCRIPT_SYSTEM_PROMPT,
)

STYLES = ("archives", "declassified")


class OGXScriptWriterAgent(OGXAgent):

    def __init__(self, style: str = "archives", allow_unverified: bool = False):
        if style not in STYLES:
            raise ValueError(f"style must be one of {STYLES}, got '{style}'")
        self.style = style
        super().__init__(allow_unverified=allow_unverified)

    @property
    def system_prompt(self) -> str:
        template = (
            OGX_DECLASSIFIED_SYSTEM_PROMPT if self.style == "declassified"
            else OGX_SCRIPT_SYSTEM_PROMPT
        )
        return template.format(
            channel_name=self.brand["name"],
            evidence_rules=OGX_EVIDENCE_RULES,
            house_style=OGX_HOUSE_STYLE,
        )

    def _define_tools(self) -> list:
        # The writer keeps the verify tool plus citations, so it can pull an
        # exact quote or page reference mid-sentence rather than paraphrasing.
        return [self._verify_tool(), self._citations_tool()]

    def write_script(self, topic_or_research: str, target_minutes: int = 0,
                     subject: str = "") -> str:
        """
        Write the full script from a topic or (preferably) a research dossier.

        target_minutes defaults to the style's natural length: 18 for archives,
        42 for a declassified receipts documentary.

        `subject` names the output file. Pass it whenever the first argument is
        a dossier rather than a topic — otherwise the filename is derived from
        the dossier's own heading and comes out as
        OGX_OGX_RESEARCH_DOSSIER__MANSA_MUSA_I_script_archives.md
        """
        if not target_minutes:
            target_minutes = 42 if self.style == "declassified" else 18
        target_words = target_minutes * 130  # ~130 wpm at OGX narration pace

        if self.style == "declassified":
            shape = """
Build it as declassified case files: cold open, then one case card per segment
with its named receipt, then the PATTERN card, then the FULL TIMELINE card,
then the outro. Every card needs a real document reference — archive, reference
number, date, declassification year. A card whose receipt you cannot name does
not get made; say so instead and move on.
"""
        else:
            shape = """
Build it on the cinematic narrative arc: cold open, stakes, tension, rhetorical
turn, context-before, main body chapters, identity reclamation, resistance,
modern legacy, CTA on a named next episode. Chapters of 400-600 words.
"""

        prompt = f"""
Write the full {self.brand['name']} script from the material below.

---
{topic_or_research}
---

Target length: {target_minutes} minutes (~{target_words} words of narration).
{shape}
Write for the ear, not the page. Vary sentence length deliberately and use
staccato only at the emotional peaks. Never repeat a paragraph.

The identity/suppression angle is mandatory — name explicitly what was erased
and by whom.
{self._evidence_reminder()}
End with the verification table: every factual claim in the script, its
database status, and its on-screen source.
"""
        script = self.run(prompt)
        self._save(script, subject or topic_or_research.split("\n")[0][:60],
                   f"script_{self.style}")
        return script
