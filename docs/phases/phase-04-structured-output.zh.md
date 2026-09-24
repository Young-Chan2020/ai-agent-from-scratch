# Phase 04 — Structured Output（結構化輸出）

## Learning Objectives
這一課學習如何讓 Agent runtime 要求 LLM 回傳機器可以直接處理的資料，並在使用資料之前進行驗證。

完成後應理解：
- JSON output 與一般文字生成的差異
- JSON Schema 如何成為 application 與 model 之間的 contract
- Provider 原生 structured-output 功能
- application-side parsing 與 validation
- 為什麼合法 JSON 不等於符合 schema 的資料
- 如何透過 Provider Adapter 隔離不同 Provider 的差異

## Core Concepts

### 1. Structured Output
一般 LLM 輸出是文字：
```text
ChatRequest → Provider → ChatResponse(message.content: str)
```
Structured output 則加入 application-level contract：
```text
ChatRequest → Provider → JSON text → parse + validate → structured data
```
API 邊界上的內容仍然是文字，Agent runtime 必須把它轉換成可以安全使用的資料。

### 2. JSON vs JSON Schema
合法 JSON 只代表語法正確。例如 `{"age": "thirty"}` 是合法 JSON，但如果 schema 要求 `age` 必須是 integer，它仍然不符合 contract。

因此這一課把兩件事分開：
1. JSON parsing
2. Schema validation

### 3. Provider-Native Structured Output
不同 Provider 的 structured-output API 並不完全相同。Adapter 會把共用的 `StructuredOutputConfig` 轉成 Provider-specific request：
- OpenAI：透過 Responses API 的 `text.format` 傳入 JSON Schema。
- DeepSeek：使用 `response_format: {"type": "json_object"}` 開啟 JSON mode，再由 common layer 做 schema validation。
- Anthropic：目前的 learning implementation 將 schema 作為 instruction 傳入，再由 common parser / validator 驗證結果。

common runtime 負責 contract，Adapter 負責 Provider-specific capability。

### 4. Local Validation
即使 Provider 提供 structured-output 功能，application 也不應該完全信任回傳值。Runtime 仍需要 parse response 並驗證資料，再交給後續邏輯。

### 5. Structured Output 不等於 Tool Calling
Structured output 是「請按照這個格式回傳資料」。Tool calling 是「選擇一個 external function，並提供執行它需要的 arguments」。兩者都會把 model output 轉成 machine-actionable data，但解決的是不同問題。

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

Tests 都使用 fake transport，因此不需要真正呼叫 API。

## Design Decisions
### 為什麼 schema 放在 common request？
Agent 只需要表達一次 intent，之後由各 Provider Adapter 把這個 intent 轉換成不同 vendor 的 API 格式。

### 為什麼還要 local validation？
不同 Provider 的 guarantee 與支援能力不同。Local validation 可以建立一致的 validation boundary。

### 為什麼只實作一小部分 JSON Schema？
這是一個 learning project。目標是理解 validation boundary，而不是重新實作完整 JSON Schema specification。

### 為什麼現在還不用 Pydantic？
簡單且明確的 validator 可以直接看到核心機制。之後可以再用成熟 validation library 做比較實驗。

## Limitations
- Validator 目前只實作 JSON Schema 的一小部分。
- 尚未支援 Pydantic/dataclass 自動產生 schema。
- 尚未提供 generic typed model deserialization。
- Anthropic 目前使用 instruction-based JSON generation。
- 尚未建立專門的 streaming structured-output reconstruction abstraction。
- Validation 失敗目前直接報錯；automatic repair/retry 留到 Reliability phase。

## Interview Questions
1. Valid JSON 與 schema-valid JSON 有什麼差異？
2. 如果 Provider 支援 structured output，為什麼 application 還需要 local validation？
3. 為什麼 schema handling 要分布在 common layer 與 Provider Adapter？
4. 一個 Provider 支援 JSON Schema、另一個只支援 JSON mode 時，應該怎麼設計？
5. Structured output 與 tool calling 有什麼不同？
6. 如何把 Python dataclass 或 Pydantic model 轉成 JSON Schema？
7. Structured output validation 失敗時應該怎麼處理？
8. Structured output 如何與 streaming 配合？

## Phase Completion Checklist
- [ ] 理解 structured output configuration。
- [ ] 理解 JSON parsing。
- [ ] 理解 schema validation。
- [ ] 理解 Provider-specific mapping。
- [ ] 完成 OpenAI mapping。
- [ ] 完成 DeepSeek JSON mode mapping。
- [ ] 完成 Anthropic instruction-based mapping。
- [ ] 本地相關 tests 通過。
- [ ] Review design trade-offs。
- [ ] 理解 limitations。
- [ ] 中英文 documentation 同步。
- [ ] Merge 前 review branch diff。

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