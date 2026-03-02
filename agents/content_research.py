"""
ContentResearchAgent: Researches historical topics for the YouTube channel.

Searches the web for facts, sources, and narrative angles, then structures
findings into a detailed research outline ready for the Script Writer.
"""

from agents.base_agent import BaseAgent
from prompts.research_prompts import RESEARCH_SYSTEM_PROMPT
from tools.web_search import web_search, format_search_results


class ContentResearchAgent(BaseAgent):

    @property
    def system_prompt(self) -> str:
        return RESEARCH_SYSTEM_PROMPT

    def _define_tools(self) -> list:
        return [
            {
                "name": "web_search",
                "description": (
                    "Search the web for historical information, primary sources, "
                    "academic references, and factual data about a topic."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query string",
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of results to return (default 8, max 15)",
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "search_academic_sources",
                "description": (
                    "Search specifically for academic papers, scholarly articles, "
                    "books, and peer-reviewed sources on a historical topic."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                    },
                    "required": ["query"],
                },
            },
        ]

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        if tool_name == "web_search":
            results = web_search(
                tool_input["query"],
                num_results=tool_input.get("num_results", 8),
            )
            return format_search_results(results)
        if tool_name == "search_academic_sources":
            academic_query = tool_input["query"] + " academic scholarly research peer-reviewed"
            results = web_search(academic_query, num_results=6)
            return format_search_results(results)
        return f"Unknown tool: {tool_name}"

    def research_topic(self, topic: str) -> dict:
        """
        Research a historical topic and return a structured outline.
        Returns: dict with 'topic' and 'research' keys.
        """
        prompt = f"""
Research the following historical topic thoroughly for a YouTube educational video:

TOPIC: {topic}

Research process:
1. Search for a general overview of the topic
2. Search for key events, dates, figures, and context
3. Find at least 3-5 credible sources
4. Search for lesser-known facts or surprising angles
5. Structure findings into a video outline:
   - Hook suggestion (attention-grabbing opening)
   - Background/context
   - Main narrative arc (3-5 key points with dates and sources)
   - Impact and legacy
   - Modern relevance or parallel
   - Sources to cite on screen
   - Suggested B-roll visuals

Output a detailed, structured research document in markdown.
"""
        result = self.run(prompt)
        safe_topic = topic.replace(" ", "_")[:40]
        self.save_output(result, "scripts", f"{safe_topic}_research_{self._timestamp()}.md")
        return {"topic": topic, "research": result}
