from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field


OUTBOX_TEXT_MAX_LEN = 8192


class OutboxItem(BaseModel):
    """Элемент очереди max:outbox (JSON на одну строку списка Redis)."""

    max_user_id: str
    text: str = Field(max_length=OUTBOX_TEXT_MAX_LEN)
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
