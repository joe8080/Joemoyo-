"""
Web search tool using the Brave Search API.
Falls back to a clear error message if no API key is configured.
"""

import requests
from config.settings import settings


def web_search(query: str, num_results: int = 8) -> list[dict]:
    """
    Search the web using Brave Search API.
    Returns a list of {title, url, snippet} dicts.

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
        }]

    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": settings.brave_api_key,
    }
    params = {"q": query, "count": num_results, "search_lang": "en"}

    response = requests.get(
        "https://api.search.brave.com/res/v1/web/search",
        headers=headers,
        params=params,
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()

    results = []
    for item in data.get("web", {}).get("results", []):
        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "snippet": item.get("description", ""),
        })
    return results


def format_search_results(results: list[dict]) -> str:
    """Format search results into readable text for Claude."""
    if not results:
        return "No search results found."
    lines = []
    for i, r in enumerate(results, 1):
        url_part = f" ({r['url']})" if r["url"] else ""
        lines.append(f"{i}. {r['title']}{url_part}\n   {r['snippet']}")
    return "\n\n".join(lines)
