# Phase 06 — Tool Execution（工具執行）

## Learning Objectives（學習目標）

這一課把 LLM 產生的 Tool Call 轉成受 Agent Runtime 控制的實際 action。

- 將不同 Provider 的 Tool Call normalize 成 common ToolCall。
- 在 runtime executor 中註冊可執行的 Tool。
- 根據 name 找到 Tool。
- 根據 Tool parameter schema 驗證 LLM 產生的 arguments。
- 執行 Tool handler。
- 將 execution output 與 failure 統一成 ToolResult。
- 理解為什麼真正的 execution 必須由 runtime 控制。

## Core Concepts（核心概念）

### Tool Call vs Tool Execution

Phase 05 established:

```
LLM
 ↓
Tool Call
 ├── name
 └── arguments
```

Phase 06 adds:

```
Tool Call
    ↓
ToolExecutor
    ├── find Tool
    ├── validate arguments
    ├── execute handler
    └── create ToolResult
```

Model 只是提出 action request；真正是否執行、如何執行，由 runtime 控制。

### Provider-independent ToolCall

不同 Provider 的 Tool Call 格式不同。Common layer 將它們 normalize 成：

```python
ToolCall(
    id="call-1",
    name="get_weather",
    arguments={"city": "Los Angeles"},
)
```

Agent runtime 不需要知道這個 call 原本來自 OpenAI、Anthropic 還是 DeepSeek。

### Tool Execution Flow（工具執行流程）

```
LLM
 │
 │ provider-specific Tool Call
 ▼
Provider Adapter
 │
 │ normalize
 ▼
ToolCall
 │
 ▼
ToolExecutor
 │
 ├── lookup by name
 ├── validate arguments
 └── invoke handler
 │
 ▼
ToolResult
 │
 ▼
Agent
```

### Argument Validation（參數驗證）

Model 產生的 arguments 應該被視為 untrusted input。

If a Tool expects:

```
city: string
```

but the model produces:

```json
{"city": 123}
```

executor 會在 handler 執行前拒絕這些 arguments。

這建立了 model output 與 application code 之間的明確安全邊界。

### ToolResult 不是 Final Answer

```
ToolResult
├── tool_call_id
├── name
├── content
└── is_error
```

ToolResult 通常會回到 Agent/LLM loop，讓 LLM 根據結果產生最後給 user 的回答。

## 實際例子

### 例子 1 — 註冊 Tool

```python
weather_tool = Tool(
    definition=ToolDefinition(
        name="get_weather",
        description="Get the current weather for a city.",
        parameters={
            "type": "object",
            "properties": {
                "city": {"type": "string"},
            },
            "required": ["city"],
        },
    ),
    handler=lambda city: f"Weather in {city}: 22°C, Sunny",
)

executor = ToolExecutor([weather_tool])
```

LLM 只看到 ToolDefinition；真正的 Python handler 由 executor 持有。

### 例子 2 — 執行 Tool Call

```python
tool_call = ToolCall(
    id="call-1",
    name="get_weather",
    arguments={"city": "Los Angeles"},
)

result = executor.execute(tool_call)
```

Result:

```python
ToolResult(
    tool_call_id="call-1",
    name="get_weather",
    content="Weather in Los Angeles: 22°C, Sunny",
    is_error=False,
)
```

這裡的 transformation 是：

```
LLM Tool Call
        ↓
ToolExecutor
        ↓
Python handler
        ↓
ToolResult
```

### 例子 3 — Invalid Arguments

If the model generates:

```json
{"city": 123}
```

handler 不會被呼叫，而是由 executor 回傳 error ToolResult。

### 例子 4 — Handler Failure

Even valid arguments can lead to a runtime failure:

```
Tool Call
    ↓
argument validation ✓
    ↓
handler execution
    ↓
API/network/database failure
    ↓
ToolResult(is_error=True)
```

Timeouts, retries, permissions, sandboxing, and human approval are later concerns.

### 例子 5 — 完整流程

```
User
 ↓
Agent
 ↓
LLM
 ↓
Tool Call
 ↓
Provider Adapter
 ↓
ToolCall
 ↓
ToolExecutor
 ├── lookup
 ├── validate
 └── execute
 ↓
ToolResult
 ↓
Agent
 ↓
LLM
 ↓
Final Answer
```

Phase 06 實作 execution boundary；完整的反覆呼叫 LLM、執行 Tool、加入 Tool Result 的 Agent Loop 會在後面的 Agent Loop phase 實作。

## Architecture（架構）

```
Provider
   │
   ├── OpenAI
   ├── Anthropic
   └── DeepSeek
          │
          ▼
       ToolCall
          │
          ▼
    ToolExecutor
      /   |   \
 lookup validate execute
          │
          ▼
      ToolResult
          │
          ▼
        Agent
```

## Implementation Mapping（實作對應）

| Concept | Source | Implementation |
|---|---|---|
| Common Tool Call | src/ai_agent/core/response.py | ToolCall |
| Common Tool Result | src/ai_agent/core/response.py | ToolResult |
| Executable Tool | src/ai_agent/core/tool.py | Tool |
| Registry + dispatcher | src/ai_agent/core/tool.py | ToolExecutor |
| Argument validation | src/ai_agent/core/structured.py | validate_json_schema() |
| OpenAI normalization | src/ai_agent/providers/openai.py | _extract_tool_calls() |
| Anthropic normalization | src/ai_agent/providers/anthropic.py | _parse_response() |
| DeepSeek normalization | src/ai_agent/providers/deepseek.py | _parse_tool_calls() |

## Tests（測試）

Core tests cover successful execution, argument validation, unknown tools, handler failures, result serialization, and duplicate Tool registration.

Provider tests cover representative Tool Call normalization for OpenAI, Anthropic, and DeepSeek.

Tests use fake transports and local handlers. No real external API execution is required.

Tests 預期由 learner 在本地執行。

## Design Decisions（設計決策）

### Why normalize Tool Calls at the Provider boundary?

Vendor APIs expose different response shapes. The Agent runtime should operate on one common ToolCall model.

### Why validate arguments in the runtime?

Model output is not application code. Runtime validation creates an explicit safety boundary before arguments reach a Python handler.

### Why return ToolResult instead of raising every Tool failure?

A Tool failure is information the Agent can reason about. A structured error result lets a later Agent Loop decide what to do next.

### Why keep execution synchronous?

This phase focuses on the fundamental execution boundary. Async execution, concurrency, timeout, retry, and cancellation are separate concepts.

## Limitations（限制）

- No full Agent Loop yet.
- Tool Results are not automatically appended to provider-specific conversation formats.
- No timeout or cancellation.
- No retry policy.
- No permission or approval layer.
- No sandboxing.
- JSON Schema validation is intentionally a small subset.
- Streaming Tool Calls are not yet normalized.

## Interview Questions（面試問題）

1. What is the difference between a Tool Call and Tool Execution?
2. Why normalize Tool Calls at the Provider boundary?
3. Why validate model-generated Tool arguments?
4. What happens when the Tool name does not exist?
5. What happens when the Tool handler raises an exception?
6. Why return a ToolResult instead of crashing the runtime?
7. Where would timeout and retry logic live?
8. Where should permission checks happen?
9. How would you support multiple Tool Calls?
10. How would you execute Tools concurrently?
11. How would you prevent unauthorized Tool invocation?
12. How would Tool Results be fed back into the Agent Loop?

## Phase Completion Checklist（完成檢查）

- [ ] ToolCall model implemented.
- [ ] ToolResult model implemented.
- [ ] Provider-specific Tool Calls normalized.
- [ ] Tool lookup implemented.
- [ ] Argument validation implemented.
- [ ] Handler execution implemented.
- [ ] Execution failures converted to ToolResults.
- [ ] Core execution tests added.
- [ ] Provider normalization tests added.
- [ ] Relevant tests pass locally.
- [ ] Design trade-offs reviewed.
- [ ] Limitations understood.
- [ ] English and Traditional Chinese documentation synchronized.
- [ ] Branch diff reviewed before merging.

## Source Map（Source 對應）

```
Provider-specific Tool Call
        ↓
Provider Adapter
        ↓
ToolCall
        ↓
ToolExecutor
        ├── lookup
        ├── validate
        └── execute
        ↓
ToolResult
        ↓
Future Agent Loop
```
