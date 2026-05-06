from __future__ import annotations

import asyncio

import pytest

from app.bot import outbox_consumer
from app.models.outbox import OutboxItem


class _FakeBot:
    def __init__(self, fail_send: bool = False) -> None:
        self.fail_send = fail_send
        self.calls: list[tuple[int, str]] = []

    async def send_message(self, chat_id: int, text: str) -> None:
        if self.fail_send:
            raise RuntimeError("send failed")
        self.calls.append((chat_id, text))


class _FakeRedis:
    def __init__(self, responses: list) -> None:
        self._responses = responses
        self.rpush_calls: list[tuple[str, str]] = []
        self.set_result = True

    async def blpop(self, _key: str, timeout: float):
        item = self._responses.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item

    async def rpush(self, key: str, value: str) -> None:
        self.rpush_calls.append((key, value))

    async def set(self, *args, **kwargs):
        return self.set_result


@pytest.mark.asyncio
async def test_outbox_consumer_sends_message(monkeypatch: pytest.MonkeyPatch) -> None:
    item = OutboxItem(
        max_user_id="100",
        text="hello",
        task_id="task-1",
        created_at=123.0,
    )
    redis = _FakeRedis(
        [("max:outbox", item.to_redis_json()), asyncio.CancelledError()],
    )
    bot = _FakeBot()
    async def fake_get_redis():
        return redis
    monkeypatch.setattr(outbox_consumer, "get_redis", fake_get_redis)

    with pytest.raises(asyncio.CancelledError):
        await outbox_consumer.outbox_consumer_loop(bot)
    assert bot.calls == [(100, "hello")]


@pytest.mark.asyncio
async def test_outbox_consumer_handles_timeout_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis = _FakeRedis([None, asyncio.CancelledError()])
    bot = _FakeBot()
    async def fake_get_redis():
        return redis
    monkeypatch.setattr(outbox_consumer, "get_redis", fake_get_redis)

    with pytest.raises(asyncio.CancelledError):
        await outbox_consumer.outbox_consumer_loop(bot)
    assert bot.calls == []


@pytest.mark.asyncio
async def test_outbox_consumer_requeues_on_send_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    item = OutboxItem(
        max_user_id="100",
        text="hello",
        task_id="task-retry",
        created_at=123.0,
        retry_count=0,
    )
    redis = _FakeRedis([("max:outbox", item.to_redis_json()), asyncio.CancelledError()])
    bot = _FakeBot(fail_send=True)
    async def fake_get_redis():
        return redis
    monkeypatch.setattr(outbox_consumer, "get_redis", fake_get_redis)
    monkeypatch.setattr(outbox_consumer.settings, "outbox_send_max_retries", 1)

    with pytest.raises(asyncio.CancelledError):
        await outbox_consumer.outbox_consumer_loop(bot)

    assert len(redis.rpush_calls) == 1
    _key, payload = redis.rpush_calls[0]
    assert "\"retry_count\":1" in payload


@pytest.mark.asyncio
async def test_outbox_consumer_skips_duplicate_task(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    item = OutboxItem(
        max_user_id="100",
        text="hello",
        task_id="dup-task",
        created_at=123.0,
    )
    redis = _FakeRedis([("max:outbox", item.to_redis_json()), asyncio.CancelledError()])
    redis.set_result = False
    bot = _FakeBot()
    async def fake_get_redis():
        return redis
    monkeypatch.setattr(outbox_consumer, "get_redis", fake_get_redis)
    monkeypatch.setattr(outbox_consumer.settings, "outbox_dedup_enabled", True)

    with pytest.raises(asyncio.CancelledError):
        await outbox_consumer.outbox_consumer_loop(bot)

    assert bot.calls == []
