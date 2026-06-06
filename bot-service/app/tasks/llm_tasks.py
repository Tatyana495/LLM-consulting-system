import logging

from app.core.config import settings
from app.infra.celery_app import celery_app
from app.services.openrouter_client import OpenRouterError, call_openrouter


logger = logging.getLogger(__name__)

TELEGRAM_MESSAGE_LIMIT = 4096


def _split_text(text: str, limit: int = TELEGRAM_MESSAGE_LIMIT) -> list[str]:
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    current = text

    while len(current) > limit:
        split_at = current.rfind("\n", 0, limit)

        if split_at == -1:
            split_at = current.rfind(" ", 0, limit)

        if split_at == -1:
            split_at = limit

        chunks.append(current[:split_at].strip())
        current = current[split_at:].strip()

    if current:
        chunks.append(current)

    return chunks


def _send_telegram_message(tg_chat_id: int, text: str) -> None:
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is not configured")

    import httpx

    url = f"https://api.telegram.org/bot{settings.bot_token}/sendMessage"

    with httpx.Client(timeout=30) as client:
        for chunk in _split_text(text):
            response = client.post(
                url,
                json={
                    "chat_id": tg_chat_id,
                    "text": chunk,
                },
            )
            response.raise_for_status()


@celery_app.task(name="llm_request")
def llm_request(tg_chat_id: int, prompt: str) -> dict[str, str | int]:
    """
    Celery-задача обработки LLM-запроса.

    Получает:
    - tg_chat_id;
    - prompt.

    Делает:
    - вызывает OpenRouter через services/openrouter_client.py;
    - формирует ответ;
    - отправляет сообщение пользователю в Telegram.

    JWT здесь не проверяется.
    JWT проверяется ботом до постановки задачи в очередь.
    """
    logger.info("LLM request started for tg_chat_id=%s", tg_chat_id)

    try:
        answer = call_openrouter(prompt)
    except OpenRouterError as exc:
        logger.exception("OpenRouter client error")

        answer = f"Не удалось получить ответ от OpenRouter.\n\nПричина: {exc}"
    except Exception:
        logger.exception("Unexpected LLM task error")

        answer = (
            "Произошла внутренняя ошибка при обработке LLM-запроса. Попробуй позже."
        )

    _send_telegram_message(
        tg_chat_id=tg_chat_id,
        text=answer,
    )

    logger.info("LLM request finished for tg_chat_id=%s", tg_chat_id)

    return {
        "tg_chat_id": tg_chat_id,
        "status": "sent",
    }
