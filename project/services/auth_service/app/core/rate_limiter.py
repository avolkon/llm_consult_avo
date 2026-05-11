"""Rate limiter configuration for Auth Service.

Лимиты привязаны к процессу (in-memory): при нескольких репликах без общего
хранилища эффективный порог умножается на число инстансов; много разных IP
обходит per-IP квоту. Для строгой политики нужен общий backend (Redis) или edge/WAF.
"""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import get_settings


def rate_limit_key(request: Request) -> str:
    """Клиент за reverse proxy: первый IP из X-Forwarded-For (только при TRUSTED_PROXY_HEADERS)."""
    if get_settings().trusted_proxy_headers:
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=rate_limit_key, default_limits=["100/minute"])
