"""House styles, loaded from presets.yaml."""

from functools import lru_cache
from pathlib import Path

import yaml

from studio import StudioError

_FILE = Path(__file__).with_name("presets.yaml")


@lru_cache(maxsize=None)
def _all() -> dict:
    return yaml.safe_load(_FILE.read_text())


def preset_names() -> list[str]:
    return list(_all())


def get_preset(name: str) -> dict:
    try:
        return dict(_all()[name])
    except KeyError:
        raise StudioError(
            f"No preset called '{name}'. Choose one of: {', '.join(preset_names())}."
        ) from None
