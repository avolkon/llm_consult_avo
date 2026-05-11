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
    jwt_audience: str | None = Field(
        default=None,
        description="Если задано, claim aud в JWT и строгая проверка при decode (должно совпадать с bot_service)",
    )
    access_token_expire_minutes: int = 60

    database_url: str = "sqlite+aiosqlite:///./auth.db"

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # За nginx/traefik: доверять X-Forwarded-For для slowapi (только если прокси под вашим контролем).
    trusted_proxy_headers: bool = False

    # Ограничение размера тела запроса (по заголовку Content-Length), байт.
    max_request_body_bytes: int = 1_048_576

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if v in {"change_me_super_secret", "replace-with-secret-matching-auth-service", ""}:
            msg = "JWT_SECRET must be set to a strong secret (not a placeholder)"
            raise ValueError(msg)
        return v

    @field_validator("jwt_alg")
    @classmethod
    def validate_jwt_alg(cls, v: str) -> str:
        allowed = {"HS256"}
        if v not in allowed:
            msg = f"JWT_ALG must be one of {sorted(allowed)}"
            raise ValueError(msg)
        return v

    @field_validator("jwt_audience")
    @classmethod
    def normalize_jwt_audience(cls, v: str | None) -> str | None:
        if v is not None and not str(v).strip():
            return None
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
