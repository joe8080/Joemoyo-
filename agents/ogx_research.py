"""
OGXResearchAgent: builds the evidence dossier every other OGX stage depends on.

Database first, web second. The database is the channel's evidence gate; the
web fills gaps it cannot cover and is labelled as such, because a web fact has
not passed that gate.
"""

from agents.ogx_base import OGXAgent
from prompts.ogx_prompts import OGX_RESEARCH_SYSTEM_PROMPT
from tools.web_search import web_search, format_search_results


class OGXResearchAgent(OGXAgent):

    @property
    def system_prompt(self) -> str:
        return OGX_RESEARCH_SYSTEM_PROMPT

    def _define_tools(self) -> list:
        tools = self._ogx_db_tools()
        tools += [
            {
                "name": "web_search",
                "description": (
                    "Search the web. Use ONLY after the database searches, to "
                    "fill gaps, find primary-source quotes, or find archival "
                    "imagery leads. Label everything found here as web-sourced "
                    "and therefore not database-verified."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "num_results": {
                            "type": "integer",
                            "description": "Number of results (default 8, max 15)",
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "search_academic_sources",
                "description": (
                    "Search specifically for academic papers, scholarly "
                    "articles, and peer-reviewed work on a topic."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            },
        ]
        return tools

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        result = self._execute_ogx_tool(tool_name, tool_input)
        if result is not None:
            return result

        if tool_name == "web_search":
            results = web_search(
                tool_input["query"],
                num_results=tool_input.get("num_results", 8),
            )
            return format_search_results(results)

        if tool_name == "search_academic_sources":
            query = tool_input["query"] + " academic scholarly peer-reviewed history"
            return format_search_results(web_search(query, num_results=6))

        return f"Unknown tool: {tool_name}"

    def _cli_allowed_tools(self) -> tuple[str, ...]:
        # Claude Code's own web tools stand in for the Brave search tool, so
        # the research agent keeps both halves of its method in CLI mode.
        return super()._cli_allowed_tools() + ("WebSearch", "WebFetch")

    def research_topic(self, topic: str) -> dict:
        """
        Build a full OGX research dossier for a topic.
        Returns: dict with 'topic', 'research', and 'path'.
        """
        prompt = f"""
Build the OGX research dossier for this topic:

TOPIC: {topic}

Work through the research method in order — database searches first (people,
events, places, civilizations, documents, themes), then citations, then the
contested record, then a check of content_ideas for existing work on this
subject, and only then the web for gaps and primary-source quotes.

Search the database more than once. Try the subject's alternate names and slug
variants; a single query rarely surfaces everything.

Produce the full dossier in markdown, including the evidence summary table, the
contested claims section, the identity/suppression angle, the sources
bibliography, and an explicit list of gaps for a human to chase.
{self._evidence_reminder()}
"""
        dossier = self.run(prompt)
        path = self._save(dossier, topic, "research")
        return {"topic": topic, "research": dossier, "path": path}
