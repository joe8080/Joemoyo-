import json
from pathlib import Path

import pytest

from video_agent.utils.manifest import (
    ClipSpec,
    Manifest,
    ManifestError,
    load_manifest,
    parse_manifest,
)


def test_parse_minimal_manifest():
    m = parse_manifest({"clips": [{"image": "a.jpg"}]})
    assert isinstance(m, Manifest)
    assert m.clips == [ClipSpec(image="a.jpg")]


def test_parse_full_manifest():
    m = parse_manifest({
        "clips": [
            {"image": "01.jpg", "duration": 8.0, "pan": "left-to-right", "caption": "Rome"},
            {"image": "02.jpg", "duration": 6.5, "pan": "zoom-in"},
        ]
    })
    assert len(m.clips) == 2
    assert m.clips[0].caption == "Rome"
    assert m.clips[0].pan == "left-to-right"
    assert m.clips[1].caption is None


def test_invalid_top_level_raises():
    with pytest.raises(ManifestError):
        parse_manifest({})
    with pytest.raises(ManifestError):
        parse_manifest({"clips": []})


def test_missing_image_raises():
    with pytest.raises(ManifestError):
        parse_manifest({"clips": [{"pan": "zoom-in"}]})


def test_invalid_pan_raises():
    with pytest.raises(ManifestError):
        parse_manifest({"clips": [{"image": "a.jpg", "pan": "diagonal"}]})


def test_invalid_duration_raises():
    with pytest.raises(ManifestError):
        parse_manifest({"clips": [{"image": "a.jpg", "duration": -1}]})
    with pytest.raises(ManifestError):
        parse_manifest({"clips": [{"image": "a.jpg", "duration": "fast"}]})


def test_load_manifest_from_file(tmp_path: Path):
    f = tmp_path / "m.json"
    f.write_text(json.dumps({"clips": [{"image": "a.jpg", "duration": 3}]}))
    m = load_manifest(f)
    assert m.clips[0].duration == 3.0
