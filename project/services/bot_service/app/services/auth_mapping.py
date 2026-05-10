from __future__ import annotations

import json
import time
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import WatchError

from app.core.constants import max_auth_key, user_chat_key

_REGISTER_MAX_WATCH_RETRIES = 64


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

    auth_json = json.dumps({"sub": sub, "role": role}, ensure_ascii=False)
    uc_key = user_chat_key(sub)
    ma_key = max_auth_key(max_user_id)

    # WATCH + MULTI/EXEC: атомарное применение инвалидаций и SETEX (без гонок между GET и записями).
    for _ in range(_REGISTER_MAX_WATCH_RETRIES):
        pipe = redis.pipeline(transaction=True)
        try:
            await pipe.watch(uc_key, ma_key)
            old_max_user_id = await pipe.get(uc_key)
            old_data = await pipe.get(ma_key)
            pipe.multi()
            if old_max_user_id:
                pipe.delete(max_auth_key(old_max_user_id))
            if old_data:
                old_sub = json.loads(old_data)["sub"]
                pipe.delete(user_chat_key(str(old_sub)))
            pipe.setex(ma_key, ttl, auth_json)
            pipe.setex(uc_key, ttl, max_user_id)
            await pipe.execute()
        except WatchError:
            continue
        else:
            return
        finally:
            await pipe.reset()

    msg = "register_token: превышено число повторов после конфликта WATCH"
    raise RuntimeError(msg)


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
