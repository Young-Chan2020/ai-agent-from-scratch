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


class OpenAIProvider:
    """OpenAI Responses API adapter for the common Provider interface."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        transport: HttpTransport | None = None,
        stream_transport: StreamTransport | None = None,
        endpoint: str = "https://api.openai.com/v1/responses",
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required")

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

        # English: OpenAI accepts these common roles as input items.
        # 中文：OpenAI 可以接收這些共用 role，因此這裡只需要做格式轉換。
        payload: dict[str, object] = {
            "model": request.config.model,
            "input": [
                {"role": message.role, "content": message.content}
                for message in request.messages
            ],
        }

        if request.config.temperature is not None:
            payload["temperature"] = request.config.temperature
        if request.config.max_tokens is not None:
            payload["max_output_tokens"] = request.config.max_tokens

        if request.tools:
            # English: OpenAI's Responses API expects function tools as top-level tool definitions.
            # 中文：OpenAI Responses API 將 function tool definitions 放在 request 的 tools 欄位。
            payload["tools"] = [
                {
                    "type": "function",
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                    "strict": tool.strict,
                }
                for tool in request.tools
            ]

        if request.structured_output is not None:
            structured = request.structured_output
            # English: OpenAI supports JSON Schema directly, so the adapter can pass the schema natively.
            # 中文：OpenAI 原生支援 JSON Schema，因此 Adapter 可以直接把 schema 傳給 Provider。
            payload["text"] = {
                "format": {
                    "type": "json_schema",
                    "name": structured.name,
                    "schema": structured.schema,
                    "strict": structured.strict,
                }
            }

        return payload

    @staticmethod
    def _validate_messages(messages: list[Message]) -> None:
        if any(message.role == "tool" for message in messages):
            raise InvalidRequestError(
                "OpenAI Responses API tool messages require provider-specific mapping"
            )

    def _parse_response(self, data: JsonResponse) -> ChatResponse:
        output_text = data.get("output_text")
        if not isinstance(output_text, str):
            output_text = self._extract_output_text(data)

        usage = self._parse_usage(data.get("usage"))
        return ChatResponse(
            message=Message(role="assistant", content=output_text),
            finish_reason=str(data.get("status", "completed")),
            usage=usage,
            raw=data,
        )

    @staticmethod
    def _parse_stream_event(event: JsonResponse) -> ChatChunk | None:
        event_type = event.get("type")

        if event_type == "response.output_text.delta":
            delta = event.get("delta")
            if isinstance(delta, str):
                return ChatChunk(content=delta, raw=event)
            return None

        if event_type == "response.completed":
            response = event.get("response")
            if isinstance(response, dict):
                usage = OpenAIProvider._parse_usage(response.get("usage"))
                status = response.get("status")
                return ChatChunk(
                    finish_reason=str(status) if status is not None else "completed",
                    usage=usage,
                    raw=event,
                )
            return ChatChunk(finish_reason="completed", raw=event)

        return None

    @staticmethod
    def _extract_output_text(data: JsonResponse) -> str:
        output = data.get("output")
        if not isinstance(output, list):
            raise InvalidRequestError("OpenAI response did not contain output text")

        texts: list[str] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                text = block.get("text")
                if isinstance(text, str):
                    texts.append(text)

        if not texts:
            raise InvalidRequestError("OpenAI response did not contain output text")
        return "".join(texts)

    @staticmethod
    def _parse_usage(value: object) -> Usage | None:
        if not isinstance(value, dict):
            return None

        input_tokens = value.get("input_tokens")
        output_tokens = value.get("output_tokens")
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
