"""HMAC для значений в Redis: привязка сессии max↔sub и очередь max:outbox.

Снижает риск подмены при компрометации только Redis (без секрета целостности):
записи без валидного MAC отклоняются воркером/consumer.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets

from app.models.outbox import OutboxItem


def _canonical_json(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8",
    )


def seal_session_json(sub: str, role: str, secret: str | None) -> str:
    if not secret:
        return json.dumps({"sub": sub, "role": role}, ensure_ascii=False)
    body = {"v": 1, "sub": sub, "role": role}
    inner = _canonical_json(body)
    mac = hmac.new(secret.encode("utf-8"), inner, hashlib.sha256).hexdigest()
    out = {**body, "mac": mac}
    return json.dumps(out, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def parse_session_json(raw: str, secret: str | None) -> tuple[str, str] | None:
    try:
        data: dict = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not secret:
        sub = str(data.get("sub", ""))
        if not sub:
            return None
        return sub, str(data.get("role", "user"))
    if data.get("v") != 1 or "mac" not in data:
        return None
    mac = str(data["mac"])
    body = {k: v for k, v in data.items() if k != "mac"}
    inner = _canonical_json(body)
    expected = hmac.new(secret.encode("utf-8"), inner, hashlib.sha256).hexdigest()
    if not secrets.compare_digest(mac, expected):
        return None
    sub = str(body.get("sub", ""))
    if not sub:
        return None
    return sub, str(body.get("role", "user"))


def seal_outbox_for_redis(item: OutboxItem, secret: str | None) -> str:
    if not secret:
        return item.model_dump_json()
    payload = item.model_dump(mode="json")
    payload.pop("mac", None)
    canonical = _canonical_json(payload)
    mac = hmac.new(secret.encode("utf-8"), canonical, hashlib.sha256).hexdigest()
    payload["mac"] = mac
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def outbox_line_is_valid(item: OutboxItem, secret: str | None) -> bool:
    if not secret:
        return True
    mac = item.mac
    if mac is None:
        return False
    payload = item.model_dump(mode="json")
    payload.pop("mac", None)
    canonical = _canonical_json(payload)
    expected = hmac.new(secret.encode("utf-8"), canonical, hashlib.sha256).hexdigest()
    return secrets.compare_digest(mac, expected)
