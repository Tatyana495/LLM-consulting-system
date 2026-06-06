from datetime import UTC, datetime

from sqlalchemy import DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    """
    ORM-модель пользователя Auth Service.

    Здесь описывается только структура таблицы.
    Здесь не должно быть логики регистрации, логина,
    проверки пароля или выпуска JWT.
    """

    __tablename__ = "users"

    __table_args__ = (Index("uq_users_email", "email", unique=True),)

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    email: Mapped[str] = mapped_column(
        String(length=320),
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(length=255),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(length=50),
        nullable=False,
        default="user",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
