from aiogram import Bot, Dispatcher

from app.bot.router import bot_router
from app.core.config import settings


def create_bot() -> Bot:
    """
    Создаёт объект aiogram Bot.

    Здесь только техническая сборка Bot.
    Здесь нет бизнес-логики, JWT-проверок или LLM-запросов.
    """
    if not settings.bot_token:
        raise RuntimeError(
            "BOT_TOKEN is empty. Create .env file from .env.example and set BOT_TOKEN."
        )

    return Bot(token=settings.bot_token)


def create_dispatcher() -> Dispatcher:
    """
    Создаёт Dispatcher и подключает роутеры.

    Здесь только регистрация handlers/routers.
    Бизнес-логика находится в handlers/services/tasks.
    """
    dispatcher = Dispatcher()

    dispatcher.include_router(bot_router)

    return dispatcher
