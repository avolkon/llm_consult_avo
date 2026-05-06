from __future__ import annotations

import pytest


@pytest.fixture
def noop_fixture() -> None:
    """Базовая фикстура-заглушка для расширения тестового bootstrap."""
    return None
