# Coding Skill

## Project Type

This is a **learning project**.

The purpose is to understand AI Agent engineering by implementing the underlying concepts ourselves.

The goal is NOT to build the most sophisticated, optimized, or production-ready Agent framework.

---

## 1. Prioritize Readability

Code should be easy for a human learner to read and understand.

Prefer:

- straightforward control flow
- simple functions
- meaningful variable names
- explicit data flow
- small modules
- clear interfaces
- type hints where useful

Avoid clever code when simple code is sufficient.

---

## 2. Do Not Over-Engineer

Do not write unnecessarily advanced code simply because it is possible.

Avoid introducing:

- complex design patterns without a clear reason
- excessive abstraction
- unnecessary inheritance
- metaprogramming
- complicated generics
- premature optimization
- unnecessary concurrency
- unnecessary distributed-system patterns

The simplest implementation that clearly demonstrates the concept is usually preferred.

---

## 3. Learning Value Comes First

When choosing between two implementations, prefer the one that makes the underlying concept easier to understand.

For example:

If we are learning how an Agent loop works, prefer an explicit loop such as:

```python
while not finished:
    response = model.generate(...)
    ...
```

over hiding the entire process behind a high-level Agent framework.

The learner should be able to see the mechanism.

---

## 4. Implement Agent Concepts From Scratch

This project intentionally implements Agent functionality ourselves.

Do NOT use existing Agent frameworks to implement the core learning objectives.

Do not use frameworks such as:

- LangChain
- LangGraph
- LlamaIndex
- AutoGen
- CrewAI
- similar Agent frameworks

to replace the Agent implementation.

For example, if the goal is to learn:

- Agent loops
- tool execution
- planning
- ReAct
- memory
- routing
- reflection
- multi-agent systems

implement the mechanism directly.

External libraries may be used for supporting functionality when appropriate.

For example:

- HTTP clients
- data validation
- serialization
- testing
- logging

These libraries must not hide the core Agent mechanism that we are trying to learn.

---

## 5. Do Not Hide Important Logic Behind Libraries

Before adding a library, ask:

1. What problem does it solve?
2. Can the problem be implemented simply ourselves?
3. Would using the library hide an important learning concept?
4. Is the dependency necessary?

If a small amount of code can clearly demonstrate the concept, prefer implementing it ourselves.

---

## 6. Avoid Premature Production Optimization

Do not optimize code before understanding the basic implementation.

For example, do not introduce:

- complex caching
- sophisticated concurrency
- distributed execution
- elaborate retry systems
- advanced scheduling
- complex plugin systems

unless the current learning phase specifically requires them.

First make the basic mechanism correct and understandable.

Then improve it step by step.

---

## 7. Make Architecture Visible

Important architecture should be visible in the source code.

For example:

```text
Agent
  ↓
Model Provider
  ↓
Model
```

or:

```text
Agent Loop
  ↓
Model Decision
  ↓
Tool Call
  ↓
Tool Execution
  ↓
Tool Result
  ↓
Model
```

The code should make these relationships understandable.

Avoid collapsing important layers into a single opaque abstraction.

---

## 8. Implement in Small Steps

When implementing a new concept:

1. Start with the simplest working version.
2. Add tests.
3. Understand its limitations.
4. Add complexity only when needed.
5. Test again.

Do not implement the "final architecture" immediately.

This project is intentionally incremental.

---

## 9. Prefer Explicit Failure Handling

Failures are part of the learning process.

When appropriate, make failure behavior explicit.

Examples:

- model errors
- invalid tool arguments
- tool execution errors
- timeouts
- malformed responses
- unexpected model output
- Agent loop termination

Do not silently swallow errors just to make the demo appear to work.

---

## 10. Tests Are Part of Learning

Tests should help demonstrate how the implementation behaves.

For new functionality, consider testing:

- normal behavior
- edge cases
- invalid input
- failure behavior
- termination behavior
- interaction between components

Tests should be simple enough that a learner can understand what they are proving.

---

## 11. Explain Important Design Decisions

When a change introduces an important architectural decision, explain:

- why this design was chosen
- what alternatives exist
- what trade-offs exist
- what limitations remain

The purpose is not merely to produce working code.

The purpose is to develop the ability to explain the implementation during technical interviews.

---

## 12. Production Readiness Is a Later Goal

Production concerns are important, but they should be introduced progressively.

The project should first establish a clear and understandable implementation.

Later phases may introduce:

- reliability
- observability
- evaluation
- security
- guardrails
- performance
- concurrency
- production runtime concerns

Do not introduce these concerns prematurely if they make the fundamental concept harder to understand.

---

## 13. Final Principle

When in doubt, prefer:

**Simple > Clever**

**Readable > Optimized**

**Explicit > Hidden**

**Understandable > Abstract**

**Learning Value > Production Complexity**

**Implement Ourselves > Use an Agent Framework**

The purpose of this repository is to understand how AI Agent systems work by building them step by step.
