# Comment Skill

## Purpose

Comments in this repository are part of the learning process.

When writing comments, the goal is not simply to describe what the code does.

Comments should help the learner understand:

- what the code is doing
- why it is implemented this way
- what AI Agent or software engineering concept is involved
- what trade-off or design decision is being demonstrated

---

## 1. Comments Must Be Bilingual

When adding explanatory comments, write them in both:

- English
- Chinese

For example:

```python
# English: Store the conversation history so the next model call can use previous context.
# 中文：保存對話歷史，讓下一次呼叫 LLM 時可以使用之前的上下文。
messages.append(message)
```

The English and Chinese comments should explain the same idea.

Do not write one language as a direct meaningless duplicate of the other.

---

## 2. Explain Knowledge, Not Just Code

Avoid comments that merely repeat the code.

Bad:

```python
# Add message to messages
# 將訊息加入 messages
messages.append(message)
```

Better:

```python
# English: The Agent keeps conversation history because an LLM call is stateless by itself.
# 中文：Agent 需要保存對話歷史，因為單次 LLM 呼叫本身通常不會自動記住之前的上下文。
messages.append(message)
```

The second comment teaches a concept instead of simply translating the syntax.

---

## 3. Explain the "Why"

When an implementation decision is not obvious, explain why it exists.

For example:

```python
# English: We keep the Provider interface independent from any specific LLM vendor.
# This allows the Agent layer to work with different model providers without changing
# the Agent's core logic.
#
# 中文：這裡讓 Provider interface 與特定 LLM 廠商解耦。
# 這樣 Agent 核心邏輯就可以使用不同的模型供應商，而不需要修改 Agent 本身。
class Provider(Protocol):
    ...
```

Prefer explaining design decisions over describing syntax.

---

## 4. Explain Important AI Agent Concepts

When code introduces an important Agent concept, the comment should explain the concept briefly.

Examples include:

- Agent loop
- tool calling
- function calling
- planning
- ReAct
- memory
- context
- routing
- reflection
- streaming
- structured output
- MCP
- multi-agent communication
- retry
- termination conditions

The explanation does not need to be long.

It should provide enough context for a learner to understand why the code exists.

---

## 5. Do Not Comment Every Line

Do not add comments to every line simply to satisfy the bilingual requirement.

Comments are most valuable when they explain:

- concepts
- design decisions
- non-obvious behavior
- important assumptions
- potential failure modes
- learning points

Straightforward code should remain readable without excessive comments.

---

## 6. Keep Comments Close to the Relevant Code

Comments should normally appear immediately before the code they explain.

Avoid large blocks of unrelated explanation far away from the implementation.

---

## 7. Comments Should Match the Current Implementation

Do not write comments based on assumptions.

If the implementation changes, update the relevant comments.

Incorrect comments are worse than missing comments because they teach the wrong concept.

---

## 8. Learning-Oriented Comments

When a piece of code demonstrates an important engineering concept, prefer a short teaching explanation.

For example:

```python
# English: The loop continues until the model produces a final answer.
# This termination condition is important because an Agent must have a way to stop
# instead of repeatedly calling the model forever.
#
# 中文：這個迴圈會一直執行，直到模型產生最終答案。
# 終止條件非常重要，因為 Agent 必須有明確的停止機制，
# 否則可能會無限重複呼叫模型。
while not finished:
    ...
```

The purpose is to connect the implementation to the underlying engineering concept.

---

## 9. Comment Depth

Use different levels of explanation depending on importance.

### Simple code

A short bilingual comment is enough.

### Non-obvious code

Explain the reason for the implementation.

### Core Agent concepts

Explain:

1. what the mechanism does
2. why it is needed
3. what problem it solves

Do not turn every comment into a textbook.

---

## 10. Goal

The final code should be understandable both as software and as learning material.

A good comment should answer at least one of these questions:

- What concept am I learning here?
- Why does this code exist?
- Why was it implemented this way?
- What problem does this mechanism solve?
- What could go wrong without it?
