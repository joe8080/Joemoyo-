"""A video project: its plan, its jobs, and the budget guard.

Everything lives in one project.json so a half-made video can be picked up in
a later session. Every change is saved straight away.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from studio import BudgetError, StudioError
from studio.planner import plan
from studio.presets import get_preset
from studio.router import pick_route

_OPEN = ("pending", "failed")  # statuses that can still be started


def _slug(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60].strip("-")
    if not slug:
        raise StudioError("The title needs at least one letter or number.")
    return slug


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _job(job_id: str, kind: str, ref: str | None) -> dict:
    job = {"id": job_id, "kind": kind, "ref": ref, "status": "pending",
           "quote": None, "result": None, "tried": [], "note": None}
    _apply_route(job, pick_route(kind))
    return job


def _apply_route(job: dict, route: dict) -> None:
    job.update(route=route["id"], wallet=route["wallet"], connector=route["connector"],
               tool=route["tool"], paid=route["paid"], quote_how=route["quote"],
               why=route["why"], notes=route["notes"], quote=None)
    job["tried"].append(route["id"])


class Project:
    def __init__(self, path: Path, data: dict):
        self.path = Path(path)
        self.data = data

    # ---- create / load / save -------------------------------------------

    @classmethod
    def create(cls, root, title: str, preset_name: str, script: str,
               preset: dict | None = None) -> "Project":
        preset = preset or get_preset(preset_name)
        slug = _slug(title)
        path = Path(root) / slug / "project.json"
        if path.exists():
            raise StudioError(
                f"A project called '{slug}' already exists. Pick another title, "
                f"or carry on with the existing one.")
        scenes = plan(script, preset)

        jobs = []
        for scene in scenes:
            jobs.append(_job(f"vo-{scene['id']}", "voiceover", scene["id"]))
            for shot in scene["shots"]:
                jobs.append(_job(f"img-{shot['id']}", "image", shot["id"]))
                if shot["hero"]:
                    jobs.append(_job(f"mot-{shot['id']}", "motion", shot["id"]))
        jobs.append(_job("music", "music", None))

        project = cls(path, {
            "title": title, "slug": slug, "created": _now(),
            "preset_name": preset_name, "preset": preset,
            "scenes": scenes, "jobs": jobs, "budgets": {}, "charges": [],
        })
        project.save()
        return project

    @classmethod
    def load(cls, root, slug: str) -> "Project":
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
            raise StudioError(
                f"'{slug}' is not a project name. Names use lowercase letters, numbers and dashes only.")
        path = Path(root) / slug / "project.json"
        if not path.exists():
            found = sorted(p.parent.name for p in Path(root).glob("*/project.json"))
            raise StudioError(
                f"No project called '{slug}'. "
                + (f"Existing projects: {', '.join(found)}." if found else "There are no projects yet."))
        return cls(path, json.loads(path.read_text()))

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2))

    # ---- lookups ---------------------------------------------------------

    @property
    def slug(self) -> str:
        return self.data["slug"]

    @property
    def dir(self) -> Path:
        return self.path.parent

    @property
    def jobs(self) -> list[dict]:
        return self.data["jobs"]

    @property
    def preset(self) -> dict:
        return self.data["preset"]

    def job(self, job_id: str) -> dict:
        for job in self.jobs:
            if job["id"] == job_id:
                return job
        raise StudioError(f"No job called '{job_id}' in this project.")

    def shots(self) -> list[dict]:
        return [shot for scene in self.data["scenes"] for shot in scene["shots"]]

    def _shot(self, shot_id: str) -> dict:
        for shot in self.shots():
            if shot["id"] == shot_id:
                return shot
        raise StudioError(f"No shot called '{shot_id}' in this project.")

    def _scene(self, scene_id: str) -> dict:
        return next(s for s in self.data["scenes"] if s["id"] == scene_id)

    def spent(self, wallet: str) -> float:
        return sum(c["credits"] for c in self.data["charges"] if c["wallet"] == wallet)

    # ---- creative input --------------------------------------------------

    def set_prompts(self, prompts: dict[str, str]) -> None:
        shots = {shot_id: self._shot(shot_id) for shot_id in prompts}  # all-or-nothing
        for shot_id, prompt in prompts.items():
            shots[shot_id]["prompt"] = prompt.strip()
        self.save()

    # ---- money -----------------------------------------------------------

    def set_budget(self, caps: dict[str, float]) -> None:
        for wallet, cap in caps.items():
            if cap < 0:
                raise StudioError(f"The cap for {wallet} cannot be negative.")
        self.data["budgets"].update(caps)
        self.save()

    def record_quote(self, credits: float, job_ids: list[str] | None = None,
                     kind: str | None = None) -> list[str]:
        """Store the live price for the named jobs, or for every open paid job of a kind."""
        if credits < 0:
            raise StudioError("A quote cannot be negative.")
        if job_ids:
            jobs = [self.job(job_id) for job_id in job_ids]
        elif kind:
            jobs = [j for j in self.jobs if j["kind"] == kind and j["paid"] and j["status"] in _OPEN]
        else:
            raise StudioError("Say which jobs the quote is for: job ids or a kind.")
        for job in jobs:
            job["quote"] = credits
        self.save()
        return [job["id"] for job in jobs]

    def start(self, job_id: str) -> dict:
        """The budget guard. Call before running the paid tool; it refuses overspend."""
        job = self.job(job_id)
        if job["status"] not in _OPEN:
            raise StudioError(f"{job_id} is already {job['status']}; it cannot be started again.")
        if job["paid"]:
            wallet = job["wallet"]
            if job["quote"] is None:
                raise BudgetError(
                    f"{job_id} has no quote yet. Get the live price first: {job['quote_how']}")
            cap = self.data["budgets"].get(wallet)
            if cap is None:
                raise BudgetError(
                    f"No spending cap is set for {wallet}. Joe approves a cap before anything is spent.")
            after = self.spent(wallet) + job["quote"]
            if after > cap:
                raise BudgetError(
                    f"{job_id} costs {job['quote']:g} and would take {wallet} to {after:g}, "
                    f"past the cap of {cap:g}. Raise the cap with Joe's say-so, or reroute the job.")
            self.data["charges"].append(
                {"job": job_id, "wallet": wallet, "credits": job["quote"], "at": _now()})
        job["status"] = "running"
        self.save()
        return job

    def finish(self, job_id: str, location: str) -> dict:
        job = self.job(job_id)
        if job["status"] != "running":
            raise StudioError(
                f"{job_id} is not running (it is {job['status']}). Start it through the "
                f"budget guard before recording a result.")
        if not location:
            raise StudioError(f"{job_id} needs the link or file path of its result.")
        job.update(status="done", result=location, note=None)
        self.save()
        return job

    def fail(self, job_id: str, reason: str, refunded: bool = False) -> dict:
        job = self.job(job_id)
        if job["status"] != "running":
            raise StudioError(f"{job_id} is not running (it is {job['status']}).")
        if refunded:
            for i in range(len(self.data["charges"]) - 1, -1, -1):
                if self.data["charges"][i]["job"] == job_id:
                    del self.data["charges"][i]
                    break
        job.update(status="failed", note=reason)
        self.save()
        return job

    def reroute(self, job_id: str) -> dict:
        """Move a job to the next tool down its list. The old quote no longer applies."""
        job = self.job(job_id)
        if job["status"] not in _OPEN:
            raise StudioError(f"{job_id} is {job['status']}; only a pending or failed job can be rerouted.")
        _apply_route(job, pick_route(job["kind"], skip=set(job["tried"])))
        job["status"] = "pending"
        self.save()
        return job

    # ---- what to do next -------------------------------------------------

    def _instructions(self, job: dict) -> dict:
        preset = self.preset
        if job["kind"] == "voiceover":
            text = self._scene(job["ref"])["text"]
            return {"text": text, "characters": len(text), "voice": preset["voice"]}
        if job["kind"] == "music":
            seconds = sum(s["seconds"] for s in self.data["scenes"])
            return {"mood": preset["music"], "seconds": round(seconds)}
        shot = self._shot(job["ref"])
        do = {"prompt": f"{shot['prompt']}, {preset['style']}", "aspect": preset["aspect"]}
        if job["kind"] == "motion":
            source = self.job(f"img-{shot['id']}")
            do.update(seconds=max(1, round(shot["seconds"])), camera=shot["motion"],
                      source_image=source["result"], source_job=source["id"])
        return do

    def next_jobs(self) -> dict:
        queue = {"ready": [], "needs_prompt": [], "waiting": [], "running": []}
        for job in self.jobs:
            if job["status"] == "running":
                queue["running"].append({"id": job["id"], "connector": job["connector"], "tool": job["tool"]})
                continue
            if job["status"] not in _OPEN:
                continue
            if job["kind"] in ("image", "motion"):
                shot = self._shot(job["ref"])
                if job["kind"] == "image" and shot["prompt"] is None:
                    queue["needs_prompt"].append({
                        "id": job["id"], "shot": shot["id"],
                        "narration": shot["narration"], "brief": shot["brief"]})
                    continue
                if job["kind"] == "motion" and self.job(f"img-{shot['id']}")["status"] != "done":
                    queue["waiting"].append({"id": job["id"], "waiting_for": f"img-{shot['id']}"})
                    continue
            queue["ready"].append({
                key: job[key] for key in
                ("id", "kind", "status", "connector", "tool", "wallet", "paid",
                 "quote", "quote_how", "why", "notes", "note")
            } | {"do": self._instructions(job)})
        return queue

    def status(self) -> dict:
        queue = self.next_jobs()
        counts: dict[str, dict[str, int]] = {}
        for job in self.jobs:
            counts.setdefault(job["kind"], {}).setdefault(job["status"], 0)
            counts[job["kind"]][job["status"]] += 1

        wallets = {}
        for wallet in sorted({j["wallet"] for j in self.jobs if j["paid"]} | set(self.data["budgets"])):
            wallets[wallet] = {
                "cap": self.data["budgets"].get(wallet),
                "spent": self.spent(wallet),
                "to_come": sum(j["quote"] for j in self.jobs
                               if j["wallet"] == wallet and j["paid"]
                               and j["status"] in _OPEN and j["quote"] is not None),
            }
        unquoted = [j["id"] for j in self.jobs
                    if j["paid"] and j["status"] in _OPEN and j["quote"] is None]
        short = [w for w, v in wallets.items()
                 if v["to_come"] and (v["cap"] is None or v["spent"] + v["to_come"] > v["cap"])]
        failed = [j["id"] for j in self.jobs if j["status"] == "failed"]

        if queue["needs_prompt"]:
            step = f"Write picture prompts for {len(queue['needs_prompt'])} shots."
        elif unquoted:
            step = f"Get a live quote for {len(unquoted)} paid jobs and record it."
        elif short:
            step = (f"Show Joe the totals and ask him to approve the spend, "
                    f"then set caps for: {', '.join(short)}.")
        elif failed:
            step = f"Retry or reroute {len(failed)} failed jobs: {', '.join(failed)}."
        elif queue["ready"]:
            step = f"Run {len(queue['ready'])} ready jobs through the budget guard."
        elif queue["running"]:
            step = f"Wait for {len(queue['running'])} running jobs and record their results."
        else:
            step = "Everything is in. Assemble the video."

        return {
            "slug": self.slug, "title": self.data["title"],
            "preset": self.data["preset_name"],
            "planned_minutes": round(sum(s["seconds"] for s in self.data["scenes"]) / 60, 1),
            "scenes": len(self.data["scenes"]), "shots": len(self.shots()),
            "jobs": counts, "wallets": wallets, "unquoted": unquoted,
            "needs_prompt": len(queue["needs_prompt"]), "next_step": step,
        }
