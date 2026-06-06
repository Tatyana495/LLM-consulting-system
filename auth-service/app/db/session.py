from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


def build_async_database_url() -> str:
    """
    Собирает async-строку подключения к БД из настроек.

    Для SQLite нужен async-драйвер aiosqlite:

        sqlite:///./auth.db
        ->
        sqlite+aiosqlite:///./auth.db

    Если DATABASE_URL уже задан с async-драйвером,
    например postgresql+asyncpg://..., используем его как есть.
    """
    database_url = settings.resolved_database_url

    if database_url.startswith("sqlite+aiosqlite:///"):
        return database_url

    if database_url.startswith("sqlite:///"):
        return database_url.replace(
            "sqlite:///",
            "sqlite+aiosqlite:///",
            1,
        )

    return database_url


DATABASE_URL = build_async_database_url()


engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)
