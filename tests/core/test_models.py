import pytest

from ai_agent.core.message import Message
from ai_agent.core.request import ChatRequest, ModelConfig
from ai_agent.core.response import ChatChunk, Usage
from ai_agent.core.tool import ToolDefinition


def test_message_keeps_provider_independent_fields() -> None:
    message = Message(role="user", content="Hello")

    assert message.role == "user"
    assert message.content == "Hello"
    assert message.name is None


def test_chat_request_requires_a_message() -> None:
    with pytest.raises(ValueError, match="at least one message"):
        ChatRequest(messages=[], config=ModelConfig(model="mock-model"))


def test_chat_request_rejects_invalid_model_config() -> None:
    with pytest.raises(ValueError, match="temperature"):
        ChatRequest(
            messages=[Message(role="user", content="Hello")],
            config=ModelConfig(model="mock-model", temperature=-1),
        )

    with pytest.raises(ValueError, match="max_tokens"):
        ChatRequest(
            messages=[Message(role="user", content="Hello")],
            config=ModelConfig(model="mock-model", max_tokens=0),
        )


def test_usage_tracks_token_counts() -> None:
    usage = Usage(input_tokens=10, output_tokens=5, total_tokens=15)

    assert usage.total_tokens == 15


def test_chat_chunk_represents_partial_output() -> None:
    chunk = ChatChunk(content="Hello")

    assert chunk.content == "Hello"
    assert chunk.finish_reason is None
    assert chunk.usage is None


def test_chat_chunk_can_carry_completion_metadata() -> None:
    chunk = ChatChunk(
        finish_reason="stop",
        usage=Usage(input_tokens=10, output_tokens=5, total_tokens=15),
    )

    assert chunk.content == ""
    assert chunk.finish_reason == "stop"
    assert chunk.usage is not None
    assert chunk.usage.total_tokens == 15


def test_chat_request_accepts_tool_definitions() -> None:
    tool = ToolDefinition(
        name="calculator",
        description="Calculate an arithmetic expression.",
        parameters={
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"],
        },
    )
    request = ChatRequest(
        messages=[Message(role="user", content="Calculate 2 + 2.")],
        config=ModelConfig(model="test-model"),
        tools=[tool],
    )

    assert request.tools == [tool]


def test_chat_request_rejects_duplicate_tool_names() -> None:
    tool = ToolDefinition(
        name="calculator",
        description="Calculate an arithmetic expression.",
        parameters={"type": "object"},
    )

    with pytest.raises(ValueError, match="tool names must be unique"):
        ChatRequest(
            messages=[Message(role="user", content="Calculate 2 + 2.")],
            config=ModelConfig(model="test-model"),
            tools=[tool, tool],
        )
