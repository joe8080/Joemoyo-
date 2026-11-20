import json
import os
import subprocess
import sys

import pytest

SCRIPT = (
    "The harbour burned for six days. [B-ROLL: harbour in flames]\n\n"
    + " ".join(["stone"] * 60) + "."
)


@pytest.fixture
def studio(tmp_path):
    """Run `python -m studio ...` against a throwaway projects folder."""
    env = {**os.environ, "STUDIO_HOME": str(tmp_path / "projects")}
    (tmp_path / "script.md").write_text(SCRIPT)

    def run(*args, stdin=None):
        done = subprocess.run([sys.executable, "-m", "studio", *args], env=env,
                              input=stdin, capture_output=True, text=True)
        return done.returncode, json.loads(done.stdout)

    run.script = str(tmp_path / "script.md")
    return run


@pytest.fixture
def carthage(studio):
    studio("new", "--title", "Carthage", "--preset", "history", "--script", studio.script)
    return studio


def test_presets_lists_the_house_styles(studio):
    code, out = studio("presets")
    assert code == 0 and "history" in out


def test_new_plans_the_video_and_says_what_to_do_next(studio):
    code, out = studio("new", "--title", "Carthage", "--preset", "history", "--script", studio.script)
    assert code == 0
    assert (out["slug"], out["shots"], out["needs_prompt"]) == ("carthage", 4, 4)


def test_a_mistake_exits_non_zero_with_a_plain_message(studio):
    code, out = studio("new", "--title", "X", "--preset", "nope", "--script", studio.script)
    assert code == 1 and "history" in out["error"]


def test_list_shows_existing_projects(carthage):
    assert [p["slug"] for p in carthage("list")[1]] == ["carthage"]


def test_prompts_are_read_from_json_on_stdin(carthage):
    carthage("prompts", "carthage", "-", stdin=json.dumps({"s01-1": "a harbour on fire"}))
    ready = carthage("next", "carthage")[1]["ready"]
    assert "a harbour on fire" in next(j for j in ready if j["id"] == "img-s01-1")["do"]["prompt"]


def test_start_reports_which_job_the_budget_guard_refused(carthage):
    carthage("prompts", "carthage", "-", stdin=json.dumps({"s01-1": "a", "s01-2": "b"}))
    carthage("quote", "carthage", "30", "--kind", "image")
    carthage("budget", "carthage", "openart=50")
    code, out = carthage("start", "carthage", "img-s01-1", "img-s01-2")
    assert out["started"] == ["img-s01-1"]
    assert out["refused"]["job"] == "img-s01-2" and "cap" in out["refused"]["why"]
    assert out["wallets"]["openart"]["spent"] == 30


def test_done_records_several_results_including_links_with_equals_signs(carthage):
    carthage("start", "carthage", "music")
    code, out = carthage("done", "carthage", "music=https://cdn.example/track.mp3?sig=a=b")
    assert code == 0 and out["jobs"]["music"] == {"done": 1}


def test_fail_then_reroute_moves_the_job_to_the_next_tool(carthage):
    carthage("start", "carthage", "music")
    carthage("fail", "carthage", "music", "nothing in the catalog fits")
    code, out = carthage("reroute", "carthage", "music")
    assert out["rerouted"] == [{"job": "music", "tool": "generate_music", "connector": "Artlist"}]
