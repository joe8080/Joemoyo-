"""
OGXAgent: shared base for every OrigineX Human Archives agent.

Gives all four OGX agents the same evidence tools and the same brand profile,
so the database gate cannot be skipped by one stage of the pipeline and quietly
reintroduce an unchecked claim downstream.

The important behaviour here is how a database failure is reported to Claude.
tools/ogx_db.py raises on read failure rather than returning an empty list,
because "the query returned nothing" and "the database was unreachable" mean
opposite things to a researcher. This class converts a raised error into an
explicit DATABASE ERROR message that tells the agent NOT to read it as absence
of evidence — otherwise a network blip would silently downgrade every claim in
the script to "unsupported" and the agent would cheerfully cut real history.
"""

from agents.base_agent import BaseAgent
from config.brand_profiles import BRAND_PROFILES
from tools import ogx_db
from tools.ogx_db import OGXDatabaseError

_DB_ERROR_NOTICE = (
    "DATABASE ERROR — the OGX research database could not be read: {error}\n"
    "This is NOT evidence of absence. Do not treat this subject as unverified "
    "and do not cut claims because of it. Retry the tool once; if it fails "
    "again, continue and mark every affected claim as 'DB UNAVAILABLE — needs "
    "human verification' in your output."
)


class OGXAgent(BaseAgent):
    """Base for OGX agents. Subclasses still define their own system prompt."""

    def __init__(self, allow_unverified: bool = False):
        self.brand = BRAND_PROFILES["origine_x"]
        self.allow_unverified = allow_unverified
        super().__init__()

    # ---- tool definitions -------------------------------------------- #

    def _verify_tool(self) -> dict:
        return {
            "name": "ogx_verify_claim",
            "description": (
                "Check a claim against the OGX research database before writing "
                "it. Returns a verdict of supported / contested / unsupported "
                "with the backing records. Use the claim's SUBJECT as the term "
                "(a person, event, place, or civilisation name) — not a full "
                "sentence. Call this for every date, figure, quote, and "
                "document reference before it reaches the page."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "term": {
                        "type": "string",
                        "description": "Subject of the claim, e.g. 'Mansa Musa' or 'Katyn'",
                    },
                },
                "required": ["term"],
            },
        }

    def _search_tool(self) -> dict:
        return {
            "name": "ogx_db_search",
            "description": (
                "Search one entity type in the OGX research database. "
                "Search repeatedly with alternate names and slug variants — "
                "one query rarely surfaces everything on a subject."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "entity_type": {
                        "type": "string",
                        "enum": list(ogx_db.SEARCHABLE),
                        "description": "Which table to search",
                    },
                    "term": {"type": "string", "description": "Search term"},
                    "limit": {
                        "type": "integer",
                        "description": "Max rows to return (default 5)",
                    },
                },
                "required": ["entity_type", "term"],
            },
        }

    def _citations_tool(self) -> dict:
        return {
            "name": "ogx_db_citations",
            "description": (
                "Pull citations for a subject from the OGX database — author, "
                "title, year, page reference, quote, reliability. Verified "
                "citations only unless include_unverified is true."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "term": {"type": "string"},
                    "include_unverified": {
                        "type": "boolean",
                        "description": "Include citations not yet marked verified",
                    },
                },
                "required": ["term"],
            },
        }

    def _evidence_tool(self) -> dict:
        return {
            "name": "ogx_db_evidence",
            "description": (
                "Pull the disputed record for a subject: scholarly debates and "
                "oral/testimonial evidence with contestation flags. Everything "
                "returned here must be attributed on screen, never asserted."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "term": {"type": "string"},
                    "contested_only": {
                        "type": "boolean",
                        "description": "Return only claims flagged as contested",
                    },
                },
                "required": ["term"],
            },
        }

    def _ogx_db_tools(self) -> list:
        """The full evidence toolkit — used by the research agent."""
        return [
            self._search_tool(),
            self._citations_tool(),
            self._evidence_tool(),
            self._verify_tool(),
        ]

    # ---- tool execution ----------------------------------------------- #

    def _execute_ogx_tool(self, tool_name: str, tool_input: dict) -> str | None:
        """
        Run an OGX database tool. Returns None if the tool is not one of ours,
        so subclasses can chain their own tools after calling this.
        """
        try:
            if tool_name == "ogx_verify_claim":
                return ogx_db.format_verdict(ogx_db.verify_claim(tool_input["term"]))

            if tool_name == "ogx_db_search":
                entity_type = tool_input["entity_type"]
                rows = ogx_db.search(
                    entity_type,
                    tool_input["term"],
                    limit=tool_input.get("limit", 5),
                )
                return ogx_db.format_rows(entity_type, rows)

            if tool_name == "ogx_db_citations":
                rows = ogx_db.find_citations(
                    tool_input["term"],
                    verified_only=not tool_input.get("include_unverified", False),
                )
                return ogx_db.format_rows("citations", rows)

            if tool_name == "ogx_db_evidence":
                contested_only = tool_input.get("contested_only", False)
                debates = ogx_db.find_debates(tool_input["term"])
                oral = ogx_db.find_oral_evidence(
                    tool_input["term"], contested_only=contested_only
                )
                return (
                    ogx_db.format_rows("scholarly_debates", debates)
                    + "\n\n"
                    + ogx_db.format_rows("oral_evidence", oral)
                )
        except OGXDatabaseError as e:
            return _DB_ERROR_NOTICE.format(error=e)

        return None

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        result = self._execute_ogx_tool(tool_name, tool_input)
        if result is not None:
            return result
        return f"Unknown tool: {tool_name}"

    # ---- shared helpers ------------------------------------------------ #

    def _evidence_reminder(self) -> str:
        """Appended to every task prompt so the gate is restated at call time."""
        if self.allow_unverified:
            return (
                "\nNOTE: running in --allow-unverified mode. The research "
                "database is unavailable, so you are working from trained "
                "knowledge. Mark EVERY factual claim as 'UNVERIFIED — needs "
                "database check' and keep the claim count low.\n"
            )
        return (
            "\nBefore any factual claim reaches your output, check it with "
            "ogx_verify_claim. Cut or attribute anything the database does not "
            "support. State plainly where the record is thin.\n"
        )

    def _save(self, content: str, subject: str, suffix: str) -> str:
        safe = "".join(
            c if c.isalnum() or c in " -_" else "" for c in subject
        ).strip().replace(" ", "_")[:50]
        return self.save_output(content, "ogx", f"OGX_{safe}_{suffix}_{self._timestamp()}.md")
