# Phase 03 — Streaming

## Learning Objectives

This phase adds incremental LLM output to the common Provider abstraction.

By the end of this phase, we should understand:
- why ChatResponse and ChatChunk are different
- how Iterator / Generator models incremental output
- how SSE transports streaming events
- how provider-specific events are normalized
- how completion metadata and usage can arrive separately
- how to test streaming without real network requests

## Core Concepts

### 1. ChatResponse vs ChatChunk

Phase 02 uses:
~~~text
ChatRequest → Provider.chat() → ChatResponse
~~~
ChatResponse represents a completed result. Streaming uses:
~~~text
ChatRequest → Provider.stream() → Iterator[ChatChunk]
~~~
ChatChunk represents partial text or completion metadata.

### 2. Iterator and Generator

Provider.stream() returns an iterator, so callers can consume output incrementally:
~~~python
for chunk in provider.stream(request):
    print(chunk.content, end="")
~~~

### 3. SSE Transport

The shared HTTP layer handles the basic Server-Sent Events framing:
~~~text
data: {...}
data: {...}
data: [DONE]
~~~
The transport parses HTTP/SSE framing. Provider adapters interpret the provider-specific event schema.

### 4. Provider-specific Event Mapping

OpenAI Responses API uses events such as response.output_text.delta and response.completed.
Anthropic Messages API uses content_block_delta and message_delta.
DeepSeek Chat Completions uses choices[].delta.content and a final usage event when requested.

All are normalized into ChatChunk.

### 5. Streaming Does Not Remove Provider Differences

The common interface hides differences; it does not make providers identical. Each adapter remains responsible for event-specific parsing and metadata handling.

## Architecture

~~~text
                         Provider
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
               chat()               stream()
                 │                     │
                 ▼                     ▼
           ChatResponse        Iterator[ChatChunk]
                                       │
                              Provider event parser
                                       │
                              SSE StreamTransport
~~~

## Implementation Mapping

| Concept | Source | Implementation |
|---|---|---|
| Streaming result model | src/ai_agent/core/response.py | ChatChunk |
| Common streaming contract | src/ai_agent/providers/base.py | Provider.stream() |
| SSE transport | src/ai_agent/providers/http.py | send_sse_json() |
| Streaming transport type | src/ai_agent/providers/http.py | StreamTransport |
| Mock streaming | src/ai_agent/providers/mock.py | MockProvider.stream() |
| OpenAI streaming | src/ai_agent/providers/openai.py | OpenAIProvider.stream() |
| OpenAI event normalization | src/ai_agent/providers/openai.py | _parse_stream_event() |
| Anthropic streaming | src/ai_agent/providers/anthropic.py | AnthropicProvider.stream() |
| Anthropic event normalization | src/ai_agent/providers/anthropic.py | _parse_stream_event() |
| DeepSeek streaming | src/ai_agent/providers/deepseek.py | DeepSeekProvider.stream() |
| DeepSeek event normalization | src/ai_agent/providers/deepseek.py | _parse_stream_event() |

## Tests

Tests use injected stream transports rather than real network connections.

Core model tests verify ChatChunk can represent partial text and completion metadata.
Mock tests verify incremental output and the final finish reason.
Provider tests verify that OpenAI, Anthropic, and DeepSeek streaming events become common ChatChunk objects and preserve usage when available.

## Design Decisions

### Why Iterator[ChatChunk]?

Streaming is sequential data flow. An iterator lets callers consume pieces without waiting for the complete response.

### Why a separate ChatChunk?

A chunk represents partial output; ChatResponse represents a completed call. Separate types make the lifecycle explicit.

### Why keep SSE parsing in the HTTP layer?

SSE is transport/framing. Provider event schemas are adapter concerns. Keeping them separate avoids duplicating HTTP stream handling.

### Why inject StreamTransport?

Network access is an external dependency. Injecting the transport makes streaming tests deterministic and independent of API keys and latency.

### Why preserve raw?

Raw provider events may contain metadata that the common model does not expose yet. Keeping them supports debugging and future features.

## Limitations

- The SSE parser implements only the basic data: event format needed here.
- No advanced SSE reconnect, event IDs, heartbeat handling, or multi-line data aggregation.
- No streaming cancellation abstraction.
- No async streaming.
- No tool-call streaming.
- Agent orchestration does not consume streaming yet.
- No streaming retry or backpressure policy.

## Interview Questions

1. Why should streaming return an iterator instead of a normal response?
2. What is the difference between ChatResponse and ChatChunk?
3. Where should SSE parsing live?
4. How do you normalize different provider event schemas?
5. Why can streaming improve perceived latency?
6. What happens if the connection fails after several chunks?
7. How would cancellation work?
8. How would async streaming change the interface?
9. Where should usage be collected when providers report it differently?
10. What information should remain provider-specific?

## Phase Completion Checklist

- [ ] ChatChunk is understood.
- [ ] Provider.stream() is implemented.
- [ ] Mock streaming is implemented.
- [ ] Shared SSE transport is implemented.
- [ ] OpenAI streaming is implemented.
- [ ] Anthropic streaming is implemented.
- [ ] DeepSeek streaming is implemented.
- [ ] Relevant tests pass locally.
- [ ] Design trade-offs have been reviewed.
- [ ] Limitations are understood.
- [ ] English and Traditional Chinese documentation are synchronized.
- [ ] The branch diff has been reviewed before merging.


## Source Map

~~~text
Streaming Model
      ↓
src/ai_agent/core/response.py
      ↓
ChatChunk
      ↓
tests/core/test_models.py

Provider Contract
      ↓
src/ai_agent/providers/base.py
      ↓
Provider.stream()

SSE Transport
      ↓
src/ai_agent/providers/http.py
      ↓
send_sse_json()

Provider Event Mapping
      ↓
OpenAIProvider._parse_stream_event()
AnthropicProvider._parse_stream_event()
DeepSeekProvider._parse_stream_event()
~~~