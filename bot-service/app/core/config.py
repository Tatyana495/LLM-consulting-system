from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Конфигурация Bot Service.

    Здесь только:
    - чтение переменных окружения;
    - описание настроек сервиса;
    - создание единого объекта settings.

    Здесь не должно быть:
    - запуска FastAPI;
    - запуска aiogram;
    - обращений к Redis/RabbitMQ/OpenRouter;
    - бизнес-логики.
    """

    app_name: str = Field(default="bot-service", alias="APP_NAME")
    env: Literal["local", "dev", "test", "prod"] = Field(
        default="local",
        alias="ENV",
    )

    bot_token: str = Field(
        default="",
        validation_alias=AliasChoices("BOT_TOKEN", "TELEGRAM_BOT_TOKEN"),
    )

    auth_service_url: str = Field(
        default="http://auth-service:8000",
        alias="AUTH_SERVICE_URL",
    )

    jwt_secret: str = Field(
        default="change-me-auth-secret-at-least-32-bytes",
        alias="JWT_SECRET",
    )
    jwt_alg: str = Field(
        default="HS256",
        alias="JWT_ALG",
    )

    rabbitmq_url: str = Field(
        default="amqp://guest:guest@rabbitmq:5672/",
        alias="RABBITMQ_URL",
    )

    redis_url: str = Field(
        default="redis://redis:6379/0",
        alias="REDIS_URL",
    )

    openrouter_api_key: str = Field(
        default="",
        alias="OPENROUTER_API_KEY",
    )
    openrouter_model: str = Field(
        default="openai/gpt-4o-mini",
        alias="OPENROUTER_MODEL",
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        alias="OPENROUTER_BASE_URL",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def telegram_bot_token(self) -> str:
        """
        Совместимость со старым кодом, где использовалось имя
        settings.telegram_bot_token.
        """
        return self.bot_token

    @property
    def openrouter_chat_completions_url(self) -> str:
        return f"{self.openrouter_base_url.rstrip('/')}/chat/completions"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
