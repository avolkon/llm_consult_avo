from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.db import session as db_session
from app.main import create_app


def test_sqlite_db_file_is_created_on_startup(tmp_path: Path) -> None:
    db_file = tmp_path / "startup_init.db"
    original_env = settings.env
    original_database_url = settings.database_url
    original_engine = db_session.engine
    settings.env = "local"
    settings.database_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    db_session.engine = create_async_engine(settings.database_url, echo=False)

    try:
        with TestClient(create_app()) as client:
            response = client.get("/health")
            assert response.status_code == 200
    finally:
        settings.env = original_env
        settings.database_url = original_database_url
        db_session.engine = original_engine

    assert db_file.exists()
