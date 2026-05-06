from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.users import UserRepository
from app.schemas.auth import RegisterRequest, TokenResponse
from app.schemas.user import UserPublic


class AuthUseCase:
    def __init__(self, users_repo: UserRepository) -> None:
        self._users_repo = users_repo

    async def register(self, payload: RegisterRequest) -> UserPublic:
        existing = await self._users_repo.get_by_email(payload.email)
        if existing is not None:
            raise UserAlreadyExistsError()
        try:
            user = await self._users_repo.create(
                email=payload.email,
                password_hash=hash_password(payload.password),
                role="user",
            )
        except IntegrityError as exc:
            raise UserAlreadyExistsError() from exc
        return UserPublic.model_validate(user)

    async def login(self, username: str, password: str) -> TokenResponse:
        user = await self._users_repo.get_by_email(username)
        if user is None:
            raise InvalidCredentialsError()
        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()
        token = create_access_token(sub=str(user.id), role=user.role)
        return TokenResponse(access_token=token, token_type="bearer")

    async def me(self, user_id: int) -> UserPublic:
        user = await self._users_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError()
        return UserPublic.model_validate(user)
