from jose import ExpiredSignatureError, JWTError, jwt

from app.core.config import get_settings


def decode_and_validate(token: str) -> dict:
    """Проверка JWT (подпись, exp, aud при настройке) без логики пользователей."""
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
        raise ValueError("Срок действия JWT истек") from exc
    except JWTError as exc:
        raise ValueError("Недействительный JWT") from exc

    if not payload.get("sub"):
        raise ValueError("В JWT отсутствует поле sub")
    return payload
