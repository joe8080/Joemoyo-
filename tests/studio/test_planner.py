import pytest

from studio import StudioError
from studio.planner import parse_script, plan

PRESET = {
    "wpm": 120, "shot_seconds": 7, "hero_every": 0, "scene_chars": 1500,
    "motion": ["zoom_in", "pan_right"],
}

AGENT_SCRIPT = """TITLE: The Fall of Carthage
TAGS: rome, carthage, punic wars

## FULL SCRIPT

[TIMESTAMP: 00:00]
The harbour burned for six days. [PAUSE] Nobody came. [B-ROLL: ancient harbour in flames at night]

## Chapter One

**Rome** had waited a century for this.
"""


def words(n, word="stone"):
    return " ".join([word] * n) + "."


def test_parse_keeps_only_the_spoken_words():
    paragraphs = parse_script(AGENT_SCRIPT)
    assert [p["text"] for p in paragraphs] == [
        "The harbour burned for six days. Nobody came.",
        "Rome had waited a century for this.",
    ]


def test_parse_keeps_broll_notes_as_picture_briefs():
    assert parse_script(AGENT_SCRIPT)[0]["briefs"] == ["ancient harbour in flames at night"]


def test_plain_narration_needs_no_markers():
    assert parse_script("One line.\n\nAnother line.")[1]["text"] == "Another line."


def test_empty_script_is_refused():
    with pytest.raises(StudioError):
        plan("  \n[PAUSE]\n", PRESET)


def test_scene_length_follows_narration_pace():
    scene = plan(words(60), PRESET)[0]
    assert scene["seconds"] == pytest.approx(30.0)


def test_scene_is_cut_into_shots_near_the_preset_shot_length():
    scene = plan(words(60), PRESET)[0]  # 30s at 7s a shot
    assert len(scene["shots"]) == 4
    assert sum(s["seconds"] for s in scene["shots"]) == pytest.approx(scene["seconds"])


def test_shots_share_out_every_word_of_the_scene_once():
    scene = plan(words(60), PRESET)[0]
    assert " ".join(s["narration"] for s in scene["shots"]) == scene["text"]


def test_short_paragraphs_are_packed_into_one_voiceover_scene():
    para = words(100)  # 600 characters
    scenes = plan("\n\n".join([para, para, para]), PRESET)
    assert [len(s["text"]) for s in scenes] == [1201, 600]


def test_a_long_paragraph_is_split_at_sentence_ends():
    sentence = words(40)  # 240 characters
    scenes = plan(" ".join([sentence] * 20), PRESET)
    assert all(len(s["text"]) <= 1500 for s in scenes)
    assert all(s["text"].endswith(".") for s in scenes)
    assert sum(s["words"] for s in scenes) == 800


def test_broll_brief_lands_on_a_shot_and_the_rest_wait_for_a_prompt():
    shots = plan(AGENT_SCRIPT + "\n\n" + words(60), PRESET)[0]["shots"]
    assert shots[0]["brief"] == "ancient harbour in flames at night"
    assert shots[-1]["brief"] is None
    assert all(s["prompt"] is None for s in shots)


def test_camera_moves_cycle_through_the_preset_list():
    shots = plan(words(60), PRESET)[0]["shots"]
    assert [s["motion"] for s in shots] == ["zoom_in", "pan_right", "zoom_in", "pan_right"]


def test_hero_every_three_marks_every_third_shot_for_animation():
    shots = [s for scene in plan(words(120), {**PRESET, "hero_every": 3}) for s in scene["shots"]]
    assert [i for i, s in enumerate(shots) if s["hero"]] == [0, 3, 6]


def test_no_hero_shots_when_hero_every_is_zero():
    assert not any(s["hero"] for scene in plan(words(120), PRESET) for s in scene["shots"])


def test_ids_are_stable_and_readable():
    scenes = plan(words(60), PRESET)
    assert scenes[0]["id"] == "s01"
    assert [s["id"] for s in scenes[0]["shots"]] == ["s01-1", "s01-2", "s01-3", "s01-4"]
