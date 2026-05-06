"""Celery: брокер задач LLM. Воркер не использует maxapi / MAX Bot API."""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "bot_service",
    broker=settings.celery_broker_url,
    include=["app.tasks.llm_tasks"],
)

celery_app.conf.update(
    task_default_queue="llm",
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=5,
)
