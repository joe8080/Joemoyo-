"""Builds the finished MP4 from a project's voiceovers, pictures, clips and music.

Runs locally with ffmpeg and costs nothing. Picture timing follows the real
length of each voiceover, not the planned length, so sound and picture stay in step.
"""

import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse

import requests

from studio import StudioError
from studio.ledger import Project

_DEFAULT_EXT = {"voiceover": ".mp3", "image": ".png", "motion": ".mp4", "music": ".mp3"}
_CAPTION_WORDS = 12
_ZOOM = 0.12  # how far a still zooms or travels over its time on screen
_AUDIO = "aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo"
_ENCODE = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p"]


def _run(*args: str) -> str:
    done = subprocess.run(args, capture_output=True, text=True)
    if done.returncode != 0:
        raise StudioError(f"{args[0]} failed: {done.stderr.strip()[-600:]}")
    return done.stdout


def _seconds(path: Path) -> float:
    return float(_run("ffprobe", "-v", "error", "-show_entries", "format=duration",
                      "-of", "csv=p=0", str(path)).strip())


def download(url: str, dest: Path) -> None:
    host = urlparse(url).netloc
    try:
        with requests.get(url, stream=True, timeout=120) as response:
            response.raise_for_status()
            with open(dest, "wb") as out:
                for chunk in response.iter_content(1 << 16):
                    out.write(chunk)
    except requests.RequestException as err:
        dest.unlink(missing_ok=True)
        raise StudioError(
            f"Could not download from {host}: {err}. If this session's network blocks "
            f"{host}, allow that host in the environment settings, or save the file "
            f"locally and record its path instead.") from None


def _local(project: Project, job: dict, fetch) -> Path:
    """The job's result as a file on disk, downloading it the first time if it is a link."""
    location = job["result"]
    if re.match(r"https?://", location):
        ext = Path(urlparse(location).path).suffix or _DEFAULT_EXT[job["kind"]]
        dest = project.dir / "assets" / f"{job['id']}{ext}"
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            fetch(location, dest)
        return dest
    for path in (Path(location), project.dir / location):
        if path.exists():
            return path.resolve()
    raise StudioError(f"The file recorded for {job['id']} is missing: {location}")


# ---- timing ----------------------------------------------------------------

def timeline(project: Project, voice_seconds: dict[str, float]) -> list[dict]:
    """When each shot is on screen, with every scene scaled to its real voiceover length."""
    shots, clock = [], 0.0
    for scene in project.data["scenes"]:
        scale = voice_seconds[scene["id"]] / scene["seconds"]
        for shot in scene["shots"]:
            seconds = shot["seconds"] * scale
            shots.append({"shot": shot["id"], "start": clock, "seconds": seconds,
                          "motion": shot["motion"]})
            clock += seconds
    return shots


def captions(project: Project, voice_seconds: dict[str, float]) -> list[dict]:
    cues, clock = [], 0.0
    for scene in project.data["scenes"]:
        per_word = voice_seconds[scene["id"]] / scene["words"]
        for sentence in re.split(r"(?<=[.!?])\s+", scene["text"]):
            words = sentence.split()
            pieces = -(-len(words) // _CAPTION_WORDS)  # ceiling
            for i in range(pieces):
                part = words[i * len(words) // pieces:(i + 1) * len(words) // pieces]
                end = clock + len(part) * per_word
                cues.append({"start": round(clock, 3), "end": round(end, 3), "text": " ".join(part)})
                clock = end
    return cues


def _stamp(seconds: float) -> str:
    ms = round(seconds * 1000)
    return f"{ms // 3_600_000:02d}:{ms // 60_000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def _srt(cues: list[dict]) -> str:
    return "\n".join(
        f"{n}\n{_stamp(c['start'])} --> {_stamp(c['end'])}\n{c['text']}\n"
        for n, c in enumerate(cues, start=1))


# ---- picture ---------------------------------------------------------------

def _camera(motion: str, frames: int) -> str:
    centre_x, centre_y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    travel = "(iw-iw/zoom)"
    z, x = {
        "zoom_in": (f"1+{_ZOOM}*on/{frames}", centre_x),
        "zoom_out": (f"{1 + _ZOOM}-{_ZOOM}*on/{frames}", centre_x),
        "pan_right": (f"{1 + _ZOOM}", f"{travel}*on/{frames}"),
        "pan_left": (f"{1 + _ZOOM}", f"{travel}*(1-on/{frames})"),
    }.get(motion, (f"1+{_ZOOM}*on/{frames}", centre_x))
    return f"z='{z}':x='{x}':y='{centre_y}'"


def _still_clip(image: Path, out: Path, frames: int, motion: str, w: int, h: int, fps: int) -> None:
    # Working at double size keeps the slow zoom smooth instead of jittery.
    vf = (f"scale={w * 2}:{h * 2}:force_original_aspect_ratio=increase,crop={w * 2}:{h * 2},"
          f"zoompan={_camera(motion, frames)}:d={frames}:s={w}x{h}:fps={fps}")
    _run("ffmpeg", "-y", "-v", "error", "-i", str(image), "-vf", vf,
         "-frames:v", str(frames), "-r", str(fps), *_ENCODE, str(out))


def _video_clip(video: Path, out: Path, frames: int, w: int, h: int, fps: int) -> None:
    # A clip shorter than its shot holds on its last frame.
    vf = (f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps={fps},"
          f"tpad=stop_mode=clone:stop_duration={frames / fps + 1}")
    _run("ffmpeg", "-y", "-v", "error", "-i", str(video), "-vf", vf,
         "-frames:v", str(frames), "-an", "-r", str(fps), *_ENCODE, str(out))


# ---- the build -------------------------------------------------------------

def assemble(project: Project, fetch=download) -> dict:
    jobs = {job["id"]: job for job in project.jobs}
    missing = [j["id"] for j in project.jobs
               if j["kind"] in ("voiceover", "image") and j["status"] != "done"]
    if missing:
        raise StudioError(
            f"Not ready to assemble: {len(missing)} voiceover or picture jobs are not done "
            f"({', '.join(missing[:8])}{'...' if len(missing) > 8 else ''}).")

    w, h = project.preset["resolution"]
    fps = project.preset["fps"]
    build = project.dir / "build"
    shutil.rmtree(build, ignore_errors=True)
    build.mkdir(parents=True)

    voices = [_local(project, jobs[f"vo-{s['id']}"], fetch) for s in project.data["scenes"]]
    voice_seconds = {s["id"]: _seconds(v) for s, v in zip(project.data["scenes"], voices)}
    total = sum(voice_seconds.values())

    # Picture: one clip per shot, cut on whole-frame boundaries so timing never drifts.
    listing = []
    for n, shot in enumerate(timeline(project, voice_seconds)):
        frames = round((shot["start"] + shot["seconds"]) * fps) - round(shot["start"] * fps)
        if frames < 1:
            continue
        out = build / f"{n:04d}.mp4"
        motion_job = jobs.get(f"mot-{shot['shot']}")
        if motion_job and motion_job["status"] == "done":
            _video_clip(_local(project, motion_job, fetch), out, frames, w, h, fps)
        else:
            _still_clip(_local(project, jobs[f"img-{shot['shot']}"], fetch),
                        out, frames, shot["motion"], w, h, fps)
        listing.append(f"file '{out.resolve()}'")
    (build / "clips.txt").write_text("\n".join(listing))
    _run("ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", str(build / "clips.txt"), "-c", "copy", str(build / "picture.mp4"))

    # Sound: the voiceovers end to end, with music underneath if there is any.
    inputs, chains = ["-i", str(build / "picture.mp4")], []
    for i, voice in enumerate(voices, start=1):
        inputs += ["-i", str(voice)]
        chains.append(f"[{i}:a]{_AUDIO}[v{i}]")
    labels = "".join(f"[v{i}]" for i in range(1, len(voices) + 1))
    chains.append(f"{labels}concat=n={len(voices)}:v=0:a=1[voice]")
    mix = "[voice]"
    music = jobs.get("music")
    if music and music["status"] == "done":
        inputs += ["-stream_loop", "-1", "-i", str(_local(project, music, fetch))]
        fade = max(0.0, total - 2)
        chains.append(f"[{len(voices) + 1}:a]{_AUDIO},volume={project.preset['music_db']}dB,"
                      f"afade=t=out:st={fade:.3f}:d=2[music]")
        chains.append("[voice][music]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[mix]")
        mix = "[mix]"

    video = project.dir / f"{project.slug}.mp4"
    _run("ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(chains),
         "-map", "0:v", "-map", mix, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-t", f"{total:.3f}", "-movflags", "+faststart", str(video))

    subtitle = project.dir / f"{project.slug}.srt"
    subtitle.write_text(_srt(captions(project, voice_seconds)))
    shutil.rmtree(build, ignore_errors=True)
    return {"video": str(video), "captions": str(subtitle), "seconds": round(total, 1)}
