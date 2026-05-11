from functools import lru_cache
from typing import Literal, Self
from urllib.parse import urlparse

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_MAX_BOT_TOKEN_PLACEHOLDERS: frozenset[str] = frozenset({"replace-with-max-bot-token"})


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = "local"

    max_bot_token: SecretStr = SecretStr("replace-with-max-bot-token")
    jwt_secret: str = Field(
        ...,
        min_length=32,
        description="Тот же секрет, что в auth_service (не плейсхолдер из репозитория)",
    )
    jwt_alg: str = "HS256"
    jwt_audience: str | None = Field(
        default=None,
        description="Должно совпадать с JWT_AUDIENCE в auth_service, если там задано",
    )

    openrouter_api_key: SecretStr = SecretStr("")
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "stepfun/step-3.5-flash:free"
    openrouter_site_url: str = "https://example.com"
    openrouter_app_name: str = "bot-service"
    openrouter_timeout_seconds: float = 60.0

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "amqp://guest:guest@localhost:5672//"

    api_host: str = "0.0.0.0"
    api_port: int = 8080

    # Ограничение размера тела запроса (по заголовку Content-Length), байт.
    max_request_body_bytes: int = 1_048_576
    webhook_path: str = "/webhook"
    max_delivery_mode: Literal["webhook", "polling"] = "polling"
    outbox_dedup_enabled: bool = False
    outbox_dedup_ttl_seconds: int = 3600
    outbox_send_max_retries: int = 3

    # Опционально: общий секрет HMAC для max_auth:* и max:outbox (защита от подмены только в Redis).
    redis_integrity_secret: SecretStr | None = None

    # Доп. слой для MAX webhook (прокси может подставлять заголовок; MAX сам заголовок не шлёт).
    webhook_request_secret: SecretStr | None = None
    webhook_request_header: str = "x-webhook-secret"
    # Через запятую, напр. 203.0.113.0/24,2001:db8::/32
    webhook_allowed_cidrs: str | None = None
    # Если >0 — брать клиентский IP из первой части X-Forwarded-For (доверять только своему прокси).
    webhook_forwarded_for_trust_hops: int = 0

    # None → False в prod/production, True иначе; явно задайте LOG_PROMPT_CONTENT для переопределения.
    log_prompt_content: bool | None = Field(default=None)

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

    @field_validator("webhook_forwarded_for_trust_hops")
    @classmethod
    def clamp_webhook_xff_hops(cls, v: int) -> int:
        return max(0, int(v))

    @model_validator(mode="after")
    def prod_max_token_log_prompt_defaults(self) -> Self:
        if self.log_prompt_content is None:
            object.__setattr__(
                self,
                "log_prompt_content",
                False if self.env in ("prod", "production") else True,
            )
        raw = self.max_bot_token.get_secret_value().strip()
        if self.env in ("prod", "production"):
            if not raw:
                msg = "MAX_BOT_TOKEN must be set in production"
                raise ValueError(msg)
            low = raw.lower()
            if any(low == p.lower() for p in _MAX_BOT_TOKEN_PLACEHOLDERS):
                msg = "MAX_BOT_TOKEN must not be a placeholder value in production"
                raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def validate_openrouter_base_url(self) -> Self:
        raw = self.openrouter_base_url.strip()
        p = urlparse(raw)
        if p.scheme not in ("http", "https"):
            msg = "OPENROUTER_BASE_URL must use http or https"
            raise ValueError(msg)
        host = (p.hostname or "").lower()
        if not host:
            msg = "OPENROUTER_BASE_URL must include a host"
            raise ValueError(msg)
        if self.env in ("prod", "production"):
            if p.scheme != "https":
                msg = "OPENROUTER_BASE_URL must use https in production (ENV=prod|production)"
                raise ValueError(msg)
            if host != "openrouter.ai" and not host.endswith(".openrouter.ai"):
                msg = "OPENROUTER_BASE_URL host must be openrouter.ai in production"
                raise ValueError(msg)
        object.__setattr__(self, "openrouter_base_url", raw)
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
