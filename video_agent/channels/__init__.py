"""Channel presets. Register new presets in ``get_preset``."""
from __future__ import annotations

from .base import ChannelPreset
from .finance import FINANCE_LONG, FINANCE_SHORT
from .history import HISTORY

_REGISTRY: dict[str, ChannelPreset] = {
    "history": HISTORY,
    "finance": FINANCE_LONG,        # default finance is long-form 16:9
    "finance.long": FINANCE_LONG,
    "finance.short": FINANCE_SHORT,
}


def get_preset(name: str) -> ChannelPreset:
    key = name.strip().lower()
    if key not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY))
        raise KeyError(f"Unknown channel {name!r}. Available: {available}")
    return _REGISTRY[key]


def available_channels() -> list[str]:
    return sorted(_REGISTRY.keys())


__all__ = ["ChannelPreset", "get_preset", "available_channels"]
