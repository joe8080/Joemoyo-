import json
import shutil
import subprocess

import pytest
from PIL import Image

from studio import StudioError
from studio.assemble import assemble, captions, timeline
from studio.ledger import Project
from studio.presets import get_preset

# Two scenes at 120 words a minute: 6 words (3s, 2 shots) and 8 words (4s, 2 shots).
SCRIPT = "The harbour burned for six days.\n\nRome had waited a century for this moment."
SMALL = {"resolution": [320, 180], "fps": 10, "wpm": 120, "shot_seconds": 2, "scene_chars": 45}


def make_project(tmp_path, **overrides):
    preset = {**get_preset("history"), **SMALL, **overrides}
    return Project.create(tmp_path / "projects", "Carthage", "history", SCRIPT, preset=preset)


def tone(path, seconds):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                    f"sine=frequency=330:duration={seconds}", str(path)], check=True)
    return str(path)


def picture(path, colour):
    Image.new("RGB", (640, 360), colour).save(path)
    return str(path)


def clip(path, seconds):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                    f"testsrc=size=640x360:rate=10:duration={seconds}",
                    "-pix_fmt", "yuv420p", str(path)], check=True)
    return str(path)


def complete(project, job_id, location):
    job = project.job(job_id)
    if job["paid"]:
        project.set_budget({job["wallet"]: 10_000})
        project.record_quote(1, [job_id])
    project.start(job_id)
    project.finish(job_id, location)


def fill(project, tmp_path, music=True):
    complete(project, "vo-s01", tone(tmp_path / "vo1.wav", 2.0))
    complete(project, "vo-s02", tone(tmp_path / "vo2.wav", 3.0))
    for n, shot in enumerate(project.shots()):
        complete(project, f"img-{shot['id']}", picture(tmp_path / f"{shot['id']}.png", (40 * n, 60, 90)))
    if music:
        complete(project, "music", tone(tmp_path / "music.wav", 1.0))


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=codec_type,width,height", "-of", "json", str(path)],
        check=True, capture_output=True, text=True).stdout
    info = json.loads(out)
    video = next(s for s in info["streams"] if s["codec_type"] == "video")
    return {
        "seconds": float(info["format"]["duration"]),
        "size": (video["width"], video["height"]),
        "has_audio": any(s["codec_type"] == "audio" for s in info["streams"]),
    }


def test_timeline_stretches_each_scenes_shots_to_its_real_voice_length(tmp_path):
    project = make_project(tmp_path)
    shots = timeline(project, {"s01": 4.0, "s02": 2.0})
    assert [(s["shot"], s["start"], s["seconds"]) for s in shots] == [
        ("s01-1", 0.0, 2.0), ("s01-2", 2.0, 2.0), ("s02-1", 4.0, 1.0), ("s02-2", 5.0, 1.0),
    ]


def test_captions_follow_the_real_voice_timing(tmp_path):
    project = make_project(tmp_path)
    cues = captions(project, {"s01": 4.0, "s02": 2.0})
    assert [(c["start"], c["end"], c["text"]) for c in cues] == [
        (0.0, 4.0, "The harbour burned for six days."),
        (4.0, 6.0, "Rome had waited a century for this moment."),
    ]


def test_a_long_sentence_is_broken_into_readable_caption_lines(tmp_path):
    script = " ".join(f"word{n}" for n in range(30)) + "."
    project = Project.create(tmp_path, "Long", "history", script,
                             preset={**get_preset("history"), **SMALL, "scene_chars": 1500})
    cues = captions(project, {"s01": 15.0})
    assert [len(c["text"].split()) for c in cues] == [10, 10, 10]
    assert cues[-1]["end"] == pytest.approx(15.0)


def test_assemble_builds_a_video_as_long_as_the_narration(tmp_path):
    project = make_project(tmp_path)
    fill(project, tmp_path)
    result = assemble(project)
    info = probe(result["video"])
    assert info["seconds"] == pytest.approx(5.0, abs=0.3)
    assert info["size"] == (320, 180)
    assert info["has_audio"]


def test_assemble_writes_a_caption_file_beside_the_video(tmp_path):
    project = make_project(tmp_path)
    fill(project, tmp_path)
    text = open(assemble(project)["captions"]).read()
    assert "00:00:00,000 --> 00:00:02,000\nThe harbour burned for six days." in text


def test_music_is_optional(tmp_path):
    project = make_project(tmp_path)
    fill(project, tmp_path, music=False)
    info = probe(assemble(project)["video"])
    assert info["has_audio"] and info["seconds"] == pytest.approx(5.0, abs=0.3)


def test_a_missing_picture_stops_the_build_and_is_named(tmp_path):
    project = make_project(tmp_path)
    complete(project, "vo-s01", tone(tmp_path / "vo1.wav", 2.0))
    complete(project, "vo-s02", tone(tmp_path / "vo2.wav", 3.0))
    with pytest.raises(StudioError, match="img-s01-1"):
        assemble(project)


def test_an_animated_clip_replaces_its_still_and_keeps_the_timing(tmp_path):
    project = make_project(tmp_path, hero_every=1)
    fill(project, tmp_path)
    complete(project, "mot-s01-1", clip(tmp_path / "hero.mp4", 0.5))  # shorter than its shot
    info = probe(assemble(project)["video"])
    assert info["seconds"] == pytest.approx(5.0, abs=0.3)


def test_results_stored_as_links_are_downloaded_once(tmp_path):
    project = make_project(tmp_path)
    fill(project, tmp_path, music=False)
    source = picture(tmp_path / "remote.png", (200, 10, 10))
    job = project.job("img-s01-1")
    job["result"] = "https://cdn.example/pictures/harbour.png?sig=abc"
    project.save()

    fetched = []

    def fake_fetch(url, dest):
        fetched.append(url)
        shutil.copy(source, dest)

    assemble(project, fetch=fake_fetch)
    assemble(project, fetch=fake_fetch)
    assert fetched == ["https://cdn.example/pictures/harbour.png?sig=abc"]
    assert (project.dir / "assets" / "img-s01-1.png").exists()
