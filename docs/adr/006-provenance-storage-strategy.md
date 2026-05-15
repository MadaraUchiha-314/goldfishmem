# ADR-006: Provenance Storage Strategy

- **Status:** Accepted
- **Date:** 2026-05-15
- **Resolves:** PRD open question #6 (§14)
- **Epic:** #5 (E0: Project bootstrap & ADRs)

## Context

The goldfishmem PRD (§5) defines a provenance model where every memory carries a
derivation record from the moment of creation. A provenance record captures
source interactions, source observations, parent memories (for reflection and
consolidation), extraction run ID, timestamp, and extraction method. The PRD
(§6) further specifies that the metadata store maintains **provenance indexes**
supporting both forward (source -> derived memories) and backward (memory ->
sources) lineage queries.

ADR-001 chose Neo4j as the graph store, with an abstract `GraphStore` interface
backed by NetworkX for testing. ADR-002 established that the core retrieval API
returns **ranked memories + provenance** as its contract, making provenance a
first-class part of every API response.

The open question is: where should provenance and lineage data live? The graph
store is a natural fit for multi-hop traversal queries (lineage exploration,
impact analysis), but the metadata store is where memory records already reside
and where single-record lookups are fastest. The PRD does not prescribe a
specific storage strategy, leaving this as an explicit architectural decision
(§14, open question #6).

## Options Considered

### Option 1: Graph store only (Neo4j)

Store all provenance as relationships and nodes in the graph store. Each memory
node has `DERIVED_FROM`, `EXTRACTED_FROM`, and `REFLECTS_ON` relationships
linking it to its source interactions, observations, and parent memories.

**Pros:**

- Multi-hop lineage queries are native graph operations — Cypher handles
  arbitrary-depth traversal efficiently.
- Single source of truth for all relationship data.
- Provenance is naturally a graph; storing it in a graph database is a direct
  conceptual mapping.

**Cons:**

- Every memory read that needs "who created this?" requires a graph query, even
  for simple single-record lookups. This adds latency to the critical retrieval
  path.
- The graph store becomes a hard dependency for all provenance access, including
  the common case where only immediate provenance (not full lineage) is needed.
- Provenance data is split from the memory record itself — consumers must join
  data from two stores (metadata + graph) for a complete picture.

### Option 2: Metadata store only

Store provenance as structured fields on the memory record in the metadata store.
Each memory record carries its provenance inline (source references, extraction
metadata, parent memory IDs).

**Pros:**

- Simple — provenance is co-located with the memory, no cross-store joins.
- Fast single-record lookups; reading a memory gives you its provenance for free.
- No additional infrastructure dependency for provenance access.

**Cons:**

- Multi-hop lineage requires application-level traversal: recursive queries or
  iterative lookups to walk the derivation chain.
- Forward queries (source -> all derived memories) require scanning or
  maintaining secondary indexes in the metadata store.
- The metadata store is not optimized for graph traversal patterns; performance
  degrades as lineage depth increases.

### Option 3: Dual storage (primary in metadata, projected to graph)

Store the canonical provenance record in the metadata store, co-located with
each memory record. Project the lineage relationships (edges between memories,
between memories and sources) into the graph store as a materialized view. The
graph store is not the source of truth for provenance — it is a projection
optimized for traversal queries.

Sync happens during `write_memories()`: after the memory and its provenance are
persisted to the metadata store, the lineage relationships are written to the
graph store in the same write path.

**Pros:**

- Fast single-record lookups from the metadata store — reading a memory gives
  immediate provenance without a graph query.
- Efficient multi-hop traversal from the graph store — lineage exploration and
  impact analysis use native graph operations.
- Clean separation of read patterns: simple lookups go to metadata, traversal
  goes to graph.
- The metadata store remains the single source of truth; the graph projection
  can be rebuilt from it if needed.

**Cons:**

- Two stores must be kept in sync. A failure in the graph write after a
  successful metadata write creates inconsistency.
- Slightly more complex write path (two writes instead of one).
- Storage overhead — provenance relationships are stored twice (inline in
  metadata, as edges in graph).

## Decision

**Option 3: Dual storage — canonical provenance in metadata store, lineage
relationships projected to graph store.**

Every memory record carries its provenance inline in the metadata store. During
`write_memories()`, the lineage relationships (memory-to-source, memory-to-parent)
are also written to the graph store as edges. The graph store's provenance data
is a materialized view, not the source of truth.

### Rationale

Most memory reads need just the immediate provenance: "what sources contributed
to this memory?" and "when was it extracted?". These are single-record lookups
that the metadata store handles efficiently — no graph query required.

Lineage exploration ("show me the full derivation chain from raw interaction to
final consolidated memory") and impact analysis ("what memories are affected if
this source is retracted?") are less frequent but require multi-hop traversal.
These are the queries the graph store (Neo4j, per ADR-001) excels at.

The dual approach optimizes for both access patterns without forcing every read
through the graph store.

| Criterion                    | Graph only       | Metadata only       | Dual storage        |
|------------------------------|------------------|---------------------|---------------------|
| Single-record lookup latency | High (graph hop) | Low (co-located)    | Low (co-located)    |
| Multi-hop traversal          | Native (Cypher)  | Poor (app-level)    | Native (Cypher)     |
| Consistency model            | Single store     | Single store        | Eventual (two stores) |
| Write complexity             | Low              | Low                 | Medium (two writes) |
| Storage overhead             | Low              | Low                 | Medium (duplicated edges) |

The consistency trade-off is manageable: `write_memories()` writes to both
stores in the same call, and if the graph write fails, the metadata store still
has the canonical record. A background reconciliation process can detect and
repair drift by replaying metadata provenance into the graph store.

### Sync strategy

1. **Write path:** `write_memories()` persists the memory (with inline
   provenance) to the metadata store, then writes the lineage edges to the
   graph store. Both writes happen in the same method call.
2. **Failure handling:** If the graph write fails, the memory is still
   persisted with its provenance in the metadata store. The graph projection
   is marked as potentially stale, and a reconciliation pass can repair it.
3. **Rebuild:** The graph store's provenance projection can be fully rebuilt
   from the metadata store at any time, since the metadata store is the source
   of truth.

## Consequences

### Positive

- The critical retrieval path (read memory + immediate provenance) does not
  require a graph query, keeping latency low.
- Lineage exploration and impact analysis use native graph traversal, avoiding
  slow application-level recursive queries.
- The metadata store is the single source of truth for provenance, simplifying
  the consistency model — the graph is a rebuildable projection.
- Aligns with ADR-002: the core API returns ranked memories with provenance,
  and provenance is available directly from the memory record without a
  secondary lookup.

### Negative

- Two stores must be kept in sync during writes, adding complexity to the
  write path.
- Storage overhead from duplicating lineage relationships across both stores.
- The reconciliation process (to repair graph drift) is additional
  infrastructure to implement and operate.

### Follow-up actions

- Implement the provenance fields on the memory record type in the metadata
  store schema (E1/E2).
- Implement the graph projection of lineage edges as part of `write_memories()`
  (E2/E3).
- Design and implement the background reconciliation process that detects and
  repairs drift between metadata and graph provenance.
- Add integration tests that verify provenance consistency across both stores
  after writes.
