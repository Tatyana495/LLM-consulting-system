from app.core.exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import User
from app.repositories.users import UserRepository
from app.schemas.auth import TokenResponse


class AuthUseCase:
    """
    Бизнес-логика Auth Service.

    Здесь можно:
    - проверять существование пользователя;
    - хешировать пароль;
    - проверять пароль;
    - создавать JWT;
    - проверять наличие пользователя для /me.

    Здесь нельзя:
    - писать SQL-запросы напрямую;
    - работать напрямую с FastAPI HTTPException;
    - описывать ORM-модели.
    """

    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    async def register(
        self,
        email: str,
        password: str,
        role: str = "user",
    ) -> User:
        """
        Регистрирует нового пользователя.

        Если пользователь с таким email уже существует,
        выбрасывает UserAlreadyExistsError.
        """
        normalized_email = self._normalize_email(email)

        existing_user = await self.user_repository.get_by_email(normalized_email)
        if existing_user is not None:
            raise UserAlreadyExistsError()

        password_hash = hash_password(password)

        user = await self.user_repository.create(
            email=normalized_email,
            password_hash=password_hash,
            role=role,
        )

        await self.user_repository.session.commit()
        await self.user_repository.session.refresh(user)

        return user

    async def login(
        self,
        email: str,
        password: str,
    ) -> TokenResponse:
        """
        Проверяет email и пароль пользователя.

        При успехе возвращает JWT access token.
        При ошибке выбрасывает InvalidCredentialsError.
        """
        normalized_email = self._normalize_email(email)

        user = await self.user_repository.get_by_email(normalized_email)
        if user is None:
            raise InvalidCredentialsError()

        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()

        access_token = create_access_token(
            subject=user.id,
            role=user.role,
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
        )

    async def me(self, user_id: int) -> User:
        """
        Возвращает текущего пользователя по user_id.

        Используется для /auth/me после проверки JWT в dependencies.
        """
        user = await self.user_repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError()

        return user

    @staticmethod
    def _normalize_email(email: str) -> str:
        """
        Приводит email к единому виду.

        Это снижает риск дублей вида:
        User@Example.com и user@example.com.
        """
        return email.strip().lower()
