# Architecture

This page describes the high-level architecture of goldfish. Diagrams are
written in [mermaid](https://mermaid.js.org/) so they render inline on GitHub.

> The project is in its earliest stage — this page currently shows the intended
> shape of the system as a placeholder. Concrete components will land here as
> they are built and merged.

## High-level shape

```mermaid
flowchart LR
    Agent[LLM Agent]
    API[goldfishmem API]
    Store[(Memory Store)]
    Index[[Search / Recall Index]]

    Agent -->|write| API
    Agent -->|recall| API
    API --> Store
    API --> Index
    Index --> Store
```

## Lifecycle of a memory

```mermaid
sequenceDiagram
    participant Agent
    participant API as goldfishmem
    participant Store
    participant Index

    Agent->>API: remember(text, metadata)
    API->>Store: persist
    API->>Index: embed + insert
    Index-->>API: ack
    API-->>Agent: id

    Agent->>API: recall(query)
    API->>Index: search(query)
    Index-->>API: ranked ids
    API->>Store: fetch(ids)
    Store-->>API: records
    API-->>Agent: results
```

## Where to read next

- The package source lives under [`goldfishmem/`](https://github.com/MadaraUchiha-314/goldfish/tree/main/goldfishmem).
- Test layout: [`tests/unit/`](https://github.com/MadaraUchiha-314/goldfish/tree/main/tests/unit) and [`tests/integration/`](https://github.com/MadaraUchiha-314/goldfish/tree/main/tests/integration).
