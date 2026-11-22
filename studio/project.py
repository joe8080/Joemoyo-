"""Load a project file, check it, voice it, and work out the timeline."""
from __future__ import annotations

import json
from pathlib import Path

from . import brands, transitions, voice as V
from .captions import STYLES as CAPTION_STYLES
from .layers import OVERLAYS
from .sources import CARD_STYLES, GRADES, MOTIONS
from .util import IMAGE_EXT, VIDEO_EXT, StudioError, file_sig, slugify

FORMATS = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080), "4:5": (1080, 1350)}
TOP_KEYS = {"title", "brand", "formats", "fps", "voice", "captions", "music", "finish", "grade", "scenes",
            "progress", "watermark", "sfx", "audio", "out", "description"}
SCENE_KEYS = {"id", "say", "audio", "duration", "visual", "overlays", "transition", "transition_duration",
              "lead", "tail", "sfx", "chapter", "note", "captions"}


def _abs(base, p):
    p = Path(str(p)).expanduser()
    return str(p if p.is_absolute() else (Path(base) / p))


def load(path):
    path = Path(path)
    if path.is_dir():
        path = path / "project.json"
    if not path.is_file():
        raise StudioError(f"Project file not found: {path}")
    try:
        pr = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise StudioError(f"{path.name} is not valid JSON (line {e.lineno}): {e.msg}")
    if not isinstance(pr, dict) or not isinstance(pr.get("scenes"), list) or not pr["scenes"]:
        raise StudioError("A project needs a 'scenes' list with at least one scene.")
    pr["_dir"] = str(path.parent.resolve())
    pr["_file"] = str(path.resolve())
    return pr


def _visual(v, base, kit, problems, where):
    if v is None:
        v = {"card": kit.get("card", "gradient")}
    if isinstance(v, str):
        v = {"card": v} if v in CARD_STYLES else {"src": v}
    v = dict(v)
    if "src" in v:
        v["src"] = _abs(base, v["src"])
        ext = Path(v["src"]).suffix.lower()
        v["type"] = "video" if ext in VIDEO_EXT else "image" if ext in IMAGE_EXT else None
        if v["type"] is None:
            problems.append(f"{where}: '{Path(v['src']).name}' is not a supported image or video type.")
        elif not Path(v["src"]).is_file():
            problems.append(f"{where}: file not found: {v['src']}")
        if v.get("motion") not in (None, "auto") and v["motion"] not in MOTIONS:
            problems.append(f"{where}: unknown motion '{v['motion']}'. Options: auto, {', '.join(MOTIONS)}.")
        if v.get("grade") and v["grade"] not in GRADES:
            problems.append(f"{where}: unknown grade '{v['grade']}'. Options: {', '.join(GRADES)}.")
        if v.get("fit", "cover") not in ("cover", "blur"):
            problems.append(f"{where}: fit must be 'cover' or 'blur'.")
    else:
        v["type"] = "card"
        v.setdefault("card", kit.get("card", "gradient"))
        if v["card"] not in CARD_STYLES:
            problems.append(f"{where}: unknown card '{v['card']}'. Options: {', '.join(CARD_STYLES)}.")
    return v


def _reading_time(sc):
    n = 0
    for o in sc.get("overlays", []):
        for k in ("text", "kicker", "sub", "label", "title", "by"):
            n += len(str(o.get(k, "")).split())
        n += sum(len(str(i).split()) for i in o.get("items", []))
        if o.get("type") == "chart":
            n += 10
    return min(8.0, max(3.0, 1.6 + n * 0.33))


def prepare(pr, log=print):
    """Resolve everything a render needs. Returns the plan (plain JSON-able dict)."""
    base = pr["_dir"]
    problems, notes = [], []
    for k in pr:
        if k not in TOP_KEYS and not k.startswith("_"):
            notes.append(f"Ignoring unknown setting '{k}'.")
    kit = brands.resolve(pr.get("brand"), base)
    fps = int(pr.get("fps") or kit.get("fps", 30))
    if not 12 <= fps <= 60:
        problems.append("fps must be between 12 and 60.")
    formats = pr.get("formats") or ["16:9"]
    if isinstance(formats, str):
        formats = [formats]
    for f in formats:
        if f not in FORMATS:
            problems.append(f"Unknown format '{f}'. Options: {', '.join(FORMATS)}.")
    vcfg = dict(pr.get("voice") or {})
    if isinstance(pr.get("voice"), str):
        vcfg = {"provider": pr["voice"]}
    provider = vcfg.get("provider", "piper")
    cap = pr.get("captions", True)
    cap_cfg = None if cap is False else ({} if cap is True else ({"style": cap} if isinstance(cap, str) else dict(cap)))
    if cap_cfg is not None and cap_cfg.get("style") and cap_cfg["style"] not in CAPTION_STYLES:
        problems.append(f"Unknown caption style '{cap_cfg['style']}'. Options: {', '.join(CAPTION_STYLES)}.")
    grade = pr.get("grade", kit.get("grade", "none"))
    if grade not in GRADES:
        problems.append(f"Unknown grade '{grade}'. Options: {', '.join(GRADES)}.")

    scenes = []
    for i, raw in enumerate(pr["scenes"]):
        where = f"Scene {i + 1}" + (f" ({raw.get('id')})" if isinstance(raw, dict) and raw.get("id") else "")
        if not isinstance(raw, dict):
            problems.append(f"{where}: must be an object.")
            continue
        for k in raw:
            if k not in SCENE_KEYS:
                notes.append(f"{where}: ignoring unknown setting '{k}'.")
        sc = {"id": str(raw.get("id") or f"s{i + 1}"), "say": str(raw.get("say") or "").strip(),
              "chapter": raw.get("chapter"), "captions": raw.get("captions", True)}
        sc["visual"] = _visual(raw.get("visual"), base, kit, problems, where)
        if sc["visual"]["type"] == "image":
            sc["visual"].setdefault("grade", grade)
        if sc["visual"]["type"] == "video":
            sc["visual"].setdefault("grade", grade)
        ovs = []
        for o in raw.get("overlays") or []:
            if not isinstance(o, dict) or o.get("type") not in OVERLAYS:
                problems.append(f"{where}: unknown overlay type '{o.get('type') if isinstance(o, dict) else o}'. "
                                f"Options: {', '.join(OVERLAYS)}.")
                continue
            o = dict(o)
            if o["type"] == "image" and o.get("src"):
                o["src"] = _abs(base, o["src"])
                if not Path(o["src"]).is_file():
                    problems.append(f"{where}: overlay image not found: {o['src']}")
            ovs.append(o)
        sc["overlays"] = ovs
        tr = raw.get("transition", kit.get("transition", "fade")) if i else "fade"
        if tr not in transitions.DEFAULT_DURATION:
            problems.append(f"{where}: unknown transition '{tr}'. Options: {', '.join(transitions.DEFAULT_DURATION)}.")
            tr = "fade"
        sc["transition"] = tr
        sc["trans_dur"] = float(raw.get("transition_duration", transitions.DEFAULT_DURATION[tr] if i else 0.4))
        if raw.get("audio"):
            sc["audio"] = _abs(base, raw["audio"])
            if not Path(sc["audio"]).is_file():
                problems.append(f"{where}: narration audio not found: {sc['audio']}")
        fx = raw.get("sfx")
        sc["sfx"] = [fx] if isinstance(fx, (str, dict)) else list(fx or [])
        sc["_raw"] = {k: raw.get(k) for k in ("duration", "lead", "tail")}
        scenes.append(sc)

    music = pr.get("music")
    if isinstance(music, str):
        music = {"synth": "ambient"} if music in ("ambient", "synth") else {"file": music}
    if music:
        music = dict(music)
        if music.get("file"):
            music["file"] = _abs(base, music["file"])
            if not Path(music["file"]).is_file():
                problems.append(f"Music file not found: {music['file']}")
    master = None
    if vcfg.get("file"):
        master = _abs(base, vcfg["file"])
        if not Path(master).is_file():
            problems.append(f"Narration file not found: {master}")
    if problems:
        raise StudioError("Please fix these before rendering:\n  - " + "\n  - ".join(problems))

    cache = Path(base) / ".studio_cache"
    cache.mkdir(exist_ok=True)
    (cache / ".gitignore").write_text("*\n")

    # ---- optional repairs ("fix" on a clip, "clean" on narration) ---------
    def _strength(v):
        return v if v in ("light", "normal", "strong") else "normal"

    for sc in scenes:
        v = sc["visual"]
        if v["type"] == "video" and v.get("fix"):
            from . import fix as F
            log(f"  repairing clip: {Path(v['src']).name}")
            v["src"] = F.fixed_copy(v["src"], cache / "fixed", audio=False, strength=_strength(v["fix"]))
        if sc.get("audio") and vcfg.get("clean"):
            from . import fix as F
            log(f"  cleaning narration: {Path(sc['audio']).name}")
            sc["audio"] = F.fixed_copy(sc["audio"], cache / "fixed", video=False, strength=_strength(vcfg["clean"]),
                                       target_lufs=float((pr.get("audio") or {}).get("voice_lufs", -16.0)))
    if master and vcfg.get("clean"):
        from . import fix as F
        log(f"  cleaning narration: {Path(master).name}")
        master = F.fixed_copy(master, cache / "fixed", video=False, strength=_strength(vcfg["clean"]),
                              target_lufs=float((pr.get("audio") or {}).get("voice_lufs", -16.0)))

    # ---- narration ----------------------------------------------------
    for sc in scenes:
        sc["vo"] = None
    voices = []                                        # (path, absolute start) pairs for the mix
    if master:
        _master_timeline(scenes, master, vcfg, cache, fps, log)
    else:
        for sc in scenes:
            if sc.get("audio"):
                sc["vo"] = V.from_file(sc["audio"], sc["say"], vcfg, cache)
            elif sc["say"] and provider not in ("none", "file"):
                sc["vo"] = V.synthesize(sc["say"], vcfg, cache, lambda sid=sc["id"]: log(f"  voicing: {sid}"))
            elif sc["say"] and provider == "none":
                words = V.tokens(sc["say"])
                dur = max(1.2, len(words) / (2.75 * float(vcfg.get("speed", 1.0))))
                sc["vo"] = {"path": None, "duration": dur, "words": V.spread(words, 0, dur)}
            elif sc["say"] and provider == "file":
                raise StudioError(f"Scene {sc['id']}: voice provider is 'file' but the scene has no 'audio'.")
        _timeline(scenes, fps)

    t_frames, words, chapters = 0, [], []
    for i, sc in enumerate(scenes):
        sc["start"] = t_frames / fps
        sc["dur"] = sc["frames"] / fps
        if sc["vo"]:
            vs = sc["start"] + sc["lead"]
            if sc["vo"].get("path") and not master:
                voices.append((sc["vo"]["path"], vs))
            if sc.get("captions", True):
                for w in sc["vo"]["words"]:
                    words.append({"t": w["t"], "s": round(vs + w["s"], 3), "e": round(vs + w["e"], 3)})
        if sc.get("chapter"):
            chapters.append((sc["start"], str(sc["chapter"])))
        t_frames += sc["frames"]
        sc.pop("_raw", None)
    total = t_frames / fps
    if master:
        voices.append((master, scenes[0]["_vo_offset"]))

    effects = []
    sfx_cfg = pr.get("sfx", True)
    for i, sc in enumerate(scenes):
        if i and sfx_cfg and sc["transition"] in transitions.WHOOSH:
            effects.append(("whoosh", max(0.0, sc["start"] - 0.12), -13.0))
        for fx in sc["sfx"]:
            if isinstance(fx, str):
                fx = {"name": fx}
            name = fx.get("name") or fx.get("file")
            if fx.get("file"):
                name = _abs(base, fx["file"])
                if not Path(name).is_file():
                    raise StudioError(f"Sound effect not found: {name}")
            effects.append((name, sc["start"] + float(fx.get("at", 0.0)), float(fx.get("gain_db", -10.0))))

    audio_cfg = pr.get("audio") or {}
    plan = {
        "title": pr.get("title") or Path(pr["_file"]).stem, "slug": slugify(pr.get("title") or Path(pr["_file"]).stem),
        "dir": base, "cache": str(cache), "kit": kit, "fps": fps, "formats": formats,
        "captions": cap_cfg, "words": words, "scenes": scenes, "total": total,
        "music": music, "voices": voices, "effects": effects,
        "voice_lufs": float(audio_cfg.get("voice_lufs", -16.0)),
        "finish": {"grain": 0.08, "vignette": 0.2, "crf": 18, **(pr.get("finish") or {})},
        "progress": pr.get("progress", False), "watermark": pr.get("watermark"),
        "chapters": chapters, "notes": notes + list(V.TIMING_NOTES), "out": _abs(base, pr.get("out", "out")),
    }
    return plan


def _timeline(scenes, fps):
    n = len(scenes)
    for i, sc in enumerate(scenes):
        raw = sc["_raw"]
        d = sc["trans_dur"]
        lead = float(raw["lead"]) if raw.get("lead") is not None else max(0.3, d * 0.75)
        tail = float(raw["tail"]) if raw.get("tail") is not None else (0.9 if i == n - 1 else 0.35)
        if sc["vo"]:
            dur = lead + sc["vo"]["duration"] + tail
        else:
            dur = _reading_time(sc)
        if raw.get("duration") is not None:
            dur = max(dur, float(raw["duration"])) if sc["vo"] else float(raw["duration"])
        sc["lead"] = lead
        sc["frames"] = max(int(round(dur * fps)), int(round(d * fps)) + 2, 6)


def _master_timeline(scenes, master, vcfg, cache, fps, log):
    """One narration file for the whole video: cut the scenes to the spoken words."""
    said = [i for i, sc in enumerate(scenes) if sc["say"]]
    if not said:
        raise StudioError("voice.file is set but no scene has 'say' text to sync against.")
    first, last = said[0], said[-1]
    for i in range(first, last + 1):
        if not scenes[i]["say"]:
            raise StudioError(f"Scene {scenes[i]['id']}: with a single narration file, every scene between the "
                              "first and last spoken scene needs 'say' text (silent scenes can open or close).")
    full = " ".join(scenes[i]["say"] for i in said)
    log("  syncing scenes to the narration file")
    info = V.from_file(master, full, vcfg, cache)
    words, total = info["words"], info["duration"]
    intro = 0.0
    for i in range(first):
        sc = scenes[i]
        d = float(sc["_raw"]["duration"] if sc["_raw"].get("duration") is not None else _reading_time(sc))
        sc["lead"], sc["frames"] = 0.0, max(6, int(round(d * fps)))
        intro += sc["frames"] / fps
    k, bounds = 0, []
    for i in said:
        cnt = len(V.tokens(scenes[i]["say"]))
        bounds.append((k, k + cnt))
        k += cnt
    starts = []
    for j, (a, b) in enumerate(bounds):
        starts.append(0.0 if j == 0 else max(0.0, words[a]["s"] - 0.18))
    acc = 0
    for j, i in enumerate(said):
        a, b = bounds[j]
        s0 = starts[j]
        s1 = starts[j + 1] if j + 1 < len(said) else total + 0.5
        want = int(round((intro + s1) * fps)) - int(round(intro * fps)) - acc
        sc = scenes[i]
        sc["frames"] = max(6, want)
        acc += sc["frames"]
        sc["lead"] = 0.0
        t0 = acc / fps - sc["frames"] / fps           # scene start relative to narration start
        sc["vo"] = {"path": None, "duration": s1 - s0,
                    "words": [{"t": w["t"], "s": round(w["s"] - t0, 3), "e": round(w["e"] - t0, 3)}
                              for w in words[a:b]]}
    for i in range(last + 1, len(scenes)):
        sc = scenes[i]
        d = float(sc["_raw"]["duration"] if sc["_raw"].get("duration") is not None else _reading_time(sc))
        sc["lead"], sc["frames"] = 0.0, max(6, int(round(d * fps)))
    scenes[0]["_vo_offset"] = int(round(intro * fps)) / fps


def asset_sigs(plan):
    """Fingerprints of every file a render reads, so caches refresh when assets change."""
    sigs = {}
    for sc in plan["scenes"]:
        v = sc["visual"]
        if v.get("src"):
            sigs[v["src"]] = file_sig(v["src"])
        for o in sc["overlays"]:
            if o.get("type") == "image" and o.get("src"):
                sigs[o["src"]] = file_sig(o["src"])
    return sigs
