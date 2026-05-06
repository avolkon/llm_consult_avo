from __future__ import annotations

import pytest

from app.bot import handlers


@pytest.mark.asyncio
async def test_process_token_command_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_get_redis():
        return object()

    async def fake_register_token(_redis, _max_user_id: str, _payload: dict) -> None:
        return None

    def fake_decode(_token: str) -> dict:
        return {"sub": "42", "role": "user", "exp": 9999999999}

    monkeypatch.setattr(handlers, "get_redis", fake_get_redis)
    monkeypatch.setattr(handlers, "register_token", fake_register_token)
    monkeypatch.setattr(handlers, "decode_and_validate", fake_decode)

    text = await handlers.process_token_command("token", "chat-1")
    assert "Токен принят" in text


@pytest.mark.asyncio
async def test_process_user_text_without_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_get_redis():
        return object()

    async def fake_get_auth(_redis, _max_user_id: str):
        return None

    monkeypatch.setattr(handlers, "get_redis", fake_get_redis)
    monkeypatch.setattr(handlers, "get_auth", fake_get_auth)

    text = await handlers.process_user_text("hello", "chat-1")
    assert "Сначала авторизуйтесь" in text


@pytest.mark.asyncio
async def test_process_user_text_calls_celery(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict[str, tuple[str, str, str]] = {}

    async def fake_get_redis():
        return object()

    async def fake_get_auth(_redis, _max_user_id: str):
        return ("sub-1", "user")

    def fake_delay(sub: str, role: str, prompt: str) -> None:
        called["args"] = (sub, role, prompt)

    monkeypatch.setattr(handlers, "get_redis", fake_get_redis)
    monkeypatch.setattr(handlers, "get_auth", fake_get_auth)
    monkeypatch.setattr(handlers.llm_request, "delay", fake_delay)

    text = await handlers.process_user_text("hello", "chat-1")
    assert called["args"] == ("sub-1", "user", "hello")
    assert "Запрос отправлен" in text
