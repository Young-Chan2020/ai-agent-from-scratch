# Phase 01 — LLM Abstraction

## Learning Objectives

Phase 1 establishes the provider-independent foundation of the Agent runtime.

By the end of this phase, the project should make the following ideas explicit:

1. An Agent should not depend directly on one LLM vendor's SDK or response format.
2. Messages, requests, responses, configuration, usage, and provider errors should have project-level representations.
3. A Provider should expose a small, stable interface to the rest of the Agent system.
4. A deterministic MockProvider should make the runtime testable without a real LLM API.
5. The abstraction should be simple enough that the underlying mechanism remains visible.

The purpose is not to build a production-grade provider framework yet. The purpose is to understand the boundary between the Agent runtime and an LLM provider.

## Core Concepts

### 1. Provider-independent messages

**What:** `Message` represents one conversation message using a small common schema: role, content, optional name, and optional tool-call ID.

**Why:** Different providers expose different SDK objects and payload formats. If those provider-specific objects spread through the Agent codebase, the Agent becomes coupled to one vendor.

**Agent relevance:** Later phases will add tool calls, ReAct, memory, context management, and multi-step execution. Those components need a stable representation of conversation state.

**Implementation:** `src/ai_agent/core/message.py::Message`

### 2. Request and response abstractions

**What:** `ChatRequest` describes an LLM call and `ChatResponse` describes the normalized result.

**Why:** The Agent runtime should reason about an LLM call without knowing whether the underlying implementation uses OpenAI, Anthropic, Gemini, a local model, or a mock.

**Agent relevance:** The Agent loop will eventually call a provider repeatedly. A stable request/response boundary keeps that loop independent from provider-specific SDK details.

**Implementation:**
- `src/ai_agent/core/request.py::ChatRequest`
- `src/ai_agent/core/response.py::ChatResponse`

### 3. Model configuration as data

**What:** `ModelConfig` stores model selection and common generation controls such as temperature and maximum output tokens.

**Why:** Configuration belongs to the request boundary rather than being hard-coded inside a provider implementation.

**Tradeoff:** Not every provider supports exactly the same parameters. This initial model intentionally contains only a small common subset. Provider-specific options can be introduced later without making the first abstraction unnecessarily complicated.

**Implementation:** `src/ai_agent/core/request.py::ModelConfig`

### 4. Provider abstraction with `Protocol`

**What:** `Provider` defines the minimum interface required by an LLM provider: `chat(request) -> ChatResponse`.

**Why:** The Agent should depend on behavior, not on a concrete provider class. Python's `Protocol` gives us structural typing, so a class can satisfy the interface without inheriting from a base class.

**Tradeoff:** A protocol is intentionally small and flexible, but it does not solve every provider concern. Authentication, retries, rate limits, streaming, structured output, and provider-specific capabilities belong to later phases.

**Implementation:** `src/ai_agent/providers/base.py::Provider`

### 5. Mock provider

**What:** `MockProvider` returns a deterministic response and records received requests.

**Why:** Tests for the Agent runtime should not require network access, API keys, money, or nondeterministic model behavior.

**Agent relevance:** Once the Agent loop exists, the mock becomes the controlled environment in which loop behavior can be tested.

**Implementation:** `src/ai_agent/providers/mock.py::MockProvider`

### 6. Unified usage information

**What:** `Usage` represents input, output, and total token counts.

**Why:** Token usage is important for cost analysis, observability, and later optimization. The runtime should not need to understand each provider's raw usage object.

**Implementation:** `src/ai_agent/core/response.py::Usage`

### 7. Provider error boundary

**What:** `ProviderError` is the common provider failure type, with `InvalidRequestError` and `ProviderUnavailableError` as initial categories.

**Why:** Provider-specific exceptions should not leak throughout the Agent runtime. A common error boundary gives later runtime components a stable way to handle provider failures.

**Implementation:** `src/ai_agent/core/errors.py`

## Architecture

The Phase 1 boundary is intentionally small:

```text
Agent Runtime (future)
        |
        v
+-----------------------+
| Provider              |
| chat(ChatRequest)     |
| -> ChatResponse       |
+-----------------------+
        |
        v
+-----------------------+
| Concrete Provider     |
| MockProvider (now)    |
| OpenAI/etc. (later)   |
+-----------------------+
```

The important dependency direction is:

```text
Agent/runtime code
      |
      v
project-level core models + Provider interface
      |
      v
concrete provider implementation
      |
      v
external LLM SDK/API
```

The upper layers should not need to know the concrete provider implementation.

## Implementation Mapping

| Concept | Source | Symbol | Purpose |
|---|---|---|---|
| Message model | `src/ai_agent/core/message.py` | `Message` | Provider-independent conversation message |
| Model configuration | `src/ai_agent/core/request.py` | `ModelConfig` | Common model/generation settings |
| Request model | `src/ai_agent/core/request.py` | `ChatRequest` | Provider-independent chat request |
| Response model | `src/ai_agent/core/response.py` | `ChatResponse` | Provider-independent chat response |
| Usage model | `src/ai_agent/core/response.py` | `Usage` | Normalized token accounting |
| Provider interface | `src/ai_agent/providers/base.py` | `Provider` | Stable LLM boundary |
| Provider errors | `src/ai_agent/core/errors.py` | `ProviderError` and subclasses | Common provider failure boundary |
| Test provider | `src/ai_agent/providers/mock.py` | `MockProvider` | Deterministic provider for tests |

## Tests

The phase includes tests for both the core models and the mock provider.

### Core model tests

`tests/core/test_models.py`

- `test_message_keeps_provider_independent_fields`
- `test_chat_request_requires_a_message`
- `test_chat_request_rejects_invalid_model_config`
- `test_usage_tracks_token_counts`

These tests verify the basic invariants of the provider-independent data model.

### Provider tests

`tests/providers/test_mock.py`

- `test_mock_provider_returns_deterministic_response`
- `test_mock_provider_records_requests`
- `test_mock_provider_matches_provider_protocol`

These tests verify that the concrete mock implementation satisfies the intended provider boundary and behaves deterministically.

**Test execution:** The test suite is intentionally executed by the project owner as part of the learning workflow. Passing test results should be recorded after local execution.

## Design Decisions

### Standard-library dataclasses instead of a larger validation framework

The phase uses `dataclass` because the models are small and the learning goal is to make the data structures visible. Introducing a larger validation framework at this point would add capability, but it would also hide some of the mechanics we are trying to learn.

### `Protocol` instead of an abstract base class

The Provider interface describes required behavior rather than a shared implementation hierarchy. `Protocol` makes that distinction explicit and keeps concrete providers lightweight.

### Mock before real providers

A deterministic provider lets us validate the abstraction itself before introducing network calls, credentials, retries, vendor SDK behavior, and provider-specific differences.

### Small common configuration surface

Only common parameters are included initially. The project deliberately avoids trying to model every feature of every LLM provider in Phase 1.

### Immutable core models

The main data models use `frozen=True`. This makes requests and responses safer to pass between components because their contents cannot be modified accidentally after construction.

## Limitations

Phase 1 is intentionally incomplete.

1. There is no real LLM provider yet.
2. Streaming is not implemented; it is a separate roadmap phase.
3. Structured output is not implemented.
4. Tool/function calling is not implemented.
5. Provider-specific capabilities are not modeled yet.
6. Retry, timeout, rate-limit handling, and circuit-breaking are not implemented.
7. The error hierarchy is only a starting point.
8. Token accounting is represented, but the mock does not calculate real token usage.
9. `ChatRequest` currently models a simple chat completion rather than the richer request surface required by later Agent phases.

These limitations are intentional. They keep the first abstraction small enough to understand before complexity is added.

## Interview Questions

### Q1. Why not call the OpenAI/Anthropic SDK directly from the Agent?

Because that would couple the Agent runtime to a vendor-specific API. A provider abstraction gives the runtime a stable contract and allows providers to be replaced or tested independently.

### Q2. Why do we need `Message` instead of using provider SDK message objects everywhere?

Because provider SDK objects are implementation details. A project-level message model prevents vendor-specific types from leaking into the Agent architecture.

### Q3. Why use `Protocol` instead of inheritance?

The Agent only needs a behavioral contract. Structural typing allows any compatible implementation to satisfy the interface without requiring inheritance from a common concrete base class.

### Q4. Why is `MockProvider` important if it is not a real model?

It provides deterministic behavior. Agent tests should be able to verify runtime logic without network access, credentials, cost, or model nondeterminism.

### Q5. Why normalize `Usage`?

Different providers may report usage differently. A common representation lets later observability and cost-related code consume usage without depending on a specific provider SDK.

### Q6. What should happen when a provider is unavailable?

The provider implementation should translate its low-level failure into the project's provider error boundary. Later runtime phases can then decide whether to retry, stop, fall back, or surface the failure.

### Q7. What is the main tradeoff of this abstraction?

A common interface improves portability and testability, but it can only represent the capabilities shared by providers. If the abstraction becomes too generic, provider-specific features become awkward to expose. The project therefore starts with a deliberately small common surface and will evolve it as later phases introduce streaming, structured output, and tools.

## Phase Completion Checklist

- [x] Understand the purpose of the provider boundary.
- [x] Define provider-independent message/request/response models.
- [x] Define common model configuration.
- [x] Define a Provider interface.
- [x] Implement a deterministic MockProvider.
- [x] Add core model tests.
- [x] Add provider tests.
- [ ] Execute the test suite locally and verify that all tests pass.
- [ ] Review local test results before marking Phase 1 fully complete.

## Source Map

```text
Concept
  -> Architecture
  -> Source
  -> Symbol
  -> Test

Message
  -> Core data model
  -> src/ai_agent/core/message.py
  -> Message
  -> tests/core/test_models.py::test_message_keeps_provider_independent_fields

Request validation
  -> Core request boundary
  -> src/ai_agent/core/request.py
  -> ChatRequest.__post_init__
  -> tests/core/test_models.py::test_chat_request_requires_a_message
  -> tests/core/test_models.py::test_chat_request_rejects_invalid_model_config

Provider abstraction
  -> Provider boundary
  -> src/ai_agent/providers/base.py
  -> Provider.chat()
  -> tests/providers/test_mock.py::test_mock_provider_matches_provider_protocol

Mock provider
  -> Concrete provider implementation
  -> src/ai_agent/providers/mock.py
  -> MockProvider.chat()
  -> tests/providers/test_mock.py::test_mock_provider_returns_deterministic_response
  -> tests/providers/test_mock.py::test_mock_provider_records_requests

Usage
  -> Normalized response metadata
  -> src/ai_agent/core/response.py
  -> Usage
  -> tests/core/test_models.py::test_usage_tracks_token_counts
```
