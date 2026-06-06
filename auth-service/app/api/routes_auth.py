from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import get_auth_uc, get_current_user
from app.db.models import User
from app.schemas.auth import LoginResponse, RegisterRequest
from app.schemas.user import UserPublic
from app.usecases.auth import AuthUseCase


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post(
    "/register",
    response_model=UserPublic,
    status_code=201,
)
async def register(
    payload: RegisterRequest,
    auth_uc: Annotated[AuthUseCase, Depends(get_auth_uc)],
) -> User:
    """
    Регистрирует нового пользователя.

    Эндпоинт тонкий:
    - принимает входные данные;
    - вызывает usecase;
    - возвращает результат.

    SQL, хеширования пароля и генерации токена здесь нет.
    """
    return await auth_uc.register(
        email=payload.email,
        password=payload.password,
    )


@router.post(
    "/login",
    response_model=LoginResponse,
)
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_uc: Annotated[AuthUseCase, Depends(get_auth_uc)],
) -> LoginResponse:
    """
    Выполняет логин пользователя.

    OAuth2PasswordRequestForm передаёт:
    - form.username — используем как email;
    - form.password — пароль пользователя.
    """
    return await auth_uc.login(
        email=form.username,
        password=form.password,
    )


@router.get(
    "/me",
    response_model=UserPublic,
)
async def me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Возвращает текущего пользователя.

    Проверка JWT и получение пользователя выполняются в dependencies/usecase.
    """
    return current_user
