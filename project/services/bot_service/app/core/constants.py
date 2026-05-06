"""Ключи и имена сущностей Redis, общие для бота и Celery-воркера."""

OUTBOX_LIST_KEY = "max:outbox"


def max_auth_key(max_user_id: str) -> str:
    return f"max_auth:{max_user_id}"


def user_chat_key(sub: str) -> str:
    return f"user_chat:{sub}"
