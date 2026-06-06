import logging
from typing import Any

import httpx

from app.core.config import settings


logger = logging.getLogger(__name__)


class OpenRouterError(Exception):
    """
    Базовая ошибка клиента OpenRouter.

    Эту ошибку можно ловить в Celery-задаче и отправлять пользователю
    понятное сообщение вместо падения worker.
    """


class OpenRouterConfigError(OpenRouterError):
    """
    Ошибка конфигурации OpenRouter.
    Например, не задан OPENROUTER_API_KEY.
    """


class OpenRouterRequestError(OpenRouterError):
    """
    Ошибка сетевого запроса к OpenRouter.
    """


class OpenRouterResponseError(OpenRouterError):
    """
    OpenRouter вернул неуспешный HTTP-статус.
    """


class OpenRouterFormatError(OpenRouterError):
    """
    OpenRouter вернул неожиданный формат ответа.
    """


class OpenRouterClient:
    """
    HTTP-клиент для обращения к OpenRouter.

    Здесь только:
    - формирование payload для /chat/completions;
    - выставление HTTP-заголовков;
    - отправка запроса через httpx;
    - обработка сетевых ошибок;
    - обработка не-200 ответов;
    - извлечение текста ответа.

    Здесь не должно быть:
    - Telegram-логики;
    - Celery-логики;
    - JWT-логики;
    - работы с Redis.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        timeout_seconds: float = 60.0,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    @property
    def chat_completions_url(self) -> str:
        return f"{self.base_url}/chat/completions"

    def ask(self, prompt: str) -> str:
        """
        Отправляет пользовательский prompt в OpenRouter
        и возвращает текст ответа модели.
        """
        if not self.api_key:
            raise OpenRouterConfigError("OPENROUTER_API_KEY is not configured")

        payload = self._build_payload(prompt)
        headers = self._build_headers()

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(
                    self.chat_completions_url,
                    headers=headers,
                    json=payload,
                )
        except httpx.TimeoutException as exc:
            logger.exception("OpenRouter request timeout")
            raise OpenRouterRequestError("OpenRouter request timed out") from exc
        except httpx.RequestError as exc:
            logger.exception("OpenRouter network request error")
            raise OpenRouterRequestError("OpenRouter network request failed") from exc

        if response.status_code < 200 or response.status_code >= 300:
            raise OpenRouterResponseError(self._build_error_message(response))

        return self._extract_answer(response)

    def _build_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _build_payload(self, prompt: str) -> dict[str, Any]:
        return {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Ты полезный ассистент для LLM-консультаций. "
                        "Отвечай понятно, кратко и по делу."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        }

    def _extract_answer(self, response: httpx.Response) -> str:
        try:
            data = response.json()
        except ValueError as exc:
            logger.exception("OpenRouter returned non-JSON response")
            raise OpenRouterFormatError(
                "OpenRouter returned non-JSON response"
            ) from exc

        try:
            answer = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            logger.exception("Unexpected OpenRouter response format")
            raise OpenRouterFormatError(
                "Unexpected OpenRouter response format"
            ) from exc

        if not isinstance(answer, str) or not answer.strip():
            raise OpenRouterFormatError("OpenRouter returned empty answer")

        return answer.strip()

    def _build_error_message(self, response: httpx.Response) -> str:
        body_preview = response.text[:500]

        return (
            "OpenRouter returned unsuccessful response. "
            f"status_code={response.status_code}, "
            f"body={body_preview}"
        )


openrouter_client = OpenRouterClient(
    api_key=settings.openrouter_api_key,
    model=settings.openrouter_model,
    base_url=settings.openrouter_base_url,
)


def call_openrouter(prompt: str) -> str:
    """
    Удобная функция для вызова OpenRouter из задач/тестов.
    """
    return openrouter_client.ask(prompt)
