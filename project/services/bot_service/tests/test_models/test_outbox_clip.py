from __future__ import annotations

from app.models.outbox import MAX_API_MESSAGE_TEXT_LEN, clip_text_for_max_api


def test_clip_text_for_max_api_short_unchanged() -> None:
    assert clip_text_for_max_api("hello") == "hello"


def test_clip_text_for_max_api_long_fits_limit() -> None:
    raw = "z" * 8000
    out = clip_text_for_max_api(raw)
    assert len(out) <= MAX_API_MESSAGE_TEXT_LEN
    assert len(out) < 4000
    assert "обрезан" in out
