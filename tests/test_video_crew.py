"""Unit tests for the deterministic parts of the video production crew.

These need no API keys, network, or ffmpeg — they exercise the editor and
helpers, and verify the editor's manifest round-trips through video_agent.
"""

import pytest

from agents.video._utils import extract_json, slugify
from agents.video.manifest_editor import ManifestEditorAgent
from video_agent.utils.manifest import parse_manifest


def test_extract_json_tolerates_prose_and_fences():
    assert extract_json('prose before {"a": 1} after') == {"a": 1}
    assert extract_json("```json\n{\"b\": [1, 2]}\n```") == {"b": [1, 2]}
    assert extract_json('[{"x": 1}]') == [{"x": 1}]


def test_extract_json_raises_when_absent():
    with pytest.raises(ValueError):
        extract_json("no json here at all")


def test_slugify():
    assert slugify("Great Zimbabwe: The Stone City!") == "great-zimbabwe-the-stone-city"
    assert slugify("") == "untitled"


def _shotlist():
    return {"clips": [
        {"sequence": 1, "image_prompt": "stone walls", "caption": "Great Zimbabwe",
         "pan": "zoom-in", "duration": 9},
        {"sequence": 2, "image_prompt": "great enclosure", "caption": "The Great Enclosure",
         "pan": "left-to-right", "duration": 8},
        {"sequence": 3, "image_prompt": "soapstone birds", "caption": "",
         "pan": "not-a-pan", "duration": 7},
    ]}


def test_editor_fits_durations_to_narration():
    ed = ManifestEditorAgent(crossfade=1.0)
    res = ed.assemble(_shotlist(), narration_seconds=30.0)
    clips = res["manifest"]["clips"]
    total = sum(c["duration"] for c in clips) - 1.0 * (len(clips) - 1)
    assert round(total, 1) == 30.0


def test_editor_clamps_pops_and_fixes_invalid_pan():
    ed = ManifestEditorAgent(crossfade=1.0)
    res = ed.assemble(_shotlist(), narration_seconds=5.0)  # tiny -> clamp kicks in
    clips = res["manifest"]["clips"]
    assert all(c["duration"] >= 2 * 1.0 + 0.5 for c in clips)  # no zoom "pop"
    assert clips[2]["pan"] == "zoom-in"  # invalid pan falls back


def test_editor_output_roundtrips_through_video_agent():
    ed = ManifestEditorAgent(crossfade=1.0)
    res = ed.assemble(_shotlist(), narration_seconds=30.0)
    parsed = parse_manifest(res["manifest"])
    assert len(parsed.clips) == 3
    assert parsed.clips[0].image.endswith(".png")


def test_editor_builds_srt_only_for_captioned_clips():
    ed = ManifestEditorAgent(crossfade=1.0)
    res = ed.assemble(_shotlist(), narration_seconds=30.0)
    # Two of three clips have captions.
    assert res["srt"].count("-->") == 2


def test_editor_raises_on_empty_shotlist():
    with pytest.raises(ValueError):
        ManifestEditorAgent().assemble({"clips": []})
