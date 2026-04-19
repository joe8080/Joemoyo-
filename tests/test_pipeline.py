"""Tests for pipeline planning logic that doesn't require ffmpeg."""
from pathlib import Path

import pytest

from video_agent.channels import get_preset
from video_agent.pipeline import (
    discover_images,
    distribute_durations,
    plan_clips,
)
from video_agent.utils.manifest import Manifest, ClipSpec


def _touch_images(tmp_path: Path, names):
    for n in names:
        (tmp_path / n).write_bytes(b"x")
    return tmp_path


def test_discover_images_sorted_and_filtered(tmp_path: Path):
    _touch_images(tmp_path, ["b.jpg", "a.png", "note.txt", "c.webp"])
    found = discover_images(tmp_path)
    assert [p.name for p in found] == ["a.png", "b.jpg", "c.webp"]


def test_discover_images_empty_folder_raises(tmp_path: Path):
    with pytest.raises(ValueError):
        discover_images(tmp_path)


def test_discover_images_non_directory_raises(tmp_path: Path):
    f = tmp_path / "not_a_dir"
    f.write_bytes(b"x")
    with pytest.raises(NotADirectoryError):
        discover_images(f)


def test_distribute_durations_auto_fits_to_narration():
    preset = get_preset("history")     # crossfade 1.5
    durations = distribute_durations(
        narration_seconds=60.0,
        n_clips=10,
        preset=preset,
        crossfade=preset.crossfade_seconds,
    )
    # total after fades = sum(d) - 9*1.5 ; we want it == 60.
    total = sum(durations) - (len(durations) - 1) * preset.crossfade_seconds
    assert total == pytest.approx(60.0)
    # All equal.
    assert len(set(durations)) == 1


def test_distribute_durations_explicit_override_ignores_narration():
    preset = get_preset("finance.short")
    durations = distribute_durations(
        narration_seconds=60.0,
        n_clips=5,
        preset=preset,
        crossfade=preset.crossfade_seconds,
        seconds_per_image=3.0,
    )
    assert durations == [3.0, 3.0, 3.0, 3.0, 3.0]


def test_plan_clips_without_manifest_uses_preset_pans_round_robin(tmp_path: Path):
    preset = get_preset("history")
    imgs = [tmp_path / f"{i}.jpg" for i in range(6)]
    for p in imgs:
        p.write_bytes(b"x")
    planned = plan_clips(
        images=imgs, preset=preset,
        durations=[5.0] * 6, manifest=None, seed=None,
    )
    assert len(planned) == 6
    # First 4 pans should match the preset's default_pans in order.
    assert tuple(p.pan for p in planned[:4]) == preset.default_pans
    # Round-robin: clip 4 reuses pans[0].
    assert planned[4].pan == preset.default_pans[0]


def test_plan_clips_with_seed_is_deterministic(tmp_path: Path):
    preset = get_preset("history")
    imgs = [tmp_path / f"{i}.jpg" for i in range(6)]
    for p in imgs:
        p.write_bytes(b"x")
    a = plan_clips(images=imgs, preset=preset, durations=[5.0]*6, manifest=None, seed=42)
    b = plan_clips(images=imgs, preset=preset, durations=[5.0]*6, manifest=None, seed=42)
    assert [c.pan for c in a] == [c.pan for c in b]


def test_plan_clips_manifest_resolves_images_by_basename(tmp_path: Path):
    preset = get_preset("finance.long")
    imgs = [tmp_path / "01.jpg", tmp_path / "02.jpg"]
    for p in imgs:
        p.write_bytes(b"x")
    manifest = Manifest(clips=[
        ClipSpec(image="01.jpg", duration=4.0, pan="zoom-in", caption="A"),
        ClipSpec(image="02.jpg", duration=5.0, pan="zoom-out", caption="B"),
    ])
    planned = plan_clips(
        images=imgs, preset=preset, durations=[4.0, 5.0],
        manifest=manifest, seed=None,
    )
    assert [p.image.name for p in planned] == ["01.jpg", "02.jpg"]
    assert planned[0].caption == "A"
    assert planned[0].duration == 4.0
    assert planned[1].pan == "zoom-out"
