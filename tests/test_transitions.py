import pytest

from video_agent.effects.transitions import build_xfade_graph, total_duration


def test_total_duration_empty_is_zero():
    assert total_duration([], 1.0) == 0.0


def test_total_duration_single_clip_ignores_crossfade():
    assert total_duration([5.0], 1.0) == 5.0


def test_total_duration_subtracts_crossfade_per_join():
    # 3 clips of 4s each with a 1s crossfade: 4+4+4 - 2*1 = 10.
    assert total_duration([4.0, 4.0, 4.0], 1.0) == pytest.approx(10.0)


def test_xfade_graph_rejects_empty():
    with pytest.raises(ValueError):
        build_xfade_graph([], crossfade=1.0)


def test_xfade_graph_single_clip_uses_copy_not_xfade():
    graph, label = build_xfade_graph([5.0], crossfade=1.0)
    assert "xfade" not in graph
    assert label == "vout"
    assert graph.endswith("[vout]")


def test_xfade_graph_zero_crossfade_uses_concat():
    graph, label = build_xfade_graph([4.0, 4.0, 4.0], crossfade=0.0)
    assert "concat=n=3" in graph
    assert "xfade" not in graph
    assert label == "vout"


def test_xfade_graph_two_clips_has_one_xfade_with_correct_offset():
    # Two 5s clips, 1.5s crossfade — the xfade offset for the boundary is
    # durations[0] - crossfade = 3.5.
    graph, label = build_xfade_graph([5.0, 5.0], crossfade=1.5)
    assert label == "vout"
    assert "xfade=transition=fade:duration=1.5:offset=3.5" in graph


def test_xfade_graph_three_clips_accumulates_offsets():
    # d = [4, 6, 5], x = 1. Offsets:
    #   first xfade:  running=4,         offset = 4 - 1 = 3
    #   after fade: running = 4 + 6 - 1 = 9
    #   second xfade: offset = 9 - 1 = 8
    graph, _ = build_xfade_graph([4.0, 6.0, 5.0], crossfade=1.0)
    assert "offset=3" in graph
    assert "offset=8" in graph


def test_xfade_graph_uses_custom_transition_name():
    graph, _ = build_xfade_graph([4.0, 4.0], crossfade=0.5, transition="slideleft")
    assert "transition=slideleft" in graph
