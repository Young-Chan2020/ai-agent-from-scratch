from dataclasses import dataclass

from .message import Message


@dataclass(frozen=True)
class Usage:
    """Token usage reported by an LLM provider."""

    input_tokens: int
    output_tokens: int
    total_tokens: int


@dataclass(frozen=True)
class ChatResponse:
    """A provider-independent response returned by an LLM."""

    message: Message
    finish_reason: str
    usage: Usage | None = None
    raw: object | None = None
