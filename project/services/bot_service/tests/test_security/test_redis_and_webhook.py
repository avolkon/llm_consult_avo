from __future__ import annotations

import json

import pytest
from fakeredis.aioredis import FakeRedis
from pydantic import SecretStr
from starlette.requests import Request

from app.core.config import Settings, get_settings
from app.core.constants import max_auth_key
from app.models.outbox import OutboxItem
from app.security.redis_integrity import (
    outbox_line_is_valid,
    parse_session_json,
    seal_outbox_for_redis,
    seal_session_json,
)
from app.security.webhook_gate import webhook_preflight_response
from app.services.auth_mapping import get_auth, register_token


def _scope(
    method: str,
    path: str,
    *,
    headers: dict[str, str] | None = None,
    client: tuple[str, int] = ("203.0.113.50", 0),
) -> dict:
    raw_headers: list[tuple[bytes, bytes]] = []
    if headers:
        for k, v in headers.items():
            raw_headers.append((k.lower().encode("latin-1"), v.encode("latin-1")))
    return {
        "type": "http",
        "method": method,
        "path": path,
        "headers": raw_headers,
        "client": client,
    }


def test_seal_and_parse_session() -> None:
    secret = "012345678901234567890123456789ab"
    raw = seal_session_json("u1", "admin", secret)
    assert parse_session_json(raw, secret) == ("u1", "admin")
    assert parse_session_json(raw + "x", secret) is None


def test_session_plain_without_secret() -> None:
    raw = seal_session_json("u1", "user", None)
    assert '"mac"' not in raw
    assert parse_session_json(raw, None) == ("u1", "user")


def test_outbox_seal_and_verify() -> None:
    secret = "012345678901234567890123456789ab"
    item = OutboxItem(max_user_id="1", text="hi", task_id="t", created_at=1.5, retry_count=0)
    line = seal_outbox_for_redis(item, secret)
    back = OutboxItem.from_redis_json(line)
    assert outbox_line_is_valid(back, secret)
    back_bad = OutboxItem.model_validate({**json.loads(line), "text": "no"})
    assert not outbox_line_is_valid(back_bad, secret)


def test_webhook_gate_secret_header() -> None:
    s = Settings(
        jwt_secret="01234567890123456789012345678901",
        webhook_path="/webhook",
        webhook_request_secret=SecretStr("whsek"),
    )
    req = Request(_scope("POST", "/webhook", headers={"x-webhook-secret": "whsek"}))
    assert webhook_preflight_response(req, s) is None

    bad = Request(_scope("POST", "/webhook", headers={"x-webhook-secret": "nope"}))
    resp = webhook_preflight_response(bad, s)
    assert resp is not None
    assert resp.status_code == 403


def test_webhook_gate_skips_non_post() -> None:
    s = Settings(
        jwt_secret="01234567890123456789012345678901",
        webhook_path="/webhook",
        webhook_request_secret=SecretStr("whsek"),
    )
    req = Request(_scope("GET", "/webhook"))
    assert webhook_preflight_response(req, s) is None


def test_webhook_gate_cidr() -> None:
    s = Settings(
        jwt_secret="01234567890123456789012345678901",
        webhook_path="/webhook",
        webhook_allowed_cidrs="203.0.113.0/24",
    )
    ok = Request(_scope("POST", "/webhook", client=("203.0.113.10", 0)))
    assert webhook_preflight_response(ok, s) is None

    bad = Request(_scope("POST", "/webhook", client=("198.51.100.1", 0)))
    resp = webhook_preflight_response(bad, s)
    assert resp is not None
    assert resp.status_code == 403


@pytest.fixture
def clear_integrity_env(monkeypatch: pytest.MonkeyPatch) -> None:
    yield
    monkeypatch.delenv("REDIS_INTEGRITY_SECRET", raising=False)
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_auth_mapping_integrity_roundtrip(
    monkeypatch: pytest.MonkeyPatch,
    clear_integrity_env: object,
) -> None:
    monkeypatch.setenv("REDIS_INTEGRITY_SECRET", "012345678901234567890123456789ab")
    get_settings.cache_clear()

    redis = FakeRedis(decode_responses=True)
    await register_token(
        redis,
        "101",
        {"sub": "user-1", "role": "user", "exp": 9_999_999_999},
    )
    raw = await redis.get(max_auth_key("101"))
    assert raw is not None
    assert '"v"' in raw
    auth = await get_auth(redis, "101")
    assert auth == ("user-1", "user")
