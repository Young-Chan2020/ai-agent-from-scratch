import os
from collections.abc import Iterator

from ai_agent.core.errors import InvalidRequestError
from ai_agent.core.message import Message
from ai_agent.core.request import ChatRequest
from ai_agent.core.response import ChatChunk, ChatResponse, Usage
from ai_agent.providers.http import (
    HttpTransport,
    JsonResponse,
    StreamTransport,
    send_json,
    send_sse_json,
)


class DeepSeekProvider:
    """DeepSeek Chat Completions API adapter for the common Provider interface."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        transport: HttpTransport | None = None,
        stream_transport: StreamTransport | None = None,
        endpoint: str = "https://api.deepseek.com/chat/completions",
    ) -> None:
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY is required")

        self.endpoint = endpoint
        self._transport: HttpTransport = transport or send_json
        self._stream_transport: StreamTransport = stream_transport or send_sse_json

    def chat(self, request: ChatRequest) -> ChatResponse:
        payload = self._build_payload(request)
        data = self._transport(
            self.endpoint,
            {"Authorization": f"Bearer {self.api_key}"},
            payload,
        )
        return self._parse_response(data)

    def stream(self, request: ChatRequest) -> Iterator[ChatChunk]:
        payload = self._build_payload(request)
        payload["stream"] = True
        payload["stream_options"] = {"include_usage": True}

        for event in self._stream_transport(
            self.endpoint,
            {"Authorization": f"Bearer {self.api_key}"},
            payload,
        ):
            chunk = self._parse_stream_event(event)
            if chunk is not None:
                yield chunk

    def _build_payload(self, request: ChatRequest) -> dict[str, object]:
        self._validate_messages(request.messages)

        # English: DeepSeek's Chat Completions API closely matches the common chat-message shape.
        # 中文：DeepSeek 的 Chat Completions API 與我們的 common message 結構很接近，因此主要工作是格式轉換。
        payload: dict[str, object] = {
            "model": request.config.model,
            "messages": [
                {"role": message.role, "content": message.content}
                for message in request.messages
            ],
        }

        if request.config.temperature is not None:
            payload["temperature"] = request.config.temperature
        if request.config.max_tokens is not None:
            payload["max_tokens"] = request.config.max_tokens

        if request.tools:
            # English: DeepSeek's Chat Completions API uses the common function-tool shape.
            # 中文：DeepSeek Chat Completions API 使用標準的 function tool 結構。
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                        "strict": tool.strict,
                    },
                }
                for tool in request.tools
            ]

        if request.structured_output is not None:
            # English: DeepSeek's JSON mode guarantees valid JSON, while schema validation remains our responsibility.
            # 中文：DeepSeek 的 JSON mode 保證輸出是合法 JSON，但 schema validation 仍由我們自己的 common layer 負責。
            payload["response_format"] = {"type": "json_object"}

        return payload

    @staticmethod
    def _validate_messages(messages: list[Message]) -> None:
        if any(message.role == "tool" for message in messages):
            raise InvalidRequestError(
                "DeepSeek tool messages require provider-specific mapping"
            )

    @staticmethod
    def _parse_stream_event(event: JsonResponse) -> ChatChunk | None:
        choices = event.get("choices")
        if not isinstance(choices, list) or not choices:
            usage = DeepSeekProvider._parse_usage(event.get("usage"))
            if usage is not None:
                return ChatChunk(usage=usage, raw=event)
            return None

        choice = choices[0]
        if not isinstance(choice, dict):
            return None

        delta = choice.get("delta")
        content = ""
        if isinstance(delta, dict) and isinstance(delta.get("content"), str):
            content = delta["content"]

        finish_reason = choice.get("finish_reason")
        usage = DeepSeekProvider._parse_usage(event.get("usage"))

        if content or finish_reason is not None or usage is not None:
            return ChatChunk(
                content=content,
                finish_reason=str(finish_reason) if finish_reason else None,
                usage=usage,
                raw=event,
            )
        return None

    @staticmethod
    def _parse_response(data: JsonResponse) -> ChatResponse:
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise InvalidRequestError("DeepSeek response did not contain choices")

        choice = choices[0]
        if not isinstance(choice, dict):
            raise InvalidRequestError("DeepSeek response contained an invalid choice")

        message = choice.get("message")
        if not isinstance(message, dict):
            raise InvalidRequestError("DeepSeek response did not contain a message")

        content = message.get("content")
        if not isinstance(content, str):
            raise InvalidRequestError("DeepSeek response did not contain text content")

        usage = DeepSeekProvider._parse_usage(data.get("usage"))
        return ChatResponse(
            message=Message(role="assistant", content=content),
            finish_reason=str(choice.get("finish_reason") or "stop"),
            usage=usage,
            raw=data,
        )

    @staticmethod
    def _parse_usage(value: object) -> Usage | None:
        if not isinstance(value, dict):
            return None

        input_tokens = value.get("prompt_tokens")
        output_tokens = value.get("completion_tokens")
        total_tokens = value.get("total_tokens")

        if not all(
            isinstance(item, int)
            for item in (input_tokens, output_tokens, total_tokens)
        ):
            return None

        return Usage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
        )
