import pytest

from studio import StudioError
from studio.presets import get_preset, preset_names
from studio.router import pick_route, routes_for

PLANNER_AND_ASSEMBLER_FIELDS = (
    "resolution", "fps", "wpm", "shot_seconds", "hero_every", "scene_chars",
    "style", "voice", "music", "music_db", "motion",
)


def test_history_preset_is_landscape_1080p():
    assert get_preset("history")["resolution"] == [1920, 1080]


def test_short_preset_is_vertical_and_keeps_its_parent_look():
    short, parent = get_preset("history_short"), get_preset("history")
    assert short["resolution"] == [1080, 1920]
    assert short["style"] == parent["style"]


def test_unknown_preset_error_lists_the_real_ones():
    with pytest.raises(StudioError) as err:
        get_preset("nope")
    assert "history" in str(err.value)


@pytest.mark.parametrize("name", preset_names())
def test_preset_has_every_field_the_engine_reads(name):
    missing = [f for f in PLANNER_AND_ASSEMBLER_FIELDS if f not in get_preset(name)]
    assert missing == []


@pytest.mark.parametrize("kind", ["voiceover", "image", "motion", "music"])
def test_every_paid_route_says_how_to_get_a_quote(kind):
    for route in routes_for(kind):
        assert route["connector"] and route["tool"] and route["wallet"]
        if route["paid"]:
            assert route["quote"], f"{route['id']} is paid but has no quote step"


def test_pick_route_defaults_to_first_choice():
    assert pick_route("voiceover")["id"] == routes_for("voiceover")[0]["id"]


def test_pick_route_skips_routes_already_tried():
    first, second = routes_for("image")[:2]
    assert pick_route("image", skip={first["id"]})["id"] == second["id"]


def test_pick_route_with_nothing_left_raises():
    everything = {r["id"] for r in routes_for("image")}
    with pytest.raises(StudioError):
        pick_route("image", skip=everything)


def test_unknown_job_kind_raises():
    with pytest.raises(StudioError):
        routes_for("hologram")
