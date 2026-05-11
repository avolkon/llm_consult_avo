#!/usr/bin/env python3
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.responses import JSONResponse

from app.api.router import build_api_router
from app.core.config import get_settings, settings
from app.core.rate_limiter import limiter
from app.db.session import init_db_schema


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    is_local_like = settings.env in {"local", "dev", "test"}
    is_sqlite = settings.database_url.startswith("sqlite+aiosqlite")
    if is_local_like and is_sqlite:
        await init_db_schema()
    yield


def create_app() -> FastAPI:
    _prod = settings.env in {"prod", "production"}
    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
        docs_url=None if _prod else "/docs",
        redoc_url=None if _prod else "/redoc",
        openapi_url=None if _prod else "/openapi.json",
    )
    app.include_router(build_api_router())

    # Attach rate limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Security headers middleware
    @app.middleware("http")
    async def security_headers_middleware(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if settings.env in {"prod", "production"}:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    @app.middleware("http")
    async def request_body_size_middleware(request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH"):
            cl = request.headers.get("content-length")
            if cl is not None:
                try:
                    if int(cl) > get_settings().max_request_body_bytes:
                        return JSONResponse({"detail": "Request body too large"}, status_code=413)
                except ValueError:
                    return JSONResponse({"detail": "Invalid Content-Length"}, status_code=400)
        return await call_next(request)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


def run_server() -> None:
    import uvicorn

    uvicorn.run(
        create_app(),
        host=settings.api_host,
        port=settings.api_port,
    )


def main() -> None:
    run_server()


if __name__ == "__main__":
    main()
