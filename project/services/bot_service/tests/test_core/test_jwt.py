from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from app.core.config import settings
from app.core.jwt import decode_and_validate


def _make_token(exp_offset_minutes: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "42",
        "role": "user",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=exp_offset_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def test_decode_and_validate_valid_jwt() -> None:
    token = _make_token(exp_offset_minutes=30)

    payload = decode_and_validate(token)
    assert payload["sub"] == "42"
    assert payload["role"] == "user"


def test_decode_and_validate_invalid_jwt() -> None:
    with pytest.raises(ValueError, match="Недействительный JWT"):
        decode_and_validate("invalid.jwt.token")


def test_decode_and_validate_expired_jwt() -> None:
    token = _make_token(exp_offset_minutes=-1)
    with pytest.raises(ValueError, match="Срок действия JWT истек"):
        decode_and_validate(token)
