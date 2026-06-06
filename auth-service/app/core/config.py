from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Конфигурация auth-service.

    Здесь только:
    - чтение переменных окружения;
    - описание настроек приложения;
    - формирование единого объекта settings.

    Здесь не должно быть:
    - запуска FastAPI;
    - SQL-запросов;
    - бизнес-логики;
    - работы с пользователями и токенами.
    """

    app_name: str = Field(default="auth-service", alias="APP_NAME")
    env: Literal["local", "dev", "test", "prod"] = Field(
        default="local",
        alias="ENV",
    )

    jwt_secret: str = Field(
        default="change-me-auth-secret-at-least-32-bytes",
        alias="JWT_SECRET",
    )
    jwt_alg: str = Field(default="HS256", alias="JWT_ALG")
    access_token_expire_minutes: int = Field(
        default=60,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )

    sqlite_path: str = Field(default="./auth.db", alias="SQLITE_PATH")
    database_url: str | None = Field(default=None, alias="DATABASE_URL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def resolved_database_url(self) -> str:
        """
        Итоговая строка подключения к БД.

        Если DATABASE_URL задан явно, используется он.
        Иначе формируется SQLite URL на основе SQLITE_PATH.
        """
        if self.database_url:
            return self.database_url

        return f"sqlite:///{self.sqlite_path}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
