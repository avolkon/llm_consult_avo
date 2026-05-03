from maxapi import Bot, Dispatcher

from app.bot.handlers import register_handlers
from app.core.config import settings


def build_bot() -> tuple[Bot, Dispatcher]:
    bot = Bot(token=settings.max_bot_token.get_secret_value())
    dp = Dispatcher()
    register_handlers(dp)
    return bot, dp
