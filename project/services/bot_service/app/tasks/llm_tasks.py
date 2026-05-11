"""Задача LLM: только OpenRouter + RPUSH в max:outbox (без MAX API)."""

from __future__ import annotations

import logging
import sys
import time
from typing import TYPE_CHECKING, Any

import redis

from app.core.config import get_settings
from app.core.constants import OUTBOX_LIST_KEY, user_chat_key
from app.infra.celery_app import celery_app
from app.models.outbox import MAX_API_MESSAGE_TEXT_LEN, OutboxItem, clip_text_for_max_api
from app.security.redis_integrity import seal_outbox_for_redis
from app.services.openrouter_client import (
    OpenRouterError,
    call_openrouter_fit_to_max_chars_sync,
    call_openrouter_sync,
)

if TYPE_CHECKING:
    from celery.app.task import Task

log = logging.getLogger(__name__)

_worker_redis: redis.Redis | None = None


def _get_sync_redis() -> redis.Redis:
    global _worker_redis
    if _worker_redis is None:
        kw: dict = {"decode_responses": True}
        cfg = get_settings()
        if cfg.redis_ssl_ca_certs:
            kw["ssl_ca_certs"] = cfg.redis_ssl_ca_certs
        _worker_redis = redis.from_url(
            cfg.redis_url,
            **kw,
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
        if len(response_text) > MAX_API_MESSAGE_TEXT_LEN:
            log.info(
                "LLM черновик длиннее лимита MAX (%s символов, нужно ≤%s), второй запрос на вписывание в лимит",
                len(response_text),
                MAX_API_MESSAGE_TEXT_LEN,
            )
            try:
                response_text = call_openrouter_fit_to_max_chars_sync(
                    response_text, MAX_API_MESSAGE_TEXT_LEN
                )
            except OpenRouterError:
                log.warning(
                    "Не удалось вписать ответ в лимит через LLM (sub=%s task_id=%s), будет обрезка",
                    sub,
                    task_id,
                )
    except OpenRouterError:
        log.warning("OpenRouter error for sub=%s task_id=%s", sub, task_id)
        response_text = "Не удалось получить ответ от модели."
    except Exception:
        log.exception("Unexpected LLM error for sub=%s task_id=%s", sub, task_id)
        response_text = "Внутренняя ошибка при обращении к LLM."

    response_text = clip_text_for_max_api(response_text)

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
    cfg = get_settings()
    sec = cfg.redis_integrity_secret.get_secret_value() if cfg.redis_integrity_secret else None
    r.rpush(OUTBOX_LIST_KEY, seal_outbox_for_redis(outbox_item, sec))


def run_worker_main() -> None:
    """Точка входа скрипта (uv/pip console script) для Celery worker."""
    argv = ["worker", "--loglevel=INFO"]
    # Windows: пул prefork/multiprocessing часто даёт WinError 5 у дочерних процессов;
    # solo — один процесс, достаточно для локальной разработки.
    if sys.platform == "win32":
        argv.extend(["--pool=solo"])
    celery_app.worker_main(argv)
