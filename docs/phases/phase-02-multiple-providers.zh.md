# Phase 02 — Multiple LLM Providers（多 LLM Provider）

## Learning Objectives

這一課會把 Phase 01 的 Provider abstraction 延伸成多個實際的 LLM Provider。

完成這一課後，應該理解：

- 為什麼需要共同的 Provider interface
- 為什麼不同 Provider 的 API 即使用途相似，實際格式仍然不同
- Provider adapter 如何把共用 request 轉換成 Provider-specific payload
- Provider-specific response 如何被統一成共同的 response type
- 為什麼某些設定不能在不同 Provider 之間一對一映射
- 如何在不真正呼叫 API 的情況下測試 Provider integration

---

## Core Concepts

### 1. Provider Adapter

Provider Adapter 實作共同的 Provider.chat() interface，同時負責處理某一家 API 的 request / response 格式。

Agent 所看到的介面保持簡單：

~~~text
ChatRequest → Provider → ChatResponse
~~~

Provider-specific details 則留在 adapter 裡面。

### 2. Provider Differences Are Real

OpenAI、Anthropic 與 DeepSeek 並不是完全相同的 API。

本課使用：

- OpenAI Responses API
- Anthropic Messages API
- DeepSeek Chat Completions API

例如 OpenAI 使用 input 結構，並提供 output_text / usage 等欄位；Anthropic 使用 messages、獨立的 system 欄位、content blocks，以及不同的 usage 格式；DeepSeek 則使用 OpenAI-compatible 的 Chat Completions 格式，但 endpoint 與 usage 欄位不同。

因此 abstraction 不應該假裝所有 Provider 都完全一樣。

真正應該做的是：找出 Agent runtime 真正需要的最小共同 contract，然後把其他差異留在 Provider adapter 裡。

### 3. Request Translation

Provider adapter 負責：

~~~text
Common ChatRequest
      ↓
Provider-specific payload
      ↓
Provider API
~~~

例如 ModelConfig.max_tokens 在 OpenAI 會轉成 max_output_tokens，而 Anthropic 使用 max_tokens。

### 4. Response Normalization

不同 Provider 的 response 最後都轉成：

~~~text
ChatResponse
 ├── Message
 ├── finish_reason
 ├── Usage
 └── raw
~~~

raw 特別保留原始 response，方便之後除錯，以及未來需要使用 Provider-specific features 時取得原始資料。

### 5. Provider-Specific Limitations

共同 interface 不代表所有 Provider 都支援完全相同的功能。

本課刻意展示這個限制：

- Anthropic 目前對新版模型的 temperature 有 Provider / model-specific 限制。
- Tool messages 暫時不做 mapping，因為 Tool Calling 是後續 Phase 才會實作的內容。

如果目前這個 Phase 無法安全地轉換某個設定，adapter 會明確丟出 InvalidRequestError，而不是默默忽略。

### 6. Testable Network Boundary

正常的 unit test 不應該依賴真實 Provider API。

Provider adapter 接受一個可注入的 HttpTransport callable，因此測試可以檢查：

- endpoint
- authentication headers
- Provider-specific request payload
- response parsing

而不需要真的連網或消耗 API credits。

---

## Architecture

Phase 01 的架構：

~~~text
Agent
  ↓
Provider
  ↓
MockProvider
~~~

現在延伸成：

~~~text
                         Provider
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
        MockProvider   OpenAIProvider  AnthropicProvider  DeepSeekProvider
                            │             │                  │
                            ▼             ▼                  ▼
                     Responses API   Messages API   Chat Completions API
~~~

共同 contract 仍然是：

~~~text
Provider.chat(ChatRequest) -> ChatResponse
~~~

Provider adapter 負責所有 API-specific translation。

---

## Implementation Mapping

| Concept | Source | Implementation |
|---|---|---|
| Common provider contract | src/ai_agent/providers/base.py | Provider.chat() |
| Shared HTTP transport | src/ai_agent/providers/http.py | send_json() |
| OpenAI request translation | src/ai_agent/providers/openai.py | OpenAIProvider._build_payload() |
| OpenAI response normalization | src/ai_agent/providers/openai.py | OpenAIProvider._parse_response() |
| Anthropic request translation | src/ai_agent/providers/anthropic.py | AnthropicProvider.chat() |
| Anthropic system-message mapping | src/ai_agent/providers/anthropic.py | AnthropicProvider._split_system_messages() |
| Anthropic response normalization | src/ai_agent/providers/anthropic.py | AnthropicProvider._parse_response() |
| DeepSeek request translation | src/ai_agent/providers/deepseek.py | DeepSeekProvider._build_payload() |
| DeepSeek response normalization | src/ai_agent/providers/deepseek.py | DeepSeekProvider._parse_response() |
| Common response | src/ai_agent/core/response.py | ChatResponse, Usage |
| Normalized provider errors | src/ai_agent/core/errors.py | InvalidRequestError, ProviderUnavailableError |

---

## Tests

Provider tests 使用 fake transport，而不是真實 API。

### OpenAI

~~~text
tests/providers/test_openai.py::test_openai_provider_builds_provider_specific_request
tests/providers/test_openai.py::test_openai_provider_matches_provider_protocol
~~~

這些測試驗證 OpenAI adapter：

- 使用正確 endpoint
- 使用正確 authentication header
- 正確轉換 model configuration
- 正確解析 response
- 仍然符合共同的 Provider protocol

### DeepSeek

~~~text
tests/providers/test_deepseek.py::test_deepseek_provider_builds_provider_specific_request
tests/providers/test_deepseek.py::test_deepseek_provider_matches_provider_protocol
~~~

這些測試驗證 DeepSeek adapter：

- 使用正確的 Chat Completions endpoint
- 使用正確 authentication header
- 正確 mapping common message 與 model configuration
- 正確 normalization DeepSeek usage fields
- 符合共同 Provider protocol

### Anthropic

~~~text
tests/providers/test_anthropic.py::test_anthropic_provider_separates_system_prompt
tests/providers/test_anthropic.py::test_anthropic_provider_rejects_unmapped_temperature
tests/providers/test_anthropic.py::test_anthropic_provider_matches_provider_protocol
~~~

這些測試驗證 Anthropic adapter：

- 將 system messages 移到 Anthropic 的 system field
- 正確 mapping common message list
- 正確 normalization usage
- 明確拒絕目前無法安全 mapping 的設定
- 符合共同 Provider protocol

---

## Design Decisions

### 為什麼要做兩個 Provider？

只有一個 Provider 時，很難真正感受到 abstraction 的價值。

加入 OpenAI 與 Anthropic 後，可以直接看到 request / response translation 的 boundary。

### 為什麼這裡直接使用 HTTP，而不是 Provider SDK？

這個 project 的學習目標是理解 Provider boundary 本身。

Production application 使用官方 SDK 是合理的，但在這個 learning project 中直接使用 HTTP，可以讓 request / response transformation 清楚可見，也避免 SDK 本身成為我們想理解的 abstraction。

這是學習上的選擇，不代表 production 不應該使用 SDK。

### 為什麼要注入 transport？

Network 是 external dependency。

把 transport 注入後，unit test 可以 deterministic 地測試 request construction 與 response parsing。

### 為什麼保留 raw？

未來 debugging、observability、tool calling 以及其他 advanced features 都可能需要 Provider-specific metadata。

因此 common response 只 normalization runtime 真正需要的資料，同時保留原始 response。

---

## Limitations

目前刻意不處理：

- streaming
- tool calls
- structured output
- provider retries
- rate-limit handling beyond basic HTTP error normalization
- async HTTP
- automatic provider selection
- provider-specific advanced parameters
- multimodal content

這些內容會在後續 Phase 再逐步加入。

目前 Tool messages 會被明確拒絕，因為 Tool execution 要到 Phase 05 / 06 才開始實作。

---

## Interview Questions

### Architecture

1. 為什麼 Agent 應該依賴 Provider interface，而不是直接依賴 OpenAI client？
2. Provider adapter 解決了什麼問題？
3. 哪些內容應該放進 common abstraction？哪些應該留在 provider-specific implementation？
4. 支援 multiple providers 是否代表所有 Provider 必須擁有完全相同的能力？

### Trade-offs

5. Common abstraction 什麼時候會變成 leaky abstraction？
6. 如果 Provider A 支援某個功能，而 Provider B 不支援，應該怎麼處理？
7. 什麼情況下應該使用官方 Provider SDK，而不是直接 HTTP？
8. 為什麼保留 raw provider response 有價值？

### Reliability and Testing

9. 如何在不真正呼叫 API 的情況下測試 LLM Provider？
10. Provider error 應該在哪一層 normalization？
11. 如果 Provider 回傳 malformed JSON 或 unexpected response shape，應該怎麼處理？
12. 如果未來加入 retry，如何避免 Agent runtime 與特定 Provider 耦合？

---

## Phase Completion Checklist

- [ ] 已理解 Phase 02 的核心概念。
- [ ] OpenAI 與 Anthropic adapter 已實作。
- [ ] Provider-specific request translation 是明確可見的。
- [ ] Provider-specific response parsing 已 normalization。
- [ ] Network call 可以被 test transport 替換。
- [ ] Relevant tests 在本地通過。
- [ ] Design trade-offs 已 review。
- [ ] Limitations 已理解。
- [ ] English 與 Traditional Chinese 文件保持同步。
- [ ] Merge 前已 review branch diff。

---

## Source Map

~~~text
Provider Abstraction
      ↓
src/ai_agent/providers/base.py
      ↓
Provider.chat()

OpenAI Translation
      ↓
src/ai_agent/providers/openai.py
      ↓
OpenAIProvider._build_payload()
OpenAIProvider._parse_response()
      ↓
tests/providers/test_openai.py

DeepSeek Translation
      ↓
src/ai_agent/providers/deepseek.py
      ↓
DeepSeekProvider._build_payload()
DeepSeekProvider._parse_response()
      ↓
tests/providers/test_deepseek.py

Anthropic Translation
      ↓
src/ai_agent/providers/anthropic.py
      ↓
AnthropicProvider._split_system_messages()
AnthropicProvider._parse_response()
      ↓
tests/providers/test_anthropic.py

Network Boundary
      ↓
src/ai_agent/providers/http.py
      ↓
send_json()
~~~
