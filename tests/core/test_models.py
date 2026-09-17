import pytest

from ai_agent.core.message import Message
from ai_agent.core.request import ChatRequest, ModelConfig
from ai_agent.core.response import Usage


def test_message_keeps_provider_independent_fields() -> None:
    message = Message(role="user", content="Hello")

    assert message.role == "user"
    assert message.content == "Hello"
    assert message.name is None


def test_chat_request_requires_a_message() -> None:
    with pytest.raises(ValueError, match="at least one message"):
        ChatRequest(messages=[], config=ModelConfig(model="mock-model"))


def test_chat_request_rejects_invalid_model_config() -> None:
    with pytest.raises(ValueError, match="temperature"):
        ChatRequest(
            messages=[Message(role="user", content="Hello")],
            config=ModelConfig(model="mock-model", temperature=-1),
        )

    with pytest.raises(ValueError, match="max_tokens"):
        ChatRequest(
            messages=[Message(role="user", content="Hello")],
            config=ModelConfig(model="mock-model", max_tokens=0),
        )


def test_usage_tracks_token_counts() -> None:
    usage = Usage(input_tokens=10, output_tokens=5, total_tokens=15)

    assert usage.total_tokens == 15
