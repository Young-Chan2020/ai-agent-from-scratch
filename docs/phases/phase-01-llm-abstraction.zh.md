# Phase 01 — LLM Abstraction（LLM 抽象）

## 學習目標

Phase 1 建立 Agent Runtime 與 LLM Provider 之間的第一個清楚邊界。

本階段的目標不是建立一個完整、商業級的 LLM Provider Framework，而是理解 Agent 為什麼需要抽象，以及這個抽象到底解決了什麼問題。

完成本階段後，應該能理解：

1. Agent 不應該直接依賴某一家 LLM Vendor 的 SDK 或資料格式。
2. Message、Request、Response、Model Configuration、Usage 與 Provider Error 都應該有自己的專案層級表示方式。
3. Provider 應該提供一個小而穩定的介面，讓 Agent Runtime 不需要知道底層是哪一家 LLM。
4. MockProvider 可以讓我們在沒有 API Key、網路或真實模型的情況下測試 Agent Runtime。
5. 抽象本身應該保持簡單，不能因為追求「架構漂亮」而把真正重要的機制藏起來。

---

## Core Concepts

### 1. Provider-independent Message

**是什麼？**

`Message` 是 Agent 與 LLM 之間傳遞的一則訊息，目前包含 `role`、`content`，以及可選的 `name` 與 `tool_call_id`。

**為什麼需要？**

不同 LLM Provider 有不同的 SDK Object 與 Request Format。如果 Agent 到處直接使用 Provider SDK 的 Message Object，整個 Agent Runtime 就會被某一家 Vendor 綁死。

**對 AI Agent 的意義**

後續我們會加入 Tool Calling、ReAct、Memory、Context Management、Multi-Agent 等能力。這些功能都需要一個穩定的 Conversation State 表示方式。

**實作位置**

`src/ai_agent/core/message.py::Message`

---

### 2. Request / Response Abstraction

**是什麼？**

`ChatRequest` 描述一次 LLM 呼叫，而 `ChatResponse` 描述經過我們統一後的結果。

**為什麼需要？**

Agent Runtime 應該只需要知道「我要送一個 Chat Request，然後收到一個 Chat Response」，而不需要知道底層是 OpenAI、Anthropic、Gemini、Local Model 還是 Mock。

**對 AI Agent 的意義**

未來的 Agent Loop 會反覆呼叫 Provider。如果 Agent Loop 直接依賴 Vendor SDK，那麼 Agent 的核心邏輯會和 Provider 實作混在一起。抽象層可以把兩者分開。

**實作位置**

- `src/ai_agent/core/request.py::ChatRequest`
- `src/ai_agent/core/response.py::ChatResponse`

---

### 3. Model Configuration 是資料，而不是 Provider 行為

**是什麼？**

`ModelConfig` 保存模型名稱以及一些共同的 Generation Parameters，例如 `temperature` 與 `max_tokens`。

**為什麼獨立？**

這些設定描述的是「這一次 LLM Request 希望怎麼執行」，而不是某一個 Provider 本身的固定狀態。因此它應該屬於 Request Boundary。

**Trade-off**

不同 Provider 並不一定支援完全相同的參數。因此第一版只放各 Provider 共同的基本設定，而不是試圖一次把所有 Vendor-specific options 都塞進來。

**實作位置**

`src/ai_agent/core/request.py::ModelConfig`

---

### 4. 使用 `Protocol` 建立 Provider Abstraction

**是什麼？**

`Provider` 定義所有 LLM Provider 最基本的能力：

```text
chat(request) -> ChatResponse
```

**為什麼使用 `Protocol`？**

Agent 真正需要的是「這個物件能不能做 `chat()`」，而不是「這個 class 有沒有繼承某個 BaseProvider」。

Python 的 `Protocol` 提供 Structural Typing，因此只要一個 class 符合這個介面，就可以被當成 Provider 使用，而不需要強制繼承某個基底類別。

**Trade-off**

`Protocol` 可以保持介面很輕量，但它本身不會解決 Retry、Rate Limit、Streaming、Structured Output 或 Tool Calling 等問題。這些會在後面的 Phase 分別處理。

**實作位置**

`src/ai_agent/providers/base.py::Provider`

---

### 5. MockProvider

**是什麼？**

`MockProvider` 是一個 deterministic 的 Provider。它不呼叫任何真正的 LLM，而是回傳固定結果，並且記錄收到的 Request。

**為什麼需要？**

Agent 的測試不應該依賴：

- 網路
- API Key
- 真實 LLM
- API 費用
- Model 的非 deterministic 行為

因此我們需要一個完全可控制的 Provider。

**對 AI Agent 的意義**

等到 Phase 7 開始實作 Agent Loop 時，MockProvider 就可以成為我們驗證 Agent 行為的 controlled environment。

**實作位置**

`src/ai_agent/providers/mock.py::MockProvider`

---

### 6. 統一的 Usage

**是什麼？**

`Usage` 用 `input_tokens`、`output_tokens` 與 `total_tokens` 表示一次 LLM 呼叫的 Token 使用量。

**為什麼需要？**

不同 Provider 回傳 Token Usage 的格式可能不同。如果讓 Agent Runtime 直接依賴每一家 Provider 的 Usage Object，後續的 Cost Analysis、Observability 與 Evaluation 都會變得困難。

因此我們先在自己的 Core Layer 建立統一格式。

**實作位置**

`src/ai_agent/core/response.py::Usage`

---

### 7. Provider Error Boundary

**是什麼？**

`ProviderError` 是所有 Provider Failure 的共同父類別，目前包含：

- `InvalidRequestError`
- `ProviderUnavailableError`

**為什麼需要？**

底層 Provider SDK 可能有自己的 Exception Hierarchy。如果這些 Exception 一路往上洩漏到 Agent Runtime，Runtime 就必須知道每一家 Vendor 的錯誤格式。

我們需要一個自己的 Error Boundary，讓上層只處理專案層級的 Provider Errors。

**實作位置**

`src/ai_agent/core/errors.py`

---

## Architecture

Phase 1 的架構刻意保持很小：

```text
Agent Runtime（未來）
        |
        v
+-----------------------+
| Provider              |
| chat(ChatRequest)     |
| -> ChatResponse       |
+-----------------------+
        |
        v
+-----------------------+
| Concrete Provider     |
| MockProvider（現在）  |
| OpenAI 等（未來）      |
+-----------------------+
```

最重要的是 Dependency Direction：

```text
Agent / Runtime
      |
      v
Project-level Core Models + Provider Interface
      |
      v
Concrete Provider Implementation
      |
      v
External LLM SDK / API
```

上層 Agent Runtime 不應該需要知道具體使用哪一個 Provider。

---

## Implementation Mapping

| Concept | Source | Symbol | Purpose |
|---|---|---|---|
| Message Model | `src/ai_agent/core/message.py` | `Message` | Provider-independent 的對話訊息 |
| Model Configuration | `src/ai_agent/core/request.py` | `ModelConfig` | 共通模型與 Generation 設定 |
| Request Model | `src/ai_agent/core/request.py` | `ChatRequest` | Provider-independent 的 Chat Request |
| Response Model | `src/ai_agent/core/response.py` | `ChatResponse` | Provider-independent 的 Chat Response |
| Usage Model | `src/ai_agent/core/response.py` | `Usage` | 統一 Token Usage |
| Provider Interface | `src/ai_agent/providers/base.py` | `Provider` | LLM Provider 的穩定邊界 |
| Provider Errors | `src/ai_agent/core/errors.py` | `ProviderError` 及 subclasses | 統一 Provider Failure Boundary |
| Test Provider | `src/ai_agent/providers/mock.py` | `MockProvider` | Deterministic Provider |

---

## Tests

本階段已建立 Core Model 與 Mock Provider 的測試。

### Core Model Tests

`tests/core/test_models.py`

- `test_message_keeps_provider_independent_fields`
- `test_chat_request_requires_a_message`
- `test_chat_request_rejects_invalid_model_config`
- `test_usage_tracks_token_counts`

這些測試驗證 Provider-independent Data Model 的基本不變條件。

### Provider Tests

`tests/providers/test_mock.py`

- `test_mock_provider_returns_deterministic_response`
- `test_mock_provider_records_requests`
- `test_mock_provider_matches_provider_protocol`

這些測試驗證 MockProvider 是否符合 Provider Contract，以及它是否保持 deterministic。

### Test Execution

測試執行由專案作者在本機完成。這個專案的學習流程中，本文件負責記錄測試設計與對應程式碼，而本機測試結果則由專案作者自行驗證。

---

## Design Decisions

### 使用 Standard-library `dataclass`

目前的 Core Models 使用 Python Standard Library 的 `dataclass`。

原因不是因為 `dataclass` 一定是最強的方案，而是 Phase 1 的重點是理解資料模型本身。如果一開始就引入更大型的 Validation Framework，可能會讓重要的機制被 Library API 藏起來。

這個階段我們希望「資料結構本身」是看得見的。

### 使用 `Protocol` 而不是 Abstract Base Class

Provider 目前只需要描述行為 Contract，而不需要共享實作。因此使用 `Protocol` 可以讓 Concrete Provider 保持簡單，也能直接表達 Structural Typing 的概念。

### 先建立 Mock，再建立真正 Provider

如果一開始就接 OpenAI / Anthropic API，我們會同時遇到 API Key、Network、SDK、Rate Limit、Retry、Provider-specific Response Format 等問題。

先建立 Mock，可以先驗證「我們設計的 abstraction 本身是否合理」。

### 只建立小型 Common Configuration

Phase 1 不嘗試統一所有 Provider 的所有能力。

如果抽象層一開始就塞進大量 Vendor-specific options，反而會讓 abstraction 失去意義。因此目前只保留共同、容易理解的設定。

### Core Models 使用 `frozen=True`

Request、Response 等 Core Data Models 使用 immutable dataclass。

這可以降低資料在不同 Runtime Component 之間傳遞時被意外修改的風險，也讓資料流更容易理解。

---

## Limitations

Phase 1 是刻意不完整的。

目前尚未處理：

1. 真正的 LLM Provider。
2. Streaming。
3. Structured Output。
4. Tool / Function Calling。
5. Provider-specific Capabilities。
6. Retry、Timeout、Rate Limit、Circuit Breaking。
7. 更完整的 Provider Error Hierarchy。
8. 真實 Token Usage 計算。
9. Agent Runtime 所需要的完整 Request / Response Surface。

這些限制不是遺漏，而是刻意留到後續 Phase，避免第一個 abstraction 一開始就變得過度複雜。

---

## Interview Questions

### Q1. 為什麼 Agent 不直接呼叫 OpenAI / Anthropic SDK？

因為這會讓 Agent Runtime 與 Vendor-specific API 綁定。Provider abstraction 可以讓 Runtime 依賴穩定 Contract，而不是依賴某一家 Vendor 的 SDK。

### Q2. 為什麼需要自己的 `Message`？

因為 Provider SDK 的 Message Object 是 implementation detail。使用自己的 Message Model 可以避免 Vendor-specific type 滲透到 Agent Architecture。

### Q3. 為什麼使用 `Protocol` 而不是 inheritance？

因為 Agent 需要的是行為 Contract，而不是共同的 class hierarchy。`Protocol` 允許符合相同介面的 class 被使用，而不要求它們繼承同一個 Base Class。

### Q4. MockProvider 到底有什麼意義？

它提供 deterministic behavior。Agent 測試不需要依賴 Network、API Key、費用或真實模型的不確定性。

### Q5. 為什麼需要統一 `Usage`？

不同 Provider 的 Usage Format 可能不同。統一後，未來的 Observability、Cost Tracking 與 Evaluation 就可以依賴自己的 Core Model，而不是依賴 Vendor SDK。

### Q6. 如果 Provider 暫時無法服務，應該怎麼辦？

Provider 實作應該先把底層錯誤轉換成我們自己的 Provider Error Boundary。後續 Agent Runtime 才能決定要 Retry、Fallback、停止，或把錯誤交給上層。

### Q7. Provider Abstraction 的主要 Trade-off 是什麼？

Abstraction 可以提升可替換性與測試性，但 Common Interface 能表達的通常只是不同 Provider 的共同能力。如果抽象得太 Generic，Vendor-specific features 會變得難以表達。

因此我們採取「先建立小型 Common Surface，再隨後續 Phase 的需求逐步擴充」的策略。

---

## Phase Completion Checklist

- [x] 理解 Provider Boundary 的目的。
- [x] 建立 Provider-independent Message / Request / Response Models。
- [x] 建立共通 Model Configuration。
- [x] 建立 Provider Interface。
- [x] 實作 Deterministic MockProvider。
- [x] 建立 Core Model Tests。
- [x] 建立 Provider Tests。
- [ ] 在本機執行 Test Suite 並確認全部通過。
- [ ] 根據本機測試結果確認 Phase 1 完成。

---

## Source Map

```text
Learning Concept
      ↓
Architecture
      ↓
Source File
      ↓
Class / Function
      ↓
Test

Message
  → Core Data Model
  → src/ai_agent/core/message.py
  → Message
  → tests/core/test_models.py::test_message_keeps_provider_independent_fields

Request Validation
  → Core Request Boundary
  → src/ai_agent/core/request.py
  → ChatRequest.__post_init__
  → tests/core/test_models.py::test_chat_request_requires_a_message
  → tests/core/test_models.py::test_chat_request_rejects_invalid_model_config

Provider Abstraction
  → Provider Boundary
  → src/ai_agent/providers/base.py
  → Provider.chat()
  → tests/providers/test_mock.py::test_mock_provider_matches_provider_protocol

Mock Provider
  → Concrete Provider Implementation
  → src/ai_agent/providers/mock.py
  → MockProvider.chat()
  → tests/providers/test_mock.py::test_mock_provider_returns_deterministic_response
  → tests/providers/test_mock.py::test_mock_provider_records_requests

Usage
  → Normalized Response Metadata
  → src/ai_agent/core/response.py
  → Usage
  → tests/core/test_models.py::test_usage_tracks_token_counts
```
