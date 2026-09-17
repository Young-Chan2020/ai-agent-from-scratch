from typing import Protocol, runtime_checkable

from ai_agent.core.request import ChatRequest
from ai_agent.core.response import ChatResponse


@runtime_checkable
class Provider(Protocol):
    """Common interface that every LLM provider must implement."""

    def chat(self, request: ChatRequest) -> ChatResponse:
        """Generate one response for a chat request."""
        ...
