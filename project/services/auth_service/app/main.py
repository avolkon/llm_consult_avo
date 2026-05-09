#!/usr/bin/env python3
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import build_api_router
from app.core.config import settings
from app.db.session import init_db_schema


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    is_local_like = settings.env in {"local", "dev", "test"}
    is_sqlite = settings.database_url.startswith("sqlite+aiosqlite")
    if is_local_like and is_sqlite:
        await init_db_schema()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.include_router(build_api_router())

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
