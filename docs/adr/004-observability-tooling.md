# ADR-004: Observability Tooling

- **Status:** Accepted
- **Date:** 2026-05-15
- **Resolves:** PRD open question #4 (§13, §14)
- **Epic:** #5 (E0: Project bootstrap & ADRs)

## Context

The goldfishmem PRD (§13) requires a visualisation tool that makes the memory
system inspectable. The tool must support:

1. Viewing memories that were **created** and **retrieved**.
2. Inspecting the **memory agent trace** — the actions taken by the memory agent
   during extraction (when a new interaction arrives) and during retrieval (when
   memory is requested for a task).
3. Displaying **provenance lineage graphs** showing the derivation chain from raw
   sources through intermediate memories to final memories.

The PRD poses an open question: can we use Langfuse (or a similar agent
observability tool) for the trace portion, and build a thin custom UI only for
memory-specific inspector views?

This ADR evaluates the tooling strategy for observability across the entire
goldfishmem system.

## Options Considered

### Option 1: Langfuse Only

Use Langfuse as the sole observability tool for all visualisation needs: agent
traces, memory inspection, and feedback tracking.

- **Overview:** Langfuse is an open-source LLM observability platform with
  support for traces, spans, generations, scores, and prompt management. It
  provides a timeline/waterfall view of agent execution, token usage tracking,
  and evaluation scores.
- **Pros:**
  - Mature, actively developed, open-source (MIT license).
  - Self-hostable or available as a managed cloud service.
  - Excellent LLM trace support: span waterfall, token usage, latency breakdown,
    prompt/completion inspection.
  - Built-in feedback/scoring system that aligns with goldfishmem's feedback
    loop (PRD §8).
  - Python SDK with decorator-based instrumentation (`@observe`).
  - OpenAI-compatible and growing LLM provider support.
- **Cons:**
  - No native support for memory-specific views: provenance lineage graphs,
    memory hierarchy browsing, or memory diff visualisation.
  - Customising Langfuse's UI to add domain-specific views would require forking
    or contributing upstream, which is impractical for niche memory-system needs.
  - Memory entity relationships and graph structures do not map naturally to
    Langfuse's trace/span model.

### Option 2: Custom UI Only

Build a fully bespoke observability UI tailored to goldfishmem's domain.

- **Overview:** Develop a custom web application (e.g., React/Next.js frontend
  with a Python backend) that provides all observability views: agent traces,
  memory inspection, provenance lineage, feedback dashboards.
- **Pros:**
  - Fully tailored to the memory domain — every view is purpose-built.
  - No constraints from third-party data models or UI paradigms.
  - Complete control over UX, data freshness, and deployment.
- **Cons:**
  - Massive build effort — reinvents solved problems like trace timelines, span
    waterfalls, token usage dashboards, and log aggregation.
  - Ongoing maintenance burden for features that observability platforms already
    provide and continuously improve.
  - Delays delivery of the core memory system by diverting engineering effort
    to UI infrastructure.

### Option 3: Hybrid — Langfuse for Traces + Custom Memory Inspector

Use Langfuse (or an equivalent platform such as LangSmith or Arize Phoenix) for
agent trace visualisation, and build a thin custom UI only for memory-specific
views that no generic observability tool supports.

- **Overview:** Instrument goldfishmem to emit **OpenTelemetry-compatible spans**
  for all agent operations (extraction, retrieval, reflection, context
  construction). These spans are ingested by Langfuse for trace visualisation.
  Separately, build a lightweight custom inspector for memory-domain views:
  provenance lineage graphs, memory hierarchy browser, and memory diff.
- **Pros:**
  - Leverages Langfuse's strengths (trace timeline, span waterfall, token
    tracking, scoring) without rebuilding them.
  - Custom inspector is scoped to only what generic tools cannot provide,
    keeping the build effort small and focused.
  - OpenTelemetry instrumentation means the system is not locked into Langfuse —
    traces can be routed to any OTel-compatible backend (LangSmith, Arize
    Phoenix, Jaeger, Grafana Tempo).
  - Clean separation of concerns: generic observability vs. domain-specific
    inspection.
- **Cons:**
  - Two systems to operate (Langfuse + custom inspector), increasing deployment
    surface.
  - Must define a clear boundary between what lives in Langfuse and what lives
    in the custom inspector to avoid duplication.
  - OpenTelemetry instrumentation adds a dependency and requires careful span
    design to be useful across backends.

## Comparison

| Criterion                        | Langfuse Only | Custom UI Only | Hybrid (Option 3) |
|----------------------------------|---------------|----------------|--------------------|
| Agent trace visualisation        | Excellent     | Must build     | Excellent (Langfuse) |
| Memory-specific views            | Poor          | Excellent      | Good (custom)      |
| Build effort                     | Low           | Very high      | Moderate           |
| Maintenance burden               | Low           | High           | Moderate           |
| Vendor lock-in                   | Moderate      | None           | Low (OTel)         |
| Time to first usable tool        | Fast          | Slow           | Fast               |
| Provenance lineage graphs        | Not supported | Full control   | Custom inspector   |
| Memory hierarchy browser         | Not supported | Full control   | Custom inspector   |
| Memory diff visualisation        | Not supported | Full control   | Custom inspector   |
| Feedback/scoring integration     | Built-in      | Must build     | Built-in (Langfuse)|
| Portability across backends      | Low           | N/A            | High (OTel)        |

## Decision

**Option 3: Hybrid — Langfuse for traces + custom memory inspector.**

Langfuse (or an equivalent OTel-compatible platform) handles agent trace
visualisation. It is purpose-built for this and does it well. A thin custom
inspector handles memory-specific views that no generic observability tool
supports: provenance lineage graphs, memory hierarchy browsing, and memory diff.

The system will be instrumented with **OpenTelemetry-compatible spans** at all
key operations (extraction, retrieval, reflection, consolidation, context
construction). This ensures portability: if a team prefers LangSmith, Arize
Phoenix, or a self-hosted Jaeger/Grafana Tempo stack, they can route spans there
instead of Langfuse with no code changes to goldfishmem itself.

### Rationale

1. **Don't reinvent the wheel.** Trace timelines, span waterfalls, and token
   usage dashboards are solved problems. Langfuse (and peers) provide these
   out of the box with ongoing improvements.
2. **Focus custom effort where it matters.** Provenance lineage graphs, memory
   hierarchy browsing, and memory diff are unique to goldfishmem. No generic
   tool will ever provide these views natively, so custom work here has lasting
   value.
3. **OpenTelemetry as the integration contract.** By emitting OTel spans rather
   than using Langfuse's proprietary SDK directly, goldfishmem avoids vendor
   lock-in. Langfuse already supports OTel ingestion, as do most competing
   platforms.
4. **Incremental delivery.** Langfuse can be set up immediately for trace
   visibility while the custom inspector is developed incrementally alongside
   the core memory system.

## Consequences

### Positive

- Agent trace observability is available immediately via Langfuse, unblocking
  development and debugging of the memory agent from day one.
- The custom inspector stays small and focused — only three domain-specific
  views need to be built (provenance lineage, hierarchy browser, memory diff).
- OpenTelemetry instrumentation is reusable: it benefits not just visualisation
  but also alerting, SLO monitoring, and production debugging.
- No vendor lock-in — switching trace backends is a configuration change, not a
  code change.

### Negative

- Two systems to deploy and maintain (Langfuse instance + custom inspector
  service).
- The team must define and maintain a clear boundary document specifying which
  views live where, to prevent scope creep in either direction.
- OpenTelemetry span design requires upfront thought to ensure spans are
  meaningful across different backends.

### Follow-up actions

- Define the OpenTelemetry span schema for goldfishmem operations (extraction,
  retrieval, reflection, consolidation) as part of E1/E2 implementation.
- Set up a Langfuse instance (self-hosted or cloud) for development use.
- Design the custom memory inspector's three core views: provenance lineage
  graph, memory hierarchy browser, and memory diff.
- Document the boundary between Langfuse-hosted views and custom inspector views
  to prevent duplication.
