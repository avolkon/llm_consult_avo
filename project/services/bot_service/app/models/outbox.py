from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field


class OutboxItem(BaseModel):
    """Элемент очереди max:outbox (JSON на одну строку списка Redis)."""

    max_user_id: str
    text: str
    task_id: str | None = None
    created_at: float = Field(description="Unix time, seconds")
    retry_count: int = 0

    def to_redis_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_redis_json(cls, raw: str | bytes) -> OutboxItem:
        if isinstance(raw, bytes):
            raw = raw.decode()
        data: dict[str, Any] = json.loads(raw)
        return cls.model_validate(data)
