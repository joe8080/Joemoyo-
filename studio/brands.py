"""Brand kits: colours, fonts and default look for each channel.

A project picks one with "brand": "ogx", or tweaks one inline:
    "brand": {"base": "wealth", "accent": "#FF8800"}
or points at a JSON file of the same shape.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from .util import StudioError

KITS = {
    # OrigineX house style (locked colours from the OGX motion-card spec).
    "ogx": {
        "bg": "#0D0D0D", "surface": "#171512", "text": "#F0EDE8", "muted": "#A9A296",
        "accent": "#C9A84C", "accent2": "#E8CE84", "alert": "#E63946",
        "fonts": {
            "display": ["Cinzel", 700], "heading": ["Montserrat", 700],
            "body": ["Montserrat", 500], "caption": ["Montserrat", 700], "quote": ["Lora", 500],
        },
        "captions": "clean", "grade": "cinematic", "card": "spotlight",
        "uppercase_titles": True, "fps": 24, "transition": "fade",
    },
    # Clean finance / wealth education look.
    "wealth": {
        "bg": "#0A1424", "surface": "#12213B", "text": "#F4F7FB", "muted": "#9FB0C8",
        "accent": "#2DD4A7", "accent2": "#FFD166", "alert": "#FF5D5D",
        "fonts": {
            "display": ["Montserrat", 800], "heading": ["Montserrat", 700],
            "body": ["Inter", 500], "caption": ["Montserrat", 800], "quote": ["Lora", 500],
        },
        "captions": "pop", "grade": "none", "card": "grid",
        "uppercase_titles": False, "fps": 30, "transition": "fade",
    },
    # Loud short-form look for Shorts / Reels / TikTok.
    "bold": {
        "bg": "#0B0B0F", "surface": "#191922", "text": "#FFFFFF", "muted": "#B7B7C4",
        "accent": "#FFE600", "accent2": "#FF4D6D", "alert": "#FF4D6D",
        "fonts": {
            "display": ["Anton", 400], "heading": ["Montserrat", 800],
            "body": ["Montserrat", 600], "caption": ["Montserrat", 900], "quote": ["Lora", 600],
        },
        "captions": "box", "grade": "vivid", "card": "gradient",
        "uppercase_titles": True, "fps": 30, "transition": "slide_left",
    },
}

DEFAULT_KIT = "wealth"


def resolve(spec, project_dir=None):
    """Turn a project's "brand" value into a full kit dict."""
    if spec is None:
        spec = DEFAULT_KIT
    if isinstance(spec, str):
        if spec in KITS:
            kit = copy.deepcopy(KITS[spec])
            kit["name"] = spec
            return kit
        p = Path(spec)
        if project_dir and not p.is_absolute():
            p = Path(project_dir) / p
        if p.suffix == ".json" and p.exists():
            return resolve(json.loads(p.read_text()), project_dir)
        raise StudioError(f"Unknown brand '{spec}'. Built-in kits: {', '.join(KITS)}.")
    if isinstance(spec, dict):
        base = spec.get("base", DEFAULT_KIT)
        if base not in KITS:
            raise StudioError(f"Unknown base brand '{base}'. Built-in kits: {', '.join(KITS)}.")
        kit = copy.deepcopy(KITS[base])
        for k, v in spec.items():
            if k == "base":
                continue
            if k == "fonts" and isinstance(v, dict):
                kit["fonts"].update(v)
            else:
                kit[k] = v
        kit["name"] = spec.get("name", base)
        return kit
    raise StudioError("'brand' must be a kit name, a JSON path, or an object.")
