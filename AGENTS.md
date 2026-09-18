# AGENTS.md

## Project Overview

This repository is a learning project for understanding and implementing AI Agent systems from scratch.

The primary goal is not to build the most advanced or production-ready Agent framework.

The primary goal is to understand:

- how an Agent works internally
- why each component is needed
- how the components interact
- what design trade-offs exist
- how failures happen
- how to test and improve the implementation

The implementation should therefore prioritize **clarity, learning value, and explicit design** over abstraction, optimization, or framework convenience.

---

## Core Principles

### 1. Learning comes before abstraction

Prefer code that is easy for a human learner to read and understand.

Do not introduce abstractions merely because they are considered "clean", "scalable", or "production-grade".

Every abstraction should have a clear reason to exist.

### 2. Understand before implementing

Before making significant changes:

1. Inspect the existing code.
2. Understand the current architecture.
3. Identify which component is affected.
4. Consider simpler alternatives.
5. Then implement the change.

Do not modify code blindly.

### 3. Prefer explicit implementations

Prefer straightforward code over clever code.

For example, if a simple function is sufficient, do not introduce:

- unnecessary design patterns
- excessive inheritance
- complex metaprogramming
- unnecessary generic abstractions
- premature optimization

The code should be understandable by someone who is learning AI Agent engineering.

### 4. Build the Agent ourselves

This repository exists specifically to learn how Agent systems work internally.

Do not replace the core Agent implementation with an existing Agent framework.

In particular, do not use frameworks such as:

- LangChain
- LangGraph
- LlamaIndex
- AutoGen
- CrewAI
- similar Agent orchestration frameworks

unless the user explicitly asks to study or compare them.

External libraries may be used when they solve a supporting problem, but the core Agent concepts should be implemented by us.

### 5. Do not hide important concepts

If the project is implementing concepts such as:

- Agent loops
- tool calling
- planning
- memory
- context management
- routing
- reflection
- MCP
- multi-agent coordination

the implementation should make the underlying mechanism visible.

Do not hide the learning objective behind a high-level API.

---

## Coding Style

Prefer:

- simple functions
- meaningful names
- type hints where useful
- small and understandable modules
- explicit control flow
- readable data structures
- comments that explain important concepts

Avoid:

- unnecessary complexity
- overly clever one-liners
- abstractions without a learning purpose
- unnecessary dependencies
- premature optimization

---

## Changes to the Repository

When implementing a task:

1. Make the smallest reasonable change.
2. Do not modify unrelated files.
3. Preserve existing behavior unless the task requires changing it.
4. Add or update tests when behavior changes.
5. Check the resulting diff.
6. Explain important design decisions when appropriate.

---

## Testing

New functionality should have corresponding tests when practical.

Tests should cover:

- normal behavior
- important edge cases
- expected failures
- integration between components when relevant

Do not assume code works simply because it looks correct.

---

## Learning Workflow

This repository is a roadmap-driven learning project.

The primary learning roadmap is:

`ROADMAP.md`

The roadmap defines the intended learning sequence and the major phases of the project.

The Coding Agent must use `ROADMAP.md` as the primary guide when deciding what to implement next.

Do not arbitrarily skip ahead to later phases unless the user explicitly requests it.

---

## Roadmap-Driven Development

Development should generally follow this cycle:

1. Read the relevant phase in `ROADMAP.md`.
2. Identify the concepts that the phase is intended to teach.
3. Explain the concepts before implementing them when appropriate.
4. Design the simplest reasonable implementation.
5. Implement the functionality.
6. Add or update tests.
7. Run the relevant tests.
8. Analyze the implementation, limitations, and trade-offs.
9. Create the phase documentation.
10. Verify that the phase documentation links the learned concepts to the actual source code.
11. Only then consider the phase complete.

The goal is not simply to finish implementation.

A phase is complete only when its implementation, tests, understanding, and documentation are complete.

---

## Phase Branch Workflow

Each roadmap phase must be developed on its own dedicated Git branch.

Use the following workflow:

1. Start from the latest `main` branch.
2. Create a branch named `phase/<phase-number>-<short-name>`.
3. Implement the phase, tests, and documentation on that branch.
4. The phase branch must contain all previous phases plus the new phase.
5. Review the implementation and diff before merging.
6. Merge the completed phase branch into `main`.
7. Preserve the phase branch after merging so it remains a historical snapshot of that learning stage.

Example:

```text
main
  │
  ├── phase/01-llm-abstraction
  │
  ├── phase/02-multiple-providers
  │
  ├── phase/03-streaming
  │
  └── ...
```

A phase branch is a complete project snapshot at that learning stage, not a branch containing only the files newly introduced by that phase.

The branch history should make it easy to review how the project evolved from one learning phase to the next.

---

## Phase Completion Documentation

After completing each roadmap phase, create dedicated Markdown documents for that phase in **both English and Traditional Chinese**.

Phase documentation should be stored under:

`docs/phases/`

Use the following naming convention:

```text
docs/phases/phase-01-llm-abstraction.md
docs/phases/phase-01-llm-abstraction.zh.md

docs/phases/phase-02-multiple-providers.md
docs/phases/phase-02-multiple-providers.zh.md

docs/phases/phase-03-streaming.md
docs/phases/phase-03-streaming.zh.md
```

The English document uses the normal `.md` suffix. The Traditional Chinese document uses `.zh.md`.

Do **not** use `zh-TW` in filenames.

The English and Chinese documents should describe the same phase, concepts, implementation mapping, tests, design decisions, limitations, and interview questions. They should be kept synchronized with the actual implementation.

---

## Phase Documentation Requirements

Each phase document should explain the knowledge gained during that phase.

Both the English and Traditional Chinese versions must contain the same required sections.

At minimum, each document should contain:

### 1. Learning Objectives

Explain what the phase is intended to teach.

### 2. Core Concepts

For each important concept, explain:

- What it is.
- Why it is needed.
- What problem it solves.
- How it relates to AI Agent engineering.
- Important trade-offs or limitations when relevant.

### 3. Architecture

Explain where the concepts introduced by this phase fit into the overall system architecture.

### 4. Implementation Mapping

Each important concept should be connected to its actual implementation.

Whenever possible, documentation should identify:

- file path
- module
- class
- function or method

Prefer precise references such as:

```text
src/agent/loop.py::Agent.run()
```

rather than only:

```text
src/agent/loop.py
```

The purpose is to allow a learner to move directly from a knowledge concept to the code that implements it.

### 5. Tests

Document the tests that demonstrate or verify the relevant concepts.

When possible, reference the specific test file and test function.

For example:

```text
tests/agent/test_loop.py::test_agent_stops_on_final_response()
```

### 6. Design Decisions

Explain important implementation decisions and why they were made.

Mention meaningful alternatives and trade-offs when relevant.

### 7. Limitations

Document what the current implementation does not handle yet.

Do not hide limitations simply because the current phase is considered complete.

### 8. Interview Questions

Record useful technical interview questions related to the phase.

Questions should focus on understanding rather than memorization.

Examples:

- Why is this abstraction necessary?
- What happens if this component fails?
- What alternatives exist?
- What are the trade-offs?
- How would this design change in a production system?

---

## Source Code References

Phase documentation should remain connected to the implementation.

When a documented concept changes, update the corresponding phase documentation when practical.

Avoid documentation that describes an implementation that no longer exists.

The documentation should function as a map:

```text
Learning Concept
      ↓
Architecture
      ↓
Source File
      ↓
Class / Function
      ↓
Test
```

A reader should be able to use the phase document to navigate from a theoretical concept directly to the code that demonstrates it.

---

## Phase Completion Checklist

Before declaring a phase complete, verify:

- [ ] The concepts in the roadmap phase have been understood.
- [ ] The required implementation is complete.
- [ ] Relevant tests have been added or updated.
- [ ] Relevant tests pass.
- [ ] Important design decisions have been analyzed.
- [ ] Limitations have been identified.
- [ ] English phase documentation has been created.
- [ ] Traditional Chinese phase documentation has been created.
- [ ] Both language versions accurately describe the same implementation.
- [ ] Important concepts are mapped to source files.
- [ ] Important concepts are mapped to specific classes/functions where possible.
- [ ] Relevant tests are referenced.
- [ ] The documentation accurately reflects the current implementation.

Only after these requirements are satisfied should the project move to the next roadmap phase.

---

## Documentation and Comments

Comments are part of the learning experience.

When comments are added, follow the rules defined in:

`skills/comments/SKILL.md`

---

## Coding Rules

When writing or modifying code, follow:

`skills/coding/SKILL.md`

---

## When Uncertain

If an architectural decision is unclear, do not silently invent a complicated solution.

Prefer:

1. the simplest reasonable solution
2. an explicit explanation of the assumption
3. asking the user when the decision materially affects the architecture

---

## Definition of Done

A task is not considered complete merely because code has been written.

When appropriate:

1. Implementation is complete.
2. Tests are added or updated.
3. Relevant tests are run.
4. The diff is reviewed.
5. Important design decisions are understood and explainable.

The goal is not merely to make the code work.

The goal is to **understand why it works**.
