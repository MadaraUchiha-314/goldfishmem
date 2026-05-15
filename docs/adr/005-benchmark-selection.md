# ADR-005: Benchmark Selection

- **Status:** Accepted
- **Date:** 2026-05-15
- **Resolves:** PRD open question #5 (§12, §14)
- **Epic:** #5 (E0: Project bootstrap & ADRs)

## Context

The goldfishmem PRD (§12) calls for identifying benchmarks that are meaningful
for a memory system and setting up a benchmarking process so that the system can
be evaluated and results published. A memory system's quality hinges on several
distinct abilities — information extraction, multi-session reasoning, temporal
reasoning, knowledge updates, and abstraction — as well as goldfishmem-specific
capabilities like provenance accuracy, citation quality, and multi-store
retrieval precision.

Key requirements for a benchmarking strategy:

1. Cover the core memory abilities that goldfishmem targets (extraction,
   retrieval, reasoning over long conversational histories).
2. Evaluate provenance and citation correctness — a first-class concern in
   goldfishmem (PRD §5) that most public benchmarks do not address.
3. Be reproducible and automatable so results can be published as part of CI/CD.
4. Allow comparison with other memory systems using well-known public benchmarks.
5. Support goldfishmem-specific scenarios (multi-store retrieval, hierarchical
   metadata, graph traversal) that no single external benchmark covers.

## Options Considered

### 1. LongMemEval

- **Overview:** A benchmark designed to evaluate long-term memory in
  conversational agents. It tests five core memory abilities: information
  extraction, multi-session reasoning, temporal reasoning, knowledge updates,
  and abstraction.
- **Dataset:** 500+ questions spanning multiple sessions, with ground-truth
  answers and session-level annotations.
- **Strengths:** Directly targets the memory abilities that goldfishmem is built
  to support. Multi-session design mirrors real-world usage patterns. Well-
  documented evaluation methodology. Strong coverage of temporal reasoning and
  knowledge update scenarios.
- **Weaknesses:** Does not test provenance accuracy or citation quality. No
  coverage of multi-store retrieval patterns (vector + graph + hierarchy). May
  require adaptation to feed data through goldfishmem's extraction pipeline
  rather than testing end-to-end chat agents.

### 2. LoCoMo (Longitudinal Conversational Memory)

- **Overview:** A benchmark focused on long conversational contexts. Tests
  summarization, question answering, and temporal reasoning over extended
  multi-session dialogues. Provides long conversation transcripts with
  associated QA pairs.
- **Dataset:** Multi-session conversation transcripts with hundreds of turns,
  paired with questions targeting different reasoning depths.
- **Strengths:** Good coverage of conversational memory and temporal reasoning.
  Long-context dialogues stress-test extraction and retrieval over extended
  interactions. Evaluates summarization quality, which relates to memory
  consolidation.
- **Weaknesses:** Narrower scope than LongMemEval — fewer distinct memory
  abilities tested. Less emphasis on knowledge updates and abstraction. Like
  LongMemEval, does not test provenance or citation quality. Smaller community
  adoption means fewer published baselines for comparison.

### 3. Custom Benchmark Suite

- **Overview:** A domain-specific benchmark built from goldfishmem's actual
  architecture and use cases. Tests capabilities that no external benchmark
  covers: provenance accuracy, citation quality, extraction completeness,
  retrieval precision/recall across multiple stores, and multi-hop lineage
  traversal.
- **Proposed test categories:**
  - **Provenance accuracy** — given extracted memories, verify that provenance
    records correctly reference source interactions and observations.
  - **Citation quality** — verify that citations returned by the retrieval API
    point to valid, relevant source material.
  - **Extraction completeness** — given a set of interactions, measure recall
    of memories that should have been extracted (semantic, episodic, procedural).
  - **Retrieval precision/recall** — measure how well the agentic retrieval
    pipeline finds relevant memories across vector, graph, and metadata stores.
  - **Multi-hop lineage** — verify that lineage traversal (forward and backward)
    through reflected and consolidated memories is correct and complete.
- **Strengths:** Directly tests goldfishmem's differentiating features. Can
  evolve alongside the system. Full control over test scenarios, ground truth,
  and evaluation criteria. Tests the multi-store architecture that external
  benchmarks ignore.
- **Weaknesses:** Not comparable with other systems (no published baselines).
  Requires significant upfront investment to design scenarios and curate ground
  truth. Risk of self-serving metrics if not carefully designed.

## Decision

**Use LongMemEval as the primary external benchmark**, supplemented by
**LoCoMo for conversational memory scenarios**, and **build a custom benchmark
suite** for goldfishmem-specific capabilities.

### Comparison Table

| Criterion              | LongMemEval | LoCoMo    | Custom Suite |
|------------------------|-------------|-----------|--------------|
| Scope                  | Broad (5 memory abilities) | Moderate (conversational QA, summarization) | Targeted (goldfishmem-specific) |
| Memory abilities tested| Extraction, multi-session reasoning, temporal reasoning, knowledge updates, abstraction | Summarization, QA, temporal reasoning | Provenance, citations, extraction completeness, multi-store retrieval |
| Dataset size           | 500+ questions | Medium (long transcripts, fewer QA pairs) | Defined per test category |
| Provenance coverage    | None        | None      | Full         |
| Ease of integration    | Moderate (needs pipeline adapter) | Moderate (needs pipeline adapter) | High (built for goldfishmem) |
| External comparability | High (published baselines) | Moderate (fewer baselines) | None         |

### Rationale

LongMemEval offers the best coverage of memory-specific abilities among public
benchmarks. Its five-axis evaluation (extraction, multi-session reasoning,
temporal reasoning, knowledge updates, abstraction) maps closely to
goldfishmem's extraction and retrieval pipeline. Published baselines enable
meaningful comparison with other memory systems.

LoCoMo complements LongMemEval by providing longer conversational contexts that
stress-test the extraction pipeline and evaluate summarization/consolidation
quality. It serves as a supplementary benchmark rather than a primary one due to
its narrower scope.

Neither external benchmark tests provenance accuracy, citation quality, or
multi-store retrieval — all first-class concerns in goldfishmem. The custom
benchmark suite fills this gap and ensures that goldfishmem's differentiating
features are continuously measured.

## Consequences

### Positive

- LongMemEval provides a well-established external yardstick for core memory
  abilities, enabling credible comparison with other systems.
- The custom suite ensures that provenance, citations, and multi-store retrieval
  — goldfishmem's key differentiators — are measured from day one.
- LoCoMo provides additional coverage for long-context conversational scenarios
  without significant integration overhead beyond what LongMemEval requires.
- The combined strategy covers both external credibility (public benchmarks) and
  internal quality assurance (custom suite).

### Negative

- Maintaining three benchmark integrations (LongMemEval, LoCoMo, custom) adds
  CI/CD complexity and ongoing maintenance burden.
- The custom benchmark suite requires upfront investment to design test
  scenarios and curate ground truth data.
- Adapting external benchmarks to goldfishmem's pipeline (rather than testing
  end-to-end chat agents) may require non-trivial adapter code.

### Follow-up actions

- Build pipeline adapters to run LongMemEval and LoCoMo datasets through
  goldfishmem's extraction and retrieval stages.
- Design the custom benchmark suite's test categories, ground truth format, and
  scoring methodology.
- Integrate benchmark runs into CI/CD so results are tracked over time.
- Publish initial baseline results once the extraction and retrieval pipelines
  are functional.
