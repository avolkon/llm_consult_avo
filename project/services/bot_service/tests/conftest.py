from __future__ import annotations

import os

# До импорта пакета app: иначе в config сработает get_settings() без JWT_SECRET.
os.environ.setdefault(
    "JWT_SECRET",
    "bot_service_pytest_jwt_secret_32_char_minimum!!",
)

import pytest

# Для тестов с ENV=production (валидация prod): не считаются реальными подключениями.
_PROD_REDIS = "rediss://:secret@redis:6379/0"
_PROD_BROKER = "amqps://app:secret@rabbitmq:5671//"


@pytest.fixture
def prod_backend_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REDIS_URL", _PROD_REDIS)
    monkeypatch.setenv("CELERY_BROKER_URL", _PROD_BROKER)


@pytest.fixture(autouse=True)
def _clear_bot_settings_cache() -> None:
    yield
    from app.core.config import get_settings

    get_settings.cache_clear()


@pytest.fixture
def noop_fixture() -> None:
    """Базовая фикстура-заглушка для расширения тестового bootstrap."""
    return None
