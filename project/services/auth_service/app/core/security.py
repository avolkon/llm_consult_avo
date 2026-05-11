from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import ExpiredSignatureError, PyJWTError
from passlib.context import CryptContext

from app.core.config import get_settings
from app.core.exceptions import InvalidTokenError, TokenExpiredError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    *,
    sub: str,
    role: str,
    expires_minutes: int | None = None,
) -> str:
    conf = get_settings()
    now = datetime.now(timezone.utc)
    minutes = expires_minutes or conf.access_token_expire_minutes
    exp = now + timedelta(minutes=minutes)
    payload: dict = {
        "sub": sub,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    if conf.jwt_audience:
        payload["aud"] = conf.jwt_audience
    return jwt.encode(payload, conf.jwt_secret, algorithm=conf.jwt_alg)


def decode_token(token: str) -> dict:
    conf = get_settings()
    decode_kwargs: dict = {
        "algorithms": [conf.jwt_alg],
        "options": {"verify_aud": bool(conf.jwt_audience)},
    }
    if conf.jwt_audience:
        decode_kwargs["audience"] = conf.jwt_audience
    try:
        payload = jwt.decode(token, conf.jwt_secret, **decode_kwargs)
    except ExpiredSignatureError as exc:
        raise TokenExpiredError() from exc
    except PyJWTError as exc:
        raise InvalidTokenError() from exc

    sub = payload.get("sub")
    if not sub:
        raise InvalidTokenError()
    return payload
