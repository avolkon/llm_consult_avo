"""Фоновая доставка ответов в MAX из Redis LIST max:outbox."""

from __future__ import annotations

import asyncio
import logging

from maxapi import Bot

from app.core.constants import OUTBOX_LIST_KEY
from app.core.config import settings
from app.infra.redis import get_redis
from app.models.outbox import OutboxItem, clip_text_for_max_api
from app.security.redis_integrity import outbox_line_is_valid, seal_outbox_for_redis

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
        item: OutboxItem | None = None
        try:
            item = OutboxItem.from_redis_json(data)
        except Exception:
            log.exception("Отправка сообщения в MAX из outbox: raw=%s", data)
            continue

        sec = (
            settings.redis_integrity_secret.get_secret_value()
            if settings.redis_integrity_secret
            else None
        )
        if not outbox_line_is_valid(item, sec):
            log.warning("Outbox HMAC verification failed, task_id=%s", item.task_id)
            continue

        try:
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
            text_out = clip_text_for_max_api(item.text)
            await bot.send_message(chat_id=chat_id, text=text_out)
        except Exception:
            log.exception("Ошибка доставки в MAX: task_id=%s", item.task_id)
            if item.retry_count < settings.outbox_send_max_retries:
                retry_item = item.model_copy(update={"retry_count": item.retry_count + 1})
                await redis.rpush(OUTBOX_LIST_KEY, seal_outbox_for_redis(retry_item, sec))
