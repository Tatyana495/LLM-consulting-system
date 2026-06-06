import time

import jwt
import pytest

from app.core.config import settings


def make_token(
    sub: str = "42",
    role: str = "user",
    ttl_seconds: int = 3600,
) -> str:
    now = int(time.time())

    return jwt.encode(
        {
            "sub": sub,
            "role": role,
            "iat": now,
            "exp": now + ttl_seconds,
        },
        settings.jwt_secret,
        algorithm=settings.jwt_alg,
    )


@pytest.mark.asyncio
async def test_token_command_saves_token_to_fake_redis(
    patch_redis,
    make_message,
) -> None:
    from app.bot.handlers import token_handler

    tg_user_id = 777
    token = make_token(sub="123", role="user")

    message = make_message(
        text=f"/token {token}",
        user_id=tg_user_id,
        chat_id=999,
    )

    await token_handler(message)

    saved_token = await patch_redis.get(f"token:{tg_user_id}")

    assert saved_token == token
    assert message.answers
    assert "Токен принят" in message.answers[-1]


@pytest.mark.asyncio
async def test_text_without_token_does_not_call_celery(
    patch_redis,
    llm_delay_mock,
    make_message,
) -> None:
    from app.bot.handlers import text_handler

    message = make_message(
        text="Что такое JWT?",
        user_id=111,
        chat_id=222,
    )

    await text_handler(message)

    llm_delay_mock.assert_not_called()

    assert message.answers
    assert "Доступ закрыт" in message.answers[-1]


@pytest.mark.asyncio
async def test_text_with_valid_token_calls_celery(
    patch_redis,
    llm_delay_mock,
    make_message,
) -> None:
    from app.bot.handlers import text_handler

    tg_user_id = 111
    tg_chat_id = 222
    prompt = "Что такое RabbitMQ?"

    token = make_token(sub="123", role="user")

    await patch_redis.set(
        name=f"token:{tg_user_id}",
        value=token,
        ex=3600,
    )

    message = make_message(
        text=prompt,
        user_id=tg_user_id,
        chat_id=tg_chat_id,
    )

    await text_handler(message)

    llm_delay_mock.assert_called_once_with(
        tg_chat_id=tg_chat_id,
        prompt=prompt,
    )

    assert message.answers
    assert "Запрос принят" in message.answers[-1]
