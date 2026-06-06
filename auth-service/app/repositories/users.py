from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User


class UserRepository:
    """
    Репозиторий доступа к пользователям.

    Здесь только операции уровня БД:
    - получить пользователя по id;
    - получить пользователя по email;
    - создать пользователя.

    Здесь не должно быть:
    - проверки пароля;
    - хеширования пароля;
    - создания JWT;
    - raise HTTPException;
    - бизнес-логики регистрации или логина.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        email: str,
        password_hash: str,
        role: str = "user",
    ) -> User:
        user = User(
            email=email,
            password_hash=password_hash,
            role=role,
        )

        self.session.add(user)

        # flush отправляет INSERT в БД, но не делает commit.
        # commit должен выполняться выше — в usecase или dependency-слое.
        await self.session.flush()
        await self.session.refresh(user)

        return user
