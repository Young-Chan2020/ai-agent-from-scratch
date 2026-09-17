# AI Agent From Scratch

> A from-scratch learning project for understanding, designing, and implementing AI Agent systems.

## 1. Project Goal

This project is designed to learn **AI Agent engineering from first principles**.

The goal is not to simply use an existing Agent framework, but to understand what happens underneath an Agent system and gradually build the major components ourselves.

By completing this project, the target is to develop the knowledge and engineering skills required to:

- Design AI Agent architectures
- Build provider-independent LLM interfaces
- Implement tool calling and execution
- Understand and implement Agent loops
- Understand ReAct and other Agentic Patterns
- Manage context and memory
- Build reliable and observable Agent systems
- Understand MCP and external tool integration
- Design multi-agent systems
- Evaluate and improve Agent behavior
- Discuss Agent architecture and engineering trade-offs in technical interviews

The project should remain understandable from the inside out: **every major abstraction should exist because we understand the problem it solves.**

---

# 2. Learning Philosophy

This project follows a simple principle:

> **Understand → Design → Implement → Test → Analyze**

Instead of starting from an existing Agent framework, we will gradually build the system from lower-level components.

The implementation should prioritize:

- Clear architecture
- Explicit abstractions
- Small, testable components
- Provider independence
- Failure handling
- Observability
- Engineering trade-offs

The purpose is not to recreate every feature of existing frameworks.

The purpose is to understand **why those frameworks need those features in the first place.**

---

# 3. Overall Architecture

The project will gradually evolve toward a layered Agent runtime:

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

This architecture is expected to evolve throughout the project.

---

# 4. Learning Roadmap

## Phase 0 — Project Foundations

Establish the project structure, development environment, testing strategy, documentation, and basic engineering conventions.

The goal is to create a clean foundation before implementing Agent capabilities.

---

## Phase 1 — LLM Abstraction

Build a provider-independent interface for interacting with language models.

Topics include:

- Messages
- Requests and responses
- Model configuration
- Provider abstraction
- Error handling
- Usage information
- Mock providers

The goal is to understand how different model providers can be represented through a common interface.

---

## Phase 2 — Multiple LLM Providers

Implement multiple providers behind the same abstraction.

Potential providers include:

- OpenAI
- Anthropic
- Google Gemini
- Local models

The focus is not on supporting every provider.

The focus is understanding the engineering problems caused by provider differences and designing an abstraction that hides unnecessary provider-specific details.

---

## Phase 3 — Streaming

Add streaming model responses.

Topics include:

- Streaming events
- Incremental text generation
- Partial responses
- Tool-call streaming
- Stream reconstruction
- Error handling during streams

The goal is to understand how real-time LLM interaction works at the runtime level.

---

## Phase 4 — Structured Output

Add structured model responses.

Topics include:

- JSON output
- Schemas
- Validation
- Typed responses
- Structured generation
- Invalid output handling

The goal is to understand how an Agent runtime can safely consume machine-readable model output.

---

# 5. Tool System

## Phase 5 — Tool Definition

Design a general tool abstraction.

A tool should describe:

- Its name
- Its purpose
- Its input schema
- Its output
- Execution behavior

Potential initial tools:

- Calculator
- File operations
- Search
- Simple API calls

The focus is understanding how an LLM can interact with external capabilities.

---

## Phase 6 — Tool Execution

Build the execution layer between the Agent and tools.

Topics include:

- Tool selection
- Argument validation
- Execution
- Results
- Exceptions
- Timeout
- Retry
- Permission checks

The goal is to separate **model decisions** from **actual tool execution**.

---

# 6. Agent Core

## Phase 7 — Agent Loop

Build the fundamental Agent execution loop.

The Agent should be able to:

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

This is the point where the project becomes a real Agent runtime rather than simply an LLM wrapper.

---

## Phase 8 — ReAct

Study and implement the ReAct-style Agent pattern.

Core idea:

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

The goal is to understand:

- Why Agent loops work
- How reasoning and actions interact
- How observations affect future actions
- How loops terminate
- How to prevent infinite execution
- How to handle failed tools

ReAct will be treated as one Agentic Pattern, not as the definition of all Agents.

---

# 7. Agentic Patterns

After the basic Agent loop is understood, implement and compare different approaches.

## Phase 9 — Planning

Explore Agents that create a plan before execution.

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

Explore dynamic routing between models, tools, or specialized Agents.

```text
User Request
     ↓
   Router
  /   |   \
 A    B    C
```

Focus areas include:

- Task classification
- Model selection
- Cost
- Latency
- Specialization

---

## Phase 11 — Reflection

Explore self-evaluation and iterative improvement.

```text
Generate
   ↓
Evaluate
   ↓
Improve
   ↓
Final
```

The goal is to understand when reflection improves reliability and when it simply increases cost and latency.

---

## Phase 12 — Parallelization

Explore executing independent tasks concurrently.

```text
             Task
          /    |    \
         A     B     C
          \    |    /
            Combine
```

This phase introduces important engineering concepts such as:

- Async execution
- Concurrency
- Task coordination
- Failure isolation
- Result aggregation

---

## Phase 13 — Workflow vs Agent

Understand the difference between:

- Deterministic workflows
- LLM-driven Agents
- Hybrid systems

A major principle of this project is:

> **Use an Agent when dynamic decision-making is useful; use deterministic code when deterministic behavior is sufficient.**

---

# 8. Memory and Context

## Phase 14 — Context Management

Learn how an Agent manages the information provided to the model.

Topics include:

- Context windows
- Token budgets
- Conversation history
- Summarization
- Context selection
- Tool-result management
- Context compression

---

## Phase 15 — Memory

Explore different forms of Agent memory.

Potential concepts include:

- Short-term memory
- Long-term memory
- Semantic memory
- Episodic memory
- Working memory

The goal is to understand how memory differs from simply storing conversation history.

---

# 9. MCP and External Systems

## Phase 16 — MCP

Study and implement integration with the Model Context Protocol.

The goal is to understand how standardized protocols can connect Agents with external tools and systems.

Potential integrations include:

- Files
- Databases
- APIs
- Development tools
- External services

MCP should be understood as an integration protocol, not the Agent itself.

---

# 10. Multi-Agent Systems

## Phase 17 — Multi-Agent Architecture

Explore systems where multiple specialized Agents collaborate.

Potential architecture:

```text
                  Supervisor
                 /     |     \
                /      |      \
        Researcher   Coder   Reviewer
                \      |      /
                 \     |     /
                    Result
```

Topics include:

- Agent specialization
- Delegation
- Coordination
- Supervisor patterns
- Agent communication
- Shared context
- Failure handling

This phase comes after understanding single-Agent systems.

---

# 11. Reliability and Production Engineering

## Phase 18 — Reliability

Build mechanisms for reliable Agent execution.

Topics include:

- Retry
- Timeout
- Rate limits
- Circuit breaking
- Error recovery
- Maximum iterations
- Tool failures
- Provider failures

The goal is to move from a prototype Agent toward a reliable runtime.

---

## Phase 19 — Guardrails and Human-in-the-Loop

Explore safety and control mechanisms.

Topics include:

- Permissions
- Tool restrictions
- Approval workflows
- Sensitive operations
- Human confirmation
- Execution policies

Example:

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

Build visibility into Agent execution.

An Agent run should eventually be traceable as:

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

Potential metrics include:

- Latency
- Token usage
- Cost
- Tool calls
- Errors
- Retries
- Execution steps

---

# 12. Evaluation

## Phase 21 — Agent Evaluation

Build a way to evaluate Agent behavior systematically.

Potential metrics include:

- Task completion
- Tool selection
- Answer correctness
- Reliability
- Latency
- Token usage
- Cost
- Failure rate

The goal is to answer:

> **Did the Agent actually improve after a change?**

rather than relying only on manual demonstrations.

---

# 13. Security

## Phase 22 — Agent Security

Explore security problems specific to Agent systems.

Potential topics include:

- Prompt injection
- Tool abuse
- Excessive permissions
- Untrusted tool output
- Sensitive data exposure
- Sandboxing
- Tool authorization
- Resource limits

The objective is to understand that giving an LLM tools also gives it the ability to affect external systems.

---

# 14. Final Agent Runtime

## Phase 23 — Production-Oriented Runtime

Combine the components developed throughout the project:

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

The final system should demonstrate the major concepts learned throughout the project while remaining understandable and modular.

---

# 15. Interview Preparation

Every major phase should also produce interview knowledge.

For each component, we should be able to explain:

### What problem does it solve?

### Why is this abstraction necessary?

### What are the alternatives?

### What are the trade-offs?

### What can go wrong?

### How would we make it production-ready?

### How would we test it?

For example, after implementing ReAct, we should be able to discuss:

- ReAct vs simple tool calling
- ReAct vs planning
- Agent loop termination
- Infinite loops
- Tool failures
- Context growth
- Cost and latency
- Deterministic workflows vs autonomous Agents

The objective is not simply to have working code.

The objective is to be able to **explain the engineering decisions behind the code.**

---

# 16. Final Learning Outcome

After completing this project, the goal is to understand an AI Agent system from the bottom up:

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

The final objective is not to build the biggest Agent framework.

It is to build a system small enough to understand, but complete enough to demonstrate that we understand the fundamental engineering concepts behind modern AI Agents.

> **Build it from scratch. Understand every layer. Break it. Fix it. Measure it. Then explain why it works.**
