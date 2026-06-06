from collections.abc import AsyncIterator
from typing import Annotated, Any

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidTokenError, TokenExpiredError
from app.core.security import decode_token
from app.db.models import User
from app.db.session import AsyncSessionLocal
from app.repositories.users import UserRepository
from app.usecases.auth import AuthUseCase


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
)


async def get_db() -> AsyncIterator[AsyncSession]:
    """
    FastAPI dependency для выдачи AsyncSession.

    Сессия открывается на время обработки запроса
    и гарантированно закрывается после него.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_users_repo(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserRepository:
    """
    Фабрика репозитория пользователей.
    """
    return UserRepository(session=db)


async def get_auth_uc(
    users_repo: Annotated[UserRepository, Depends(get_users_repo)],
) -> AuthUseCase:
    """
    Фабрика usecase-слоя авторизации.
    """
    return AuthUseCase(user_repository=users_repo)


async def get_current_user_id(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> int:
    """
    Достаёт JWT из Authorization: Bearer ...,
    декодирует его и возвращает user_id из поля sub.

    При ошибках токена выбрасывает:
    - TokenExpiredError;
    - InvalidTokenError.
    """
    try:
        payload: dict[str, Any] = decode_token(token)
    except ValueError as exc:
        message = str(exc).lower()

        if "expired" in message:
            raise TokenExpiredError() from exc

        raise InvalidTokenError() from exc

    subject = payload.get("sub")

    if subject is None:
        raise InvalidTokenError()

    try:
        return int(subject)
    except (TypeError, ValueError) as exc:
        raise InvalidTokenError() from exc


async def get_current_user(
    user_id: Annotated[int, Depends(get_current_user_id)],
    auth_uc: Annotated[AuthUseCase, Depends(get_auth_uc)],
) -> User:
    """
    Возвращает текущего пользователя.

    JWT уже проверен в get_current_user_id().
    Здесь дополнительно проверяем, что пользователь всё ещё существует в БД.
    """
    return await auth_uc.me(user_id=user_id)
