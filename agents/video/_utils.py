"""Shared helpers for the video crew agents."""

from __future__ import annotations

import json
import re


def extract_json(text: str) -> dict | list:
    """Pull the first JSON object/array out of an LLM response.

    Tolerates markdown fences and surrounding prose. Raises ValueError if no
    parseable JSON is found.
    """
    # Strip ```json ... ``` fences if present.
    fenced = re.search(r"```(?:json)?\s*(.+?)```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else text

    # Try the whole candidate first.
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    # Fall back to the widest {...} or [...] span.
    for open_ch, close_ch in (("{", "}"), ("[", "]")):
        start = candidate.find(open_ch)
        end = candidate.rfind(close_ch)
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(candidate[start : end + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError("No parseable JSON found in model response.")


def slugify(text: str, max_len: int = 60) -> str:
    """Lowercase, hyphenated slug suitable for filenames and DB slugs."""
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:max_len].strip("-") or "untitled"
