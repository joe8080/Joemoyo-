import pytest

from studio import BudgetError, StudioError
from studio.ledger import Project
from studio.presets import get_preset

# 66 words at the history pace is about 27 seconds: one scene, four shots.
SCRIPT = (
    "The harbour burned for six days. [B-ROLL: harbour in flames]\n\n"
    + " ".join(["stone"] * 60) + "."
)


@pytest.fixture
def project(tmp_path):
    return Project.create(tmp_path, title="Fall of Carthage!", preset_name="history", script=SCRIPT)


@pytest.fixture
def hero_project(tmp_path):
    preset = {**get_preset("history"), "hero_every": 2}
    return Project.create(tmp_path, "Hero cut", "history", SCRIPT, preset=preset)


def ids(jobs):
    return [j["id"] for j in jobs]


def test_create_saves_a_project_that_loads_back_identically(project, tmp_path):
    assert project.slug == "fall-of-carthage"
    assert Project.load(tmp_path, "fall-of-carthage").data == project.data


def test_a_second_project_with_the_same_title_never_overwrites_the_first(project, tmp_path):
    with pytest.raises(StudioError, match="already exists"):
        Project.create(tmp_path, "Fall of Carthage!", "history", SCRIPT)


def test_loading_a_missing_project_names_the_ones_that_exist(project, tmp_path):
    with pytest.raises(StudioError, match="fall-of-carthage"):
        Project.load(tmp_path, "nope")


def test_one_voiceover_per_scene_one_picture_per_shot_one_music_track(project):
    assert ids(project.jobs) == [
        "vo-s01", "img-s01-1", "img-s01-2", "img-s01-3", "img-s01-4", "music",
    ]


def test_hero_shots_also_get_an_animation_job(hero_project):
    assert [j for j in ids(hero_project.jobs) if j.startswith("mot-")] == ["mot-s01-1", "mot-s01-3"]


def test_each_job_starts_on_the_first_choice_tool(project):
    job = project.job("vo-s01")
    assert (job["route"], job["wallet"], job["connector"]) == (
        "elevenlabs_speech", "elevenlabs", "ElevenLabs")


def test_pictures_are_not_ready_until_they_have_a_prompt(project):
    queue = project.next_jobs()
    assert ids(queue["ready"]) == ["vo-s01", "music"]
    assert ids(queue["needs_prompt"]) == ["img-s01-1", "img-s01-2", "img-s01-3", "img-s01-4"]


def test_needs_prompt_shows_the_narration_and_brief_to_write_from(project):
    first = project.next_jobs()["needs_prompt"][0]
    assert first["brief"] == "harbour in flames"
    assert first["narration"].startswith("The harbour burned")


def test_a_prompted_picture_is_ready_with_the_house_style_added(project):
    project.set_prompts({"s01-1": "a harbour on fire at night"})
    job = next(j for j in project.next_jobs()["ready"] if j["id"] == "img-s01-1")
    assert job["do"]["prompt"] == "a harbour on fire at night, " + get_preset("history")["style"]
    assert job["do"]["aspect"] == "16:9"


def test_prompt_for_an_unknown_shot_is_refused(project):
    with pytest.raises(StudioError, match="s99-9"):
        project.set_prompts({"s99-9": "nothing"})


def test_voiceover_job_carries_the_exact_text_and_voice(project):
    job = project.next_jobs()["ready"][0]
    assert job["do"]["text"] == project.data["scenes"][0]["text"]
    assert job["do"]["voice"] == get_preset("history")["voice"]


def test_animation_waits_for_its_picture(hero_project):
    hero_project.set_prompts({"s01-1": "harbour"})
    assert "mot-s01-1" in ids(hero_project.next_jobs()["waiting"])
    hero_project.set_budget({"openart": 10})
    hero_project.record_quote(2, ["img-s01-1"])
    hero_project.start("img-s01-1")
    hero_project.finish("img-s01-1", "https://cdn.example/harbour.png")
    job = next(j for j in hero_project.next_jobs()["ready"] if j["id"] == "mot-s01-1")
    assert job["do"]["source_image"] == "https://cdn.example/harbour.png"


def test_paid_job_without_a_quote_is_refused(project):
    project.set_budget({"elevenlabs": 100})
    with pytest.raises(BudgetError, match="quote"):
        project.start("vo-s01")


def test_paid_job_without_a_spending_cap_is_refused(project):
    project.record_quote(60, ["vo-s01"])
    with pytest.raises(BudgetError, match="cap"):
        project.start("vo-s01")


def test_job_within_the_cap_starts_and_is_counted_as_spent(project):
    project.set_budget({"elevenlabs": 100})
    project.record_quote(60, ["vo-s01"])
    project.start("vo-s01")
    assert project.job("vo-s01")["status"] == "running"
    assert project.spent("elevenlabs") == 60


def test_job_over_the_cap_is_refused_and_nothing_is_spent(project):
    project.set_budget({"elevenlabs": 50})
    project.record_quote(60, ["vo-s01"])
    with pytest.raises(BudgetError, match="50"):
        project.start("vo-s01")
    assert project.job("vo-s01")["status"] == "pending"
    assert project.spent("elevenlabs") == 0


def test_the_cap_counts_what_earlier_jobs_already_spent(project):
    project.set_prompts({"s01-1": "a", "s01-2": "b"})
    project.set_budget({"openart": 50})
    project.record_quote(30, ["img-s01-1", "img-s01-2"])
    project.start("img-s01-1")
    with pytest.raises(BudgetError):
        project.start("img-s01-2")


def test_quoting_by_kind_prices_every_pending_job_of_that_kind(project):
    project.record_quote(2, kind="image")
    assert [project.job(i)["quote"] for i in ids(project.jobs) if i.startswith("img-")] == [2, 2, 2, 2]


def test_a_negative_quote_is_refused(project):
    with pytest.raises(StudioError):
        project.record_quote(-1, ["vo-s01"])


def test_a_retry_after_failure_is_charged_again(project):
    project.set_budget({"elevenlabs": 200})
    project.record_quote(60, ["vo-s01"])
    project.start("vo-s01")
    project.fail("vo-s01", "timed out")
    project.start("vo-s01")
    assert project.spent("elevenlabs") == 120


def test_a_refunded_failure_gives_the_credits_back(project):
    project.set_budget({"elevenlabs": 200})
    project.record_quote(60, ["vo-s01"])
    project.start("vo-s01")
    project.fail("vo-s01", "tool refunded it", refunded=True)
    assert project.spent("elevenlabs") == 0
    assert project.job("vo-s01")["status"] == "failed"


def test_a_running_job_cannot_be_started_twice(project):
    project.set_budget({"elevenlabs": 200})
    project.record_quote(60, ["vo-s01"])
    project.start("vo-s01")
    with pytest.raises(StudioError, match="running"):
        project.start("vo-s01")
    assert project.spent("elevenlabs") == 60


def test_a_result_is_only_accepted_for_a_running_job(project):
    with pytest.raises(StudioError, match="not running"):
        project.finish("vo-s01", "https://cdn.example/vo.mp3")


def test_finishing_stores_where_the_file_is(project):
    project.set_budget({"elevenlabs": 100})
    project.record_quote(60, ["vo-s01"])
    project.start("vo-s01")
    project.finish("vo-s01", "https://cdn.example/vo.mp3")
    assert project.job("vo-s01")["status"] == "done"
    assert project.job("vo-s01")["result"] == "https://cdn.example/vo.mp3"


def test_a_free_tool_needs_no_quote_and_no_cap(project):
    project.start("music")
    assert project.job("music")["status"] == "running"


def test_reroute_moves_the_job_to_the_next_tool_and_drops_the_old_quote(project):
    project.record_quote(2, ["img-s01-1"])
    project.reroute("img-s01-1")
    job = project.job("img-s01-1")
    assert (job["route"], job["wallet"], job["quote"]) == ("higgsfield_image", "higgsfield", None)


def test_reroute_with_no_tools_left_is_refused(project):
    project.reroute("img-s01-1")
    project.reroute("img-s01-1")
    with pytest.raises(StudioError, match="none are left"):
        project.reroute("img-s01-1")


def test_a_running_job_cannot_be_rerouted(project):
    project.start("music")
    with pytest.raises(StudioError, match="running"):
        project.reroute("music")


def test_progress_survives_a_reload(project, tmp_path):
    project.set_budget({"elevenlabs": 100})
    project.record_quote(60, ["vo-s01"])
    project.start("vo-s01")
    reloaded = Project.load(tmp_path, project.slug)
    assert reloaded.job("vo-s01")["status"] == "running"
    assert reloaded.spent("elevenlabs") == 60


def test_status_totals_what_is_spent_and_what_is_still_to_come(project):
    project.set_budget({"elevenlabs": 100})
    project.record_quote(60, ["vo-s01"])
    project.record_quote(2, kind="image")
    project.start("vo-s01")
    wallets = project.status()["wallets"]
    assert wallets["elevenlabs"] == {"cap": 100, "spent": 60, "to_come": 0}
    assert wallets["openart"] == {"cap": None, "spent": 0, "to_come": 8}


def test_status_lists_paid_jobs_that_still_need_a_quote(project):
    assert "vo-s01" in project.status()["unquoted"]
    assert "music" not in project.status()["unquoted"]


def test_status_walks_through_the_next_step(project):
    assert "prompt" in project.status()["next_step"]
    project.set_prompts({f"s01-{n}": "p" for n in range(1, 5)})
    assert "quote" in project.status()["next_step"]
    project.record_quote(60, ["vo-s01"])
    project.record_quote(2, kind="image")
    assert "approve" in project.status()["next_step"]
    project.set_budget({"elevenlabs": 60, "openart": 8})
    assert "Run" in project.status()["next_step"]
    for job_id in ids(project.jobs):
        project.start(job_id)
    assert "running" in project.status()["next_step"]
    for job_id in ids(project.jobs):
        project.finish(job_id, f"https://cdn.example/{job_id}")
    assert "Assemble" in project.status()["next_step"]


@pytest.mark.parametrize("slug", ["../secrets", "a/b", "", ".."])
def test_a_project_name_cannot_reach_outside_the_projects_folder(project, tmp_path, slug):
    with pytest.raises(StudioError, match="letters, numbers and dashes"):
        Project.load(tmp_path, slug)
