import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

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
