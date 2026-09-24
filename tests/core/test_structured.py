import pytest

from ai_agent.core.errors import InvalidRequestError
from ai_agent.core.message import Message
from ai_agent.core.request import ChatRequest, ModelConfig
from ai_agent.core.response import ChatResponse
from ai_agent.core.structured import (
    StructuredOutputConfig,
    StructuredOutputError,
    parse_structured_output,
)


SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
    },
    "required": ["name", "age"],
}


def make_response(content: str) -> ChatResponse:
    return ChatResponse(
        message=Message(role="assistant", content=content),
        finish_reason="stop",
    )


def test_structured_output_config_requires_object_schema() -> None:
    with pytest.raises(ValueError, match="type='object'"):
        StructuredOutputConfig(
            name="person",
            schema={"type": "string"},
        )


def test_parse_structured_output_returns_valid_json_object() -> None:
    response = make_response('{"name": "Alice", "age": 30}')

    result = parse_structured_output(response, SCHEMA)

    assert result == {"name": "Alice", "age": 30}


def test_parse_structured_output_rejects_invalid_json() -> None:
    response = make_response("not json")

    with pytest.raises(StructuredOutputError, match="valid JSON"):
        parse_structured_output(response, SCHEMA)


def test_parse_structured_output_rejects_missing_required_field() -> None:
    response = make_response('{"name": "Alice"}')

    with pytest.raises(StructuredOutputError, match="age is required"):
        parse_structured_output(response, SCHEMA)


def test_parse_structured_output_rejects_wrong_type() -> None:
    response = make_response('{"name": "Alice", "age": "thirty"}')

    with pytest.raises(StructuredOutputError, match="age must be integer"):
        parse_structured_output(response, SCHEMA)


def test_chat_request_can_carry_structured_output_config() -> None:
    config = StructuredOutputConfig(name="person", schema=SCHEMA)
    request = ChatRequest(
        messages=[Message(role="user", content="Describe Alice.")],
        config=ModelConfig(model="test-model"),
        structured_output=config,
    )

    assert request.structured_output == config
