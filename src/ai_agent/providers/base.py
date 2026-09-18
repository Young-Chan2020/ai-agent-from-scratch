from collections.abc import Iterator
from typing import Protocol, runtime_checkable

from ai_agent.core.request import ChatRequest
from ai_agent.core.response import ChatChunk, ChatResponse


@runtime_checkable
class Provider(Protocol):
    """Common interface that every LLM provider must implement."""

    def chat(self, request: ChatRequest) -> ChatResponse:
        """Generate one complete response for a chat request."""
        ...

    def stream(self, request: ChatRequest) -> Iterator[ChatChunk]:
        """Generate a response incrementally as streaming chunks."""
        ...
