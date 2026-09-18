from typing import cast

from ai_agent.core.message import Message
from ai_agent.core.request import ChatRequest, ModelConfig
from ai_agent.providers.deepseek import DeepSeekProvider


def test_deepseek_provider_builds_provider_specific_request() -> None:
    captured: dict[str, object] = {}

    def fake_transport(url: str, headers: dict[str, str], payload: dict[str, object]) -> dict[str, object]:
        captured["url"] = url
        captured["headers"] = headers
        captured["payload"] = payload
        return {
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": "hello from deepseek"},
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
            },
        }

    provider = DeepSeekProvider(api_key="test-key", transport=fake_transport)
    request = ChatRequest(
        messages=[
            Message(role="system", content="Be concise."),
            Message(role="user", content="Hello"),
        ],
        config=ModelConfig(model="deepseek-chat", temperature=0.2, max_tokens=100),
    )

    response = provider.chat(request)
    payload = cast(dict[str, object], captured["payload"])

    assert response.message.content == "hello from deepseek"
    assert payload["temperature"] == 0.2


def test_deepseek_provider_streams_chat_completion_deltas() -> None:
    events = [
        {"choices": [{"delta": {"content": "hello"}, "finish_reason": None}]},
        {"choices": [{"delta": {"content": " world"}, "finish_reason": None}]},
        {
            "choices": [{"delta": {}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
        },
    ]

    provider = DeepSeekProvider(
        api_key="test-key",
        stream_transport=lambda url, headers, payload: iter(events),
    )
    request = ChatRequest(
        messages=[Message(role="user", content="Hi")],
        config=ModelConfig(model="deepseek-chat"),
    )

    chunks = list(provider.stream(request))

    assert [chunk.content for chunk in chunks] == ["hello", " world", ""]
    assert chunks[-1].finish_reason == "stop"
    assert chunks[-1].usage is not None
    assert chunks[-1].usage.total_tokens == 5
