from __future__ import annotations

import pytest

from app.bot import handlers


@pytest.mark.asyncio
async def test_delay_contract_sub_role_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = {}

    async def fake_get_redis():
        return object()

    async def fake_get_auth(_redis, _max_user_id: str):
        return ("sub-42", "admin")

    def fake_delay(*args) -> None:
        called["args"] = args

    monkeypatch.setattr(handlers, "get_redis", fake_get_redis)
    monkeypatch.setattr(handlers, "get_auth", fake_get_auth)
    monkeypatch.setattr(handlers.llm_request, "delay", fake_delay)

    await handlers.process_user_text("тест", "chat-99")

    assert called["args"] == ("sub-42", "admin", "тест")
