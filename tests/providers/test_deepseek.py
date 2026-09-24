from typing import cast

from ai_agent.core.message import Message
from ai_agent.core.request import ChatRequest, ModelConfig
from ai_agent.core.structured import StructuredOutputConfig
from ai_agent.core.tool import ToolDefinition
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


def test_deepseek_provider_enables_json_output() -> None:
    captured: dict[str, object] = {}

    def fake_transport(url: str, headers: dict[str, str], payload: dict[str, object]) -> dict[str, object]:
        captured["payload"] = payload
        return {
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": '{"name":"Alice"}'},
                }
            ]
        }

    provider = DeepSeekProvider(api_key="test-key", transport=fake_transport)
    request = ChatRequest(
        messages=[Message(role="user", content="Return JSON.")],
        config=ModelConfig(model="deepseek-chat"),
        structured_output=StructuredOutputConfig(
            name="person",
            schema={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        ),
    )

    provider.chat(request)
    payload = cast(dict[str, object], captured["payload"])

    assert payload["response_format"] == {"type": "json_object"}


def test_deepseek_provider_maps_tool_definition() -> None:
    captured: dict[str, object] = {}

    def fake_transport(url: str, headers: dict[str, str], payload: dict[str, object]) -> dict[str, object]:
        captured["payload"] = payload
        return {
            "choices": [
                {
                    "message": {"role": "assistant", "content": "hello"},
                    "finish_reason": "stop",
                }
            ]
        }

    provider = DeepSeekProvider(api_key="test-key", transport=fake_transport)
    tool = ToolDefinition(
        name="get_weather",
        description="Get the weather for a city.",
        parameters={
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    )
    request = ChatRequest(
        messages=[Message(role="user", content="Weather in LA?")],
        config=ModelConfig(model="test-model"),
        tools=[tool],
    )

    provider.chat(request)
    payload = cast(dict[str, object], captured["payload"])
    tools = cast(list[dict[str, object]], payload["tools"])

    assert tools == [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the weather for a city.",
                "parameters": tool.parameters,
                "strict": False,
            },
        }
    ]

def test_deepseek_provider_parses_tool_call() -> None:
    from ai_agent.core.response import ToolCall

    provider = DeepSeekProvider(
        api_key="test-key",
        transport=lambda url, headers, payload: {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call-1",
                                "type": "function",
                                "function": {
                                    "name": "get_weather",
                                    "arguments": '{"city":"Los Angeles"}',
                                },
                            }
                        ],
                    },
                    "finish_reason": "tool_calls",
                }
            ]
        },
    )
    response = provider.chat(
        ChatRequest(
            messages=[Message(role="user", content="weather?")],
            config=ModelConfig(model="test"),
        )
    )

    assert response.tool_calls == [
        ToolCall(id="call-1", name="get_weather", arguments={"city": "Los Angeles"})
    ]
