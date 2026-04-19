import pytest

from video_agent.cli import _build_parser
from video_agent.channels import available_channels


def test_parser_accepts_all_channel_presets():
    parser = _build_parser()
    for ch in available_channels():
        args = parser.parse_args([
            "--channel", ch,
            "--images", "./img",
            "--audio", "narr.mp3",
            "--out", "out.mp4",
        ])
        assert args.channel == ch


def test_parser_rejects_unknown_channel():
    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([
            "--channel", "cooking",
            "--images", "./img",
            "--audio", "narr.mp3",
            "--out", "out.mp4",
        ])


def test_parser_requires_images_audio_out():
    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--channel", "history"])


def test_dry_run_flag_is_parsed():
    parser = _build_parser()
    args = parser.parse_args([
        "--channel", "finance.short",
        "--images", "./img",
        "--audio", "narr.mp3",
        "--out", "out.mp4",
        "--dry-run",
    ])
    assert args.dry_run is True
