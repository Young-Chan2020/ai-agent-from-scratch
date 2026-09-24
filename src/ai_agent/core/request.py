from dataclasses import dataclass

from .message import Message
from .structured import StructuredOutputConfig


@dataclass(frozen=True)
class ModelConfig:
    """Configuration that describes how a model should be called."""

    model: str
    temperature: float | None = None
    max_tokens: int | None = None


@dataclass(frozen=True)
class ChatRequest:
    """A provider-independent request for a single chat completion."""

    messages: list[Message]
    config: ModelConfig
    stream: bool = False
    structured_output: StructuredOutputConfig | None = None

    def __post_init__(self) -> None:
        # English: A chat request needs at least one message so the provider has input context.
        # 中文：聊天請求至少需要一條訊息，這樣 Provider 才有可以處理的輸入上下文。
        if not self.messages:
            raise ValueError("ChatRequest requires at least one message")

        # English: Temperature is a probability-sampling control, so negative values are invalid.
        # 中文：Temperature 用於控制機率採樣，因此負數沒有合理意義，這裡直接拒絕。
        if self.config.temperature is not None and self.config.temperature < 0:
            raise ValueError("temperature must be non-negative")

        # English: max_tokens limits the generated output and therefore cannot be zero or negative.
        # 中文：max_tokens 用來限制生成內容長度，因此不能是零或負數。
        if self.config.max_tokens is not None and self.config.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
