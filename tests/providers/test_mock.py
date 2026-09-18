from typing import cast

from ai_agent.core.message import Message
from ai_agent.core.request import ChatRequest, ModelConfig
from ai_agent.providers.base import Provider
from ai_agent.providers.mock import MockProvider


def test_mock_provider_returns_deterministic_response() -> None:
    provider = MockProvider("hello")
    request = ChatRequest(
        messages=[Message(role="user", content="Hi")],
        config=ModelConfig(model="test-model"),
    )

    response = provider.chat(request)

    assert response.message.content == "hello"
    assert response.finish_reason == "stop"


def test_mock_provider_records_requests() -> None:
    provider = MockProvider()
    request = ChatRequest(
        messages=[Message(role="user", content="Hi")],
        config=ModelConfig(model="test-model"),
    )

    provider.chat(request)

    assert provider.calls == [request]


def test_mock_provider_matches_provider_protocol() -> None:
    provider: Provider = MockProvider()

    assert isinstance(provider, Provider)


def test_mock_provider_streams_incremental_chunks() -> None:
    provider = MockProvider("hello world")
    request = ChatRequest(
        messages=[Message(role="user", content="Hi")],
        config=ModelConfig(model="test-model"),
    )

    chunks = list(provider.stream(request))

    assert [chunk.content for chunk in chunks] == ["hello", " world", ""]
    assert chunks[-1].finish_reason == "stop"
    assert provider.calls == [request]


def test_mock_provider_stream_matches_provider_protocol() -> None:
    provider: Provider = MockProvider()

    assert isinstance(provider, Provider)
