# Phase 06 — Tool Execution（工具執行）

## Learning Objectives（學習目標）
- 將不同 Provider 的 Tool Call normalize 成 common ToolCall。
- 在 runtime executor 中註冊可執行的 Tool。
- 根據 name 找到 Tool。
- 在執行前驗證 LLM 產生的 arguments。
- 執行 Tool handler 並回傳 ToolResult。
- 保持真正的 execution 由 Agent runtime 控制。

## 核心概念

### Tool Call vs Tool Execution
Phase 05 停在 model 的 action request：

```
LLM → Tool Call(name + arguments)
```

Phase 06 執行：

```
Tool Call → lookup → validate → execute → ToolResult
```

Model 只提出 action request；真正是否執行、如何執行，由 runtime 控制。

### Provider-independent ToolCall
不同 Provider 的 response format 不同，common layer 將它們 normalize 成：

```python
ToolCall(
    id="call-1",
    name="get_weather",
    arguments={"city": "Los Angeles"},
)
```

### Argument Validation
LLM 產生的 arguments 應視為 untrusted input。如果 schema 要求 `city: string`，但 model 回傳 `{"city": 123}`，executor 會在 Python handler 執行前拒絕。

### ToolResult
ToolResult 包含 `tool_call_id`、`name`、`content` 和 `is_error`。它不是 final answer；後面的 Agent Loop 可以把它送回 LLM。

## 實際例子

```python
weather_tool = Tool(
    definition=ToolDefinition(
        name="get_weather",
        description="Get the current weather for a city.",
        parameters={
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    ),
    handler=lambda city: f"Weather in {city}: 22°C, Sunny",
)

executor = ToolExecutor([weather_tool])

result = executor.execute(
    ToolCall(
        id="call-1",
        name="get_weather",
        arguments={"city": "Los Angeles"},
    )
)
```

Runtime 將 LLM 的 Tool Call 轉成受控制的 ToolResult。

## 架構

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

## Implementation Mapping

| Concept | Source | Implementation |
|---|---|---|
| Tool Call | src/ai_agent/core/response.py | ToolCall |
| Tool Result | src/ai_agent/core/response.py | ToolResult |
| Executable Tool | src/ai_agent/core/tool.py | Tool |
| Registry + dispatcher | src/ai_agent/core/tool.py | ToolExecutor |
| Argument validation | src/ai_agent/core/structured.py | validate_json_schema() |
| OpenAI normalization | src/ai_agent/providers/openai.py | _extract_tool_calls() |
| Anthropic normalization | src/ai_agent/providers/anthropic.py | _parse_response() |
| DeepSeek normalization | src/ai_agent/providers/deepseek.py | _parse_tool_calls() |

## Tests
Core tests 涵蓋成功執行、invalid arguments、unknown tools、handler failure、result serialization 與 duplicate registration。Provider tests 涵蓋 OpenAI、Anthropic、DeepSeek 的代表性 Tool Call normalization。Tests 預期由 learner 在本地執行。

## Design Decisions
- 在 Provider boundary 將 vendor-specific Tool Call normalize 成 common ToolCall。
- 在 application code 執行前驗證 arguments。
- Tool failure 回傳 ToolResult，讓未來 Agent Loop 可以處理。
- 本 phase 使用 synchronous execution，保持核心概念簡單。

## Limitations
- 尚未建立完整 Agent Loop。
- 尚未加入 timeout、cancellation、retry、permission、approval 或 sandboxing。
- Tool Result 尚未自動加入 provider-specific conversation format。
- JSON Schema validator 仍是小型 subset。
- Streaming Tool Call 尚未 normalize。

## Interview Questions
1. Tool Calling 和 Tool Execution 有什麼差別？
2. 為什麼要在 Provider boundary normalize Tool Call？
3. 為什麼要驗證 LLM 產生的 arguments？
4. Tool name 不存在時怎麼處理？
5. Handler 發生 exception 時怎麼處理？
6. Timeout、retry、permission 應該放在哪一層？
7. 如何支援 multiple Tool Calls？
8. 如何把 Tool Result 送回 Agent Loop？

## Phase Completion Checklist
- [ ] ToolCall / ToolResult 完成。
- [ ] Provider-specific Tool Calls normalized。
- [ ] Tool lookup 完成。
- [ ] Argument validation 完成。
- [ ] Handler execution 完成。
- [ ] Execution failures 轉成 ToolResult。
- [ ] Core / provider tests 完成。
- [ ] Relevant tests pass locally.
- [ ] Design trade-offs reviewed.
- [ ] Limitations understood.
- [ ] English / Traditional Chinese docs synchronized.
- [ ] Branch diff reviewed before merging.
