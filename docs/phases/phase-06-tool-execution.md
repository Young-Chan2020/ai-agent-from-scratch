# Phase 06 — Tool Execution

## Learning Objectives
- Normalize provider-specific Tool Calls into a common ToolCall.
- Register executable Tools in a runtime executor.
- Find a Tool by name.
- Validate LLM-generated arguments before execution.
- Execute the Tool handler and return a ToolResult.
- Keep execution under Agent runtime control.

## Core Concepts

### Tool Call vs Tool Execution
Phase 05 stops at the model's action request:

```
LLM → Tool Call(name + arguments)
```

Phase 06 performs:

```
Tool Call → lookup → validate → execute → ToolResult
```

The model requests an action; the runtime controls whether and how it runs.

### Provider-independent ToolCall
Providers use different response formats. The common layer normalizes them into:

```python
ToolCall(
    id="call-1",
    name="get_weather",
    arguments={"city": "Los Angeles"},
)
```

### Argument Validation
Model-generated arguments are untrusted input. If the schema requires `city: string` but the model returns `{"city": 123}`, the executor rejects the arguments before the Python handler runs.

### ToolResult
A ToolResult contains `tool_call_id`, `name`, `content`, and `is_error`. It is not the final answer; a later Agent Loop can return it to the LLM.

## Practical Example

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

The runtime turns the LLM's Tool Call into a controlled ToolResult.

## Architecture

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
Core tests cover successful execution, invalid arguments, unknown tools, handler failures, result serialization, and duplicate registration. Provider tests cover representative OpenAI, Anthropic, and DeepSeek Tool Call normalization. Tests are intended to be run locally.

## Design Decisions
- Normalize vendor-specific Tool Calls at the Provider boundary.
- Validate arguments before application code executes.
- Return Tool failures as ToolResults so the future Agent Loop can reason about them.
- Keep execution synchronous in this learning phase.

## Limitations
- No full Agent Loop yet.
- No timeout, cancellation, retry, permission, approval, or sandboxing.
- Tool Results are not yet automatically appended to provider-specific conversation formats.
- JSON Schema validation remains a small subset.
- Streaming Tool Calls are not yet normalized.

## Interview Questions
1. What is the difference between Tool Calling and Tool Execution?
2. Why normalize Tool Calls at the Provider boundary?
3. Why validate model-generated arguments?
4. What happens when a Tool name does not exist?
5. What happens when a handler raises an exception?
6. Where should timeout, retry, and permission checks live?
7. How would you support multiple Tool Calls?
8. How would Tool Results be fed back into the Agent Loop?

## Phase Completion Checklist
- [ ] ToolCall and ToolResult implemented.
- [ ] Provider-specific Tool Calls normalized.
- [ ] Tool lookup implemented.
- [ ] Argument validation implemented.
- [ ] Handler execution implemented.
- [ ] Execution failures converted to ToolResults.
- [ ] Core and provider tests added.
- [ ] Relevant tests pass locally.
- [ ] Design trade-offs reviewed.
- [ ] Limitations understood.
- [ ] English and Traditional Chinese docs synchronized.
- [ ] Branch diff reviewed before merging.
