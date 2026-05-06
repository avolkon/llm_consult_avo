"""Long polling для MAX (удобно в dev). Перед запуском отключите webhook у бота на стороне MAX."""

from __future__ import annotations

import asyncio
import logging

from app.bot.dispatcher import build_bot
from app.bot.outbox_consumer import outbox_consumer_loop
from app.core.config import settings
from app.infra.redis import close_redis

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


async def _run_polling() -> None:
    if settings.max_delivery_mode != "polling":
        log.warning(
            "max_delivery_mode=%s: для polling ожидается 'polling' в .env",
            settings.max_delivery_mode,
        )
    bot, dp = build_bot()
    consumer_task = asyncio.create_task(outbox_consumer_loop(bot))
    try:
        await dp.start_polling(bot)
    finally:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
        await close_redis()


def run_polling() -> None:
    asyncio.run(_run_polling())


if __name__ == "__main__":
    run_polling()
