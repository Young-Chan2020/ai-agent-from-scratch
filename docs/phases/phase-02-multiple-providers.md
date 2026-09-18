# Phase 02 — Multiple LLM Providers

## Learning Objectives

This phase extends the provider abstraction from Phase 01 into multiple concrete LLM providers.

By the end of this phase, we should understand:

- why a common Provider interface is useful
- how provider APIs differ even when the application-level request looks similar
- how a provider adapter translates common requests into provider-specific payloads
- how provider-specific responses are normalized into one common response type
- why some configuration cannot be mapped one-to-one between providers
- how to test provider integrations without making real network requests

---

## Core Concepts

### 1. Provider Adapter

A Provider Adapter implements the common Provider.chat() interface while translating requests and responses for one specific API.

The Agent-facing interface stays small:

~~~text
ChatRequest → Provider → ChatResponse
~~~

The provider-specific details stay behind the adapter.

### 2. Provider Differences Are Real

OpenAI, Anthropic, and DeepSeek do not expose identical APIs.

This phase uses:

- OpenAI Responses API
- Anthropic Messages API
- DeepSeek Chat Completions API

For example, OpenAI uses an input structure and reports output_text / usage fields, while Anthropic uses messages, a separate system field, content blocks, and a different usage shape. DeepSeek uses an OpenAI-compatible Chat Completions format with its own endpoint and usage fields.

The abstraction therefore does not try to pretend that all providers are identical.

Instead, it defines the small common contract that the rest of the Agent runtime actually needs.

### 3. Request Translation

A provider adapter converts:

~~~text
Common ChatRequest
      ↓
Provider-specific payload
      ↓
Provider API
~~~

For example, ModelConfig.max_tokens becomes OpenAI's max_output_tokens, while Anthropic receives max_tokens.

### 4. Response Normalization

The provider-specific response is converted into:

~~~text
ChatResponse
 ├── Message
 ├── finish_reason
 ├── Usage
 └── raw
~~~

The raw field deliberately keeps the original response available for debugging and future provider-specific features.

### 5. Provider-Specific Limitations

A common interface does not mean every provider supports every option.

This phase intentionally demonstrates that limitation:

- Anthropic's current API has provider/model-specific restrictions around temperature.
- Tool messages are not mapped yet because tool calling is a later roadmap phase.

Instead of silently dropping unsupported behavior, the adapters raise InvalidRequestError when this phase cannot safely translate a request.

### 6. Testable Network Boundary

Real provider APIs should not be required for normal unit tests.

The provider adapters accept an injected HttpTransport callable. Tests can therefore inspect:

- endpoint
- authentication headers
- provider-specific request payload
- response parsing

without making network calls or consuming API credits.

---

## Architecture

The Phase 01 architecture:

~~~text
Agent
  ↓
Provider
  ↓
MockProvider
~~~

becomes:

~~~text
                         Provider
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
        MockProvider   OpenAIProvider  AnthropicProvider  DeepSeekProvider
                            │             │                  │
                            ▼             ▼                  ▼
                     Responses API   Messages API   Chat Completions API
~~~

The common contract remains:

~~~text
Provider.chat(ChatRequest) -> ChatResponse
~~~

The provider adapters own API-specific translation.

---

## Implementation Mapping

| Concept | Source | Implementation |
|---|---|---|
| Common provider contract | src/ai_agent/providers/base.py | Provider.chat() |
| Shared HTTP transport | src/ai_agent/providers/http.py | send_json() |
| OpenAI request translation | src/ai_agent/providers/openai.py | OpenAIProvider._build_payload() |
| OpenAI response normalization | src/ai_agent/providers/openai.py | OpenAIProvider._parse_response() |
| Anthropic request translation | src/ai_agent/providers/anthropic.py | AnthropicProvider.chat() |
| Anthropic system-message mapping | src/ai_agent/providers/anthropic.py | AnthropicProvider._split_system_messages() |
| Anthropic response normalization | src/ai_agent/providers/anthropic.py | AnthropicProvider._parse_response() |
| DeepSeek request translation | src/ai_agent/providers/deepseek.py | DeepSeekProvider._build_payload() |
| DeepSeek response normalization | src/ai_agent/providers/deepseek.py | DeepSeekProvider._parse_response() |
| Common response | src/ai_agent/core/response.py | ChatResponse, Usage |
| Normalized provider errors | src/ai_agent/core/errors.py | InvalidRequestError, ProviderUnavailableError |

---

## Tests

Provider tests use a fake transport rather than real APIs.

### OpenAI

~~~text
tests/providers/test_openai.py::test_openai_provider_builds_provider_specific_request
tests/providers/test_openai.py::test_openai_provider_matches_provider_protocol
~~~

These tests verify that the OpenAI adapter:

- uses the expected endpoint
- sends the API key in the expected header
- translates model configuration
- normalizes the response
- still satisfies the common Provider protocol

### DeepSeek

~~~text
tests/providers/test_deepseek.py::test_deepseek_provider_builds_provider_specific_request
tests/providers/test_deepseek.py::test_deepseek_provider_matches_provider_protocol
~~~

These tests verify that the DeepSeek adapter:

- uses the expected Chat Completions endpoint
- sends the API key in the expected header
- maps the common message and model configuration
- normalizes DeepSeek usage fields
- satisfies the common Provider protocol

### Anthropic

~~~text
tests/providers/test_anthropic.py::test_anthropic_provider_separates_system_prompt
tests/providers/test_anthropic.py::test_anthropic_provider_rejects_unmapped_temperature
tests/providers/test_anthropic.py::test_anthropic_provider_matches_provider_protocol
~~~

These tests verify that the Anthropic adapter:

- moves system messages into Anthropic's system field
- maps the common message list
- normalizes usage
- explicitly rejects an unsupported configuration mapping
- satisfies the common Provider protocol

---

## Design Decisions

### Why two concrete providers?

One provider does not demonstrate why an abstraction is useful.

Using OpenAI and Anthropic makes the translation boundary visible.

### Why use direct HTTP instead of provider SDKs?

The learning objective is the provider boundary itself.

Using the SDKs would be reasonable in a production application, but direct HTTP keeps the request/response transformation visible and avoids making the SDK the abstraction we are trying to understand.

This is a learning-oriented choice, not a claim that SDKs are undesirable in production.

### Why inject the transport?

The network is an external dependency.

Injecting the transport lets unit tests exercise request construction and response parsing deterministically.

### Why keep raw?

Provider-specific metadata will matter later for debugging, observability, tool calls, and advanced features.

The common response therefore normalizes what the runtime needs while preserving the original response for inspection.

---

## Limitations

This phase intentionally does not implement:

- streaming
- tool calls
- structured output
- provider retries
- rate-limit handling beyond basic HTTP error normalization
- async HTTP
- automatic provider selection
- provider-specific advanced parameters
- multimodal content

These topics belong to later phases or can be introduced when they become necessary.

Tool messages are explicitly rejected for now because tool execution is not implemented until Phase 05/06.

---

## Interview Questions

### Architecture

1. Why should an Agent depend on a Provider interface instead of an OpenAI client directly?
2. What problem does a provider adapter solve?
3. What belongs in the common abstraction, and what should remain provider-specific?
4. Does supporting multiple providers mean their APIs must have identical capabilities?

### Trade-offs

5. Why can a common abstraction become too leaky?
6. What happens when Provider A supports a feature that Provider B does not?
7. When would you use an official provider SDK instead of direct HTTP?
8. Why is preserving the raw provider response useful?

### Reliability and Testing

9. How would you test an LLM provider without making real API calls?
10. Where should provider errors be normalized?
11. What should happen when a provider returns malformed JSON or an unexpected response shape?
12. How would you add retries without coupling the Agent to a specific provider?

---

## Phase Completion Checklist

- [ ] The concepts in Phase 02 are understood.
- [ ] OpenAI and Anthropic adapters are implemented.
- [ ] Provider-specific request translation is explicit.
- [ ] Provider-specific response parsing is normalized.
- [ ] Network calls can be replaced by a test transport.
- [ ] Relevant tests pass locally.
- [ ] Design trade-offs have been reviewed.
- [ ] Limitations are understood.
- [ ] English and Traditional Chinese documentation are synchronized.
- [ ] The branch diff has been reviewed before merging.

---

## Source Map

~~~text
Provider Abstraction
      ↓
src/ai_agent/providers/base.py
      ↓
Provider.chat()

OpenAI Translation
      ↓
src/ai_agent/providers/openai.py
      ↓
OpenAIProvider._build_payload()
OpenAIProvider._parse_response()
      ↓
tests/providers/test_openai.py

DeepSeek Translation
      ↓
src/ai_agent/providers/deepseek.py
      ↓
DeepSeekProvider._build_payload()
DeepSeekProvider._parse_response()
      ↓
tests/providers/test_deepseek.py

Anthropic Translation
      ↓
src/ai_agent/providers/anthropic.py
      ↓
AnthropicProvider._split_system_messages()
AnthropicProvider._parse_response()
      ↓
tests/providers/test_anthropic.py

Network Boundary
      ↓
src/ai_agent/providers/http.py
      ↓
send_json()
~~~
