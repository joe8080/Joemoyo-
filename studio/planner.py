"""Turns a script into scenes (one voiceover job each) and shots (one picture each)."""

import re

from studio import StudioError

_FULL_SCRIPT = re.compile(r"^\W*full script\W*$", re.I)
_METADATA = re.compile(r"^\W*(title|tags|description|thumbnail idea)\s*:", re.I)
_BOLD_LABEL = re.compile(r"^\*\*[^*]+\*\*:?$")
_BROLL = re.compile(r"\[\s*b-?roll\s*:\s*(.*?)\s*\]", re.I)
_MARKER = re.compile(r"\[[^\]]*\]")
_EMPHASIS = re.compile(r"[*`]|(?<!\w)_|_(?!\w)")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def parse_script(script: str) -> list[dict]:
    """Paragraphs of spoken words, each with any [B-ROLL: ...] picture briefs."""
    lines = script.splitlines()
    for i, line in enumerate(lines):
        if _FULL_SCRIPT.match(line):
            lines = lines[i + 1:]
            break
    kept = [
        line for line in lines
        if not line.lstrip().startswith("#")
        and not _METADATA.match(line)
        and not _BOLD_LABEL.match(line.strip())
    ]

    paragraphs, carried_briefs = [], []
    for block in re.split(r"\n\s*\n", "\n".join(kept)):
        briefs = carried_briefs + _BROLL.findall(block)
        text = " ".join(_EMPHASIS.sub("", _MARKER.sub(" ", block)).split())
        if text:
            paragraphs.append({"text": text, "briefs": briefs})
            carried_briefs = []
        else:
            carried_briefs = briefs  # a B-roll note on its own line belongs to what follows
    return paragraphs


def _pack(paragraphs: list[dict], limit: int) -> list[dict]:
    """Group paragraphs into scenes of at most `limit` characters.

    A paragraph longer than the limit is broken at sentence ends first.
    """
    units = []
    for para in paragraphs:
        if len(para["text"]) <= limit:
            units.append(para)
            continue
        sentences = _SENTENCE_END.split(para["text"])
        units.append({"text": sentences[0], "briefs": para["briefs"]})
        units.extend({"text": s, "briefs": []} for s in sentences[1:])

    scenes = []
    for unit in units:
        if scenes and len(scenes[-1]["text"]) + 1 + len(unit["text"]) <= limit:
            scenes[-1]["text"] += " " + unit["text"]
            scenes[-1]["briefs"] += unit["briefs"]
        else:
            scenes.append({"text": unit["text"], "briefs": list(unit["briefs"])})
    return scenes


def plan(script: str, preset: dict) -> list[dict]:
    paragraphs = parse_script(script)
    if not paragraphs:
        raise StudioError("No narration found in the script: there are no spoken words to plan.")

    motions, hero_every = preset["motion"], preset["hero_every"]
    scenes, shot_number = [], 0
    for n, chunk in enumerate(_pack(paragraphs, preset["scene_chars"]), start=1):
        words = chunk["text"].split()
        seconds = len(words) / preset["wpm"] * 60
        count = min(len(words), max(1, round(seconds / preset["shot_seconds"])))
        shots = []
        for i in range(count):
            part = words[i * len(words) // count:(i + 1) * len(words) // count]
            shots.append({
                "id": f"s{n:02d}-{i + 1}",
                "seconds": seconds * len(part) / len(words),
                "narration": " ".join(part),
                "brief": chunk["briefs"][i] if i < len(chunk["briefs"]) else None,
                "prompt": None,
                "motion": motions[shot_number % len(motions)],
                "hero": bool(hero_every) and shot_number % hero_every == 0,
            })
            shot_number += 1
        scenes.append({
            "id": f"s{n:02d}",
            "text": chunk["text"],
            "words": len(words),
            "seconds": seconds,
            "shots": shots,
        })
    return scenes
