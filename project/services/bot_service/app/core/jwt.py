from jose import JWTError, jwt

from app.core.config import settings


def decode_and_validate(token: str) -> dict:
    """Проверка JWT (секрет и срок) без логики пользователей — как в архитектуре проекта."""
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    except JWTError as exc:
        raise ValueError("Недействительный или просроченный JWT") from exc
