from video_agent.captions import build_drawtext_filter, build_subtitles_filter
from video_agent.channels import get_preset


def test_drawtext_escapes_colons_in_text():
    style = get_preset("finance.short").caption
    f = build_drawtext_filter("Breaking: markets move", style)
    assert f.startswith("drawtext=")
    # The colon in "Breaking:" must be escaped so ffmpeg doesn't parse it
    # as an argument separator.
    assert "Breaking\\:" in f


def test_drawtext_includes_font_size_and_color():
    style = get_preset("finance.long").caption
    f = build_drawtext_filter("hello", style)
    assert f"fontsize={style.font_size}" in f
    assert f"fontcolor={style.primary_color}" in f
    if style.box:
        assert "box=1" in f


def test_subtitles_filter_embeds_force_style_with_font():
    style = get_preset("history").caption
    f = build_subtitles_filter("/tmp/s.srt", style)
    assert f.startswith("subtitles=")
    assert "/tmp/s.srt" in f
    assert f"FontName={style.font}" in f
    assert f"FontSize={style.font_size}" in f


def test_subtitles_filter_escapes_colon_in_path():
    style = get_preset("history").caption
    f = build_subtitles_filter("C:/videos/s.srt", style)
    # Windows-style colon in the drive letter must be escaped.
    assert "C\\:" in f
