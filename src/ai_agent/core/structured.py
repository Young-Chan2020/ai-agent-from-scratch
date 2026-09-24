import json
from dataclasses import dataclass
from typing import Any

from .errors import InvalidRequestError
from .response import ChatResponse


@dataclass(frozen=True)
class StructuredOutputConfig:
    """Configuration for JSON-schema-constrained model output."""

    name: str
    schema: dict[str, object]
    strict: bool = True

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("structured output name must not be empty")
        if self.schema.get("type") != "object":
            raise ValueError("structured output schema must have type='object'")


class StructuredOutputError(InvalidRequestError):
    """Raised when model output is not valid JSON or does not match its schema."""


def parse_structured_output(
    response: ChatResponse,
    schema: dict[str, object],
) -> dict[str, object]:
    """Parse and validate a JSON object returned by the model."""
    try:
        value = json.loads(response.message.content)
    except json.JSONDecodeError as exc:
        raise StructuredOutputError("model output was not valid JSON") from exc

    if not isinstance(value, dict):
        raise StructuredOutputError("structured output must be a JSON object")

    validate_json_schema(value, schema, error_cls=StructuredOutputError)
    return value


def validate_json_schema(
    value: Any,
    schema: dict[str, object],
    *,
    error_cls: type[Exception] = StructuredOutputError,
) -> None:
    """Validate a small JSON Schema subset shared by structured output and Tools."""
    _validate_value(value, schema, "$", error_cls)


def _validate_value(
    value: Any,
    schema: dict[str, object],
    path: str,
    error_cls: type[Exception],
) -> None:
    expected_type = schema.get("type")

    if expected_type == "object":
        if not isinstance(value, dict):
            raise error_cls(f"{path} must be an object")

        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            raise error_cls(f"{path}.properties must be an object")

        required = schema.get("required", [])
        if not isinstance(required, list):
            raise error_cls(f"{path}.required must be an array")

        for name in required:
            if isinstance(name, str) and name not in value:
                raise error_cls(f"{path}.{name} is required")

        for name, child_schema in properties.items():
            if name in value and isinstance(child_schema, dict):
                _validate_value(value[name], child_schema, f"{path}.{name}", error_cls)
        return

    if expected_type == "array":
        if not isinstance(value, list):
            raise error_cls(f"{path} must be an array")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                _validate_value(item, item_schema, f"{path}[{index}]", error_cls)
        return

    type_checks = {
        "string": lambda item: isinstance(item, str),
        "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
        "number": lambda item: isinstance(item, (int, float)) and not isinstance(item, bool),
        "boolean": lambda item: isinstance(item, bool),
        "null": lambda item: item is None,
    }

    check = type_checks.get(expected_type)
    if check is None:
        raise error_cls(f"{path} uses unsupported schema type: {expected_type!r}")

    if not check(value):
        raise error_cls(f"{path} must be {expected_type}")
