#!/usr/bin/env python3
"""
Extract narration from an OGX script into chunks ready for text-to-speech.

    python tools/extract_vo.py outputs/ogx/OGX_..._script_archives.md

Pulls every VO("…") block, groups them under their SCRIPT_HEAD chapter, and
splits each chapter into chunks small enough for one TTS call. Prints JSON.

Why chunk at all: a chapter runs 400-600 words, which is a long single render
and a single point of failure — one bad take means regenerating four minutes of
audio. Chunks also give the editor files that line up with scenes rather than
one monolithic chapter track. Splitting happens on VO-block boundaries only, so
a chunk never cuts a sentence mid-breath.
"""

import json
import re
import sys

# VO("…") blocks, allowing escaped quotes and newlines inside.
_VO = re.compile(r'VO\("(.*?)"\)\s*$', re.DOTALL | re.MULTILINE)
_HEAD = re.compile(r'SCRIPT_HEAD\("([^"]*)"\)')

MAX_WORDS = 180  # ~80 seconds at the channel's narration pace


def _slug(text: str) -> str:
    out = "".join(c.lower() if c.isalnum() else "-" for c in text)
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-")[:40]


def extract(markdown: str) -> list[dict]:
    """Return [{chapter, title, chunk, words, text}] in reading order."""
    # Split the document at chapter headings, keeping each heading with its body.
    parts = _HEAD.split(markdown)
    # parts = [preamble, title1, body1, title2, body2, ...]
    sections = [("PREAMBLE", parts[0])] if parts[0].strip() else []
    sections += list(zip(parts[1::2], parts[2::2]))

    chunks = []
    for chapter_index, (title, body) in enumerate(sections):
        blocks = [" ".join(m.strip().split()) for m in _VO.findall(body)]
        blocks = [b for b in blocks if b]
        if not blocks:
            continue

        # Pack whole VO blocks up to the word ceiling.
        current: list[str] = []
        current_words = 0
        packed: list[list[str]] = []
        for block in blocks:
            words = len(block.split())
            if current and current_words + words > MAX_WORDS:
                packed.append(current)
                current, current_words = [], 0
            current.append(block)
            current_words += words
        if current:
            packed.append(current)

        clean_title = title.split("|")[0].strip()
        for chunk_index, group in enumerate(packed, 1):
            text = " ".join(group)
            chunks.append({
                "chapter": chapter_index,
                "title": clean_title,
                "slug": _slug(clean_title),
                "chunk": chunk_index,
                "of": len(packed),
                "words": len(text.split()),
                "blocks": len(group),
                "text": text,
            })
    return chunks


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: extract_vo.py <script.md>")
    with open(sys.argv[1], encoding="utf-8") as f:
        chunks = extract(f.read())

    total = sum(c["words"] for c in chunks)
    print(json.dumps({
        "chunks": chunks,
        "totals": {
            "chunks": len(chunks),
            "words": total,
            "estimated_minutes": round(total / 130, 1),
        },
    }, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
