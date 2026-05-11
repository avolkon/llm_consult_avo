"""Асинхронный Redis для FastAPI и хендлеров maxapi."""

from redis.asyncio import Redis

from app.core.config import settings

_client: Redis | None = None


async def get_redis() -> Redis:
    """Общий клиент на процесс (bot_service / тесты с подменой)."""
    global _client
    if _client is None:
        kw: dict = {"decode_responses": True}
        if settings.redis_ssl_ca_certs:
            kw["ssl_ca_certs"] = settings.redis_ssl_ca_certs
        _client = Redis.from_url(
            settings.redis_url,
            **kw,
        )
    return _client


async def close_redis() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


def reset_redis_client_for_tests() -> None:
    """Сбросить клиент между тестами (вызывать из conftest при необходимости)."""
    global _client
    _client = None
