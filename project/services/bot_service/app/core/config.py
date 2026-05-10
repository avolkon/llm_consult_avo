from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    max_bot_token: SecretStr = SecretStr("replace-with-max-bot-token")
    jwt_secret: str = "replace-with-secret-matching-auth-service"
    jwt_alg: str = "HS256"

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


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
