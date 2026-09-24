# Phase 05 — Tool Definition（工具定義）

## Learning Objectives

這一課開始建立讓 Agent 把「外部能力」描述給 LLM 的 abstraction。

- 理解什麼是 Tool。
- 理解如何用穩定的 name、description 與 input schema 描述 Tool。
- 理解 ChatRequest 如何攜帶目前這次 request 所有可用的 Tool definitions。
- 理解 LLM 如何根據 user message 與 Tool definitions，決定是否使用 Tool、使用哪個 Tool，以及提供什麼 arguments。
- 理解 Tool definition、Tool Call 與 Tool execution 的差異。
- 理解 Provider Adapter 如何把同一個 common Tool definition 轉成不同 vendor 的格式。
- 理解為什麼由 model 選擇 Tool，但由 Agent runtime 負責真正執行。

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

LLM 不會自己執行 `get_weather`。LLM 產生的是「我想使用這個 Tool」的結構化 Tool Call，接下來由 Agent runtime 決定要做什麼。

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

Phase 05 聚焦 Tool Definition，Phase 06 才建立 Tool Execution。

### 3. Request 裡面會放目前可用的 Tools

Tool Calling 最重要的概念之一，就是 Agent 會把「這次 request 可以使用哪些 Tool」一起放進 ChatRequest，送給 LLM。

```
text
ChatRequest
├── messages
│   └── user message
└── tools
    ├── get_weather
    ├── search_web
    └── get_time
```

Agent **不是把 Python function 本身傳給 LLM**，而是把每個 capability 的描述傳給 LLM，包括：

- Tool name
- Tool description
- Tool parameter schema

例如：

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
    tools=[
        get_weather.definition,
        search_web.definition,
        get_time.definition,
    ],
)
```

概念上，LLM 看到的是：

```
text
User:
What's the weather in Los Angeles?

Available tools:
- get_weather(city: string)
- search_web(query: string)
- get_time(timezone: string)
```

接著 LLM 才會根據 user message 與這些 available Tool definitions，決定是否需要 Tool，以及需要哪個 Tool 和什麼 arguments。

### 4. Model 負責選擇，Runtime 負責執行

整個 Tool Calling 的 responsibility boundary 可以理解成：

```
text
User message
     ↓
Agent
     │
     │ ChatRequest:
     │ - messages
     │ - available Tool definitions
     ▼
LLM
     │
     │ 決定：
     │ 1. 要不要 call Tool
     │ 2. 要 call 哪個 Tool(s)
     │ 3. arguments 是什麼
     ▼
Tool Call
     │
     │ name + arguments
     ▼
Agent Runtime
     │
     │ find + validate + execute
     ▼
Tool
     │
     ▼
Tool Result
     │
     ▼
LLM
     │
     ▼
Final Answer
```

也就是：

> **LLM 負責做 Tool Calling decision；Agent runtime 負責真正的 execution。**

這個 boundary 很重要，因為 LLM 不應該直接執行任意 application code。真正執行哪一個 registered Tool、arguments 是否合法、是否允許執行，都應該由 Agent runtime 控制。

到了 Phase 06，還會加入 argument validation、permission、timeout、retry 等 runtime-level concerns。

### 5. 為什麼需要 JSON Schema？

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

這裡最重要的是：`tools` 代表**這一次 LLM request 當下可使用的 capabilities**。Agent 可以在同一個 request 裡提供多個 Tool definitions。

### 例子 3 — Provider 實際送出的內容

Common ToolDefinition 是 provider-independent 的；每個 Provider Adapter 再把它轉成自己的 API format。

OpenAI Responses API：

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

Anthropic：

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

DeepSeek Chat Completions：

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

### 例子 4 — 完整的 Tool Calling 流程

假設 user 問：

```
text
User:
What's the weather in Los Angeles?
```

Agent 會建立一個包含 user message 與 available Tool definition 的 request：

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
    tools=[
        ToolDefinition(
            name="get_weather",
            description="Get the current weather for a city.",
            parameters={
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                },
                "required": ["city"],
            },
        )
    ],
)
```

概念上：

```
text
Request
│
├── User message
│   └── "What's the weather in Los Angeles?"
│
└── Available Tools
    └── get_weather
        ├── description
        └── parameters
            └── city: string
```

LLM 接收到 user message + available Tool definitions 後，會根據這些資訊決定 Tool Calling。

例如：

```
text
Need current weather
        ↓
choose get_weather
        ↓
arguments = {"city": "Los Angeles"}
```

然後 LLM 回傳 Tool Call：

```
json
{
  "name": "get_weather",
  "arguments": {
    "city": "Los Angeles"
  }
}
```

這個 response 的意思是：

> 「請 Agent 執行 `get_weather`，參數是 `city = Los Angeles`。」

注意：**這不是 Tool Result。**

LLM 此時只是提出一個 action request，真正的 function execution 還沒發生。

接下來 Agent runtime 才接手：

```
text
LLM
 ↓
Tool Call
 │
 │ name = get_weather
 │ arguments = {"city": "Los Angeles"}
 ↓
Agent Runtime
 ↓
validate arguments
 ↓
execute get_weather(...)
 ↓
Tool Result
 │
 │ "22°C, Sunny"
 ↓
LLM
 ↓
Final Answer
 │
 │ "It's 22°C and sunny in Los Angeles."
 ↓
User
```

上面的 `"22°C, Sunny"` 與 final answer 只是示意；真正重要的是 protocol：

```
text
LLM
  ↓
「我要用哪個 Tool？參數是什麼？」
  ↓
Agent Runtime
  ↓
「我確認這個 Tool 可以執行」
  ↓
Tool
  ↓
Tool Result
  ↓
LLM
  ↓
Final Answer
```

因此，**Phase 05 的終點是 Tool Call；Phase 06 才負責 Tool Execution。**

### 例子 5 — 同時提供多個 Tools

同一個 request 可以提供很多 Tools：

```
text
Available Tools
├── get_weather(city)
├── search_web(query)
└── get_time(timezone)
```

LLM 可以根據 user message 選擇其中一個 Tool；對支援 multiple tool calls 的 API，也可能一次提出多個 Tool Calls。

但無論一次是一個還是多個，Agent runtime 都應該把每個 Tool Call 視為：

> 「請求執行一個已註冊的 Tool。」

而不是把 LLM 回傳的內容直接當成可執行程式碼。

Phase 05 定義「有哪些 Tool 可以被選擇」；Phase 06 則會實作 Tool Call 如何被 normalize、validate、dispatch，以及如何把 Tool Result 回傳給 LLM。

## Architecture

```
text
User
 │
 │ user message
 ▼
Agent Runtime
 │
 │ ChatRequest
 │ ├── messages
 │ └── available ToolDefinitions
 ▼
Provider
 │
 ├── OpenAI adapter
 ├── Anthropic adapter
 └── DeepSeek adapter
 │
 ▼
LLM
 │
 │ chooses Tool(s)
 ▼
Tool Call
 │
 │ name + arguments
 ▼
Agent Runtime
 │
 │ Phase 06 execution
 ▼
Tool
 │
 ▼
Tool Result
 │
 ▼
LLM
 │
 ▼
Final Answer
```

## Implementation Mapping

| Concept | Source | Implementation |
|---|---|---|
| Provider-independent Tool definition | src/ai_agent/core/tool.py | ToolDefinition |
| Runtime Tool registration object | src/ai_agent/core/tool.py | Tool |
| Tool handler type | src/ai_agent/core/tool.py | ToolHandler |
| Request-level available Tool definitions | src/ai_agent/core/request.py | ChatRequest.tools |
| Duplicate tool-name validation | src/ai_agent/core/request.py | ChatRequest.__post_init__() |
| OpenAI mapping | src/ai_agent/providers/openai.py | _build_payload() |
| Anthropic mapping | src/ai_agent/providers/anthropic.py | _build_payload() |
| DeepSeek mapping | src/ai_agent/providers/deepseek.py | _build_payload() |
| Tool Call normalization and execution | Phase 06 | 尚未實作 |

## Tests

Core tests 涵蓋 Tool definition fields、name validation、parameter schema validation、definition 與 executable behavior 的配對、ChatRequest 傳遞 Tool，以及 duplicate-name rejection。

Provider tests 涵蓋 OpenAI function-tool mapping、Anthropic input_schema mapping，以及 DeepSeek nested function-tool mapping。

Tests 使用 fake transport，因此不需要真正呼叫 API。

## Design Decisions

### 為什麼分開 ToolDefinition 與 Tool？

LLM 只需要 public contract：name、description、parameter schema。Runtime 另外需要 executable behavior：handler。分開之後 Provider boundary 更乾淨，也讓 Phase 06 有明確的 execution boundary。

### 為什麼把 available Tools 放在 ChatRequest？

Tool availability 是 request-specific 的。不同 Agent state、user permission 或 application context，都可能讓當下可使用的 Tools 不同。

因此把 Tool definitions 放在 request 裡，可以讓「這一次 LLM call 可以使用哪些 capability」變得明確。

### 為什麼由 LLM 選擇 Tool，但由 Runtime 執行？

LLM 擅長理解 natural-language intent，並從 Tool descriptions 中選擇適合的 capability。

但真正的 execution 可能會影響 external systems、data 或 application state，因此必須由 Agent runtime 保持控制。

### 為什麼使用 JSON Schema？

Phase 04 已經建立 JSON Schema，因此重用它可以讓核心機制保持明確且一致。

### 為什麼在 common layer 驗證 Tool name？

Provider API 都有命名限制。Common validation 可以在 definition 進入 Provider Adapter 前先拒絕明顯不合法的內容。

### 為什麼這一課不直接執行 Tool？

Execution 會引入 argument validation、exception、timeout、retry、permission 等問題，這些屬於 Phase 06。

## Limitations

- Tool Call 尚未正規化成 provider-independent response model。
- 尚未實作 Tool execution。
- 尚未在 execution time 驗證 Tool arguments。
- 尚未加入 timeout、retry、permission、sandboxing。
- Tool parameter schema 目前使用 Phase 04 的小型 JSON Schema subset。
- Vendor-specific capabilities 可能持續變動。
- Multiple Tool Calls 目前只做概念說明；實際 provider-specific response format 會在 Phase 06 處理。

## Interview Questions

1. Where are available Tools represented in an Agent request?
2. What information should a Tool definition expose to an LLM?
3. How does the LLM decide which Tool to call?
4. What is the difference between a Tool Definition, Tool Call, and Tool Result?
5. Why should the LLM not directly execute a Tool?
6. Why should Tool parameters use a schema?
7. How would you validate Tool arguments before execution?
8. How do OpenAI, Anthropic, and DeepSeek represent function Tools differently?
9. Why should the Agent runtime depend on a provider-independent Tool abstraction?
10. How would you represent a Tool Call in a provider-independent ChatResponse?
11. Where should timeout, retry, and permission checks live?
12. What security problems appear once an LLM can request external actions?

## Phase Completion Checklist

- [ ] Tool abstraction 理解。
- [ ] Tool name and description 理解。
- [ ] Tool parameter schema 理解。
- [ ] ChatRequest can carry currently available Tool definitions.
- [ ] LLM → Tool Call → Runtime → Tool Result flow 理解。
- [ ] ToolDefinition 完成。
- [ ] Runtime Tool wrapper 完成。
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
LLM receives available Tool definitions
        ↓
LLM chooses Tool(s) + arguments
        ↓
Tool Call
        ↓
Phase 06 Tool Execution
        ↓
Tool Result
        ↓
LLM final answer
```
