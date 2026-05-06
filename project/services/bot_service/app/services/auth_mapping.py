from __future__ import annotations

import json
import time
from typing import Any

from redis.asyncio import Redis

from app.core.constants import max_auth_key, user_chat_key


def _jwt_ttl_seconds(payload: dict[str, Any]) -> int:
    exp = payload.get("exp")
    if exp is None:
        msg = "В JWT отсутствует поле exp"
        raise ValueError(msg)
    ttl = int(exp) - int(time.time())
    return max(ttl, 1)


async def register_token(redis: Redis, max_user_id: str, payload: dict[str, Any]) -> None:
    """Связать max_user_id с sub/role из JWT; инвалидация старых маппингов."""
    sub_raw = payload.get("sub")
    if sub_raw is None:
        msg = "В JWT отсутствует поле sub"
        raise ValueError(msg)
    sub = str(sub_raw)
    role = str(payload.get("role", "user"))
    ttl = _jwt_ttl_seconds(payload)

    old_max_user_id = await redis.get(user_chat_key(sub))
    if old_max_user_id:
        await redis.delete(max_auth_key(old_max_user_id))

    old_data = await redis.get(max_auth_key(max_user_id))
    if old_data:
        old_sub = json.loads(old_data)["sub"]
        await redis.delete(user_chat_key(str(old_sub)))

    auth_json = json.dumps({"sub": sub, "role": role}, ensure_ascii=False)
    await redis.setex(max_auth_key(max_user_id), ttl, auth_json)
    await redis.setex(user_chat_key(sub), ttl, max_user_id)


async def get_auth(redis: Redis, max_user_id: str) -> tuple[str, str] | None:
    raw = await redis.get(max_auth_key(max_user_id))
    if raw is None:
        return None
    data: dict[str, Any] = json.loads(raw)
    sub = str(data.get("sub", ""))
    if not sub:
        return None
    role = str(data.get("role", "user"))
    return sub, role


async def get_chat(redis: Redis, sub: str) -> str | None:
    value = await redis.get(user_chat_key(sub))
    if value is None:
        return None
    return str(value)
