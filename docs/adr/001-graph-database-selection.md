# ADR-001: Graph Database Selection

- **Status:** Accepted
- **Date:** 2026-05-13
- **Resolves:** PRD open question #1 (§6, §14)
- **Epic:** #5 (E0: Project bootstrap & ADRs)

## Context

The goldfishmem architecture (PRD §6) calls for a **graph store** that holds
relationships between memory entities, enabling knowledge-graph-style retrieval
(multi-hop traversal, pattern matching, subgraph extraction). The graph store
works alongside the vector/search store and the memory metadata store to provide
a rich retrieval surface for the memory agent (PRD §7).

Key requirements derived from the PRD:

1. Store and traverse relationships between memory entities (memories, entities,
   observations, interactions).
2. Support multi-hop queries and graph pattern matching for retrieval.
3. Integrate cleanly with a Python 3.12+ codebase.
4. Provide both a production deployment path and a lightweight local/test option.
5. Be cost-effective for a project that starts small and may scale later.

## Options Considered

### 1. Neo4j

- **Overview:** The most mature and widely adopted property graph database.
  Cypher query language is the industry standard for graph pattern matching.
- **Managed option:** Neo4j AuraDB (cloud-hosted, free tier available).
- **Self-hosted:** Docker image, Helm charts, well-documented.
- **Python client:** Official `neo4j` driver (bolt protocol), excellent quality
  and maintained by Neo4j Inc.
- **Testing:** Neo4j can run in a Docker container for integration tests. No
  true in-process/embedded mode for Python, but fast container startup makes
  this workable.
- **License:** Community Edition is GPLv3; Enterprise Edition is commercial.
  AuraDB free tier is sufficient for early development.
- **Strengths:** Rich ecosystem, mature tooling, best-in-class Cypher support,
  APOC plugin library for graph algorithms, large community.
- **Weaknesses:** GPLv3 license for Community Edition may be a concern for some
  deployments; Enterprise features (clustering, role-based access) require a
  commercial license.

### 2. Amazon Neptune

- **Overview:** AWS-managed graph database supporting both property graph
  (openCypher, Gremlin) and RDF (SPARQL).
- **Python client:** Gremlin Python client or openCypher via Bolt.
- **Testing:** No local/embedded option; requires an AWS account and a running
  Neptune instance even for development.
- **License:** Proprietary (AWS service).
- **Strengths:** Fully managed, scales well, integrates with AWS ecosystem.
- **Weaknesses:** Vendor lock-in to AWS, no local development story, expensive
  for small workloads, cold-start latency.

### 3. DGraph

- **Overview:** Open-source, distributed, GraphQL-native graph database.
- **Python client:** `pydgraph` client (gRPC-based).
- **Testing:** Runs in Docker; no embedded mode.
- **License:** Apache 2.0 (core), proprietary for enterprise features.
- **Strengths:** Distributed by design, GraphQL-native API, good horizontal
  scaling story.
- **Weaknesses:** Smaller community than Neo4j, GraphQL schema is rigid for
  evolving data models, Python client is less polished, project governance
  has had instability.

### 4. FalkorDB (formerly RedisGraph)

- **Overview:** A graph database that runs as a Redis module. Uses a subset of
  Cypher (openCypher) and is optimized for low-latency queries on
  small-to-medium graphs.
- **Python client:** `falkordb` Python package (Redis-protocol-based).
- **Testing:** Runs in Docker via Redis + FalkorDB module; fast startup.
- **License:** Source-available (SSPL for the Redis module layer).
- **Strengths:** Very fast for small-medium graphs, Cypher compatibility,
  lightweight deployment.
- **Weaknesses:** Subset of Cypher (no full APOC-style algorithms), less mature
  ecosystem, SSPL license may be restrictive, in-memory-first design means
  cost scales with data size.

### 5. NetworkX (in-memory, Python-native)

- **Overview:** Python library for creating and analyzing graphs. Not a
  database — purely in-memory, no persistence, no query language.
- **Python client:** It *is* the Python library.
- **Testing:** Ideal for unit tests — zero infrastructure, instant startup,
  fully deterministic.
- **License:** BSD.
- **Strengths:** Zero dependencies, trivially embeddable in tests, full access
  to graph algorithms, Pythonic API.
- **Weaknesses:** No persistence, no query language (imperative Python API
  only), will not scale beyond single-process memory limits, not suitable for
  production.

## Decision

**Use Neo4j as the production graph store** and **define an abstract graph store
interface** (`goldfishmem.stores.graph.GraphStore`) that allows swapping
implementations.

For **testing and local development**, provide an **in-memory implementation
backed by NetworkX** that conforms to the same interface. This avoids requiring
Docker or a running Neo4j instance for unit tests while keeping the production
path well-defined.

### Rationale

| Criterion               | Neo4j     | Neptune | DGraph  | FalkorDB | NetworkX |
|--------------------------|-----------|---------|---------|----------|----------|
| Query expressiveness     | Excellent | Good    | Good    | Good     | N/A      |
| Python ecosystem         | Excellent | Fair    | Fair    | Good     | Excellent|
| Deployment flexibility   | Good      | Poor    | Good    | Good     | Excellent|
| Production scalability   | Excellent | Excellent| Good   | Fair     | None     |
| Cost (early stage)       | Free tier | Expensive| Free   | Free     | Free     |
| Testing story            | Docker    | None    | Docker  | Docker   | In-process|
| License compatibility    | GPLv3/Comm| Propri. | Apache  | SSPL     | BSD      |

Neo4j provides the best combination of query expressiveness (full Cypher +
APOC), Python ecosystem quality, community size, and managed hosting options.
The abstract interface ensures we are not locked in — if a future requirement
(e.g., license constraints, cost at scale) makes a different backend preferable,
the swap is contained to a single implementation module.

## Consequences

### Positive

- Mature, well-documented graph database with strong community support.
- Cypher is expressive enough for the multi-hop retrieval patterns the memory
  agent needs.
- The abstract interface + NetworkX test backend means unit tests run fast with
  no external dependencies.
- AuraDB free tier means zero cost during early development.

### Negative

- Neo4j Community Edition is GPLv3, which may conflict with some deployment
  scenarios. If this becomes an issue, we can implement the interface against
  DGraph (Apache 2.0) or FalkorDB.
- Integration tests that exercise the real Neo4j backend will require Docker.
- Two implementations (Neo4j + NetworkX) means maintaining interface
  compatibility across both.

### Follow-up actions

- Define the `GraphStore` abstract interface as part of E1/E2 implementation.
- Add a Neo4j Docker Compose configuration for integration tests.
- Evaluate whether the GPLv3 license is acceptable for the project's
  distribution model; if not, revisit this ADR.
