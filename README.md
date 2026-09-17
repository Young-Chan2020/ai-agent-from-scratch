# AI Agent From Scratch

> **Build an AI Agent from scratch. Learn how Agents really work.**

A hands-on learning project for understanding **AI Agent systems from the inside out** — starting from LLM abstractions and tool calling, then building toward ReAct, planning, memory, MCP, multi-agent systems, evaluation, reliability, and production-oriented runtime design.

The goal is simple:

**Don’t just use Agent frameworks. Build the Agent yourself.**

---

## Why This Project?

AI Agent frameworks make it easy to build something that *looks* like an Agent.

But if you want to understand what is actually happening underneath — or prepare for an AI Agent engineering interview — you need to understand the building blocks yourself.

This project follows a simple learning loop:

**Understand → Design → Implement → Test → Analyze**

Instead of hiding the important parts behind a framework, we progressively implement the core concepts ourselves and study the trade-offs behind each design.

By the end, the goal is not just to have a working Agent.

The goal is to be able to explain **why it works, how it fails, and how you would design it for a real system.**

---

## What You’ll Build

Starting from a minimal LLM abstraction, this project gradually evolves into an Agent runtime:

```text
User / Application
        ↓
    Agent Runtime
        ↓
 Planning / Agent Loop / Memory
        ↓
    Tool / Action Layer
        ↓
     Tools / MCP
        ↓
   Provider Layer
        ↓
 LLM / Local Model
```

Along the way, we’ll implement and study:

- LLM provider abstraction
- Multiple LLM providers
- Streaming
- Structured output
- Tool definition and execution
- Agent loops
- ReAct
- Planning
- Routing
- Reflection
- Parallelization
- Workflow vs Agent
- Context management
- Memory
- MCP
- Multi-agent architectures
- Reliability
- Guardrails and human-in-the-loop
- Observability
- Agent evaluation
- Agent security
- Production-oriented runtime design

---

## Learning Roadmap

The project is organized as a progressive roadmap rather than a collection of unrelated demos.

| Phase | Topic |
| --- | --- |
| 00 | Project Foundations |
| 01 | LLM Abstraction |
| 02 | Multiple LLM Providers |
| 03 | Streaming |
| 04 | Structured Output |
| 05 | Tool Definition |
| 06 | Tool Execution |
| 07 | Agent Loop |
| 08 | ReAct |
| 09 | Planning |
| 10 | Routing |
| 11 | Reflection |
| 12 | Parallelization |
| 13 | Workflow vs Agent |
| 14 | Context Management |
| 15 | Memory |
| 16 | MCP |
| 17 | Multi-Agent Architecture |
| 18 | Reliability |
| 19 | Guardrails & Human-in-the-Loop |
| 20 | Observability |
| 21 | Agent Evaluation |
| 22 | Agent Security |
| 23 | Production-Oriented Runtime |

Each phase is intended to answer:

> **What is this? Why do we need it? How does it work? How do we implement it? What can go wrong?**

---

## Project Philosophy

This is a **learning-first implementation**, not another Agent framework.

### Understand before abstracting

We prefer explicit implementations that make the underlying mechanism visible.

### Build before using frameworks

Core Agent concepts are implemented from scratch instead of being delegated to frameworks such as LangChain, LangGraph, LlamaIndex, AutoGen, or CrewAI.

Frameworks may be studied later for comparison, but they should not hide the concepts we are trying to learn.

### Test what we build

Tests are part of the learning process.

They help answer:

- What behavior do we expect?
- What assumptions does the implementation make?
- What happens when something fails?
- Can we change the design without breaking existing behavior?

### Analyze trade-offs

A working implementation is not necessarily a good design.

For each important component, we care about:

- Design alternatives
- Failure modes
- Complexity
- Reliability
- Observability
- Maintainability
- Production considerations

---

## Example Learning Journey

The project starts with something intentionally small:

```python
response = provider.chat(request)
```

Then we progressively build the machinery around it:

```text
LLM
 ↓
Provider abstraction
 ↓
Structured responses
 ↓
Tools
 ↓
Agent loop
 ↓
ReAct
 ↓
Planning
 ↓
Memory
 ↓
MCP
 ↓
Multi-Agent
 ↓
Reliable Agent Runtime
```

The interesting part is not the final code.

**The interesting part is understanding every step between them.**

---

## Repository Structure

```text
ai-agent-from-scratch/
│
├── src/
│   └── ai_agent/
│       ├── core/
│       ├── providers/
│       └── ...
│
├── tests/
│   ├── core/
│   ├── providers/
│   └── ...
│
├── docs/
│   └── phases/
│       ├── phase-01-llm-abstraction.md
│       ├── phase-01-llm-abstraction.zh.md
│       └── ...
│
├── skills/
│   ├── coding/
│   └── comments/
│
├── AGENTS.md
├── ROADMAP.md
└── pyproject.toml
```

Each completed phase will include both:

- English documentation
- Traditional Chinese documentation

The documentation maps concepts back to the actual implementation so that the project can be studied from both the architecture and source-code perspectives.

---

## For AI Agent Engineering Interviews

This project is also designed as an **interview preparation journey**.

For each major topic, we aim to understand more than just the implementation.

You should eventually be able to answer questions such as:

- Why do we need an LLM provider abstraction?
- How would you support multiple model providers?
- How does an Agent decide when to call a tool?
- What is the difference between a workflow and an Agent?
- How does ReAct work?
- When should an Agent plan before acting?
- How should Agent memory be designed?
- What happens when a tool fails?
- How do you prevent infinite Agent loops?
- How do you evaluate an Agent?
- How do you observe and debug Agent behavior?
- How would you make an Agent runtime reliable enough for production?
- When should you use an Agent, and when should you use a deterministic workflow?

The goal is to move from:

> **“I know how to use an Agent framework.”**

to:

> **“I understand how an Agent system works and can explain the design decisions behind it.”**

---

## Who Is This For?

This project is useful if you are:

- Learning AI Agents from the fundamentals
- Building your first Agent runtime
- Preparing for AI Agent / LLM engineering interviews
- Trying to understand what Agent frameworks do under the hood
- Studying LLM application architecture
- Interested in tool calling, MCP, memory, planning, or multi-agent systems
- Looking for a structured path from LLM APIs to production-oriented Agent systems

You **do not need to know everything about Agents beforehand**.

The project is designed to build the knowledge progressively.

---

## How We Learn

Every phase follows the same cycle:

```text
Read
 ↓
Understand
 ↓
Design
 ↓
Implement
 ↓
Test
 ↓
Break
 ↓
Fix
 ↓
Analyze
 ↓
Document
```

No magic.

No black box.

Just progressively building the system and understanding what is happening underneath.

---

## Star ⭐

If you’re learning AI Agents, LLM systems, or preparing for an AI engineering interview, consider giving this repository a ⭐.

It helps the project grow and makes it easier for other people who are learning the same things to find it.

---

## License

This project is intended as an educational and learning resource.

---

# 從零開始打造 AI Agent

> **從零打造 AI Agent，理解 Agent 真正的運作方式。**

這是一個以實作為核心的學習專案，目標是由內而外理解 **AI Agent 系統**。我們會從 LLM 抽象層與工具呼叫開始，逐步建立 ReAct、規劃、記憶、MCP、多 Agent 系統、評估、可靠性，以及面向生產環境的 Runtime 設計。

目標很簡單：

**不要只會使用 Agent Framework，而是親手打造 Agent。**

---

## 為什麼要做這個專案？

AI Agent Framework 讓我們很容易建立一個「看起來像 Agent」的系統。

但是，如果你想真正理解底層發生了什麼，或準備 AI Agent 工程師面試，就必須自己理解這些基礎組件。

這個專案遵循一個簡單的學習循環：

**理解 → 設計 → 實作 → 測試 → 分析**

我們不會把重要概念全部藏在 Framework 後面，而是逐步親手實作核心概念，並研究每個設計背後的取捨。

最後的目標不只是擁有一個可以運作的 Agent。

更重要的是，你能夠解釋：

**它為什麼能運作、可能如何失敗，以及如果要用於真實系統，你會如何設計。**

---

## 你將會打造什麼？

我們會從一個最小的 LLM 抽象層開始，逐步演進成一個 Agent Runtime：

```text
使用者 / 應用程式
        ↓
    Agent Runtime
        ↓
規劃 / Agent Loop / 記憶
        ↓
    工具 / 行動層
        ↓
     工具 / MCP
        ↓
    Provider 層
        ↓
 LLM / 本地模型
```

在這個過程中，我們會實作並研究：

- LLM Provider 抽象層
- 多個 LLM Provider
- Streaming
- 結構化輸出
- 工具定義與執行
- Agent Loop
- ReAct
- 規劃
- 路由
- 反思
- 平行化
- Workflow 與 Agent 的差異
- Context 管理
- 記憶
- MCP
- Multi-Agent 架構
- 可靠性
- Guardrails 與 Human-in-the-Loop
- 可觀測性
- Agent 評估
- Agent 安全性
- 面向生產環境的 Runtime 設計

---

## 學習路線圖

這個專案是一條循序漸進的學習路線，而不是一堆互不相關的 Demo。

| Phase | 主題 |
| --- | --- |
| 00 | 專案基礎 |
| 01 | LLM 抽象層 |
| 02 | 多個 LLM Provider |
| 03 | Streaming |
| 04 | 結構化輸出 |
| 05 | 工具定義 |
| 06 | 工具執行 |
| 07 | Agent Loop |
| 08 | ReAct |
| 09 | 規劃 |
| 10 | 路由 |
| 11 | 反思 |
| 12 | 平行化 |
| 13 | Workflow 與 Agent |
| 14 | Context 管理 |
| 15 | 記憶 |
| 16 | MCP |
| 17 | Multi-Agent 架構 |
| 18 | 可靠性 |
| 19 | Guardrails 與 Human-in-the-Loop |
| 20 | 可觀測性 |
| 21 | Agent 評估 |
| 22 | Agent 安全性 |
| 23 | 面向生產環境的 Runtime |

每個 Phase 都會回答以下問題：

> **這是什麼？為什麼需要它？它如何運作？我們如何實作？可能會出現什麼問題？**

---

## 專案理念

這是一個以學習為優先的實作專案，而不是另一個 Agent Framework。

### 先理解，再抽象化

我們偏好清楚、直接的實作，讓底層機制保持可見。

### 先親手打造，再使用 Framework

核心 Agent 概念會由我們自己實作，而不是直接交給 LangChain、LangGraph、LlamaIndex、AutoGen 或 CrewAI 等 Framework。

之後可以研究這些 Framework 作為比較，但在學習階段，它們不應該把我們想理解的概念藏起來。

### 測試我們打造的東西

測試是學習過程的一部分。

測試可以幫助我們回答：

- 我們預期系統有什麼行為？
- 實作依賴哪些假設？
- 當某個部分失敗時會發生什麼？
- 我們能否修改設計而不破壞既有行為？

### 分析設計取捨

能夠運作的實作，不一定是好的設計。

對於每個重要組件，我們都會關注：

- 設計替代方案
- 失敗模式
- 複雜度
- 可靠性
- 可觀測性
- 可維護性
- 生產環境考量

---

## 學習旅程範例

專案會從一個刻意保持簡單的呼叫開始：

```python
response = provider.chat(request)
```

接著逐步建立周邊機制：

```text
LLM
 ↓
Provider 抽象層
 ↓
結構化回應
 ↓
工具
 ↓
Agent Loop
 ↓
ReAct
 ↓
規劃
 ↓
記憶
 ↓
MCP
 ↓
Multi-Agent
 ↓
可靠的 Agent Runtime
```

有趣的地方不只是最後的程式碼。

**真正重要的是理解中間經歷的每一步。**

---

## Repository 結構

```text
ai-agent-from-scratch/
│
├── src/
│   └── ai_agent/
│       ├── core/
│       ├── providers/
│       └── ...
│
├── tests/
│   ├── core/
│   ├── providers/
│   └── ...
│
├── docs/
│   └── phases/
│       ├── phase-01-llm-abstraction.md
│       ├── phase-01-llm-abstraction.zh.md
│       └── ...
│
├── skills/
│   ├── coding/
│   └── comments/
│
├── AGENTS.md
├── ROADMAP.md
└── pyproject.toml
```

每個完成的 Phase 都會包含：

- 英文文件
- 繁體中文文件

文件會將學習到的概念對應回實際實作，讓這個專案可以同時從架構與原始碼兩個角度進行研究。

---

## AI Agent 工程面試

這個專案同時也是一段 **AI Agent 工程面試準備旅程**。

對於每個重要主題，我們不只關注如何實作，也希望真正理解背後的原因。

最終你應該能夠回答以下問題：

- 為什麼需要 LLM Provider 抽象層？
- 如何支援多個模型 Provider？
- Agent 如何決定是否呼叫工具？
- Workflow 與 Agent 有什麼差異？
- ReAct 如何運作？
- 什麼時候 Agent 應該先規劃再行動？
- Agent 記憶應該如何設計？
- 工具失敗時會發生什麼？
- 如何避免 Agent 進入無限迴圈？
- 如何評估 Agent？
- 如何觀察與除錯 Agent 行為？
- 如何讓 Agent Runtime 足夠可靠，能夠用於生產環境？
- 什麼時候應該使用 Agent，什麼時候應該使用確定性的 Workflow？

目標是從：

> **「我知道如何使用 Agent Framework。」**

進步到：

> **「我理解 Agent 系統如何運作，也能解釋背後的設計決策。」**

---

## 這個專案適合誰？

如果你符合以下其中一項，這個專案可能適合你：

- 想從基礎開始學習 AI Agent
- 想打造自己的第一個 Agent Runtime
- 正在準備 AI Agent 或 LLM 工程面試
- 想理解 Agent Framework 在底層做了什麼
- 正在研究 LLM 應用程式架構
- 對工具呼叫、MCP、記憶、規劃或 Multi-Agent 系統感興趣
- 想尋找一條從 LLM API 走向面向生產環境 Agent 系統的結構化學習路線

你**不需要事先了解所有 Agent 知識**。

這個專案會循序漸進地建立相關能力。

---

## 我們如何學習？

每個 Phase 都會遵循相同的循環：

```text
閱讀
 ↓
理解
 ↓
設計
 ↓
實作
 ↓
測試
 ↓
刻意讓它失敗
 ↓
修正
 ↓
分析
 ↓
文件化
```

沒有魔法。

沒有黑盒。

我們只會逐步建立系統，並理解底層到底發生了什麼。

---

## Star ⭐

如果你正在學習 AI Agent、LLM 系統，或準備 AI 工程相關面試，歡迎為這個 Repository 點一個 ⭐。

你的 Star 能幫助專案成長，也能讓更多正在學習相同主題的人找到這個專案。

---

## License

這個專案主要作為教育與學習資源使用。
