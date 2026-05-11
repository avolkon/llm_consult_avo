from __future__ import annotations

import pytest
from pydantic import ValidationError


def _prod_common_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("MAX_BOT_TOKEN", "real-max-token-tls-guard-test-only-xxx")


def test_prod_rejects_redis_without_tls(monkeypatch: pytest.MonkeyPatch, prod_backend_env: None) -> None:
    _prod_common_env(monkeypatch)
    monkeypatch.setenv("REDIS_URL", "redis://redis:6379/0")
    from app.core.config import get_settings

    get_settings.cache_clear()
    try:
        with pytest.raises(ValidationError, match="rediss"):
            get_settings()
    finally:
        for k in ("ENV", "OPENROUTER_BASE_URL", "MAX_BOT_TOKEN", "REDIS_URL"):
            monkeypatch.delenv(k, raising=False)
        get_settings.cache_clear()


def test_prod_rejects_broker_without_tls(monkeypatch: pytest.MonkeyPatch, prod_backend_env: None) -> None:
    _prod_common_env(monkeypatch)
    monkeypatch.setenv("CELERY_BROKER_URL", "amqp://app:secret@rabbitmq:5672//")
    from app.core.config import get_settings

    get_settings.cache_clear()
    try:
        with pytest.raises(ValidationError, match="amqps"):
            get_settings()
    finally:
        for k in ("ENV", "OPENROUTER_BASE_URL", "MAX_BOT_TOKEN", "CELERY_BROKER_URL"):
            monkeypatch.delenv(k, raising=False)
        get_settings.cache_clear()


def test_prod_rejects_guest_guest_broker(monkeypatch: pytest.MonkeyPatch, prod_backend_env: None) -> None:
    _prod_common_env(monkeypatch)
    monkeypatch.setenv("CELERY_BROKER_URL", "amqps://guest:guest@rabbitmq:5671//")
    from app.core.config import get_settings

    get_settings.cache_clear()
    try:
        with pytest.raises(ValidationError, match="guest"):
            get_settings()
    finally:
        for k in ("ENV", "OPENROUTER_BASE_URL", "MAX_BOT_TOKEN", "CELERY_BROKER_URL"):
            monkeypatch.delenv(k, raising=False)
        get_settings.cache_clear()


def test_prod_rejects_insecure_redis_tls_hint(monkeypatch: pytest.MonkeyPatch, prod_backend_env: None) -> None:
    _prod_common_env(monkeypatch)
    monkeypatch.setenv("REDIS_URL", "rediss://:p@redis:6379/0?ssl_cert_reqs=none")
    from app.core.config import get_settings

    get_settings.cache_clear()
    try:
        with pytest.raises(ValidationError, match="Insecure Redis TLS"):
            get_settings()
    finally:
        for k in ("ENV", "OPENROUTER_BASE_URL", "MAX_BOT_TOKEN", "REDIS_URL"):
            monkeypatch.delenv(k, raising=False)
        get_settings.cache_clear()
