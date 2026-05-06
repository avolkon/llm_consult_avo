from jose import ExpiredSignatureError, JWTError, jwt

from app.core.config import settings


def decode_and_validate(token: str) -> dict:
    """Проверка JWT (подпись, exp) без логики пользователей."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_alg],
            options={"verify_aud": False},
        )
    except ExpiredSignatureError as exc:
        raise ValueError("Срок действия JWT истек") from exc
    except JWTError as exc:
        raise ValueError("Недействительный JWT") from exc

    if not payload.get("sub"):
        raise ValueError("В JWT отсутствует поле sub")
    return payload
