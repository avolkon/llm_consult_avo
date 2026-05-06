from __future__ import annotations

import time

import fakeredis.aioredis
import pytest

from app.core.constants import max_auth_key, user_chat_key
from app.services.auth_mapping import get_auth, get_chat, register_token


def _payload(sub: str, role: str = "user") -> dict:
    return {
        "sub": sub,
        "role": role,
        "exp": int(time.time()) + 3600,
    }


@pytest.mark.asyncio
async def test_register_token_sets_both_mappings() -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

    await register_token(redis, "101", _payload("user-1"))

    auth = await get_auth(redis, "101")
    chat = await get_chat(redis, "user-1")
    assert auth == ("user-1", "user")
    assert chat == "101"
    assert await redis.ttl(max_auth_key("101")) > 0
    assert await redis.ttl(user_chat_key("user-1")) > 0


@pytest.mark.asyncio
async def test_register_token_invalidates_old_links() -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

    await register_token(redis, "chat-a", _payload("sub-a"))
    await register_token(redis, "chat-b", _payload("sub-a"))

    assert await get_auth(redis, "chat-a") is None
    assert await get_chat(redis, "sub-a") == "chat-b"


@pytest.mark.asyncio
async def test_get_auth_returns_none_when_absent() -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    assert await get_auth(redis, "missing") is None
