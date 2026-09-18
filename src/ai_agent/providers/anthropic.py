import os

from ai_agent.core.errors import InvalidRequestError
from ai_agent.core.message import Message
from ai_agent.core.request import ChatRequest
from ai_agent.core.response import ChatResponse, Usage
from ai_agent.providers.http import JsonResponse, HttpTransport, send_json


class AnthropicProvider:
    """Anthropic Messages API adapter for the common Provider interface."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        transport: HttpTransport | None = None,
        endpoint: str = "https://api.anthropic.com/v1/messages",
    ) -> None:
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is required")

        self.endpoint = endpoint
        self._transport: HttpTransport = transport or send_json

    def chat(self, request: ChatRequest) -> ChatResponse:
        system_messages, conversation = self._split_system_messages(request.messages)

        payload: dict[str, object] = {
            "model": request.config.model,
            "max_tokens": request.config.max_tokens or 1024,
            "messages": [
                {"role": message.role, "content": message.content}
                for message in conversation
            ],
        }

        if system_messages:
            payload["system"] = "\n\n".join(system_messages)

        # English: Provider configuration is not always portable across APIs.
        # 中文：不同 Provider 的參數規則不一定相同，因此共用設定不能直接全部原樣傳送。
        if request.config.temperature is not None:
            payload["temperature"] = request.config.temperature

        data = self._transport(
            self.endpoint,
            {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            payload,
        )
        return self._parse_response(data)

    @staticmethod
    def _split_system_messages(
        messages: list[Message],
    ) -> tuple[list[str], list[Message]]:
        system_messages = [
            message.content for message in messages if message.role == "system"
        ]
        conversation = [
            message for message in messages if message.role != "system"
        ]

        if not conversation:
            raise InvalidRequestError(
                "Anthropic requires at least one conversation message"
            )

        return system_messages, conversation

    @staticmethod
    def _parse_response(data: JsonResponse) -> ChatResponse:
        content = data.get("content")
        if not isinstance(content, list):
            raise InvalidRequestError("Anthropic response did not contain content")

        texts: list[str] = []
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text" and isinstance(block.get("text"), str):
                texts.append(block["text"])

        if not texts:
            raise InvalidRequestError("Anthropic response did not contain text content")

        usage = data.get("usage")
        parsed_usage = None
        if isinstance(usage, dict):
            input_tokens = usage.get("input_tokens")
            output_tokens = usage.get("output_tokens")
            if isinstance(input_tokens, int) and isinstance(output_tokens, int):
                parsed_usage = Usage(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=input_tokens + output_tokens,
                )

        return ChatResponse(
            message=Message(role="assistant", content="".join(texts)),
            finish_reason=str(data.get("stop_reason") or "stop"),
            usage=parsed_usage,
            raw=data,
        )
