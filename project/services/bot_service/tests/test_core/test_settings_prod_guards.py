from __future__ import annotations

import pytest
from pydantic import ValidationError


def test_log_prompt_defaults_false_in_production_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LOG_PROMPT_CONTENT", raising=False)
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("MAX_BOT_TOKEN", "real-max-token-for-test-prod-only-12345")
    from app.core.config import get_settings

    get_settings.cache_clear()
    try:
        s = get_settings()
        assert s.log_prompt_content is False
    finally:
        monkeypatch.delenv("ENV", raising=False)
        monkeypatch.delenv("OPENROUTER_BASE_URL", raising=False)
        monkeypatch.delenv("MAX_BOT_TOKEN", raising=False)
        get_settings.cache_clear()


def test_max_bot_token_placeholder_rejected_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("MAX_BOT_TOKEN", "replace-with-max-bot-token")
    from app.core.config import get_settings

    get_settings.cache_clear()
    try:
        with pytest.raises(ValidationError, match="MAX_BOT_TOKEN"):
            get_settings()
    finally:
        monkeypatch.delenv("ENV", raising=False)
        monkeypatch.delenv("OPENROUTER_BASE_URL", raising=False)
        monkeypatch.delenv("MAX_BOT_TOKEN", raising=False)
        get_settings.cache_clear()
