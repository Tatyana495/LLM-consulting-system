import logging
import time
from typing import Any

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from redis.exceptions import RedisError

from app.core.jwt import JWTExpiredError, JWTInvalidError, decode_and_validate
from app.infra.redis import get_redis
from app.tasks.llm_tasks import llm_request


logger = logging.getLogger(__name__)
router = Router(name="handlers")


def _token_key(telegram_user_id: int) -> str:
    return f"token:{telegram_user_id}"


def _get_token_ttl_seconds(payload: dict[str, Any]) -> int:
    exp = payload.get("exp")

    if not isinstance(exp, int):
        return 3600

    ttl = exp - int(time.time())

    return max(ttl, 1)


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    logger.info("START handler fired. chat_id=%s", message.chat.id)

    await message.answer(
        "Привет! Я бот LLM-консультаций.\n\n"
        "Для доступа нужно получить JWT-токен в Auth Service "
        "и отправить его сюда командой:\n\n"
        "/token <твой_jwt>\n\n"
        "После этого можно писать обычные вопросы."
    )


@router.message(Command("token"))
async def token_handler(message: Message) -> None:
    logger.info("TOKEN handler fired. chat_id=%s", message.chat.id)

    if message.from_user is None or message.text is None:
        return

    parts = message.text.split(maxsplit=1)

    if len(parts) != 2:
        await message.answer("Токен нужно отправить так:\n\n/token <твой_jwt>")
        return

    token = parts[1].strip()

    try:
        payload = decode_and_validate(token)
    except JWTExpiredError:
        await message.answer("Токен истёк. Получи новый токен через Auth Service.")
        return
    except JWTInvalidError:
        await message.answer("Токен неверный. Проверь токен или авторизуйся заново.")
        return

    redis = get_redis()
    key = _token_key(message.from_user.id)
    ttl_seconds = _get_token_ttl_seconds(payload)

    try:
        await redis.set(
            name=key,
            value=token,
            ex=ttl_seconds,
        )
    except RedisError:
        await message.answer("Не удалось сохранить токен. Redis временно недоступен.")
        return

    await message.answer(
        "Токен принят. Доступ к LLM-консультациям открыт.\n\n"
        f"Auth user id: {payload['sub']}\n"
        f"Role: {payload['role']}"
    )


@router.message(Command("logout"))
async def logout_handler(message: Message) -> None:
    logger.info("LOGOUT handler fired. chat_id=%s", message.chat.id)

    if message.from_user is None:
        return

    redis = get_redis()
    key = _token_key(message.from_user.id)

    try:
        await redis.delete(key)
    except RedisError:
        await message.answer("Не удалось удалить токен. Redis временно недоступен.")
        return

    await message.answer("Токен удалён. Для нового доступа отправь /token <твой_jwt>.")


@router.message(F.text)
async def text_handler(message: Message) -> None:
    logger.info("TEXT handler fired. chat_id=%s text=%r", message.chat.id, message.text)

    if message.from_user is None or message.text is None:
        return

    redis = get_redis()
    key = _token_key(message.from_user.id)

    try:
        token = await redis.get(key)
    except RedisError:
        await message.answer(
            "Redis временно недоступен. Не могу проверить авторизацию."
        )
        return

    if token is None:
        await message.answer(
            "Доступ закрыт.\n\n"
            "Сначала получи JWT-токен через Auth Service и отправь его командой:\n\n"
            "/token <твой_jwt>"
        )
        return

    try:
        decode_and_validate(token)
    except JWTExpiredError:
        await redis.delete(key)
        await message.answer("Токен истёк. Получи новый токен через Auth Service.")
        return
    except JWTInvalidError:
        await redis.delete(key)
        await message.answer("Токен неверный. Авторизуйся заново через Auth Service.")
        return

    llm_request.delay(
        tg_chat_id=message.chat.id,
        prompt=message.text,
    )

    await message.answer("Запрос принят. Я отправил его в очередь обработки.")
