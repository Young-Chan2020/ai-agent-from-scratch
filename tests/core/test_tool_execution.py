import pytest

from ai_agent.core.response import ToolCall
from ai_agent.core.tool import Tool, ToolDefinition, ToolExecutor


def make_weather_tool() -> Tool:
    return Tool(
        definition=ToolDefinition(
            name="get_weather",
            description="Get weather.",
            parameters={
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        ),
        handler=lambda city: f"Weather in {city}",
    )


def test_tool_executor_runs_registered_tool() -> None:
    result = ToolExecutor([make_weather_tool()]).execute(
        ToolCall(id="call-1", name="get_weather", arguments={"city": "Los Angeles"})
    )

    assert result.content == "Weather in Los Angeles"
    assert result.tool_call_id == "call-1"
    assert result.is_error is False


def test_tool_executor_rejects_invalid_arguments() -> None:
    result = ToolExecutor([make_weather_tool()]).execute(
        ToolCall(id="call-1", name="get_weather", arguments={"city": 123})
    )

    assert result.is_error is True
    assert "must be string" in result.content


def test_tool_executor_handles_unknown_tool() -> None:
    result = ToolExecutor([make_weather_tool()]).execute(
        ToolCall(id="call-2", name="search_web", arguments={"query": "AI"})
    )

    assert result.is_error is True
    assert result.name == "search_web"


def test_tool_executor_converts_handler_errors_to_tool_results() -> None:
    tool = Tool(
        definition=ToolDefinition(
            name="failing_tool",
            description="Always fails.",
            parameters={"type": "object"},
        ),
        handler=lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    result = ToolExecutor([tool]).execute(
        ToolCall(id="call-3", name="failing_tool", arguments={})
    )

    assert result.is_error is True
    assert result.content == "boom"


def test_tool_executor_serializes_non_string_results() -> None:
    tool = Tool(
        definition=ToolDefinition(
            name="get_user",
            description="Get a user.",
            parameters={"type": "object"},
        ),
        handler=lambda: {"name": "Alice", "age": 30},
    )

    result = ToolExecutor([tool]).execute(
        ToolCall(id="call-4", name="get_user", arguments={})
    )

    assert result.content == '{"name": "Alice", "age": 30}'


def test_tool_executor_rejects_duplicate_tools() -> None:
    with pytest.raises(ValueError, match="tool names must be unique"):
        ToolExecutor([make_weather_tool(), make_weather_tool()])
