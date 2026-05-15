# ADR-003: Self-Improvement Levers

- **Status:** Accepted
- **Date:** 2026-05-15
- **Resolves:** PRD open question #3 (§9, §14)
- **Epic:** #5 (E0: Project bootstrap & ADRs)

## Context

The goldfishmem PRD (§9) states an opinion about what is tunable in an agentic
system:

> **Opinion (to be challenged):** in any agentic system, only two variables are
> under our control — the **prompt** and the **LLM weights**.

The PRD itself flags this as an open question and invites challenge:

> Are there other levers — retrieval policy, index structure, tool design,
> ranking heuristics — that we should treat as tunable in the self-improvement
> loop?

This ADR resolves that question by examining which levers exist, how amenable
each is to automated tuning, and which should be included in the
self-improvement loop.

## Levers Identified

Beyond prompt and LLM weights, the following additional levers affect the
quality of the memory system's output:

1. **Retrieval policy** — search strategy (vector, BM25, graph traversal, or
   hybrid), result count per search, fan-out across stores, query rewriting
   strategy.
2. **Ranking heuristics** — re-ranking weights, recency decay functions, memory
   type boosting, diversity penalties, deduplication thresholds.
3. **Memory lifecycle policies** — TTL for memory expiry, consolidation
   thresholds (when to merge related memories), deduplication rules, archival
   triggers.
4. **Index structure** — embedding model choice, chunk size, graph schema
   (node/edge types and properties), vector index parameters (e.g., HNSW
   ef_construction).
5. **Tool design** — the schemas and descriptions of tools exposed to the memory
   agent (retrieval tools, extraction tools, reflection tools).

## Options Considered

### Option 1: Prompt + weights only (PRD status quo)

Keep the self-improvement loop focused on prompt optimization and LLM
fine-tuning. All other parameters are fixed at design time and changed only
through manual engineering effort.

**Pros:**

- Simplest implementation — the self-improvement loop has a narrow scope.
- Fewer moving parts means less risk of cascading configuration changes.
- Prompt and weights are the highest-leverage variables.

**Cons:**

- Leaves significant optimization potential on the table. Retrieval policy and
  ranking heuristics can have outsized impact on memory quality with relatively
  low risk.
- Forces manual tuning for parameters that have clear, measurable feedback
  signals (e.g., retrieval precision, ranking quality).
- Does not match the reality of the system — retrieval policy directly affects
  what the LLM sees, so tuning the prompt without tuning retrieval is
  optimizing only half the pipeline.

### Option 2: All levers are automated

Every identified lever (prompt, weights, retrieval policy, ranking heuristics,
memory lifecycle, index structure, tool design) is exposed to the automated
self-improvement loop.

**Pros:**

- Maximum optimization surface — the system can explore the full configuration
  space.
- No human bottleneck for any tuning decision.

**Cons:**

- Some levers (index structure, tool design) have high blast radius when changed
  — a bad embedding model swap or graph schema migration can break the entire
  system.
- Index structure changes require re-indexing, which is expensive and
  disruptive.
- Tool design changes affect the agent's action space in ways that are hard to
  evaluate automatically.
- The search space becomes intractably large, making optimization unreliable.

### Option 3: Two-tier lever classification

Classify levers into two tiers based on tunability, risk, and feedback signal
availability:

- **Tier 1 (automated tuning):** levers that can be safely adjusted by the
  self-improvement loop using feedback signals.
- **Tier 2 (evaluation-informed manual):** levers that should be changed by
  engineers, informed by evaluation data, but not automatically adjusted.

**Pros:**

- Expands the optimization surface beyond prompt + weights without taking on
  excessive risk.
- Tier 1 levers have clear feedback signals and bounded blast radius.
- Tier 2 levers benefit from evaluation data without being subject to
  automated, potentially destabilizing changes.
- Matches the natural change frequency of each lever — fast-moving parameters
  are automated, slow-moving parameters are manual.

**Cons:**

- More complex than Option 1 — the self-improvement loop must handle multiple
  lever types.
- Requires clear tier boundaries and governance to prevent scope creep from
  Tier 2 into Tier 1.

## Decision

**Option 3: Two-tier lever classification.**

The PRD opinion is too narrow. Prompt and weights are the highest-impact levers,
but they are not the only ones. Retrieval policy, ranking heuristics, and memory
lifecycle policies are also tunable by the self-improvement loop. Index
structure and tool design change less frequently and should remain manual
decisions informed by evaluation data.

### Tier 1 — Automated tuning

These levers are adjusted by the self-improvement loop using feedback from
extraction, retrieval, and usage signals (PRD §8):

| Lever                  | Examples                                                       |
|------------------------|----------------------------------------------------------------|
| Prompt optimization    | Extraction prompts, retrieval query prompts, reflection prompts|
| LLM fine-tuning        | Task-specific fine-tuning on feedback data                     |
| Retrieval policy       | Search strategy mix, result count, fan-out, query rewriting    |
| Ranking heuristics     | Re-ranking weights, recency decay, type boosting, diversity    |
| Memory lifecycle       | TTL values, consolidation thresholds, dedup rules              |

### Tier 2 — Evaluation-informed manual

These levers are changed by engineers based on evaluation and benchmark results,
not by the automated loop:

| Lever                  | Examples                                                       |
|------------------------|----------------------------------------------------------------|
| Index structure        | Embedding model, chunk size, graph schema, HNSW parameters     |
| Tool design            | Agent tool schemas, tool descriptions, available tool set       |

### Lever comparison

| Lever                  | Tunability       | Impact   | Feedback signal     | Change frequency |
|------------------------|------------------|----------|---------------------|------------------|
| Prompt optimization    | Automated        | High     | Direct (usage, retrieval quality) | Per evaluation cycle |
| LLM fine-tuning        | Automated        | High     | Direct (task success, feedback) | Weekly/monthly |
| Retrieval policy       | Automated        | High     | Direct (retrieval precision/recall) | Per evaluation cycle |
| Ranking heuristics     | Automated        | Medium   | Direct (ranking quality, usage) | Per evaluation cycle |
| Memory lifecycle       | Automated        | Medium   | Indirect (memory freshness, dedup rate) | Daily/weekly |
| Index structure        | Manual           | High     | Indirect (benchmark results) | Monthly/quarterly |
| Tool design            | Manual           | Medium   | Indirect (agent trace analysis) | Per release |

### Rationale

The key insight is that the self-improvement loop should encompass any lever
that meets three criteria:

1. **Measurable feedback signal** — the lever's effect can be observed through
   the feedback mechanisms defined in PRD §8 (extraction quality, retrieval
   quality, usage feedback).
2. **Bounded blast radius** — a bad configuration change can be detected and
   rolled back without data loss or system-wide disruption.
3. **Reasonable change frequency** — the lever benefits from frequent adjustment
   (per evaluation cycle or faster).

Retrieval policy and ranking heuristics clearly meet all three criteria: their
impact is directly measurable through retrieval precision and usage feedback,
changes are configuration-level (no re-indexing), and they benefit from
continuous tuning. Memory lifecycle policies also meet the criteria, though
their feedback signals are more indirect.

Index structure fails criterion 2 (re-indexing is expensive and risky) and
criterion 3 (changes are infrequent by nature). Tool design fails criterion 1
(feedback signals are indirect and noisy) and criterion 2 (changing the agent's
tool set can cause unpredictable behavior shifts).

## Consequences

### Positive

- The self-improvement loop optimizes a broader surface than prompt + weights
  alone, capturing optimization opportunities in retrieval and ranking.
- Tier 1 levers have clear feedback signals, making automated tuning
  well-grounded in measurable outcomes.
- Tier 2 levers still benefit from evaluation data without being exposed to
  automated instability.
- The tiered model provides a clear framework for deciding where future levers
  belong.

### Negative

- The self-improvement loop is more complex than a prompt-only optimizer — it
  must manage configuration for retrieval policy, ranking, and lifecycle in
  addition to prompts and weights.
- Automated tuning of memory lifecycle policies requires careful guardrails to
  prevent overly aggressive TTLs or consolidation that destroys valuable
  memories.
- The boundary between Tier 1 and Tier 2 may need revisiting as the system
  matures and feedback signals improve.

### Follow-up actions

- When designing the self-improvement layer, ensure the architecture supports
  tuning retrieval policy and ranking heuristics alongside prompt optimization.
- Define rollback mechanisms for Tier 1 lever changes (e.g., configuration
  versioning, A/B testing framework).
- Establish evaluation benchmarks (PRD §12) that measure the impact of each
  Tier 1 lever independently.
- Create a governance process for promoting levers from Tier 2 to Tier 1 as
  feedback signals and safety mechanisms mature.
