from typing import cast

from ai_agent.core.message import Message
from ai_agent.core.request import ChatRequest, ModelConfig
from ai_agent.providers.base import Provider
from ai_agent.providers.deepseek import DeepSeekProvider


def test_deepseek_provider_builds_provider_specific_request() -> None:
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
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {
                        "role": "assistant",
                        "content": "hello from deepseek",
                    },
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
        config=ModelConfig(model="deepseek-flash", temperature=0.2, max_tokens=100),
    )

    response = provider.chat(request)
    payload = cast(dict[str, object], captured["payload"])

    assert captured["url"] == "https://api.deepseek.com/chat/completions"
    assert captured["headers"] == {"Authorization": "Bearer test-key"}
    assert payload["model"] == "deepseek-flash"
    assert payload["temperature"] == 0.2
    assert payload["max_tokens"] == 100
    assert payload["messages"] == [
        {"role": "system", "content": "Be concise."},
        {"role": "user", "content": "Hello"},
    ]
    assert response.message.content == "hello from deepseek"
    assert response.usage is not None
    assert response.usage.total_tokens == 15


def test_deepseek_provider_matches_provider_protocol() -> None:
    provider: Provider = DeepSeekProvider(
        api_key="test-key",
        transport=lambda url, headers, payload: {
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {
                        "role": "assistant",
                        "content": "ok",
                    },
                }
            ]
        },
    )

    assert isinstance(provider, Provider)
