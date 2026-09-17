from dataclasses import dataclass
from typing import Literal


Role = Literal["system", "user", "assistant", "tool"]


@dataclass(frozen=True)
class Message:
    """A provider-independent message exchanged with an LLM."""

    role: Role
    content: str
    name: str | None = None
    tool_call_id: str | None = None
