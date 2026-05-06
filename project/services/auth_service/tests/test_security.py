import pytest

from app.core.exceptions import InvalidTokenError, TokenExpiredError
from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_and_verify_password() -> None:
    raw_password = "secret-pass-123"
    hashed = hash_password(raw_password)

    assert hashed != raw_password
    assert verify_password(raw_password, hashed)
    assert not verify_password("wrong-pass", hashed)


def test_create_and_decode_token_ok() -> None:
    token = create_access_token(sub="42", role="user", expires_minutes=60)
    payload = decode_token(token)

    assert payload["sub"] == "42"
    assert payload["role"] == "user"
    assert "iat" in payload
    assert "exp" in payload


def test_decode_invalid_token() -> None:
    with pytest.raises(InvalidTokenError):
        decode_token("invalid.token.value")


def test_decode_expired_token() -> None:
    token = create_access_token(sub="1", role="user", expires_minutes=-1)

    with pytest.raises(TokenExpiredError):
        decode_token(token)
