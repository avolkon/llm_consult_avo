"""Задача LLM: только OpenRouter + RPUSH в max:outbox (без MAX API)."""

from __future__ import annotations

import json
import logging
import time
from typing import TYPE_CHECKING, Any

import redis

from app.core.constants import OUTBOX_LIST_KEY, user_chat_key
from app.infra.celery_app import celery_app
from app.models.outbox import OutboxItem
from app.services.openrouter_client import OpenRouterError, call_openrouter_sync

if TYPE_CHECKING:
    from celery.app.task import Task

log = logging.getLogger(__name__)

_worker_redis: redis.Redis | None = None


def _get_sync_redis() -> redis.Redis:
    global _worker_redis
    if _worker_redis is None:
        from app.core.config import get_settings

        _worker_redis = redis.from_url(
            get_settings().redis_url,
            decode_responses=True,
        )
    return _worker_redis


@celery_app.task(name="llm_request", bind=True, ignore_result=True)
def llm_request(
    self: Task,
    sub: str,
    role: str,
    prompt: str,
) -> None:
    task_id = self.request.id
    r = _get_sync_redis()
    log.debug("LLM request accepted: sub=%s role=%s task_id=%s", sub, role, task_id)

    try:
        response_text = call_openrouter_sync(prompt)
    except OpenRouterError as exc:
        log.warning("OpenRouter: %s", exc)
        response_text = f"Не удалось получить ответ от модели: {exc}"
    except Exception:
        log.exception("Неожиданная ошибка LLM")
        response_text = "Внутренняя ошибка при обращении к LLM."

    max_user_id = r.get(user_chat_key(sub))
    if not max_user_id:
        log.warning(
            "Нет маршрута user_chat для sub=%s (сессия истекла или не залогинен), task_id=%s",
            sub,
            task_id,
        )
        return

    item: dict[str, Any] = {
        "max_user_id": str(max_user_id),
        "text": response_text,
        "task_id": task_id,
        "created_at": time.time(),
    }
    outbox_item = OutboxItem.model_validate(item)
    r.rpush(OUTBOX_LIST_KEY, outbox_item.to_redis_json())


def run_worker_main() -> None:
    """Poetry script entrypoint для запуска celery worker."""
    celery_app.worker_main(["worker", "--loglevel=INFO"])
