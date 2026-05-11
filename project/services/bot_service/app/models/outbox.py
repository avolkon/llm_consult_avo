from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field


# maxapi.methods.send_message: len(text) < 4000 (иначе ValueError при отправке)
MAX_API_MESSAGE_TEXT_LEN = 3999

# В Redis допускаем длиннее (старые записи / до обрезки); в MAX уходит только clip_text_for_max_api.
OUTBOX_TEXT_STORAGE_MAX = 65_536


def clip_text_for_max_api(text: str) -> str:
    """Один исходящий текст сообщения в MAX — не длиннее лимита API."""
    if len(text) <= MAX_API_MESSAGE_TEXT_LEN:
        return text
    tail = "\n\n[Ответ обрезан: лимит сообщения в MAX.]"
    take = MAX_API_MESSAGE_TEXT_LEN - len(tail)
    return text[:take].rstrip() + tail


class OutboxItem(BaseModel):
    """Элемент очереди max:outbox (JSON на одну строку списка Redis)."""

    max_user_id: str
    text: str = Field(max_length=OUTBOX_TEXT_STORAGE_MAX)
    task_id: str | None = None
    created_at: float = Field(description="Unix time, seconds")
    retry_count: int = 0
    mac: str | None = Field(
        default=None,
        description="HMAC-SHA256 при заданном REDIS_INTEGRITY_SECRET",
    )

    def to_redis_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_redis_json(cls, raw: str | bytes) -> OutboxItem:
        if isinstance(raw, bytes):
            raw = raw.decode()
        data: dict[str, Any] = json.loads(raw)
        return cls.model_validate(data)
