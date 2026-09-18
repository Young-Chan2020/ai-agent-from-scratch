from typing import cast

from ai_agent.core.message import Message
from ai_agent.core.request import ChatRequest, ModelConfig
from ai_agent.providers.anthropic import AnthropicProvider
from ai_agent.providers.base import Provider


def test_anthropic_provider_separates_system_prompt() -> None:
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
            "stop_reason": "end_turn",
            "content": [{"type": "text", "text": "hello from anthropic"}],
            "usage": {
                "input_tokens": 12,
                "output_tokens": 6,
            },
        }

    provider = AnthropicProvider(api_key="test-key", transport=fake_transport)
    request = ChatRequest(
        messages=[
            Message(role="system", content="Be concise."),
            Message(role="user", content="Hello"),
        ],
        config=ModelConfig(model="test-model", max_tokens=100),
    )

    response = provider.chat(request)
    payload = cast(dict[str, object], captured["payload"])

    assert captured["url"] == "https://api.anthropic.com/v1/messages"
    assert captured["headers"]["x-api-key"] == "test-key"
    assert payload["system"] == "Be concise."
    assert payload["messages"] == [{"role": "user", "content": "Hello"}]
    assert response.message.content == "hello from anthropic"
    assert response.usage is not None
    assert response.usage.total_tokens == 18


def test_anthropic_provider_matches_provider_protocol() -> None:
    provider: Provider = AnthropicProvider(
        api_key="test-key",
        transport=lambda url, headers, payload: {
            "stop_reason": "end_turn",
            "content": [{"type": "text", "text": "ok"}],
        },
    )

    assert isinstance(provider, Provider)
