from typing import cast

from ai_agent.core.message import Message
from ai_agent.core.request import ChatRequest, ModelConfig
from ai_agent.providers.base import Provider
from ai_agent.providers.openai import OpenAIProvider


def test_openai_provider_builds_provider_specific_request() -> None:
    captured: dict[str, object] = {}

    def fake_transport(
        url: str,
        headers: dict[str, str],
        payload: dict[str, object],
    ) -> dict[str, object]:
        captured["url"] = url
        captured["headers"] = headers
        captured["payload"] = payload
        return {
            "status": "completed",
            "output_text": "hello from openai",
            "usage": {
                "input_tokens": 10,
                "output_tokens": 5,
                "total_tokens": 15,
            },
        }

    provider = OpenAIProvider(api_key="test-key", transport=fake_transport)
    request = ChatRequest(
        messages=[
            Message(role="system", content="Be concise."),
            Message(role="user", content="Hello"),
        ],
        config=ModelConfig(model="test-model", temperature=0.2, max_tokens=100),
    )

    response = provider.chat(request)
    payload = cast(dict[str, object], captured["payload"])

    assert captured["url"] == "https://api.openai.com/v1/responses"
    assert captured["headers"] == {"Authorization": "Bearer test-key"}
    assert payload["model"] == "test-model"
    assert payload["temperature"] == 0.2
    assert payload["max_output_tokens"] == 100
    assert response.message.content == "hello from openai"
    assert response.usage is not None
    assert response.usage.total_tokens == 15


def test_openai_provider_matches_provider_protocol() -> None:
    provider: Provider = OpenAIProvider(
        api_key="test-key",
        transport=lambda url, headers, payload: {
            "status": "completed",
            "output_text": "ok",
        },
    )

    assert isinstance(provider, Provider)
