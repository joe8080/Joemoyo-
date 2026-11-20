"""Decides which connected tool gets each kind of job, from routes.yaml."""

from functools import lru_cache
from pathlib import Path

import yaml

from studio import StudioError

_FILE = Path(__file__).with_name("routes.yaml")


@lru_cache(maxsize=None)
def _all() -> dict:
    return yaml.safe_load(_FILE.read_text())


def job_kinds() -> list[str]:
    return list(_all())


def routes_for(kind: str) -> list[dict]:
    try:
        return [dict(route) for route in _all()[kind]]
    except KeyError:
        raise StudioError(
            f"No routes for '{kind}'. Job kinds are: {', '.join(job_kinds())}."
        ) from None


def pick_route(kind: str, skip: set[str] | frozenset[str] = frozenset()) -> dict:
    """First route for this kind that has not been tried already."""
    for route in routes_for(kind):
        if route["id"] not in skip:
            return route
    raise StudioError(f"Every {kind} tool has been tried; none are left to fall back to.")
