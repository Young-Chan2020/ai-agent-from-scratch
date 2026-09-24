# Phase 05 — Tool Definition

## Learning Objectives

This phase introduces the abstraction that lets an Agent describe external capabilities to an LLM.

- Understand what a Tool is.
- Describe a Tool with a stable name, description, and input schema.
- Understand the difference between Tool definition and Tool execution.
- Understand how Provider adapters translate one common Tool definition into vendor-specific formats.
- Understand why the model chooses a Tool while the Agent runtime executes it.

## Core Concepts

### 1. What is a Tool?

A Tool gives an LLM access to a capability outside the model itself.

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

The LLM does not execute get_weather. It produces a structured request saying that it wants to use the Tool. The Agent runtime decides what happens next.

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

Phase 05 focuses on the first part. Phase 06 will build the second part.

### 3. Why JSON Schema?

A model needs more than a Tool name. It needs to know which arguments it may provide and what their types are.

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

This reuses the JSON Schema concept from Phase 04, but the purpose is different:

```
text
Structured Output
    Schema → shape of model output

Tool Definition
    Schema → shape of Tool arguments
```

### 4. Model Chooses; Runtime Executes

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

The model makes a decision; the runtime owns execution. This boundary becomes important when Phase 06 adds argument validation, exceptions, timeouts, retries, and permissions.

## Practical Examples

### Example 1 — Define a weather Tool

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

The schema describes what the model may ask for. It does not execute anything.

### Example 2 — Put the Tool into ChatRequest

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

Conceptually:

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

### Example 3 — Provider-specific request formats

The common ToolDefinition is provider-independent. Each Provider adapter translates it into its own API format.

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

This is exactly where the Provider abstraction becomes useful: the Agent only creates one common ToolDefinition; the adapters hide vendor-specific details.

### Example 4 — What the model may return

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

This is a Tool Call decision, not the Tool result.

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

Phase 05 stops before execution. The current common ChatResponse does not yet normalize provider-specific tool-call responses; that will be addressed in Phase 06.

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

Core tests cover Tool definition fields, name validation, parameter schema validation, pairing a definition with executable behavior, passing Tools through ChatRequest, and duplicate-name rejection.

Provider tests cover OpenAI function-tool mapping, Anthropic input_schema mapping, and DeepSeek nested function-tool mapping.

Tests use fake transports, so no real API calls are required.

## Design Decisions

### Why separate ToolDefinition from Tool?

The LLM only needs the public contract: name, description, and parameter schema. The runtime also needs executable behavior: a handler. Separating them keeps the provider boundary clean and gives Phase 06 a clear execution boundary.

### Why use JSON Schema?

Phase 04 already established JSON Schema, so reusing it keeps the core mechanism explicit and familiar.

### Why validate tool names in the common layer?

Provider APIs impose naming constraints. Common validation rejects obviously invalid definitions before they reach a provider adapter.

### Why not execute Tools in this phase?

Execution introduces argument validation, exceptions, timeouts, retries, and permissions. Those concerns belong to Phase 06.

## Limitations

- Tool calls are not yet normalized into a provider-independent response model.
- Tool execution is not implemented yet.
- Tool arguments are not yet validated at execution time.
- No timeout, retry, permission, or sandboxing layer exists yet.
- The parameter schema uses the small JSON Schema subset from Phase 04.
- Vendor-specific capabilities can evolve.

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

- [ ] Tool abstraction understood.
- [ ] Tool name and description understood.
- [ ] Tool parameter schema understood.
- [ ] ToolDefinition implemented.
- [ ] Runtime Tool wrapper implemented.
- [ ] ChatRequest can carry Tool definitions.
- [ ] OpenAI tool mapping implemented.
- [ ] Anthropic tool mapping implemented.
- [ ] DeepSeek tool mapping implemented.
- [ ] Relevant tests pass locally.
- [ ] Design trade-offs reviewed.
- [ ] Limitations understood.
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