import re

from pydantic import BaseModel, EmailStr, Field, field_validator

_PASSWORD_BLOCKLIST = frozenset(
    {
        "password12345",
        "password123456",
        "qwerty123456",
        "123456789012",
        "admin12345678",
    }
)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_policy(cls, v: str) -> str:
        if not any(c.islower() for c in v):
            msg = "Пароль должен содержать хотя бы одну строчную букву"
            raise ValueError(msg)
        if not any(c.isupper() for c in v):
            msg = "Пароль должен содержать хотя бы одну заглавную букву"
            raise ValueError(msg)
        if not any(c.isdigit() for c in v):
            msg = "Пароль должен содержать хотя бы одну цифру"
            raise ValueError(msg)
        if not re.search(r"[^A-Za-z0-9]", v):
            msg = "Пароль должен содержать хотя бы один спецсимвол"
            raise ValueError(msg)
        lower = v.lower()
        if lower in _PASSWORD_BLOCKLIST:
            msg = "Этот пароль слишком распространён; выберите другой"
            raise ValueError(msg)
        if re.fullmatch(r"(.)\1{7,}", v):
            msg = "Пароль не должен состоять из одного повторяющегося символа"
            raise ValueError(msg)
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
