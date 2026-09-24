import pytest

from ai_agent.core.tool import Tool, ToolDefinition


PARAMETERS = {
    "type": "object",
    "properties": {
        "city": {"type": "string"},
    },
    "required": ["city"],
}


def test_tool_definition_describes_name_description_and_parameters() -> None:
    definition = ToolDefinition(
        name="get_weather",
        description="Get the weather for a city.",
        parameters=PARAMETERS,
    )

    assert definition.name == "get_weather"
    assert definition.description == "Get the weather for a city."
    assert definition.parameters == PARAMETERS


def test_tool_definition_rejects_invalid_name() -> None:
    with pytest.raises(ValueError, match="tool name"):
        ToolDefinition(
            name="get weather!",
            description="Get weather.",
            parameters=PARAMETERS,
        )


def test_tool_definition_requires_object_parameters() -> None:
    with pytest.raises(ValueError, match="type='object'"):
        ToolDefinition(
            name="get_weather",
            description="Get weather.",
            parameters={"type": "string"},
        )


def test_tool_pairs_definition_with_execution_behavior() -> None:
    def get_weather(city: str) -> str:
        return f"Weather in {city}"

    tool = Tool(
        definition=ToolDefinition(
            name="get_weather",
            description="Get the weather for a city.",
            parameters=PARAMETERS,
        ),
        handler=get_weather,
    )

    assert tool.name == "get_weather"
    assert tool.handler("Los Angeles") == "Weather in Los Angeles"
