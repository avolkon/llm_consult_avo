"""Фоновая доставка ответов в MAX из Redis LIST max:outbox."""

from __future__ import annotations

import asyncio
import logging

from maxapi import Bot

from app.core.constants import OUTBOX_LIST_KEY
from app.core.config import settings
from app.infra.redis import get_redis
from app.models.outbox import OutboxItem

log = logging.getLogger(__name__)


def _parse_chat_id(raw: str) -> int:
    return int(str(raw).strip())


async def outbox_consumer_loop(bot: Bot) -> None:
    redis = await get_redis()
    while True:
        try:
            result = await redis.blpop(OUTBOX_LIST_KEY, timeout=1.0)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("BLPOP max:outbox")
            await asyncio.sleep(1.0)
            continue

        if result is None:
            continue

        _key, data = result
        try:
            item = OutboxItem.from_redis_json(data)
            if settings.outbox_dedup_enabled and item.task_id:
                dedup_key = f"outbox:processed:{item.task_id}"
                is_new = await redis.set(
                    dedup_key,
                    "1",
                    ex=settings.outbox_dedup_ttl_seconds,
                    nx=True,
                )
                if not is_new:
                    continue
            chat_id = _parse_chat_id(item.max_user_id)
            await bot.send_message(chat_id=chat_id, text=item.text)
        except Exception:
            log.exception("Отправка сообщения в MAX из outbox: raw=%s", data)
