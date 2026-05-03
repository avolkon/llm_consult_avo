#!/usr/bin/env python3
"""FastAPI: healthcheck и webhook для MAX. Для long polling см. app.poll."""

import logging

from fastapi import FastAPI
from maxapi.webhook.fastapi import FastAPIMaxWebhook

from app.bot.dispatcher import build_bot
from app.core.config import settings

logging.basicConfig(level=logging.INFO)


def create_app(*, with_max_webhook: bool = True) -> FastAPI:
    """with_max_webhook=False — без вызовов API MAX (например, unit-тесты /health)."""
    if with_max_webhook:
        bot, dp = build_bot()
        webhook = FastAPIMaxWebhook(dp=dp, bot=bot)
        app = FastAPI(title="LLM consult — MAX bot", lifespan=webhook.lifespan)
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
    print("LLM project is running!")


if __name__ == "__main__":
    main()
