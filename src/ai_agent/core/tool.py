import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .errors import ToolExecutionError
from .structured import validate_json_schema

ToolHandler = Callable[..., Any]
_TOOL_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,128}$")


@dataclass(frozen=True)
class ToolDefinition:
    """Provider-independent description of a tool exposed to an LLM."""

    name: str
    description: str
    parameters: dict[str, object]
    strict: bool = False

    def __post_init__(self) -> None:
        # English: Tool names become part of provider requests, so validate them before adapters see them.
        # 中文：Tool name 最後會進入 Provider request，因此先在 common layer 驗證，避免各 Provider 各自處理。
        if not _TOOL_NAME_PATTERN.fullmatch(self.name):
            raise ValueError(
                "tool name must be 1-128 characters using letters, numbers, '_' or '-'"
            )

        # English: Tool arguments need a predictable object shape so the Agent can validate them later.
        # 中文：Tool arguments 需要可預期的 object 結構，之後 Agent 才能對 arguments 做一致的驗證。
        if self.parameters.get("type") != "object":
            raise ValueError("tool parameters schema must have type='object'")


@dataclass(frozen=True)
class Tool:
    """A runtime tool that pairs an LLM-facing definition with executable behavior."""

    definition: ToolDefinition
    handler: ToolHandler

    @property
    def name(self) -> str:
        """Return the stable name used to identify this tool."""
        return self.definition.name


class ToolExecutor:
    """Find, validate, and execute registered tools."""

    def __init__(self, tools: list[Tool]) -> None:
        names = [tool.name for tool in tools]
        if len(names) != len(set(names)):
            raise ValueError("tool names must be unique")
        self._tools = {tool.name: tool for tool in tools}

    def execute(self, tool_call: Any) -> Any:
        """Execute one normalized ToolCall and return a ToolResult."""
        from .response import ToolCall, ToolResult

        if not isinstance(tool_call, ToolCall):
            raise TypeError("tool_call must be a ToolCall")

        tool = self._tools.get(tool_call.name)
        if tool is None:
            return ToolResult(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                content=f"unknown tool: {tool_call.name}",
                is_error=True,
            )

        try:
            # English: Validate model-generated arguments before application code runs.
            # 中文：先驗證 LLM 產生的 arguments，再讓 application code 真正執行 Tool。
            validate_json_schema(tool_call.arguments, tool.definition.parameters)
            result = tool.handler(**tool_call.arguments)
            return ToolResult(
                tool_call_id=tool_call.id,
                name=tool.name,
                content=_serialize_result(result),
            )
        except Exception as exc:
            # English: Convert handler failures into ToolResult so the Agent can decide how to continue.
            # 中文：把 handler 執行失敗轉成 ToolResult，讓 Agent 決定後續如何處理，而不是直接讓 runtime 崩潰。
            return ToolResult(
                tool_call_id=tool_call.id,
                name=tool.name,
                content=str(exc),
                is_error=True,
            )


def _serialize_result(value: Any) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False)
    except TypeError:
        return str(value)
