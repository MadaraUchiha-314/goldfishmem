# ADR-002: Context Construction Ownership

- **Status:** Accepted
- **Date:** 2026-05-15
- **Resolves:** PRD open question #2 (§7, §14)
- **Epic:** #5 (E0: Project bootstrap & ADRs)

## Context

The goldfishmem PRD (§7) distinguishes two concerns:

1. **Memory retrieval** — a fuzzy search problem: given a task, find all relevant
   memories across vector, graph, and hierarchy stores.
2. **Context construction** — a domain problem: given retrieved memories plus
   domain knowledge about the task, assemble the prompt context that makes the
   executor most effective.

The PRD explicitly flags this as an open question:

> *"Construction" is a domain problem — why should this system own those
> prompts?* Whether context construction belongs inside `goldfishmem` (as an
> opinionated helper) or strictly outside it (with the system returning only
> ranked memories and provenance) is an unresolved architectural question for v1.

This ADR resolves that question.

## Options Considered

### Option 1: Outside only

goldfishmem's API boundary stops at **ranked memories + provenance**. The
consuming agent or application is fully responsible for:

- Deciding how to format memories into prompt context.
- Managing context window budgets (truncation, summarization).
- Applying domain-specific ranking adjustments.

**Pros:**

- Clean separation of concerns — goldfishmem is a pure memory retrieval library.
- Maximum flexibility for consumers; no opinions to fight.
- Smaller API surface, fewer breaking changes.

**Cons:**

- Every consumer reimplements the same boilerplate (formatting, truncation,
  deduplication).
- Best practices for context assembly are not codified — each team learns
  independently what works.
- Harder to collect feedback on context quality if construction happens entirely
  outside the system.

### Option 2: Inside as opinionated helper

goldfishmem owns context construction end-to-end. The API accepts a task
description and returns a **ready-to-use context block** (or prompt fragment)
rather than raw memories.

**Pros:**

- Turnkey experience — consumers call one method and get usable context.
- goldfishmem can optimize the full pipeline (retrieval → ranking → formatting)
  holistically.
- Feedback loop is simpler because the system controls the entire output.

**Cons:**

- Domain logic leaks into the library. A finance app and a coding assistant need
  very different context construction strategies; one opinionated path cannot
  serve both.
- Tight coupling — consumers cannot customize formatting without forking or
  monkey-patching.
- Larger API surface with more domain assumptions baked in.

### Option 3: Hybrid — retrieval core + optional construction utilities

goldfishmem's **core API boundary is ranked memories + provenance** (same as
Option 1). Additionally, goldfishmem ships an **optional `context` module** that
provides composable utilities consumers can opt into:

- **Formatters** — convert memories into prompt-friendly text representations
  (Markdown, structured XML, plain text).
- **Rankers / re-rankers** — apply secondary ranking (recency boost, type
  weighting, deduplication).
- **Budget managers** — context-window-aware truncation and summarization that
  respect token limits.
- **Assemblers** — combine formatter + ranker + budget manager into a pipeline
  that produces a context block from a set of memories.

Consumers who want full control use the core retrieval API and ignore the
`context` module. Consumers who want convenience compose the utilities or use a
default assembler.

**Pros:**

- Core API stays clean — ranked memories + provenance is the contract.
- Utilities reduce boilerplate without imposing domain opinions.
- Composable design means consumers mix and match; domain-specific logic stays
  in the consumer's code.
- The feedback loop can still instrument the optional utilities without requiring
  consumers to use them.

**Cons:**

- Two "layers" to maintain (core retrieval + optional context utilities).
- Risk of the optional layer growing into an opinionated framework over time if
  not disciplined.
- Consumers must still understand the building blocks to compose them
  effectively.

## Decision

**Option 3: Hybrid — retrieval core + optional construction utilities.**

The core `goldfishmem` API returns ranked memories and provenance. An optional
`goldfishmem.context` module provides composable utilities (formatters, rankers,
budget managers, assemblers) that consumers can opt into.

### Rationale

| Criterion              | Outside only | Inside (opinionated) | Hybrid       |
|------------------------|--------------|----------------------|--------------|
| Separation of concerns | Excellent    | Poor                 | Good         |
| Reusability            | Excellent    | Poor                 | Excellent    |
| Developer experience   | Poor         | Excellent            | Good         |
| Extensibility          | Excellent    | Poor                 | Good         |
| Feedback integration   | Poor         | Excellent            | Good         |

The hybrid approach gives us the clean API boundary that keeps goldfishmem
domain-agnostic, while shipping enough utilities that consumers don't have to
reinvent formatting and truncation. The key discipline is: **the `context`
module must remain composable and stateless** — it transforms memories into text,
it does not own domain logic or prompt templates.

## Consequences

### Positive

- goldfishmem stays reusable across domains (finance, coding, support, etc.)
  without consumers needing to fight library opinions.
- Common operations (formatting, truncation, deduplication) are codified once and
  shared across consumers.
- The core retrieval API is stable and narrow, reducing breaking changes.

### Negative

- Two layers to document and maintain.
- Requires discipline to keep the `context` module composable and prevent it
  from growing into an opinionated framework.
- Consumers who want the turnkey experience (Option 2) will need slightly more
  setup than a single function call.

### Follow-up actions

- When implementing the retrieval API (E4), ensure the response type includes
  provenance metadata alongside ranked memories.
- Design the `goldfishmem.context` module as a separate, optional subpackage
  that depends only on the core memory types.
- Document the composable utilities with examples for common patterns.
