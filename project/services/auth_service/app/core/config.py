from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "auth-service"
    env: str = "local"

    jwt_secret: str = Field(..., min_length=32, description="JWT signing secret (must be strong and unique)")
    jwt_alg: str = "HS256"
    access_token_expire_minutes: int = 60

    database_url: str = "sqlite+aiosqlite:///./auth.db"

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Ограничение размера тела запроса (по заголовку Content-Length), байт.
    max_request_body_bytes: int = 1_048_576

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if v in {"change_me_super_secret", "replace-with-secret-matching-auth-service", ""}:
            msg = "JWT_SECRET must be set to a strong secret (not a placeholder)"
            raise ValueError(msg)
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
