from ai_agent.core.message import Message
from ai_agent.core.request import ChatRequest, ModelConfig
from ai_agent.core.structured import StructuredOutputConfig
from ai_agent.providers.anthropic import AnthropicProvider


def test_anthropic_provider_separates_system_prompt() -> None:
    captured: dict[str, object] = {}

    def fake_transport(url: str, headers: dict[str, str], payload: dict[str, object]) -> dict[str, object]:
        captured["payload"] = payload
        return {
            "content": [{"type": "text", "text": "hello"}],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 4, "output_tokens": 2},
        }

    provider = AnthropicProvider(api_key="test-key", transport=fake_transport)
    request = ChatRequest(
        messages=[
            Message(role="system", content="Be concise."),
            Message(role="user", content="Hi"),
        ],
        config=ModelConfig(model="test-model"),
    )

    response = provider.chat(request)
    payload = captured["payload"]

    assert payload["system"] == "Be concise."
    assert payload["messages"] == [{"role": "user", "content": "Hi"}]
    assert response.message.content == "hello"


def test_anthropic_provider_rejects_unmapped_temperature() -> None:
    provider = AnthropicProvider(
        api_key="test-key",
        transport=lambda url, headers, payload: {},
    )
    request = ChatRequest(
        messages=[Message(role="user", content="Hi")],
        config=ModelConfig(model="test-model", temperature=0.2),
    )

    try:
        provider.chat(request)
    except Exception as exc:
        assert "temperature" in str(exc)
    else:
        raise AssertionError("expected temperature validation error")


def test_anthropic_provider_streams_text_deltas() -> None:
    events = [
        {
            "type": "content_block_delta",
            "delta": {"type": "text_delta", "text": "hello"},
        },
        {
            "type": "content_block_delta",
            "delta": {"type": "text_delta", "text": " world"},
        },
        {
            "type": "message_delta",
            "delta": {"stop_reason": "end_turn"},
            "usage": {"input_tokens": 4, "output_tokens": 2},
        },
    ]

    provider = AnthropicProvider(
        api_key="test-key",
        stream_transport=lambda url, headers, payload: iter(events),
    )
    request = ChatRequest(
        messages=[Message(role="user", content="Hi")],
        config=ModelConfig(model="test-model"),
    )

    chunks = list(provider.stream(request))

    assert [chunk.content for chunk in chunks] == ["hello", " world", ""]
    assert chunks[-1].finish_reason == "end_turn"
    assert chunks[-1].usage is not None
    assert chunks[-1].usage.total_tokens == 6


def test_anthropic_provider_instructs_structured_json_output() -> None:
    captured: dict[str, object] = {}

    def fake_transport(url: str, headers: dict[str, str], payload: dict[str, object]) -> dict[str, object]:
        captured["payload"] = payload
        return {
            "content": [{"type": "text", "text": '{"name":"Alice"}'}],
            "stop_reason": "end_turn",
        }

    provider = AnthropicProvider(api_key="test-key", transport=fake_transport)
    request = ChatRequest(
        messages=[Message(role="user", content="Return JSON.")],
        config=ModelConfig(model="test-model"),
        structured_output=StructuredOutputConfig(
            name="person",
            schema={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        ),
    )

    provider.chat(request)
    payload = captured["payload"]

    assert "Return only valid JSON" in payload["system"]
    assert '"name"' in payload["system"]
