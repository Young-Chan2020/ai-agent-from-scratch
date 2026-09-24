# Phase 06 — Tool Execution

## Learning Objectives

This phase turns an LLM-generated Tool Call into a controlled runtime action.

- Normalize provider-specific Tool Calls into a common ToolCall.
- Register executable Tools in a runtime executor.
- Find a Tool by name.
- Validate LLM-generated arguments against the Tool parameter schema.
- Execute the Tool handler.
- Convert execution output and failures into a common ToolResult.
- Understand why the runtime, not the LLM, owns execution.

## Core Concepts

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

The model requests an action; the runtime controls whether and how that action actually runs.

### Provider-independent ToolCall

Different providers represent Tool Calls differently. The common layer normalizes them into:

```python
ToolCall(
    id="call-1",
    name="get_weather",
    arguments={"city": "Los Angeles"},
)
```

The Agent runtime no longer needs to know whether the call came from OpenAI, Anthropic, or DeepSeek.

### Tool Execution Flow

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

### Argument Validation

Model-generated arguments are untrusted input.

If a Tool expects:

```
city: string
```

but the model produces:

```json
{"city": 123}
```

the executor rejects the arguments before the handler runs.

This creates an explicit boundary between model output and application code.

### ToolResult Is Not the Final Answer

```
ToolResult
├── tool_call_id
├── name
├── content
└── is_error
```

A ToolResult is normally returned to the Agent/LLM loop. The LLM can then interpret the result and produce the final user-facing answer.

## Practical Examples

### Example 1 — Register a Tool

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

The LLM sees the ToolDefinition. The executor owns the actual Python handler.

### Example 2 — Execute a Tool Call

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

The transformation is:

```
LLM Tool Call
        ↓
ToolExecutor
        ↓
Python handler
        ↓
ToolResult
```

### Example 3 — Invalid Arguments

If the model generates:

```json
{"city": 123}
```

the handler is not called. The executor returns an error ToolResult.

### Example 4 — Handler Failure

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

### Example 5 — End-to-End Flow

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

Phase 06 implements the execution boundary. The full repeated Agent Loop belongs to the later Agent Loop phase.

## Architecture

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

## Implementation Mapping

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

## Tests

Core tests cover successful execution, argument validation, unknown tools, handler failures, result serialization, and duplicate Tool registration.

Provider tests cover representative Tool Call normalization for OpenAI, Anthropic, and DeepSeek.

Tests use fake transports and local handlers. No real external API execution is required.

Tests are intended to be run locally by the learner.

## Design Decisions

### Why normalize Tool Calls at the Provider boundary?

Vendor APIs expose different response shapes. The Agent runtime should operate on one common ToolCall model.

### Why validate arguments in the runtime?

Model output is not application code. Runtime validation creates an explicit safety boundary before arguments reach a Python handler.

### Why return ToolResult instead of raising every Tool failure?

A Tool failure is information the Agent can reason about. A structured error result lets a later Agent Loop decide what to do next.

### Why keep execution synchronous?

This phase focuses on the fundamental execution boundary. Async execution, concurrency, timeout, retry, and cancellation are separate concepts.

## Limitations

- No full Agent Loop yet.
- Tool Results are not automatically appended to provider-specific conversation formats.
- No timeout or cancellation.
- No retry policy.
- No permission or approval layer.
- No sandboxing.
- JSON Schema validation is intentionally a small subset.
- Streaming Tool Calls are not yet normalized.

## Interview Questions

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

## Phase Completion Checklist

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

## Source Map

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
