"""Render pipeline: scenes -> cached chunks (in parallel) -> one finished MP4 per format."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from PIL import Image, ImageDraw

from . import audio as A, captions as C, layers as L, project as P, sources as S, text as T, transitions as TR
from .util import ENGINE_VERSION, FFMPEG, StudioError, clamp, digest, ease_in_cubic, fmt_time, run


def frame_size(fmt, draft=False):
    W, H = P.FORMATS[fmt]
    if draft:
        W, H = W // 2, H // 2
    return W - W % 2, H - H % 2


class SceneRenderer:
    """Produces the frames of one scene (background + overlays) at any local time."""

    def __init__(self, plan, i, ctx):
        self.sc = sc = plan["scenes"][i]
        self.ctx = ctx
        nxt = plan["scenes"][i + 1]["trans_dur"] if i + 1 < len(plan["scenes"]) else 0.0
        span = sc["dur"] + nxt
        v = sc["visual"]
        W, H, fps = ctx.W, ctx.H, ctx.fps
        focus = v.get("focus", (0.5, 0.5))
        self.media = v["type"] in ("image", "video")
        if v["type"] == "image":
            self.src = S.StillSource(S.load_image(v["src"], v.get("grade", "none")), W, H, fps,
                                     v.get("motion", "auto"), focus, span, i)
        elif v["type"] == "video":
            self.src = S.VideoSource(v["src"], W, H, fps, v.get("start", 0.0), v.get("speed", 1.0),
                                     v.get("fit", "cover"), focus, v.get("grade", "none"), v.get("loop", False),
                                     v.get("zoom", 1.0), v.get("bg_dim", 0.12))
        else:
            self.src = S.StillSource(S.card_image(v["card"], ctx.kit, W, H, i), W, H, fps,
                                     v.get("motion", "drift"), focus, span, i)
        self.dim = clamp(float(v.get("dim", 0.0)))
        self.overlays = [L.make(o, ctx, sc["dur"], self.media) for o in sc["overlays"]]

    def frames(self, t0, n):
        fps = self.ctx.fps
        W, H = self.ctx.W, self.ctx.H
        for k, f in enumerate(self.src.frames(t0, n)):
            t = t0 + k / fps
            if self.dim:
                f.paste((0, 0, 0), (0, 0, W, H), Image.new("L", (W, H), int(255 * self.dim)))
            for o in self.overlays:
                o.draw(f, t)
            yield f


class Globals:
    """Things drawn over the whole video: captions, progress bar, watermark, closing fade."""

    def __init__(self, plan, ctx):
        self.plan, self.ctx = plan, ctx
        self.caps = C.Captions(plan["captions"], ctx, plan["words"]) if plan["captions"] is not None and plan["words"] else None
        self.total = plan["total"]
        self.wm = None
        wm = plan.get("watermark")
        if wm:
            wm = {"text": wm} if isinstance(wm, str) else wm
            sz = ctx.px(wm.get("size", 26))
            sp = T.sprite(str(wm.get("text", "")), ctx.fnt("heading")[0], sz, 700,
                          ctx.col("text", int(255 * float(wm.get("opacity", 0.55)))), None, 0, 0.4, sz * 0.08)
            corner = wm.get("corner", "tr")
            x = ctx.mx if "l" in corner else ctx.W - ctx.mx - sp.w
            y = ctx.px(40) if "t" in corner else ctx.H - ctx.px(40) - sp.h
            self.wm = (sp, x, y)

    def draw(self, f, t):
        c = self.ctx
        if self.wm:
            T.paste_sprite(f, self.wm[0], self.wm[1], self.wm[2])
        if self.caps:
            self.caps.draw(f, t)
        if self.plan.get("progress"):
            h = c.px(8)
            w = int(c.W * clamp(t / self.total))
            f.paste(c.col("accent")[:3], (0, c.H - h, w, c.H))
        left = self.total - t
        if left < 0.5:
            a = ease_in_cubic(1 - left / 0.5)
            f.paste((0, 0, 0), (0, 0, c.W, c.H), Image.new("L", (c.W, c.H), int(255 * a)))


def _encoder(path, W, H, fps, plan, draft, threads):
    fin = plan["finish"]
    vf = []
    vg = clamp(float(fin.get("vignette", 0)))
    if vg > 0.01:
        vf.append(f"vignette=a={0.2 + vg * 0.75:.3f}")
    vf.append("scale=out_color_matrix=bt709:out_range=tv,format=yuv420p")
    gr = clamp(float(fin.get("grain", 0)))
    if gr > 0.01:
        vf.append(f"noise=c0s={max(1, int(round(gr * 26)))}:c0f=t")
    cmd = [FFMPEG, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(fps), "-i", "-", "-vf", ",".join(vf), "-c:v", "libx264",
           "-preset", "veryfast" if draft else "fast", "-crf", "25" if draft else str(int(fin.get("crf", 18))),
           "-g", str(fps * 2), "-bf", "2", "-threads", str(threads),
           "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
           "-video_track_timescale", "90000", str(path)]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)


def render_chunk(job):
    """Worker: render one scene's slot (including the transition into it) to a video file."""
    plan = json.loads(Path(job["plan"]).read_text())
    T.add_font_dir(Path(plan["dir"]) / "fonts")
    i, W, H = job["i"], job["W"], job["H"]
    fps = plan["fps"]
    ctx = L.Ctx(W, H, fps, plan["kit"], plan["captions"] is not None)
    sc = plan["scenes"][i]
    n = sc["frames"]
    nd = min(n, int(round(sc["trans_dur"] * fps))) if sc["transition"] != "cut" else 0
    cur = SceneRenderer(plan, i, ctx).frames(0.0, n)
    prev = None
    if nd and i > 0:
        prev = SceneRenderer(plan, i - 1, ctx).frames(plan["scenes"][i - 1]["dur"], nd)
    glob = Globals(plan, ctx)
    tmp = job["out"] + ".part.mp4"
    enc = _encoder(tmp, W, H, fps, plan, job["draft"], job["threads"])
    try:
        for k, f in enumerate(cur):
            if k < nd:
                f = TR.blend(sc["transition"], next(prev) if prev else None, f, (k + 1) / (nd + 1))
            glob.draw(f, sc["start"] + k / fps)
            enc.stdin.write(f.tobytes())
        enc.stdin.close()
        err = enc.stderr.read().decode("utf-8", "replace")
        if enc.wait():
            raise StudioError(f"Video encode failed for scene {sc['id']}:\n{err[-600:]}")
    except BrokenPipeError:
        err = enc.stderr.read().decode("utf-8", "replace")
        raise StudioError(f"Video encode failed for scene {sc['id']}:\n{err[-600:]}")
    finally:
        if enc.poll() is None:
            enc.kill()
            enc.wait()
        enc.stderr.close()
    os.replace(tmp, job["out"])
    return i


def _chunk_key(plan, i, W, H, draft, sigs):
    sc = plan["scenes"][i]
    prev = plan["scenes"][i - 1] if i else None
    nxt = plan["scenes"][i + 1]["trans_dur"] if i + 1 < len(plan["scenes"]) else 0
    lo, hi = sc["start"] - 1.0, sc["start"] + sc["dur"] + 1.0
    words = [w for w in plan["words"] if lo <= w["s"] <= hi] if plan["captions"] is not None else []
    return digest([ENGINE_VERSION, W, H, draft, plan["fps"], plan["kit"], plan["captions"], plan["finish"],
                   plan["progress"], plan["watermark"], plan["total"], sc, prev, nxt, words, sigs])


def render(project_path, formats=None, draft=False, jobs=None, use_cache=True, out_dir=None, log=print):
    t_start = time.time()
    pr = P.load(project_path)
    T.add_font_dir(Path(pr["_dir"]) / "fonts")
    log("Preparing narration and timeline...")
    plan = P.prepare(pr, log)
    for n in plan["notes"]:
        log("  note: " + n)
    formats = formats or plan["formats"]
    for f in formats:
        if f not in P.FORMATS:
            raise StudioError(f"Unknown format '{f}'. Options: {', '.join(P.FORMATS)}.")
    cache = Path(plan["cache"])
    chunks_dir = cache / "chunks"
    chunks_dir.mkdir(exist_ok=True)
    plan_file = cache / "plan.json"
    plan_file.write_text(json.dumps(plan))
    out_dir = Path(out_dir or plan["out"])
    out_dir.mkdir(parents=True, exist_ok=True)
    log(f"Timeline: {len(plan['scenes'])} scenes, {fmt_time(plan['total'])} ({plan['total']:.1f}s) at {plan['fps']} fps")

    log("Mixing sound...")
    mix = A.build_mix(plan["total"], plan["voices"], plan["music"], plan["effects"], plan["voice_lufs"],
                      clips=plan["clips"], clip_lufs=plan["clip_lufs"], clip_duck_db=plan["clip_duck_db"])
    wav = cache / "mix.wav"
    A.save(wav, mix)

    cpu = os.cpu_count() or 2
    jobs = int(jobs or max(1, min(4, cpu - 1 if cpu > 2 else cpu)))
    threads = max(1, min(4, cpu // jobs + 1))
    sigs = P.asset_sigs(plan)
    outputs = []
    for fmt in formats:
        W, H = frame_size(fmt, draft)
        todo, paths = [], []
        for i in range(len(plan["scenes"])):
            p = chunks_dir / f"{_chunk_key(plan, i, W, H, draft, sigs)}.mp4"
            paths.append(p)
            if not (use_cache and p.is_file() and p.stat().st_size > 500):
                todo.append({"plan": str(plan_file), "i": i, "W": W, "H": H, "draft": draft,
                             "threads": threads, "out": str(p)})
        log(f"Rendering {fmt} ({W}x{H}): {len(todo)} of {len(paths)} scenes to draw"
            + (f", {len(paths) - len(todo)} reused" if len(todo) < len(paths) else ""))
        if todo:
            if jobs == 1 or len(todo) == 1:
                for j in todo:
                    render_chunk(j)
                    log(f"  scene {j['i'] + 1}/{len(paths)} done")
            else:
                with ProcessPoolExecutor(max_workers=jobs) as ex:
                    futs = {ex.submit(render_chunk, j): j for j in todo}
                    done = 0
                    for fu in as_completed(futs):
                        fu.result()
                        done += 1
                        log(f"  {done}/{len(todo)} scenes drawn")
        lst = cache / f"concat_{fmt.replace(':', 'x')}.txt"
        lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in paths))
        name = f"{plan['slug']}_{fmt.replace(':', 'x')}{'_draft' if draft else ''}.mp4"
        out = out_dir / name
        run([FFMPEG, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(wav),
             "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
             "-t", f"{plan['total']:.3f}", "-movflags", "+faststart", str(out)])
        outputs.append(str(out))
        log(f"  wrote {out}")
    extras = write_extras(plan, out_dir)
    _prune(chunks_dir)
    log(f"Done in {time.time() - t_start:.0f}s")
    return {"outputs": outputs, "extras": extras, "duration": plan["total"], "plan": plan}


def write_extras(plan, out_dir):
    out = {}
    if plan["words"]:
        p = Path(out_dir) / f"{plan['slug']}.srt"
        p.write_text(C.srt(plan["words"]), encoding="utf-8")
        out["srt"] = str(p)
    if plan["chapters"]:
        ch = list(plan["chapters"])
        if ch[0][0] > 0.5:
            ch.insert(0, (0.0, "Intro"))
        p = Path(out_dir) / f"{plan['slug']}_chapters.txt"
        p.write_text("\n".join(f"{fmt_time(t)} {name}" for t, name in ch) + "\n", encoding="utf-8")
        out["chapters"] = str(p)
    return out


def _prune(chunks_dir, keep=400):
    files = sorted(Path(chunks_dir).glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    for p in files[keep:]:
        try:
            p.unlink()
        except OSError:
            pass


# ---------------------------------------------------------------- stills for review

def frame_at(plan, ctx, t):
    """One finished frame at absolute time t (same drawing path as the real render)."""
    scs = plan["scenes"]
    i = max(k for k, sc in enumerate(scs) if sc["start"] <= t + 1e-6)
    sc = scs[i]
    local = t - sc["start"]
    f = next(SceneRenderer(plan, i, ctx).frames(local, 1))
    d = sc["trans_dur"] if sc["transition"] != "cut" else 0
    if local < d:
        prev = next(SceneRenderer(plan, i - 1, ctx).frames(scs[i - 1]["dur"] + local, 1)) if i else None
        f = TR.blend(sc["transition"], prev, f, clamp(local / d))
    Globals(plan, ctx).draw(f, t)
    return f


def stills(project_path, fmt=None, times=None, out_dir=None, log=print):
    """Save review frames and a contact sheet, so a video can be checked without playing it."""
    pr = P.load(project_path)
    T.add_font_dir(Path(pr["_dir"]) / "fonts")
    plan = P.prepare(pr, log)
    fmt = fmt or plan["formats"][0]
    W, H = frame_size(fmt)
    ctx = L.Ctx(W, H, plan["fps"], plan["kit"], plan["captions"] is not None)
    if not times:
        times = []
        for sc in plan["scenes"]:
            times.append(sc["start"] + min(sc["dur"] * 0.62, max(0.1, sc["dur"] - 0.25)))
    out_dir = Path(out_dir or Path(plan["out"]) / "frames")
    out_dir.mkdir(parents=True, exist_ok=True)
    tw = 640 if W >= H else 360
    th = int(tw * H / W)
    thumbs, files = [], []
    for t in times:
        t = clamp(float(t), 0, plan["total"] - 1 / plan["fps"])
        f = frame_at(plan, ctx, t)
        p = out_dir / f"{plan['slug']}_{fmt.replace(':', 'x')}_{t:07.2f}s.jpg"
        f.save(p, quality=90)
        files.append(str(p))
        th_img = f.resize((tw, th), Image.LANCZOS)
        d = ImageDraw.Draw(th_img)
        d.rectangle([0, 0, 92, 26], fill=(0, 0, 0))
        d.text((6, 4), fmt_time(t) + f".{int(t * 10) % 10}", fill=(255, 255, 255),
               font=T.font("Inter", 16, 600))
        thumbs.append(th_img)
    cols = min(len(thumbs), 4 if W >= H else 6)
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw + (cols + 1) * 8, rows * th + (rows + 1) * 8), (18, 18, 20))
    for k, im in enumerate(thumbs):
        sheet.paste(im, (8 + (k % cols) * (tw + 8), 8 + (k // cols) * (th + 8)))
    sp = out_dir / f"{plan['slug']}_{fmt.replace(':', 'x')}_sheet.jpg"
    sheet.save(sp, quality=88)
    log(f"Saved {len(files)} frames and contact sheet: {sp}")
    return {"sheet": str(sp), "frames": files, "plan": plan}


def clear_cache(project_path):
    pr = P.load(project_path)
    c = Path(pr["_dir"]) / ".studio_cache"
    if c.is_dir():
        shutil.rmtree(c)
