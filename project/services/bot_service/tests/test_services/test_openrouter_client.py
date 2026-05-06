from __future__ import annotations

from dataclasses import dataclass, field

import pytest
import respx
from httpx import Response

from app.services import openrouter_client
from app.services.openrouter_client import OpenRouterError, call_openrouter_sync


@dataclass
class _Secret:
    value: str

    def get_secret_value(self) -> str:
        return self.value


@dataclass
class _Settings:
    openrouter_api_key: _Secret = field(default_factory=lambda: _Secret("test-key"))
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "stepfun/step-3.5-flash:free"
    openrouter_site_url: str = "https://example.com"
    openrouter_app_name: str = "bot-service"
    openrouter_timeout_seconds: float = 60.0


@respx.mock
def test_call_openrouter_sync_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(openrouter_client, "get_settings", lambda: _Settings())
    route = respx.post(
        "https://openrouter.ai/api/v1/chat/completions",
    ).mock(
        return_value=Response(
            200,
            json={"choices": [{"message": {"content": "hello"}}]},
        )
    )

    result = call_openrouter_sync("Привет")

    assert route.called
    assert result == "hello"


@respx.mock
def test_call_openrouter_sync_non_200(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(openrouter_client, "get_settings", lambda: _Settings())
    respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
        return_value=Response(500, text="upstream error"),
    )

    with pytest.raises(OpenRouterError, match="OpenRouter вернул 500"):
        call_openrouter_sync("Привет")


def test_call_openrouter_sync_without_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _Settings(openrouter_api_key=_Secret(""))
    monkeypatch.setattr(openrouter_client, "get_settings", lambda: settings)

    with pytest.raises(OpenRouterError, match="OPENROUTER_API_KEY не задан"):
        call_openrouter_sync("Привет")
