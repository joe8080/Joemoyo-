"""
FinancialContentAgent: Generates content for the investment YouTube channel.

Researches financial topics, market trends, and investment strategies.
Produces video outlines, script-ready analysis, and content ideas.
"""

from agents.base_agent import BaseAgent
from config.brand_profiles import BRAND_PROFILES
from prompts.financial_prompts import FINANCIAL_SYSTEM_PROMPT
from tools.web_search import web_search, format_search_results


class FinancialContentAgent(BaseAgent):

    @property
    def system_prompt(self) -> str:
        brand = BRAND_PROFILES["finance_channel"]
        return FINANCIAL_SYSTEM_PROMPT.format(
            channel_name=brand["name"],
            tone=brand["tone"],
            audience=brand["audience"],
        )

    def _define_tools(self) -> list:
        return [
            {
                "name": "search_financial_news",
                "description": (
                    "Search for current financial news, market data, earnings reports, "
                    "and investment analysis."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The financial search query",
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "search_market_data",
                "description": "Search for specific stock, crypto, or market data and statistics.",
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
        if tool_name == "search_financial_news":
            query = tool_input["query"] + " financial news 2025"
            results = web_search(query, num_results=8)
            return format_search_results(results)
        if tool_name == "search_market_data":
            query = tool_input["query"] + " market data statistics analysis"
            results = web_search(query, num_results=6)
            return format_search_results(results)
        return f"Unknown tool: {tool_name}"

    def analyze_topic(self, topic: str) -> str:
        """
        Research and analyze a financial topic for a YouTube video.
        Returns a complete analysis + script outline.
        """
        prompt = f"""
Conduct a thorough financial analysis of the following topic for a YouTube video:

TOPIC: {topic}

Research current news and data, then produce:

1. EXECUTIVE SUMMARY (3 bullets)
2. CURRENT STATE & CONTEXT
   - What is happening and why it matters now
   - Key data points and statistics (search for current numbers)
3. BULL CASE (reasons to be optimistic)
4. BEAR CASE (risks and downsides)
5. HISTORICAL COMPARISON (what does history tell us?)
6. WHAT THIS MEANS FOR RETAIL INVESTORS
7. VIDEO SCRIPT OUTLINE (12-15 minute video structure)
   - Hook idea
   - Section breakdown with key points
   - Data visualizations to include
   - CTA suggestion

DISCLAIMER: Include "This video is for educational purposes only and is not financial advice."
"""
        result = self.run(prompt)
        safe_topic = topic.replace(" ", "_")[:40]
        self.save_output(result, "scripts", f"finance_{safe_topic}_{self._timestamp()}.md")
        return result

    def generate_video_ideas(self, niche: str = "general investing", count: int = 10) -> str:
        """Generate a batch of YouTube video ideas for the finance channel."""
        brand = BRAND_PROFILES["finance_channel"]
        prompt = f"""
Generate {count} high-quality YouTube video ideas for {brand['name']}.
Focus area: {niche}

Research current financial trends and news to ensure ideas are timely.

For each idea provide:
- TITLE: (SEO-optimized, under 70 characters, click-worthy)
- HOOK: (One sentence that would make someone click)
- KEY POINTS: (3 bullets covering what the video addresses)
- SEARCH POTENTIAL: (High / Medium / Low)
- SPONSORSHIP FIT: (What type of brand would sponsor this?)

Sort ideas from highest to lowest search potential.
"""
        result = self.run(prompt)
        self.save_output(result, "scripts", f"finance_ideas_{self._timestamp()}.md")
        return result
