"""Long polling для MAX (удобно в dev). Перед запуском отключите webhook у бота на стороне MAX."""

import asyncio
import logging

from app.bot.dispatcher import build_bot
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


async def _run_polling() -> None:
    if settings.max_delivery_mode != "polling":
        log.warning(
            "max_delivery_mode=%s: для polling ожидается 'polling' в .env",
            settings.max_delivery_mode,
        )
    bot, dp = build_bot()
    await dp.start_polling(bot)


def run_polling() -> None:
    asyncio.run(_run_polling())


if __name__ == "__main__":
    run_polling()
