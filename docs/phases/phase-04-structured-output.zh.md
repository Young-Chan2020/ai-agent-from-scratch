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

## 實際例子

下面幾個例子把完整的 Request → Response 流程放在一起。最重要的是：**schema 描述的是 response 應該長什麼樣子；schema 本身不是 response。**

### 例子 1 — 把資訊抽成結構化資料

Application 要求 LLM 從一句話中抽取人物資訊：

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

Response 在 `ChatResponse.message.content` 裡仍然是文字，但這段文字應該包含符合 schema 的資料：

```json
{
    "name": "Albert Einstein",
    "birth_year": 1879,
    "occupation": "physicist"
}
```

這裡可以清楚看到：schema 定義的是 **application 想要哪些資訊**，response 才包含真正的值。

### 例子 2 — Structured Output 裡面仍然可以有「人話」

Structured Output 並不代表每個欄位都必須是純機器資料。我們可以在 schema 裡明確提供一個自然語言描述欄位：

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

對應的 response 可以是：

```json
{
    "name": "Albert Einstein",
    "description": "Albert Einstein was a famous physicist best known for developing the theory of relativity.",
    "birth_year": 1879
}
```

這裡真正的自然語言句子是在 **response 的 `description` 欄位**裡，而不是放在 schema 本身。

### 例子 3 — Agent 使用 Structured Output

當 response 不是直接給 user 看，而是交給程式邏輯處理時，Structured Output 就特別有用。

例如 Agent 可以要求 LLM 把 user 的需求轉成 Weather Tool 可以使用的資料：

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

Request：

```text
User: What's the weather in Los Angeles?
```

Response：

```json
{
    "city": "Los Angeles",
    "unit": "celsius"
}
```

Agent 接著可以使用解析後的資料：

```python
weather_tool(city="Los Angeles", unit="celsius")
```

這個例子裡，structured response 是 **給 machine / Agent runtime 使用的**，不是直接給 user 閱讀。這也是 Structured Output 為什麼會成為 Agent 系統重要基礎能力的原因之一。

### 例子 4 — 人話與結構化資料同時存在

Schema 也可以同時包含 machine-oriented fields 和自然語言回答：

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

Response：

```json
{
    "answer": "It looks fairly dry today, so you probably won't need an umbrella.",
    "temperature": 22.5,
    "rain_probability": 10,
    "bring_umbrella": false
}
```

這裡可以看到一個很重要的設計概念：**Structured Output 控制的是 LLM 與 application 之間的 interface，而不是把 LLM 的自然語言能力拿掉。**

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