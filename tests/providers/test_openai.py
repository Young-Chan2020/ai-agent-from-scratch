from typing import cast

from ai_agent.core.message import Message
from ai_agent.core.request import ChatRequest, ModelConfig
from ai_agent.providers.openai import OpenAIProvider


def test_openai_provider_builds_provider_specific_request() -> None:
    captured: dict[str, object] = {}

    def fake_transport(url: str, headers: dict[str, str], payload: dict[str, object]) -> dict[str, object]:
        captured["url"] = url
        captured["headers"] = headers
        captured["payload"] = payload
        return {
            "output_text": "hello",
            "status": "completed",
            "usage": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
        }

    provider = OpenAIProvider(api_key="test-key", transport=fake_transport)
    request = ChatRequest(
        messages=[Message(role="user", content="Hi")],
        config=ModelConfig(model="test-model", max_tokens=100),
    )

    response = provider.chat(request)
    payload = cast(dict[str, object], captured["payload"])

    assert payload["model"] == "test-model"
    assert payload["max_output_tokens"] == 100
    assert response.message.content == "hello"


def test_openai_provider_streams_output_text_deltas() -> None:
    events = [
        {"type": "response.output_text.delta", "delta": "hello"},
        {"type": "response.output_text.delta", "delta": " world"},
        {
            "type": "response.completed",
            "response": {
                "status": "completed",
                "usage": {"input_tokens": 3, "output_tokens": 2, "total_tokens": 5},
            },
        },
    ]

    provider = OpenAIProvider(
        api_key="test-key",
        stream_transport=lambda url, headers, payload: iter(events),
    )
    request = ChatRequest(
        messages=[Message(role="user", content="Hi")],
        config=ModelConfig(model="test-model"),
    )

    chunks = list(provider.stream(request))

    assert [chunk.content for chunk in chunks] == ["hello", " world", ""]
    assert chunks[-1].finish_reason == "completed"
    assert chunks[-1].usage is not None
    assert chunks[-1].usage.total_tokens == 5
