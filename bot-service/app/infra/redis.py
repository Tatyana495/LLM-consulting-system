from redis.asyncio import Redis

from app.core.config import settings


_redis_client: Redis | None = None


def get_redis() -> Redis:
    """
    Возвращает единый Redis-клиент для Bot Service.

    Клиент создаётся лениво при первом вызове и переиспользуется
    при следующих вызовах.

    Здесь не должно быть бизнес-логики.
    В тестах этот слой можно мокать.
    """
    global _redis_client

    if _redis_client is None:
        _redis_client = Redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )

    return _redis_client


async def close_redis() -> None:
    """
    Закрывает Redis-клиент при остановке приложения/процесса.

    Полезно для FastAPI lifespan или корректного завершения bot runner.
    """
    global _redis_client

    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
