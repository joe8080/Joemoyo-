"""Remotion render wrapper.

Drives the `remotion/` Node project to render the Episode composition from the
crew's props. Returns None (without raising) when the project or the Remotion
CLI isn't available, so the producer can fall back to the ffmpeg engine.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess

REMOTION_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "remotion")
COMPOSITION_ID = "Episode"


def is_available() -> bool:
    """True when the remotion project exists and npx is on PATH."""
    return (
        os.path.isdir(REMOTION_DIR)
        and os.path.exists(os.path.join(REMOTION_DIR, "package.json"))
        and shutil.which("npx") is not None
    )


def render(props: dict, out_path: str, *, install: bool = True) -> str | None:
    """Render the Episode composition with the given props to out_path."""
    if not is_available():
        return None

    out_path = os.path.abspath(out_path)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    props_path = os.path.join(REMOTION_DIR, "_props.json")
    with open(props_path, "w", encoding="utf-8") as f:
        json.dump(props, f)

    if install and not os.path.isdir(os.path.join(REMOTION_DIR, "node_modules")):
        subprocess.run(["npm", "install"], cwd=REMOTION_DIR, check=True)

    subprocess.run(
        [
            "npx", "remotion", "render", COMPOSITION_ID, out_path,
            f"--props={props_path}",
        ],
        cwd=REMOTION_DIR,
        check=True,
    )
    return out_path if os.path.exists(out_path) else None
