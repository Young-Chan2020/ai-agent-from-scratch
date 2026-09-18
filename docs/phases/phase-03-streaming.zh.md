# Phase 03 — Streaming（串流輸出）

## Learning Objectives

這一課把 LLM 的完整回應擴充成逐段輸出。

完成後應理解：
- ChatResponse 與 ChatChunk 的差異
- Iterator / Generator 如何表示逐步產生的資料
- SSE 如何傳輸 streaming event
- 不同 Provider 的 event 如何 normalize
- completion metadata 與 usage 為什麼可能分開抵達
- 如何在不呼叫真實 API 的情況下測試 streaming

## Core Concepts

### 1. ChatResponse vs ChatChunk

Phase 02：
~~~text
ChatRequest → Provider.chat() → ChatResponse
~~~
ChatResponse 代表完整結果。Phase 03 新增：
~~~text
ChatRequest → Provider.stream() → Iterator[ChatChunk]
~~~
ChatChunk 代表部分文字或 completion metadata。

### 2. Iterator 與 Generator

Provider.stream() 回傳 iterator，呼叫端可以逐段消費：
~~~python
for chunk in provider.stream(request):
    print(chunk.content, end="")
~~~

### 3. SSE Transport

共用 HTTP layer 處理基本 Server-Sent Events framing：
~~~text
data: {...}
data: {...}
data: [DONE]
~~~
Transport 負責 HTTP / SSE framing；Provider adapter 負責解讀 Provider-specific event schema。

### 4. Provider-specific Event Mapping

OpenAI Responses API 使用例如 response.output_text.delta、response.completed。
Anthropic Messages API 使用例如 content_block_delta、message_delta。
DeepSeek Chat Completions 使用 choices[].delta.content，並可在最後 event 提供 usage。

這些不同格式最後都轉成 ChatChunk。

### 5. Streaming 不會消除 Provider 差異

共同 interface 只是把差異隔離，不代表 Provider 行為完全一致。各 Adapter 仍負責自己的 event parsing 與 metadata mapping。

## Architecture

~~~text
                         Provider
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
               chat()               stream()
                 │                     │
                 ▼                     ▼
           ChatResponse        Iterator[ChatChunk]
                                       │
                              Provider event parser
                                       │
                              SSE StreamTransport
~~~

## Implementation Mapping

| Concept | Source | Implementation |
|---|---|---|
| Streaming result model | src/ai_agent/core/response.py | ChatChunk |
| Common streaming contract | src/ai_agent/providers/base.py | Provider.stream() |
| SSE transport | src/ai_agent/providers/http.py | send_sse_json() |
| Streaming transport type | src/ai_agent/providers/http.py | StreamTransport |
| Mock streaming | src/ai_agent/providers/mock.py | MockProvider.stream() |
| OpenAI streaming | src/ai_agent/providers/openai.py | OpenAIProvider.stream() |
| OpenAI event normalization | src/ai_agent/providers/openai.py | _parse_stream_event() |
| Anthropic streaming | src/ai_agent/providers/anthropic.py | AnthropicProvider.stream() |
| Anthropic event normalization | src/ai_agent/providers/anthropic.py | _parse_stream_event() |
| DeepSeek streaming | src/ai_agent/providers/deepseek.py | DeepSeekProvider.stream() |
| DeepSeek event normalization | src/ai_agent/providers/deepseek.py | _parse_stream_event() |

## Tests

測試使用注入的 StreamTransport，不呼叫真實網路。

Core model 驗證 ChatChunk 可以表示部分文字與 completion metadata。Mock 驗證逐段輸出與最後的 finish reason。各 Provider 測試驗證不同 streaming event 可以 normalize 成共同 ChatChunk，並保留可取得的 usage。

## Design Decisions

### 為什麼使用 Iterator[ChatChunk]？

Streaming 本質上是 sequential data flow。Iterator 讓 caller 可以逐段消費資料，而不用等待完整 response。

### 為什麼新增 ChatChunk？

Chunk 是部分輸出；ChatResponse 是完成結果。分成兩個 type 可以讓生命週期更清楚。

### 為什麼把 SSE parsing 放在 HTTP layer？

SSE 是 transport / framing 問題；Provider event schema 則是 Adapter 的責任。這樣可以避免各 Provider 重複處理 HTTP stream。

### 為什麼注入 StreamTransport？

Network 是 external dependency。注入 transport 後，可以用固定 event sequence 做 deterministic testing。

### 為什麼保留 raw？

Provider event 可能包含 common model 尚未暴露的 metadata。保留 raw 有助於 debug 與後續擴充。

## Limitations

- SSE parser 目前只處理本課需要的基本 data: event format。
- 尚未處理 reconnect、event ID、heartbeat、multi-line data aggregation。
- 尚未建立 streaming cancellation abstraction。
- 尚未支援 async streaming。
- 尚未支援 tool-call streaming。
- Agent orchestration 尚未直接消費 streaming。
- 尚未實作 streaming retry / backpressure policy。

## Interview Questions

1. 為什麼 streaming 應該回傳 iterator，而不是一般 response？
2. ChatResponse 與 ChatChunk 有什麼差異？
3. SSE parsing 應該放在哪一層？
4. 不同 Provider event schema 不同時，如何 normalize？
5. 為什麼 streaming 可以降低 perceived latency？
6. 收到數個 chunk 後 connection failure，應該怎麼處理？
7. 如何設計 cancellation？
8. async streaming 會如何改變 interface？
9. Provider 在不同時間回傳 usage 時，應該在哪裡收集？
10. 哪些資訊應該保持 provider-specific？

## Phase Completion Checklist

- [ ] 理解 ChatChunk。
- [ ] 實作 Provider.stream()。
- [ ] 實作 Mock streaming。
- [ ] 實作共用 SSE transport。
- [ ] 實作 OpenAI streaming。
- [ ] 實作 Anthropic streaming。
- [ ] 實作 DeepSeek streaming。
- [ ] 本地相關 tests 通過。
- [ ] Review design trade-offs。
- [ ] 理解 limitations。
- [ ] 中英文 documentation 同步。
- [ ] Merge 前 review branch diff。

## Source Map

~~~text
Streaming Model
      ↓
src/ai_agent/core/response.py
      ↓
ChatChunk
      ↓
tests/core/test_models.py

Provider Contract
      ↓
src/ai_agent/providers/base.py
      ↓
Provider.stream()

SSE Transport
      ↓
src/ai_agent/providers/http.py
      ↓
send_sse_json()

Provider Event Mapping
      ↓
OpenAIProvider._parse_stream_event()
AnthropicProvider._parse_stream_event()
DeepSeekProvider._parse_stream_event()
~~~