import pytest

from video_agent.channels import get_preset
from video_agent.effects.ken_burns import (
    UPSCALE_FACTOR,
    build_ken_burns_filter,
    build_clip_ffmpeg_args,
)


def test_filter_includes_upscale_zoompan_setsar():
    preset = get_preset("history")
    f = build_ken_burns_filter(preset=preset, duration=4.0, pan="zoom-in")
    assert f"scale=iw*{UPSCALE_FACTOR}:ih*{UPSCALE_FACTOR}:flags=lanczos" in f
    assert "zoompan=" in f
    assert "setsar=1" in f


def test_filter_embeds_target_resolution_and_fps():
    preset = get_preset("finance.short")  # 1080x1920 @ 60fps
    f = build_ken_burns_filter(preset=preset, duration=3.0, pan="zoom-in")
    assert "s=1080x1920" in f
    assert "fps=60" in f


def test_duration_to_frames_respects_fps():
    preset = get_preset("history")       # 30 fps
    f = build_ken_burns_filter(preset=preset, duration=5.0, pan="zoom-in")
    # 5 seconds * 30 fps = 150 frames.
    assert ":d=150:" in f


def test_zoom_out_inverts_z_range():
    preset = get_preset("finance.long")
    f_in = build_ken_burns_filter(preset=preset, duration=4.0, pan="zoom-in")
    f_out = build_ken_burns_filter(preset=preset, duration=4.0, pan="zoom-out")
    # Both use the same extremes but in opposite order. The z expression
    # starts with the "from" value — make sure they differ.
    assert f_in != f_out


def test_pan_directions_produce_distinct_x_or_y_expressions():
    preset = get_preset("history")
    filters = {
        pan: build_ken_burns_filter(preset=preset, duration=4.0, pan=pan)
        for pan in ("zoom-in", "left-to-right", "right-to-left",
                    "top-to-bottom", "bottom-to-top")
    }
    # All five must be distinct strings.
    assert len(set(filters.values())) == 5


def test_unknown_pan_raises():
    preset = get_preset("history")
    with pytest.raises(ValueError):
        build_ken_burns_filter(preset=preset, duration=4.0, pan="diagonal")  # type: ignore[arg-type]


def test_zero_duration_raises():
    preset = get_preset("history")
    with pytest.raises(ValueError):
        build_ken_burns_filter(preset=preset, duration=0, pan="zoom-in")


def test_color_grade_is_appended_to_filter():
    preset = get_preset("history")
    f = build_ken_burns_filter(preset=preset, duration=4.0, pan="zoom-in")
    # The preset's color_grade string must appear somewhere in the chain.
    assert preset.color_grade.split(",")[0] in f


def test_clip_args_includes_loop_and_duration():
    preset = get_preset("history")
    args = build_clip_ffmpeg_args(
        image="/tmp/foo.jpg",
        output="/tmp/foo.mp4",
        preset=preset,
        duration=6.5,
        pan="zoom-in",
    )
    assert "-loop" in args and "1" in args
    assert "-t" in args
    # ``-t 6.500`` should be present.
    assert any(a.startswith("6.") for a in args)
    assert args[-1] == "/tmp/foo.mp4"
