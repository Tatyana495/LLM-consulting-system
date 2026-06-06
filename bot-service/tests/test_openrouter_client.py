import json

import httpx
import respx

from app.services.openrouter_client import OpenRouterClient


@respx.mock
def test_openrouter_client_returns_answer_and_sends_payload() -> None:
    route = respx.post(
        "https://openrouter.ai/api/v1/chat/completions",
    ).mock(
        return_value=httpx.Response(
            status_code=200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": "Тестовый ответ LLM",
                        },
                    },
                ],
            },
        ),
    )

    client = OpenRouterClient(
        api_key="test-key",
        model="test-model",
        base_url="https://openrouter.ai/api/v1",
    )

    answer = client.ask("Привет")

    assert answer == "Тестовый ответ LLM"
    assert route.called

    request = route.calls[0].request

    assert request.headers["Authorization"] == "Bearer test-key"

    payload = json.loads(request.content.decode("utf-8"))

    assert payload["model"] == "test-model"
    assert payload["messages"][0]["role"] == "system"
    assert payload["messages"][1]["role"] == "user"
    assert payload["messages"][1]["content"] == "Привет"
