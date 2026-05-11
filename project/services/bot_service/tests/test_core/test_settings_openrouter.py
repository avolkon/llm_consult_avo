from __future__ import annotations

import pytest
from pydantic import ValidationError


def test_openrouter_rejects_non_openrouter_host_in_prod(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("OPENROUTER_BASE_URL", "https://evil.com/v1")
    from app.core.config import get_settings

    get_settings.cache_clear()
    try:
        with pytest.raises(ValidationError, match="openrouter"):
            get_settings()
    finally:
        monkeypatch.delenv("ENV", raising=False)
        monkeypatch.delenv("OPENROUTER_BASE_URL", raising=False)
        get_settings.cache_clear()


def test_openrouter_allows_http_on_local_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENV", "local")
    monkeypatch.setenv("OPENROUTER_BASE_URL", "http://127.0.0.1:9999/v1")
    from app.core.config import get_settings

    get_settings.cache_clear()
    try:
        s = get_settings()
        assert "127.0.0.1" in s.openrouter_base_url
    finally:
        monkeypatch.delenv("OPENROUTER_BASE_URL", raising=False)
        monkeypatch.setenv("ENV", "local")
        get_settings.cache_clear()
