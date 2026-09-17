# AI Agent From Scratch

> 一個從零開始學習、設計與實作 AI Agent 系統的專案。

## 1. 專案目標

本專案旨在從基礎開始學習 **AI Agent Engineering**。

目標不是單純使用現有的 Agent Framework，而是理解一個 Agent 系統底層發生了什麼，並逐步自行實作其中的主要元件。

完成這個專案後，希望具備以下能力：

- 設計 AI Agent 架構
- 建立與模型供應商無關的 LLM Interface
- 實作 Tool Calling 與 Tool Execution
- 理解並實作 Agent Loop
- 理解 ReAct 以及其他 Agentic Patterns
- 管理 Context 與 Memory
- 建立可靠且可觀測的 Agent 系統
- 理解 MCP 與外部工具整合
- 設計 Multi-Agent 系統
- 評估並改善 Agent 行為
- 能夠在技術面試中討論 Agent 架構與工程取捨

本專案應該從內到外保持可理解性：**每一個主要 abstraction 都應該存在，是因為我們理解它所要解決的問題。**

---

# 2. 學習理念

本專案遵循一個簡單原則：

> **理解 → 設計 → 實作 → 測試 → 分析**

我們不從現有的 Agent Framework 開始，而是逐步從較底層的元件建立整個系統。

實作過程應優先考慮：

- 清晰的架構
- 明確的抽象
- 小型且可測試的元件
- Provider Independence
- Failure Handling
- Observability
- Engineering Trade-offs

本專案的目的不是重新實作所有現有 Agent Framework 的功能。

真正的目的，是理解：

> **為什麼這些 Framework 需要這些功能。**

---

# 3. 整體架構

專案最終會逐步演進成一個分層的 Agent Runtime：

```text
                    User / Application
                           │
                           ▼
                    Agent Runtime
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
          Planning      Agent Loop      Memory
             │             │             │
             └─────────────┼─────────────┘
                           │
                           ▼
                    Tool / Action Layer
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
           Tools          MCP        External APIs
                           │
                           ▼
                    Provider Layer
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
          Provider A    Provider B    Local Model
```

這個架構會隨著專案發展逐步演進。

---

# 4. 學習 Roadmap

## Phase 0 — 專案基礎

建立專案結構、開發環境、測試策略、文件以及基本工程規範。

目標是在開始實作 Agent 能力之前，先建立乾淨且可維護的基礎。

---

## Phase 1 — LLM Abstraction

建立與 Provider 無關的 Language Model Interface。

學習內容包括：

- Messages
- Requests / Responses
- Model Configuration
- Provider Abstraction
- Error Handling
- Usage Information
- Mock Provider

目標是理解不同模型供應商如何透過共同的 Interface 被抽象化。

---

## Phase 2 — Multiple LLM Providers

在相同的抽象之下實作多個 Provider。

可能包含：

- OpenAI
- Anthropic
- Google Gemini
- Local Models

重點不是支援所有 Provider。

而是理解不同 Provider 之間的差異，以及如何設計一個合理的 Abstraction 來隱藏不必要的 Provider-specific details。

---

## Phase 3 — Streaming

加入模型輸出的 Streaming 能力。

學習內容包括：

- Streaming Events
- Incremental Text Generation
- Partial Responses
- Tool-call Streaming
- Stream Reconstruction
- Streaming Error Handling

目標是理解即時 LLM Interaction 在 Runtime 層面的運作方式。

---

## Phase 4 — Structured Output

加入 Structured Model Response。

學習內容包括：

- JSON Output
- Schemas
- Validation
- Typed Responses
- Structured Generation
- Invalid Output Handling

目標是理解 Agent Runtime 如何安全地處理 Machine-readable Model Output。

---

# 5. Tool System

## Phase 5 — Tool Definition

設計通用的 Tool Abstraction。

一個 Tool 應該描述：

- 名稱
- 用途
- Input Schema
- Output
- Execution Behavior

初期可以實作：

- Calculator
- File Operations
- Search
- Simple API Calls

重點是理解 LLM 如何與外部能力互動。

---

## Phase 6 — Tool Execution

建立 Agent 與 Tool 之間的 Execution Layer。

學習內容包括：

- Tool Selection
- Argument Validation
- Execution
- Results
- Exceptions
- Timeout
- Retry
- Permission Checks

目標是將：

> **Model Decision**

與：

> **Actual Tool Execution**

清楚分離。

---

# 6. Agent Core

## Phase 7 — Agent Loop

建立最基本的 Agent Execution Loop。

Agent 應該能夠：

```text
User Request
     ↓
LLM
     ↓
Decision
     ↓
Tool Call
     ↓
Tool Execution
     ↓
Observation
     ↓
LLM
     ↓
...
     ↓
Final Answer
```

這個階段開始，專案才真正從 LLM Wrapper 變成 Agent Runtime。

---

## Phase 8 — ReAct

學習並實作 ReAct-style Agent Pattern。

核心概念：

```text
Reason
  ↓
Act
  ↓
Observe
  ↓
Reason
  ↓
Act
  ↓
Observe
  ↓
...
```

目標是理解：

- 為什麼 Agent Loop 可以運作
- Reasoning 與 Action 如何互動
- Observation 如何影響後續決策
- Agent Loop 如何終止
- Tool Failure 如何處理
- 如何避免 Infinite Loop

ReAct 會被視為一種 Agentic Pattern，而不是所有 Agent 的定義。

---

# 7. Agentic Patterns

理解基本 Agent Loop 之後，開始實作與比較不同的 Agent Patterns。

## Phase 9 — Planning

研究在執行之前先建立計畫的 Agent。

```text
Goal
 ↓
Plan
 ↓
Tasks
 ↓
Execution
 ↓
Result
```

---

## Phase 10 — Routing

研究如何在不同 Model、Tool 或 Specialized Agent 之間進行動態 Routing。

```text
User Request
     ↓
   Router
  /   |   \
 A    B    C
```

重點包括：

- Task Classification
- Model Selection
- Cost
- Latency
- Specialization

---

## Phase 11 — Reflection

研究 Self-evaluation 與 Iterative Improvement。

```text
Generate
   ↓
Evaluate
   ↓
Improve
   ↓
Final
```

目標是理解 Reflection 什麼時候能提高可靠性，以及什麼時候只會增加 Cost 與 Latency。

---

## Phase 12 — Parallelization

研究如何並行執行彼此獨立的 Task。

```text
             Task
          /    |    \
         A     B     C
          \    |    /
            Combine
```

這個階段會開始接觸：

- Async Execution
- Concurrency
- Task Coordination
- Failure Isolation
- Result Aggregation

---

## Phase 13 — Workflow vs Agent

理解以下三者之間的差異：

- Deterministic Workflows
- LLM-driven Agents
- Hybrid Systems

一個重要原則是：

> **當需要動態決策時使用 Agent；當行為可以被明確定義時，優先使用 Deterministic Code。**

---

# 8. Memory 與 Context

## Phase 14 — Context Management

學習 Agent 如何管理提供給 Model 的資訊。

內容包括：

- Context Windows
- Token Budgets
- Conversation History
- Summarization
- Context Selection
- Tool-result Management
- Context Compression

---

## Phase 15 — Memory

研究不同形式的 Agent Memory。

可能包含：

- Short-term Memory
- Long-term Memory
- Semantic Memory
- Episodic Memory
- Working Memory

目標是理解：

> Memory 與單純儲存 Conversation History 並不是同一件事。

---

# 9. MCP 與外部系統

## Phase 16 — MCP

學習並實作 Model Context Protocol 的整合。

目標是理解標準化 Protocol 如何將 Agent 與外部 Tools / Systems 連接起來。

可能整合：

- Files
- Databases
- APIs
- Development Tools
- External Services

MCP 應被理解為一種 Integration Protocol，而不是 Agent 本身。

---

# 10. Multi-Agent Systems

## Phase 17 — Multi-Agent Architecture

研究多個 Specialized Agents 協作的系統。

可能的架構：

```text
                  Supervisor
                 /     |     \
                /      |      \
        Researcher   Coder   Reviewer
                \      |      /
                 \     |     /
                    Result
```

學習內容包括：

- Agent Specialization
- Delegation
- Coordination
- Supervisor Patterns
- Agent Communication
- Shared Context
- Failure Handling

這個階段應該放在 Single-Agent 系統理解之後。

---

# 11. Reliability 與 Production Engineering

## Phase 18 — Reliability

建立可靠的 Agent Execution 機制。

內容包括：

- Retry
- Timeout
- Rate Limits
- Circuit Breaking
- Error Recovery
- Maximum Iterations
- Tool Failures
- Provider Failures

目標是讓 Agent 從 Prototype 逐漸走向 Reliable Runtime。

---

## Phase 19 — Guardrails 與 Human-in-the-Loop

研究 Agent 的安全與控制機制。

內容包括：

- Permissions
- Tool Restrictions
- Approval Workflows
- Sensitive Operations
- Human Confirmation
- Execution Policies

例如：

```text
Agent
 ↓
Dangerous Action
 ↓
Human Approval
 ↓
Execute
```

---

## Phase 20 — Observability

建立 Agent Execution 的可觀測性。

最終一個 Agent Run 應該可以被追蹤：

```text
Agent Run
 ├── LLM Call
 ├── Tool Call
 ├── Tool Result
 ├── LLM Call
 ├── Retry
 ├── Reflection
 └── Final Result
```

可能追蹤的 Metrics 包括：

- Latency
- Token Usage
- Cost
- Tool Calls
- Errors
- Retries
- Execution Steps

---

# 12. Evaluation

## Phase 21 — Agent Evaluation

建立系統化評估 Agent 行為的方法。

可能的 Metrics 包括：

- Task Completion
- Tool Selection
- Answer Correctness
- Reliability
- Latency
- Token Usage
- Cost
- Failure Rate

最終希望能回答：

> **修改 Agent 之後，它真的變好了嗎？**

而不是只依靠人工 Demo 判斷。

---

# 13. Security

## Phase 22 — Agent Security

研究 Agent 系統特有的 Security 問題。

可能包括：

- Prompt Injection
- Tool Abuse
- Excessive Permissions
- Untrusted Tool Output
- Sensitive Data Exposure
- Sandboxing
- Tool Authorization
- Resource Limits

核心概念是：

> 當我們給 LLM Tools 時，也同時給了它影響外部系統的能力。

因此 Tool Permission 與 Execution Boundary 會變得非常重要。

---

# 14. Final Agent Runtime

## Phase 23 — Production-Oriented Runtime

整合整個專案中建立的主要元件：

```text
                 Application
                      │
                      ▼
                Agent Runtime
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
    Planning       Memory        Agent Loop
       │              │              │
       └──────────────┼──────────────┘
                      │
                      ▼
                Tool System
                      │
              ┌───────┴───────┐
              ▼               ▼
             Tools            MCP
                      │
                      ▼
                LLM Providers
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
       Provider A  Provider B  Local Model
```

最終系統應該展示整個學習過程中的主要概念，同時保持架構清晰、模組化且可以理解。

---

# 15. 面試準備

每一個主要階段都應該同時產生對應的 Interview Knowledge。

對於每一個 Component，我們應該能回答：

### 它解決了什麼問題？

### 為什麼需要這個 Abstraction？

### 有哪些替代方案？

### Trade-offs 是什麼？

### 哪些地方可能出錯？

### 如何讓它 Production-ready？

### 如何測試？

例如完成 ReAct 後，我們應該能討論：

- ReAct vs Simple Tool Calling
- ReAct vs Planning
- Agent Loop Termination
- Infinite Loops
- Tool Failures
- Context Growth
- Cost 與 Latency
- Deterministic Workflows vs Autonomous Agents

目標不只是擁有可以執行的 Code。

真正的目標是：

> **能夠解釋 Code 背後的 Engineering Decisions。**

---

# 16. 最終學習成果

完成這個專案後，希望能夠從底層理解一個 AI Agent System：

```text
LLM
 │
 ├── Provider Abstraction
 ├── Streaming
 ├── Structured Output
 │
 ▼
Tool System
 │
 ├── Tool Definition
 ├── Tool Execution
 ├── Validation
 └── Permissions
 │
 ▼
Agent Loop
 │
 ├── ReAct
 ├── Planning
 ├── Routing
 ├── Reflection
 └── Parallelization
 │
 ▼
Memory / Context
 │
 ├── Short-term Memory
 ├── Long-term Memory
 └── Context Management
 │
 ▼
MCP / External Systems
 │
 ▼
Multi-Agent
 │
 ▼
Production Engineering
 │
 ├── Reliability
 ├── Security
 ├── Observability
 └── Evaluation
```

最終目標不是建立一個最大的 Agent Framework。

而是建立一個**小到可以理解、完整到足以展示現代 AI Agent 核心工程概念**的系統。

> **從零開始建立。理解每一層。讓它失敗。修復它。測量它。最後說清楚它為什麼能運作。**
