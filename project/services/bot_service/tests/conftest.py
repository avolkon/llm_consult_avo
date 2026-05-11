from __future__ import annotations

import os

# До импорта пакета app: иначе в config сработает get_settings() без JWT_SECRET.
os.environ.setdefault(
    "JWT_SECRET",
    "bot_service_pytest_jwt_secret_32_char_minimum!!",
)

import pytest


@pytest.fixture(autouse=True)
def _clear_bot_settings_cache() -> None:
    yield
    from app.core.config import get_settings

    get_settings.cache_clear()


@pytest.fixture
def noop_fixture() -> None:
    """Базовая фикстура-заглушка для расширения тестового bootstrap."""
    return None
