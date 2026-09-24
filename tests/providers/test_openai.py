from typing import cast

from ai_agent.core.message import Message
from ai_agent.core.request import ChatRequest, ModelConfig
from ai_agent.core.structured import StructuredOutputConfig
from ai_agent.core.tool import ToolDefinition
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


def test_openai_provider_maps_structured_output_to_json_schema() -> None:
    captured: dict[str, object] = {}

    def fake_transport(url: str, headers: dict[str, str], payload: dict[str, object]) -> dict[str, object]:
        captured["payload"] = payload
        return {
            "output_text": '{"name":"Alice","age":30}',
            "status": "completed",
        }

    provider = OpenAIProvider(api_key="test-key", transport=fake_transport)
    request = ChatRequest(
        messages=[Message(role="user", content="Describe Alice as JSON.")],
        config=ModelConfig(model="test-model"),
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
    text_config = cast(dict[str, object], payload["text"])
    format_config = cast(dict[str, object], text_config["format"])

    assert format_config["type"] == "json_schema"
    assert format_config["name"] == "person"


def test_openai_provider_maps_tool_definition() -> None:
    captured: dict[str, object] = {}

    def fake_transport(url: str, headers: dict[str, str], payload: dict[str, object]) -> dict[str, object]:
        captured["payload"] = payload
        return {"output_text": "hello", "status": "completed"}

    provider = OpenAIProvider(api_key="test-key", transport=fake_transport)
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
            "name": "get_weather",
            "description": "Get the weather for a city.",
            "parameters": tool.parameters,
            "strict": False,
        }
    ]

def test_openai_provider_parses_tool_call() -> None:
    from ai_agent.core.response import ToolCall

    provider = OpenAIProvider(
        api_key="test-key",
        transport=lambda url, headers, payload: {
            "output": [
                {
                    "type": "function_call",
                    "call_id": "call-1",
                    "name": "get_weather",
                    "arguments": '{"city":"Los Angeles"}',
                }
            ],
            "status": "completed",
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
