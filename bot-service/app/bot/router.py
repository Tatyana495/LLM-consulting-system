from aiogram import Router

from app.bot.handlers import router as handlers_router


bot_router = Router(name="bot")

bot_router.include_router(handlers_router)
