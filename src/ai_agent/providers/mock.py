from ai_agent.core.message import Message
from ai_agent.core.request import ChatRequest
from ai_agent.core.response import ChatResponse, Usage


class MockProvider:
    """Deterministic provider used to develop and test the Agent runtime."""

    def __init__(self, response_text: str = "mock response") -> None:
        self.response_text = response_text
        self.calls: list[ChatRequest] = []

    def chat(self, request: ChatRequest) -> ChatResponse:
        # English: Recording requests lets tests inspect what the Agent sent to the provider.
        # 中文：記錄收到的請求，讓測試可以檢查 Agent 實際傳給 Provider 的內容。
        self.calls.append(request)

        # English: The mock always returns the same response, making tests deterministic.
        # 中文：Mock 每次都回傳固定內容，讓測試結果保持 deterministic，不依賴真實 LLM。
        return ChatResponse(
            message=Message(role="assistant", content=self.response_text),
            finish_reason="stop",
            usage=Usage(input_tokens=0, output_tokens=0, total_tokens=0),
        )
