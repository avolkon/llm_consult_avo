"""Синхронный HTTP-клиент OpenRouter для Celery-воркера."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import get_settings

log = logging.getLogger(__name__)


class OpenRouterError(RuntimeError):
    """Ошибка вызова OpenRouter (сеть или ответ API)."""


def _extract_message_text(data: dict[str, Any]) -> str:
    try:
        choices = data["choices"]
        message = choices[0]["message"]
        content = message["content"]
    except (KeyError, IndexError, TypeError) as exc:
        msg = "Неожиданная форма ответа OpenRouter"
        raise OpenRouterError(msg) from exc
    if not isinstance(content, str):
        msg = "Поле content не является строкой"
        raise OpenRouterError(msg)
    return content


def call_openrouter_sync(prompt: str) -> str:
    """POST /chat/completions; при ошибке поднимает OpenRouterError."""
    settings = get_settings()
    key = settings.openrouter_api_key.get_secret_value().strip()
    if not key:
        msg = "OPENROUTER_API_KEY не задан"
        raise OpenRouterError(msg)

    base = settings.openrouter_base_url.rstrip("/")
    url = f"{base}/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.openrouter_site_url,
        "X-Title": settings.openrouter_app_name,
    }
    payload = {
        "model": settings.openrouter_model,
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        with httpx.Client(timeout=settings.openrouter_timeout_seconds) as client:
            response = client.post(url, headers=headers, json=payload)
    except httpx.RequestError as exc:
        log.exception("OpenRouter: сетевая ошибка")
        msg = "Сетевая ошибка при обращении к OpenRouter"
        raise OpenRouterError(msg) from exc

    if response.status_code != httpx.codes.OK:
        body = response.text[:500]
        log.error(
            "OpenRouter HTTP %s: %s",
            response.status_code,
            body,
        )
        msg = f"OpenRouter вернул {response.status_code}"
        raise OpenRouterError(msg)

    try:
        data = response.json()
    except ValueError as exc:
        msg = "Ответ OpenRouter не JSON"
        raise OpenRouterError(msg) from exc

    return _extract_message_text(data)
