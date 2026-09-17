from ai_agent.core.message import Message
from ai_agent.core.request import ChatRequest, ModelConfig
from ai_agent.providers.base import Provider
from ai_agent.providers.mock import MockProvider


def test_mock_provider_returns_deterministic_response() -> None:
    provider = MockProvider(response_text="hello from mock")
    request = ChatRequest(
        messages=[Message(role="user", content="Hello")],
        config=ModelConfig(model="mock-model"),
    )

    response = provider.chat(request)

    assert response.message.role == "assistant"
    assert response.message.content == "hello from mock"
    assert response.finish_reason == "stop"
    assert response.usage is not None


def test_mock_provider_records_requests() -> None:
    provider = MockProvider()
    request = ChatRequest(
        messages=[Message(role="user", content="Hello")],
        config=ModelConfig(model="mock-model"),
    )

    provider.chat(request)

    assert provider.calls == [request]


def test_mock_provider_matches_provider_protocol() -> None:
    provider: Provider = MockProvider()

    assert isinstance(provider, Provider)
