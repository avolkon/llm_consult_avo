from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import get_db_session
from app.repositories.users import UserRepository
from app.usecases.auth import AuthUseCase

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_db() -> AsyncIterator[AsyncSession]:
    async for session in get_db_session():
        yield session


def get_users_repo(db: Annotated[AsyncSession, Depends(get_db)]) -> UserRepository:
    return UserRepository(db)


def get_auth_uc(
    users_repo: Annotated[UserRepository, Depends(get_users_repo)],
) -> AuthUseCase:
    return AuthUseCase(users_repo)


async def get_current_user_id(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> int:
    payload = decode_token(token)
    return int(payload["sub"])
