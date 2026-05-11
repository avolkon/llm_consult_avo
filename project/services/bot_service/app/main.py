#!/usr/bin/env python3
"""FastAPI: healthcheck и webhook для MAX. Для long polling см. app.poll."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from starlette.responses import JSONResponse
from maxapi import Bot
from maxapi.webhook.fastapi import FastAPIMaxWebhook

from app.bot.dispatcher import build_bot
from app.bot.outbox_consumer import outbox_consumer_loop
from app.core.config import get_settings, settings
from app.infra.redis import close_redis
from app.security.webhook_gate import webhook_preflight_response

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

LifespanFn = Callable[[FastAPI], AsyncIterator[None]]


def _webhook_and_consumer_lifespan(
    bot: Bot,
    webhook: FastAPIMaxWebhook,
) -> LifespanFn:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        async with webhook.lifespan(app):
            consumer_task = asyncio.create_task(outbox_consumer_loop(bot))
            log.info("Outbox consumer started (webhook mode)")
            try:
                yield
            finally:
                consumer_task.cancel()
                try:
                    await consumer_task
                except asyncio.CancelledError:
                    pass
                log.info("Outbox consumer stopped (webhook mode)")
                await close_redis()

    return lifespan


def create_app(*, with_max_webhook: bool = True) -> FastAPI:
    """with_max_webhook=False — без вызовов API MAX (например, unit-тесты /health)."""
    _prod = settings.env in {"prod", "production"}
    doc_kw = {
        "docs_url": None if _prod else "/docs",
        "redoc_url": None if _prod else "/redoc",
        "openapi_url": None if _prod else "/openapi.json",
    }
    if with_max_webhook:
        bot, dp = build_bot()
        webhook = FastAPIMaxWebhook(dp=dp, bot=bot)
        app = FastAPI(
            title="LLM consult — MAX bot",
            lifespan=_webhook_and_consumer_lifespan(bot, webhook),
            **doc_kw,
        )
        webhook.setup(app, path=settings.webhook_path)
    else:
        app = FastAPI(title="LLM consult — MAX bot (health-only)", **doc_kw)

    @app.middleware("http")
    async def security_headers_middleware(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if settings.env in {"prod", "production"}:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response

    @app.middleware("http")
    async def request_body_size_middleware(request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH"):
            cl = request.headers.get("content-length")
            if cl is not None:
                try:
                    if int(cl) > get_settings().max_request_body_bytes:
                        return JSONResponse({"detail": "Request body too large"}, status_code=413)
                except ValueError:
                    return JSONResponse({"detail": "Invalid Content-Length"}, status_code=400)
        return await call_next(request)

    @app.middleware("http")
    async def webhook_gate_middleware(request: Request, call_next):
        block = webhook_preflight_response(request, get_settings())
        if block is not None:
            return block
        return await call_next(request)

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
