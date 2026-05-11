from __future__ import annotations

import json
from dataclasses import dataclass, field

import pytest
import respx
from httpx import Response

from app.services import openrouter_client
from app.services.openrouter_client import (
    OpenRouterError,
    _soft_reply_char_target,
    call_openrouter_fit_to_max_chars_sync,
    call_openrouter_sync,
)


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
    openrouter_reply_max_chars: int = 3999
    openrouter_max_output_tokens: int = 4500
    openrouter_system_prompt_extra: str = ""


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
    body = json.loads(route.calls[0].request.content)
    assert body["messages"][0]["role"] == "system"
    assert "3999" in body["messages"][0]["content"]
    assert "3800" in body["messages"][0]["content"]
    assert body["messages"][1] == {"role": "user", "content": "Привет"}
    assert body["max_tokens"] == 4500


@respx.mock
def test_call_openrouter_sync_omits_max_tokens_when_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    s = _Settings(openrouter_max_output_tokens=0)
    monkeypatch.setattr(openrouter_client, "get_settings", lambda: s)
    route = respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
        return_value=Response(
            200,
            json={"choices": [{"message": {"content": "x"}}]},
        ),
    )
    call_openrouter_sync("hi")
    body = json.loads(route.calls[0].request.content)
    assert "max_tokens" not in body


@respx.mock
def test_call_openrouter_sync_appends_system_prompt_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    s = _Settings(openrouter_system_prompt_extra="Говори кратко.")
    monkeypatch.setattr(openrouter_client, "get_settings", lambda: s)
    route = respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
        return_value=Response(
            200,
            json={"choices": [{"message": {"content": "ok"}}]},
        ),
    )
    call_openrouter_sync("q")
    body = json.loads(route.calls[0].request.content)
    assert "Говори кратко." in body["messages"][0]["content"]


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


@respx.mock
def test_call_openrouter_fit_to_max_chars_sync_posts_editor_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(openrouter_client, "get_settings", lambda: _Settings())
    route = respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
        return_value=Response(
            200,
            json={"choices": [{"message": {"content": "short"}}]},
        ),
    )
    result = call_openrouter_fit_to_max_chars_sync("draft" * 1000, 3999)
    assert result == "short"
    body = json.loads(route.calls[0].request.content)
    assert body["messages"][0]["role"] == "system"
    assert "редактор" in body["messages"][0]["content"].lower()
    assert "3999" in body["messages"][0]["content"]
    assert body["messages"][1] == {"role": "user", "content": "draft" * 1000}
    assert body["max_tokens"] == 4096


def test_call_openrouter_fit_to_max_chars_sync_rejects_bad_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(openrouter_client, "get_settings", lambda: _Settings())
    with pytest.raises(OpenRouterError, match="max_chars must be positive"):
        call_openrouter_fit_to_max_chars_sync("x", 0)


def test_soft_reply_char_target() -> None:
    assert _soft_reply_char_target(3999) == 3800
    assert _soft_reply_char_target(500, margin=100) == 400
    assert _soft_reply_char_target(300, margin=500) == 256