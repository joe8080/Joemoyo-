"""The studio's operations, shared by the command line and the connector."""

import os
from pathlib import Path

from studio import BudgetError, StudioError
from studio.assemble import assemble as _assemble
from studio.ledger import Project
from studio.presets import get_preset, preset_names
from studio.router import job_kinds, routes_for


def _root() -> Path:
    return Path(os.environ.get("STUDIO_HOME", "outputs/studio"))


def _load(slug: str) -> Project:
    return Project.load(_root(), slug)


def presets() -> dict:
    keys = ("label", "aspect", "shot_seconds", "hero_every", "voice", "music", "style")
    return {name: {k: get_preset(name)[k] for k in keys} for name in preset_names()}


def routes(kind: str | None = None) -> dict:
    return {k: routes_for(k) for k in ([kind] if kind else job_kinds())}


def new(title: str, preset: str, script: str) -> dict:
    return Project.create(_root(), title, preset, script).status()


def projects() -> list[dict]:
    found = []
    for path in sorted(_root().glob("*/project.json")):
        status = _load(path.parent.name).status()
        found.append({k: status[k] for k in ("slug", "title", "preset", "next_step")})
    return found


def status(slug: str) -> dict:
    return _load(slug).status()


def next_jobs(slug: str) -> dict:
    return _load(slug).next_jobs()


def set_prompts(slug: str, prompts: dict[str, str]) -> dict:
    project = _load(slug)
    project.set_prompts(prompts)
    return project.status()


def set_budget(slug: str, caps: dict[str, float]) -> dict:
    project = _load(slug)
    project.set_budget(caps)
    return project.status()


def quote(slug: str, credits: float, job_ids: list[str] | None = None,
          kind: str | None = None) -> dict:
    project = _load(slug)
    quoted = project.record_quote(credits, job_ids, kind)
    return {"quoted": quoted, **project.status()}


def start(slug: str, job_ids: list[str]) -> dict:
    """Pass jobs through the budget guard in order, stopping at the first refusal."""
    project = _load(slug)
    started, refused = [], None
    for job_id in job_ids:
        try:
            project.start(job_id)
        except BudgetError as err:
            refused = {"job": job_id, "why": str(err)}
            break
        started.append(job_id)
    return {"started": started, "refused": refused, **project.status()}


def done(slug: str, results: dict[str, str]) -> dict:
    project = _load(slug)
    for job_id, location in results.items():
        project.finish(job_id, location)
    return project.status()


def fail(slug: str, job_id: str, reason: str, refunded: bool = False) -> dict:
    project = _load(slug)
    project.fail(job_id, reason, refunded)
    return project.status()


def reroute(slug: str, job_ids: list[str]) -> dict:
    project = _load(slug)
    moved = []
    for job_id in job_ids:
        job = project.reroute(job_id)
        moved.append({"job": job_id, "tool": job["tool"], "connector": job["connector"]})
    return {"rerouted": moved, **project.status()}


def assemble(slug: str) -> dict:
    return _assemble(_load(slug))


__all__ = [
    "StudioError", "presets", "routes", "new", "projects", "status", "next_jobs",
    "set_prompts", "set_budget", "quote", "start", "done", "fail", "reroute", "assemble",
]
