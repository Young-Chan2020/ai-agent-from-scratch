import json
import os
from collections.abc import Iterator

from ai_agent.core.errors import InvalidRequestError
from ai_agent.core.message import Message
from ai_agent.core.request import ChatRequest
from ai_agent.core.response import ChatChunk, ChatResponse, ToolCall, Usage
from ai_agent.providers.http import (
    HttpTransport,
    JsonResponse,
    StreamTransport,
    send_json,
    send_sse_json,
)


class AnthropicProvider:
    """Anthropic Messages API adapter for the common Provider interface."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        transport: HttpTransport | None = None,
        stream_transport: StreamTransport | None = None,
        endpoint: str = "https://api.anthropic.com/v1/messages",
    ) -> None:
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is required")

        self.endpoint = endpoint
        self._transport: HttpTransport = transport or send_json
        self._stream_transport: StreamTransport = stream_transport or send_sse_json

    def chat(self, request: ChatRequest) -> ChatResponse:
        system_messages, conversation = self._split_system_messages(request.messages)
        payload = self._build_payload(request, system_messages, conversation)

        data = self._transport(
            self.endpoint,
            {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            payload,
        )
        return self._parse_response(data)

    def stream(self, request: ChatRequest) -> Iterator[ChatChunk]:
        system_messages, conversation = self._split_system_messages(request.messages)
        payload = self._build_payload(request, system_messages, conversation)
        payload["stream"] = True

        for event in self._stream_transport(
            self.endpoint,
            {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            payload,
        ):
            chunk = self._parse_stream_event(event)
            if chunk is not None:
                yield chunk

    def _build_payload(
        self,
        request: ChatRequest,
        system_messages: list[str],
        conversation: list[Message],
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "model": request.config.model,
            "max_tokens": request.config.max_tokens or 1024,
            "messages": [
                {"role": message.role, "content": message.content}
                for message in conversation
            ],
        }

        if request.tools:
            # English: Anthropic calls the tool input schema input_schema rather than parameters.
            # 中文：Anthropic 使用 input_schema 表示 Tool 的 arguments schema，而不是 parameters。
            payload["tools"] = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.parameters,
                }
                for tool in request.tools
            ]

        if request.structured_output is not None:
            # English: Anthropic receives the schema as an instruction, while our common layer validates the result.
            # 中文：Anthropic 在這裡透過 instruction 傳遞 schema，而 common layer 負責最終 validation。
            schema_text = json.dumps(request.structured_output.schema)
            system_messages = [
                *system_messages,
                (
                    "Return only valid JSON matching this schema: "
                    f"{schema_text}"
                ),
            ]

        if system_messages:
            payload["system"] = "\n\n".join(system_messages)

        # English: Anthropic has provider-specific restrictions on temperature in this phase.
        # 中文：Anthropic 對新版模型的 temperature 有 Provider-specific 限制，因此這裡明確拒絕不相容設定。
        if request.config.temperature is not None:
            raise InvalidRequestError(
                "AnthropicProvider does not map temperature in this phase"
            )

        return payload

    @staticmethod
    def _split_system_messages(
        messages: list[Message],
    ) -> tuple[list[str], list[Message]]:
        system_messages = [
            message.content for message in messages if message.role == "system"
        ]
        conversation = [
            message for message in messages if message.role not in {"system", "tool"}
        ]

        if any(message.role == "tool" for message in messages):
            raise InvalidRequestError(
                "Anthropic tool messages require provider-specific mapping"
            )

        if not conversation:
            raise InvalidRequestError(
                "Anthropic requires at least one conversation message"
            )

        return system_messages, conversation

    @staticmethod
    def _parse_stream_event(event: JsonResponse) -> ChatChunk | None:
        event_type = event.get("type")

        if event_type == "content_block_delta":
            delta = event.get("delta")
            if isinstance(delta, dict) and delta.get("type") == "text_delta":
                text = delta.get("text")
                if isinstance(text, str):
                    return ChatChunk(content=text, raw=event)
            return None

        if event_type == "message_delta":
            delta = event.get("delta")
            usage = event.get("usage")
            stop_reason = None
            if isinstance(delta, dict):
                stop_reason = delta.get("stop_reason")
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
            return ChatChunk(
                content="",
                finish_reason=str(stop_reason) if stop_reason else None,
                usage=parsed_usage,
                raw=event,
            )

        return None

    @staticmethod
    def _parse_response(data: JsonResponse) -> ChatResponse:
        content = data.get("content")
        if not isinstance(content, list):
            raise InvalidRequestError("Anthropic response did not contain content")

        texts: list[str] = []
        tool_calls: list[ToolCall] = []
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text" and isinstance(block.get("text"), str):
                texts.append(block["text"])
            if block.get("type") == "tool_use":
                call_id = block.get("id")
                name = block.get("name")
                input_value = block.get("input")
                if not isinstance(call_id, str) or not isinstance(name, str):
                    raise InvalidRequestError("Anthropic response contained an invalid tool call")
                if not isinstance(input_value, dict):
                    raise InvalidRequestError("Anthropic tool input must be an object")
                tool_calls.append(ToolCall(id=call_id, name=name, arguments=input_value))

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
            tool_calls=tool_calls or None,
            raw=data,
        )
