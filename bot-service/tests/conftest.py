import os
from dataclasses import dataclass
from typing import Any

import pytest
import pytest_asyncio
from fakeredis.aioredis import FakeRedis


os.environ.setdefault("APP_NAME", "bot-service-test")
os.environ.setdefault("ENV", "test")
os.environ.setdefault("BOT_TOKEN", "123456:test-token")
os.environ.setdefault("JWT_SECRET", "test-secret-at-least-32-bytes-long")
os.environ.setdefault("JWT_ALG", "HS256")
os.environ.setdefault("AUTH_SERVICE_URL", "http://auth-service:8000")
os.environ.setdefault("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
os.environ.setdefault("REDIS_URL", "redis://redis:6379/0")
os.environ.setdefault("OPENROUTER_API_KEY", "test-openrouter-key")
os.environ.setdefault("OPENROUTER_MODEL", "openai/gpt-4o-mini")
os.environ.setdefault("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")


@dataclass
class FakeUser:
    id: int


@dataclass
class FakeChat:
    id: int


class FakeMessage:
    def __init__(
        self,
        text: str,
        user_id: int = 100,
        chat_id: int = 200,
    ) -> None:
        self.text = text
        self.from_user = FakeUser(id=user_id)
        self.chat = FakeChat(id=chat_id)
        self.answers: list[str] = []

    async def answer(self, text: str, *args: Any, **kwargs: Any) -> None:
        self.answers.append(text)


@pytest_asyncio.fixture
async def fake_redis() -> FakeRedis:
    redis = FakeRedis(
        encoding="utf-8",
        decode_responses=True,
    )

    try:
        yield redis
    finally:
        await redis.flushall()
        await redis.aclose()


@pytest.fixture
def patch_redis(
    fake_redis: FakeRedis,
    monkeypatch: pytest.MonkeyPatch,
) -> FakeRedis:
    import app.bot.handlers as handlers_module

    monkeypatch.setattr(
        handlers_module,
        "get_redis",
        lambda: fake_redis,
    )

    return fake_redis


@pytest.fixture
def llm_delay_mock(mocker: Any) -> Any:
    import app.bot.handlers as handlers_module

    delay_mock = mocker.Mock()

    fake_task = mocker.Mock()
    fake_task.delay = delay_mock

    mocker.patch.object(
        handlers_module,
        "llm_request",
        fake_task,
    )

    return delay_mock


@pytest.fixture
def make_message() -> type[FakeMessage]:
    return FakeMessage
