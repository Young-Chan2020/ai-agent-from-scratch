# Phase 05 — Tool Definition

## Learning Objectives

This phase introduces the abstraction that lets an Agent describe external capabilities to an LLM.

- Understand what a Tool is.
- Describe a Tool with a stable name, description, and input schema.
- Understand how a ChatRequest carries all currently available Tool definitions.
- Understand how the LLM chooses whether to use a Tool, which Tool to use, and what arguments to provide.
- Understand the difference between Tool definition, Tool Call, and Tool execution.
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

The LLM does not execute `get_weather`. It produces a structured Tool Call saying that it wants to use the Tool. The Agent runtime decides what happens next.

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

Phase 05 focuses on Tool Definition. Phase 06 will build Tool Execution.

### 3. The Request Carries the Available Tools

A key part of Tool Calling is that the Agent sends the LLM the user message together with the Tool definitions that are currently available.

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

The Agent does not send the Python function implementation to the LLM. It sends a description of each available capability: its name, description, and parameter schema.

For example:

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

Conceptually, the model receives:

```
text
User:
What's the weather in Los Angeles?

Available tools:
- get_weather(city: string)
- search_web(query: string)
- get_time(timezone: string)
```

The model can then decide whether a Tool is needed and, if so, which Tool and arguments to request.

### 4. Model Chooses; Runtime Executes

The complete responsibility boundary is:

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
     │ decides:
     │ 1. whether to call a Tool
     │ 2. which Tool(s) to call
     │ 3. what arguments to provide
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

The model makes the Tool Calling decision. The runtime owns execution.

This distinction is important because the LLM should not directly execute arbitrary application code. The Agent runtime controls which registered Tool is actually invoked and can later enforce argument validation, permissions, timeouts, retries, and other runtime policies.

### 5. Why JSON Schema?

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

The important point is that `tools` represents the set of capabilities available to the model for this request. The Agent can provide multiple Tool definitions at the same time.

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

### Example 4 — End-to-end Tool Calling flow

Suppose the user asks:

```
text
User:
What's the weather in Los Angeles?
```

The Agent sends a request containing the user message and the available Tool definition:

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

Conceptually:

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

The LLM then reasons from the user message and the available Tool definitions. It may decide:

```
text
Need current weather
        ↓
choose get_weather
        ↓
arguments = {"city": "Los Angeles"}
```

The model returns a Tool Call:

```
json
{
  "name": "get_weather",
  "arguments": {
    "city": "Los Angeles"
  }
}
```

This response means:

> "Please execute `get_weather` with `city = Los Angeles`."

It is **not** the Tool result. The LLM is requesting an action from the Agent runtime.

The Agent then takes over:

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

The exact Tool result is only an example; the important protocol is that the runtime executes the requested Tool and returns its result to the LLM, which can then produce the final answer.

### Example 5 — Multiple Tools

The same request can expose several Tools:

```
text
Available Tools
├── get_weather(city)
├── search_web(query)
└── get_time(timezone)
```

The model may choose one Tool, or in APIs that support it, request multiple Tool Calls. The Agent runtime should treat each Tool Call as a request to execute a registered Tool rather than as executable code supplied by the model.

Phase 05 defines the available Tool interface. Phase 06 will implement how these Tool Calls are normalized, validated, dispatched, and returned as Tool results.

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
| Tool Call normalization and execution | Phase 06 | Not implemented yet |

## Tests

Core tests cover Tool definition fields, name validation, parameter schema validation, pairing a definition with executable behavior, passing Tools through ChatRequest, and duplicate-name rejection.

Provider tests cover OpenAI function-tool mapping, Anthropic input_schema mapping, and DeepSeek nested function-tool mapping.

Tests use fake transports, so no real API calls are required.

## Design Decisions

### Why separate ToolDefinition from Tool?

The LLM only needs the public contract: name, description, and parameter schema. The runtime also needs executable behavior: a handler. Separating them keeps the provider boundary clean and gives Phase 06 a clear execution boundary.

### Why put available Tools on ChatRequest?

Tool availability is request-specific. Different Agent states, user permissions, or application contexts may expose different Tools. Putting Tool definitions on the request makes the model's available capabilities explicit for that LLM call.

### Why let the LLM choose the Tool but keep execution in the runtime?

The model is good at interpreting natural-language intent and selecting from described capabilities. The runtime must remain in control of actual execution because execution can affect external systems, data, or application state.

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
- Multiple Tool Calls are described conceptually here; their provider-specific response formats will be handled in Phase 06.

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

- [ ] Tool abstraction understood.
- [ ] Tool name and description understood.
- [ ] Tool parameter schema understood.
- [ ] ChatRequest carries the currently available Tool definitions.
- [ ] LLM → Tool Call → Runtime → Tool Result flow understood.
- [ ] ToolDefinition implemented.
- [ ] Runtime Tool wrapper implemented.
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
