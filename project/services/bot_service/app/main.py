#!/usr/bin/env python3
"""FastAPI: healthcheck и webhook для MAX. Для long polling см. app.poll."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI
from maxapi import Bot
from maxapi.webhook.fastapi import FastAPIMaxWebhook

from app.bot.dispatcher import build_bot
from app.bot.outbox_consumer import outbox_consumer_loop
from app.core.config import settings
from app.infra.redis import close_redis

logging.basicConfig(level=logging.INFO)

LifespanFn = Callable[[FastAPI], AsyncIterator[None]]


def _webhook_and_consumer_lifespan(
    bot: Bot,
    webhook: FastAPIMaxWebhook,
) -> LifespanFn:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        async with webhook.lifespan(app):
            consumer_task = asyncio.create_task(outbox_consumer_loop(bot))
            try:
                yield
            finally:
                consumer_task.cancel()
                try:
                    await consumer_task
                except asyncio.CancelledError:
                    pass
                await close_redis()

    return lifespan


def create_app(*, with_max_webhook: bool = True) -> FastAPI:
    """with_max_webhook=False — без вызовов API MAX (например, unit-тесты /health)."""
    if with_max_webhook:
        bot, dp = build_bot()
        webhook = FastAPIMaxWebhook(dp=dp, bot=bot)
        app = FastAPI(
            title="LLM consult — MAX bot",
            lifespan=_webhook_and_consumer_lifespan(bot, webhook),
        )
        webhook.setup(app, path=settings.webhook_path)
    else:
        app = FastAPI(title="LLM consult — MAX bot (health-only)")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "transport": "max"}

    return app


def run_webhook_server() -> None:
    import uvicorn

    uvicorn.run(
        create_app(),
        host=settings.api_host,
        port=settings.api_port,
    )


def main() -> None:
    run_webhook_server()


if __name__ == "__main__":
    main()
