import pytest

from video_agent.channels import available_channels, get_preset
from video_agent.channels.base import ChannelPreset


def test_available_channels_exposes_all_variants():
    names = available_channels()
    assert "history" in names
    assert "finance" in names
    assert "finance.long" in names
    assert "finance.short" in names


def test_get_preset_returns_channel_preset():
    history = get_preset("history")
    assert isinstance(history, ChannelPreset)
    assert history.name == "history"
    assert history.width == 1920 and history.height == 1080


def test_history_is_horizontal_finance_short_is_vertical():
    assert not get_preset("history").is_vertical
    assert not get_preset("finance.long").is_vertical
    assert get_preset("finance.short").is_vertical


def test_finance_short_uses_60fps_for_shorts():
    assert get_preset("finance.short").fps == 60


def test_history_pacing_is_slower_than_finance():
    assert get_preset("history").seconds_per_image > get_preset("finance.long").seconds_per_image
    assert get_preset("finance.long").seconds_per_image > get_preset("finance.short").seconds_per_image


def test_history_has_sepia_colorbalance_finance_has_saturation_boost():
    history_grade = get_preset("history").color_grade
    finance_grade = get_preset("finance.long").color_grade
    assert "colorbalance" in history_grade
    assert "saturation=1" in finance_grade    # i.e. saturation >= 1.0


def test_get_preset_rejects_unknown_channel():
    with pytest.raises(KeyError):
        get_preset("cooking")


def test_finance_default_alias_maps_to_long():
    assert get_preset("finance") is get_preset("finance.long")


def test_preset_is_immutable():
    # dataclass(frozen=True) — assignment must raise.
    with pytest.raises(Exception):
        get_preset("history").fps = 120
