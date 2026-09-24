# Phase 05 — Tool Definition（工具定義）

## Learning Objectives

這一課開始建立讓 Agent 把「外部能力」描述給 LLM 的 abstraction。

- 理解什麼是 Tool。
- 理解如何用穩定的 name、description 與 input schema 描述 Tool。
- 理解 Tool definition 與 Tool execution 的差異。
- 理解 Provider Adapter 如何把同一個 common Tool definition 轉成不同 vendor 的格式。
- 理解為什麼是 model 選擇 Tool，而 Agent runtime 負責執行。

## Core Concepts

### 1. 什麼是 Tool？

Tool 讓 LLM 可以使用模型本身以外的能力。

```
text
get_weather
    ↓
Get the weather for a city.
    ↓
arguments:
{
    "city": "Los Angeles"
}
```

LLM 不會自己執行 get_weather。LLM 產生的是「我想使用這個 Tool」的結構化請求，接下來由 Agent runtime 決定要做什麼。

### 2. Tool Definition vs Tool Execution

```
text
Tool Definition
    ├── name
    ├── description
    ├── parameter schema
    └── strictness

Tool Execution
    ├── find registered tool
    ├── validate arguments
    ├── call handler
    ├── handle errors
    └── return result
```

Phase 05 聚焦前半部分，Phase 06 才建立後半部分。

### 3. 為什麼需要 JSON Schema？

Model 不只需要知道 Tool 叫什麼，也需要知道可以提供哪些 arguments，以及它們的型別。

```
python
{
    "type": "object",
    "properties": {
        "city": {"type": "string"}
    },
    "required": ["city"]
}
```

這裡重用 Phase 04 的 JSON Schema 概念，但目的不同：

```
text
Structured Output
    Schema → model 輸出資料應該長什麼樣子

Tool Definition
    Schema → model 提供給 Tool 的 arguments 應該長什麼樣子
```

### 4. Model 負責選擇，Runtime 負責執行

```
text
LLM
  │
  │ "I want to call get_weather"
  ▼
Agent Runtime
  │
  │ validate + execute
  ▼
Weather Tool
```

Model 做 decision；runtime 擁有 execution。到了 Phase 06 加入 argument validation、exception、timeout、retry、permission 後，這條 boundary 會更重要。

## 實際例子

### 例子 1 — 定義一個 Weather Tool

```
python
weather_tool = ToolDefinition(
    name="get_weather",
    description="Get the current weather for a city.",
    parameters={
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "The city whose weather should be retrieved.",
            }
        },
        "required": ["city"],
    },
)
```

Schema 只描述 model 可以要求什麼，不會執行任何東西。

### 例子 2 — 把 Tool Definition 放進 ChatRequest

```
python
request = ChatRequest(
    messages=[
        Message(
            role="user",
            content="What's the weather in Los Angeles?",
        )
    ],
    config=ModelConfig(model="test-model"),
    tools=[weather_tool],
)
```

概念上：

```
text
ChatRequest
├── messages
│   └── "What's the weather in Los Angeles?"
└── tools
    └── get_weather
        ├── description
        └── parameters
            └── city: string
```

### 例子 3 — Provider 實際送出的內容

Common ToolDefinition 是 provider-independent 的；每個 Provider Adapter 再把它轉成自己的 API format。

OpenAI Responses API:

```
json
{
  "tools": [
    {
      "type": "function",
      "name": "get_weather",
      "description": "Get the current weather for a city.",
      "parameters": {
        "type": "object",
        "properties": {"city": {"type": "string"}},
        "required": ["city"]
      },
      "strict": false
    }
  ]
}
```

Anthropic:

```
json
{
  "tools": [
    {
      "name": "get_weather",
      "description": "Get the current weather for a city.",
      "input_schema": {
        "type": "object",
        "properties": {"city": {"type": "string"}},
        "required": ["city"]
      }
    }
  ]
}
```

DeepSeek Chat Completions:

```
json
{
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get the current weather for a city.",
        "parameters": {
          "type": "object",
          "properties": {"city": {"type": "string"}},
          "required": ["city"]
        },
        "strict": false
      }
    }
  ]
}
```

這正是 Provider abstraction 發揮作用的地方：Agent 只建立一個 common ToolDefinition，vendor-specific details 由 Adapter 隔離。

### 例子 4 — Model 可能回傳什麼

After receiving the Tool definition and the user request, the model may decide to call it:

```
json
{
  "name": "get_weather",
  "arguments": {
    "city": "Los Angeles"
  }
}
```

這是 Tool Call decision，不是 Tool result。

```
text
LLM
 ↓
tool call
 ↓
Agent Runtime
 ↓
validate arguments
 ↓
execute get_weather
 ↓
tool result
 ↓
LLM
```

Phase 05 停在 execution 之前。目前 common ChatResponse 還沒有把不同 Provider 的 tool-call response 正規化；這會在 Phase 06 處理。

## Architecture

```
text
Agent Runtime
      │
      ▼
ToolDefinition
 ┌──────┼──────┐
 ▼      ▼      ▼
name  description schema
      │
      ▼
   Provider
 ┌──────┼──────┐
 ▼      ▼      ▼
OpenAI Anthropic DeepSeek
      │
      ▼
     LLM
      │
      ▼
   Tool Call
      │
      ▼
Phase 06 Execution
```

## Implementation Mapping

| Concept | Source | Implementation |
|---|---|---|
| Provider-independent Tool definition | src/ai_agent/core/tool.py | ToolDefinition |
| Runtime Tool registration object | src/ai_agent/core/tool.py | Tool |
| Tool handler type | src/ai_agent/core/tool.py | ToolHandler |
| Request-level tool definitions | src/ai_agent/core/request.py | ChatRequest.tools |
| Duplicate tool-name validation | src/ai_agent/core/request.py | ChatRequest.__post_init__() |
| OpenAI mapping | src/ai_agent/providers/openai.py | _build_payload() |
| Anthropic mapping | src/ai_agent/providers/anthropic.py | _build_payload() |
| DeepSeek mapping | src/ai_agent/providers/deepseek.py | _build_payload() |

## Tests

Core tests 涵蓋 Tool definition fields、name validation、parameter schema validation、definition 與 executable behavior 的配對、ChatRequest 傳遞 Tool，以及 duplicate-name rejection。

Provider tests 涵蓋 OpenAI function-tool mapping、Anthropic input_schema mapping，以及 DeepSeek nested function-tool mapping。

Tests 使用 fake transport，因此不需要真正呼叫 API。

## Design Decisions

### 為什麼分開 ToolDefinition 與 Tool？

LLM 只需要 public contract：name、description、parameter schema。Runtime 另外需要 executable behavior：handler。分開之後 Provider boundary 更乾淨，也讓 Phase 06 有明確的 execution boundary。

### 為什麼使用 JSON Schema？

Phase 04 已經建立 JSON Schema，因此重用它可以讓核心機制保持明確且一致。

### 為什麼在 common layer 驗證 Tool name？

Provider API 都有命名限制。Common validation 可以在 definition 進入 Provider Adapter 前先拒絕明顯不合法的內容。

### 為什麼這一課不直接執行 Tool？

Execution 會引入 argument validation、exception、timeout、retry、permission 等問題，這些屬於 Phase 06。

## Limitations

- Tool call 尚未正規化成 provider-independent response model。
- 尚未實作 Tool execution。
- 尚未在 execution time 驗證 Tool arguments。
- 尚未加入 timeout、retry、permission、sandboxing。
- Tool parameter schema 目前使用 Phase 04 的小型 JSON Schema subset。
- Vendor-specific capabilities 可能持續變動。

## Interview Questions

1. What information should a Tool definition expose to an LLM?
2. Why should Tool parameters use a schema?
3. What is the difference between Tool definition and Tool execution?
4. Why should the LLM not directly execute a Tool?
5. How would you validate Tool arguments before execution?
6. How do OpenAI, Anthropic, and DeepSeek represent function Tools differently?
7. Why should the Agent runtime depend on a provider-independent Tool abstraction?
8. What security problems appear once an LLM can request external actions?
9. Where should timeout, retry, and permission checks live?
10. How would you represent a Tool Call in a provider-independent ChatResponse?

## Phase Completion Checklist

- [ ] Tool abstraction 理解。
- [ ] Tool name and description 理解。
- [ ] Tool parameter schema 理解。
- [ ] ToolDefinition 完成。
- [ ] Runtime Tool wrapper 完成。
- [ ] ChatRequest can carry Tool definitions.
- [ ] OpenAI tool mapping 完成。
- [ ] Anthropic tool mapping 完成。
- [ ] DeepSeek tool mapping 完成。
- [ ] Relevant tests pass locally.
- [ ] Design trade-offs Review。
- [ ] Limitations 理解。
- [ ] English and Traditional Chinese documentation synchronized.
- [ ] Branch diff reviewed before merging.

## Source Map

```
text
ToolDefinition / Tool
        ↓
src/ai_agent/core/tool.py
        ↓
ChatRequest.tools
        ↓
Provider-specific _build_payload()
        ↓
LLM tool definition
        ↓
Tool call
        ↓
Phase 06 Tool Execution
```