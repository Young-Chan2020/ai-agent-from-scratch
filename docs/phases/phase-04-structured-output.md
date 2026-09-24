# Phase 04 — Structured Output

## Learning Objectives
This phase teaches how an Agent runtime can ask an LLM for machine-readable output and validate that output before using it.

By the end of this phase, we should understand:
- JSON output vs ordinary text generation
- JSON Schema as an application/model contract
- provider-native structured-output features
- local parsing and validation
- why valid JSON is not the same as schema-valid data
- how Provider adapters isolate vendor differences

## Core Concepts

### 1. Structured Output
Normal LLM output is text:
```text
ChatRequest → Provider → ChatResponse(message.content: str)
```
Structured output adds an application-level contract:
```text
ChatRequest → Provider → JSON text → parse + validate → structured data
```
The model response is still text at the API boundary. The runtime turns that text into data that downstream code can safely consume.

### 2. JSON vs JSON Schema
Valid JSON only guarantees syntax. For example, `{"age": "thirty"}` is valid JSON but does not satisfy a schema requiring `age` to be an integer.

This phase therefore separates:
1. JSON parsing
2. Schema validation

### 3. Provider-Native Structured Output
Providers expose different structured-output capabilities. The adapters translate `StructuredOutputConfig` into provider-specific requests:
- OpenAI: JSON Schema through the Responses API `text.format` field.
- DeepSeek: JSON mode through `response_format: {"type": "json_object"}`; our runtime performs schema validation.
- Anthropic: this learning implementation sends the schema as an instruction and relies on our common parser/validator.

The common runtime owns the contract; adapters own provider-specific capability.

### 4. Local Validation
Even when a provider offers structured output, the application should still parse and validate the result before using it.

### 5. Structured Output vs Tool Calling
Structured output asks the model to return data in a format. Tool calling asks the model to choose an external operation and provide arguments for it. They are related but solve different problems.

## Architecture
```text
                    ChatRequest
                         │
                         ▼
                 StructuredOutputConfig
                         │
                         ▼
                      Provider
              ┌──────────┼──────────┐
              ▼          ▼          ▼
           OpenAI     Anthropic   DeepSeek
           JSON       Prompt      JSON Mode
           Schema     Guidance
              └──────────┼──────────┘
                         ▼
                    ChatResponse
                         │
                         ▼
                JSON Parse + Validate
                         │
                         ▼
                  Structured Data
```

## Implementation Mapping
| Concept | Source | Implementation |
|---|---|---|
| Structured output configuration | `src/ai_agent/core/structured.py` | `StructuredOutputConfig` |
| Structured output parsing | `src/ai_agent/core/structured.py` | `parse_structured_output()` |
| Schema validation | `src/ai_agent/core/structured.py` | `_validate_value()` |
| Request-level configuration | `src/ai_agent/core/request.py` | `ChatRequest.structured_output` |
| OpenAI mapping | `src/ai_agent/providers/openai.py` | `_build_payload()` |
| DeepSeek mapping | `src/ai_agent/providers/deepseek.py` | `_build_payload()` |
| Anthropic mapping | `src/ai_agent/providers/anthropic.py` | `_build_payload()` |

## Tests
- `tests/core/test_structured.py::test_parse_structured_output_returns_valid_json_object`
- `tests/core/test_structured.py::test_parse_structured_output_rejects_invalid_json`
- `tests/core/test_structured.py::test_parse_structured_output_rejects_missing_required_field`
- `tests/core/test_structured.py::test_parse_structured_output_rejects_wrong_type`
- `tests/providers/test_openai.py::test_openai_provider_maps_structured_output_to_json_schema`
- `tests/providers/test_deepseek.py::test_deepseek_provider_enables_json_output`
- `tests/providers/test_anthropic.py::test_anthropic_provider_instructs_structured_json_output`

Tests inject fake transports, so no real API calls are required.

## Practical Examples

The following examples show the complete flow from request to response. The important point is that the schema describes the **shape of the response**; it is not the response itself.

### Example 1 — Extract structured data

The application asks the LLM to extract information from a sentence:

```python
ChatRequest(
    messages=[
        Message(
            role="user",
            content="Albert Einstein was born in 1879 and was a physicist.",
        )
    ],
    config=ModelConfig(model="gpt-5"),
    structured_output=StructuredOutputConfig(
        name="person",
        schema={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "birth_year": {"type": "integer"},
                "occupation": {"type": "string"},
            },
            "required": ["name", "birth_year", "occupation"],
        },
    ),
)
```

The response is still carried as text in `ChatResponse.message.content`, but the text is expected to contain data matching the schema:

```json
{
    "name": "Albert Einstein",
    "birth_year": 1879,
    "occupation": "physicist"
}
```

Here, the schema defines **what information the application wants**, while the response contains the actual values.

### Example 2 — Structured output can still contain natural language

Structured output does not mean that every field must be machine-like values. A schema can explicitly provide a string field for a natural-language description:

```python
schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "description": {"type": "string"},
        "birth_year": {"type": "integer"},
    },
    "required": ["name", "description", "birth_year"],
}
```

A corresponding response could be:

```json
{
    "name": "Albert Einstein",
    "description": "Albert Einstein was a famous physicist best known for developing the theory of relativity.",
    "birth_year": 1879
}
```

The natural-language sentence is in the **response**, inside the `description` field. It is not part of the schema itself.

### Example 3 — Structured output for an Agent

Structured output becomes especially useful when the response is consumed by program logic rather than shown directly to a user.

For example, an Agent may ask the LLM to convert a user's request into data for a weather tool:

```python
schema = {
    "type": "object",
    "properties": {
        "city": {"type": "string"},
        "unit": {"type": "string"},
    },
    "required": ["city", "unit"],
}
```

Request:

```text
User: What's the weather in Los Angeles?
```

Response:

```json
{
    "city": "Los Angeles",
    "unit": "celsius"
}
```

The Agent can then consume the parsed data:

```python
weather_tool(city="Los Angeles", unit="celsius")
```

In this case, the structured response is **machine-facing**, not a user-facing answer. This is one reason structured output is an important building block for Agent systems.

### Example 4 — Natural language and structured data together

A schema can also contain both machine-oriented fields and a natural-language answer:

```python
schema = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "temperature": {"type": "number"},
        "rain_probability": {"type": "number"},
        "bring_umbrella": {"type": "boolean"},
    },
    "required": [
        "answer",
        "temperature",
        "rain_probability",
        "bring_umbrella",
    ],
}
```

Response:

```json
{
    "answer": "It looks fairly dry today, so you probably won't need an umbrella.",
    "temperature": 22.5,
    "rain_probability": 10,
    "bring_umbrella": false
}
```

This illustrates an important design idea: **structured output controls the interface between the LLM and the application; it does not remove the LLM's ability to generate natural language.**

## Design Decisions
### Why keep the schema in the common request?
The Agent expresses its intent once. Provider adapters translate that intent into each vendor's API format.

### Why validate locally?
Provider guarantees differ. Local validation gives the runtime one consistent validation boundary.

### Why implement only a small JSON Schema validator?
This is a learning project. The goal is to understand the validation boundary rather than recreate the full JSON Schema specification.

### Why not add Pydantic yet?
A small explicit validator keeps the core mechanism visible. A future experiment can compare this with a mature validation library.

## Limitations
- The validator implements only a small subset of JSON Schema.
- No Pydantic/dataclass-to-schema conversion yet.
- No generic typed model deserialization yet.
- Anthropic uses instruction-based JSON generation in this learning implementation.
- Streaming structured-output reconstruction is not a dedicated abstraction yet.
- Validation failures are errors; automatic repair/retry is deferred to the reliability phase.

## Interview Questions
1. What is the difference between valid JSON and schema-valid JSON?
2. Why do we need local validation if a provider supports structured output?
3. Why should schema handling live partly in the common layer and partly in Provider adapters?
4. What happens when one provider supports JSON Schema and another only supports JSON mode?
5. Why is structured output different from tool calling?
6. How would you convert a Python dataclass or Pydantic model into JSON Schema?
7. What should happen when validation fails?
8. How would structured output interact with streaming?

## Phase Completion Checklist
- [ ] Structured output configuration understood.
- [ ] JSON parsing understood.
- [ ] Schema validation understood.
- [ ] Provider-specific mapping understood.
- [ ] OpenAI mapping implemented.
- [ ] DeepSeek JSON mode implemented.
- [ ] Anthropic instruction-based mapping implemented.
- [ ] Relevant tests pass locally.
- [ ] Design trade-offs reviewed.
- [ ] Limitations understood.
- [ ] English and Traditional Chinese documentation synchronized.
- [ ] Branch diff reviewed before merging.

## Source Map
```text
StructuredOutputConfig / parse_structured_output / _validate_value
        ↓
src/ai_agent/core/structured.py
        ↓
ChatRequest.structured_output
        ↓
Provider-specific _build_payload() methods
```