import asyncio
import logging

from app.bot.dispatcher import create_bot, create_dispatcher
from app.infra.redis import close_redis


async def main() -> None:
    """
    Отдельная точка входа для Telegram-бота.

    FastAPI Bot Service запускается отдельно через app.main.
    Этот процесс запускает только aiogram polling.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    bot = create_bot()
    dispatcher = create_dispatcher()

    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()
        await close_redis()


if __name__ == "__main__":
    asyncio.run(main())
