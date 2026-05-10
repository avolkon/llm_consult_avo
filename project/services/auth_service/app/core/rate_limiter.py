"""Rate limiter configuration for Auth Service."""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Limiter instance shared across the application
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
