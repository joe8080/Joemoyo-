"""
Web search tool using the Brave Search API.
Falls back to a clear error message if no API key is configured.

API docs: https://api.search.brave.com/app/documentation/web-search/get-started
"""

import requests
from config.settings import settings

_BASE_URL = "https://api.search.brave.com/res/v1/web/search"
_MAX_COUNT = 20  # Brave API hard limit per request


def web_search(
    query: str,
    num_results: int = 10,
    freshness: str = "",
    country: str = "US",
    search_lang: str = "en",
) -> list[dict]:
    """
    Search the web using the Brave Search API.
    Returns a list of {title, url, snippet, extra_snippets} dicts.

    Args:
        query:       Search query (max 400 chars / 50 words).
        num_results: Number of results (1-20, API max is 20).
        freshness:   Filter by age — "" (any), "pd" (24h), "pw" (7d),
                     "pm" (31d), "py" (365d), or "YYYY-MM-DDtoYYYY-MM-DD".
        country:     2-letter country code for results (default "US").
        search_lang: Language code for results (default "en").

    Requires BRAVE_SEARCH_API_KEY in .env
    Get a free key at: https://api.search.brave.com
    """
    if not settings.brave_api_key:
        return [{
            "title": "Web Search Not Configured",
            "url": "",
            "snippet": (
                "BRAVE_SEARCH_API_KEY is not set in your .env file. "
                "Get a free key at https://api.search.brave.com and add it to .env. "
                "Claude will continue with its trained knowledge for this task."
            ),
            "extra_snippets": [],
        }]

    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": settings.brave_api_key,
    }

    params: dict = {
        "q": query[:400],
        "count": min(num_results, _MAX_COUNT),
        "country": country,
        "search_lang": search_lang,
        "safesearch": "moderate",
        "text_decorations": False,   # clean text — no bold/highlight markers
        "extra_snippets": True,      # up to 5 additional excerpts per result
        "spellcheck": True,
    }
    if freshness:
        params["freshness"] = freshness

    response = requests.get(_BASE_URL, headers=headers, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    results = []
    for item in data.get("web", {}).get("results", []):
        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "snippet": item.get("description", ""),
            "extra_snippets": item.get("extra_snippets", []),
        })
    return results


def format_search_results(results: list[dict]) -> str:
    """Format search results into readable text for Claude."""
    if not results:
        return "No search results found."
    lines = []
    for i, r in enumerate(results, 1):
        url_part = f" ({r['url']})" if r["url"] else ""
        entry = f"{i}. {r['title']}{url_part}\n   {r['snippet']}"
        extras = r.get("extra_snippets", [])
        if extras:
            entry += "\n   Additional context:\n" + "\n".join(f"   - {s}" for s in extras)
        lines.append(entry)
    return "\n\n".join(lines)
