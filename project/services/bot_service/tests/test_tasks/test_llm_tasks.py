from __future__ import annotations

import json

import fakeredis

from app.core.constants import OUTBOX_LIST_KEY, user_chat_key
from app.tasks import llm_tasks


def test_llm_request_pushes_outbox(monkeypatch) -> None:
    redis = fakeredis.FakeRedis(decode_responses=True)
    redis.set(user_chat_key("sub-1"), "chat-1")

    monkeypatch.setattr(llm_tasks, "_get_sync_redis", lambda: redis)
    monkeypatch.setattr(llm_tasks, "_worker_redis", None)
    monkeypatch.setattr(llm_tasks, "call_openrouter_sync", lambda _prompt: "answer")

    llm_tasks.llm_request.run("sub-1", "user", "hello")

    assert redis.llen(OUTBOX_LIST_KEY) == 1
    payload = json.loads(redis.lindex(OUTBOX_LIST_KEY, 0))
    assert payload["max_user_id"] == "chat-1"
    assert payload["text"] == "answer"
    assert "created_at" in payload


def test_llm_request_outbox_includes_hmac_when_integrity_configured(monkeypatch) -> None:
    from app.core.config import get_settings

    monkeypatch.setenv("REDIS_INTEGRITY_SECRET", "012345678901234567890123456789ab")
    get_settings.cache_clear()
    try:
        redis = fakeredis.FakeRedis(decode_responses=True)
        redis.set(user_chat_key("sub-1"), "chat-1")

        monkeypatch.setattr(llm_tasks, "_get_sync_redis", lambda: redis)
        monkeypatch.setattr(llm_tasks, "_worker_redis", None)
        monkeypatch.setattr(llm_tasks, "call_openrouter_sync", lambda _prompt: "answer")

        llm_tasks.llm_request.run("sub-1", "user", "hello")

        payload = json.loads(redis.lindex(OUTBOX_LIST_KEY, 0))
        assert payload["max_user_id"] == "chat-1"
        assert "mac" in payload
    finally:
        monkeypatch.delenv("REDIS_INTEGRITY_SECRET", raising=False)
        get_settings.cache_clear()


def test_llm_request_skips_when_chat_mapping_missing(monkeypatch) -> None:
    redis = fakeredis.FakeRedis(decode_responses=True)

    monkeypatch.setattr(llm_tasks, "_get_sync_redis", lambda: redis)
    monkeypatch.setattr(llm_tasks, "_worker_redis", None)
    monkeypatch.setattr(llm_tasks, "call_openrouter_sync", lambda _prompt: "answer")

    llm_tasks.llm_request.run("missing-sub", "user", "hello")

    assert redis.llen(OUTBOX_LIST_KEY) == 0
