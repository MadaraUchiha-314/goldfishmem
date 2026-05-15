"""Core data models for the goldfishmem memory system.

Defines the foundational types referenced throughout the PRD:
- Input types: Interaction, Observation
- Memory type: Memory (single type, memory_type is config-driven)
- Provenance types: Provenance, Citation, InteractionRef, ObservationRef, MemoryRef
- Supporting types: ExtractionMethod, EmbeddingMetadata
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

# ---------------------------------------------------------------------------
# Default type constants
# ---------------------------------------------------------------------------

# Default source types (PRD §4). Users can define additional source types
# through configuration.
SOURCE_TYPE_CONVERSATION: str = "conversation"
SOURCE_TYPE_CLICKSTREAM: str = "clickstream"
SOURCE_TYPE_DOCUMENT: str = "document"
SOURCE_TYPE_DOMAIN_ENTITY: str = "domain_entity"

# Default memory types (PRD §5). Users can define additional memory types
# through configuration.
MEMORY_TYPE_SEMANTIC: str = "semantic"
MEMORY_TYPE_EPISODIC: str = "episodic"
MEMORY_TYPE_PROCEDURAL: str = "procedural"


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ExtractionMethod(Enum):
    """How a memory was produced (PRD §5 lifecycle).

    LLM_EXTRACTION: extracted directly from interactions/observations by the LLM.
    REFLECTION: synthesized from existing memories by the reflect() step.
    CONSOLIDATION: created by merging/deduplicating existing memories.
    """

    LLM_EXTRACTION = "llm_extraction"
    REFLECTION = "reflection"
    CONSOLIDATION = "consolidation"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _new_id() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# Provenance & citation types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class InteractionRef:
    """Lightweight reference to an Interaction."""

    id: str
    source_type: str


@dataclass(frozen=True)
class ObservationRef:
    """Lightweight reference to an Observation."""

    id: str


@dataclass(frozen=True)
class MemoryRef:
    """Lightweight reference to a Memory."""

    id: str
    memory_type: str


@dataclass(frozen=True)
class Provenance:
    """Derivation record attached to every Memory (PRD §5 provenance model).

    Tracks which sources a memory was derived from, when, and how.
    """

    extraction_run_id: str
    extracted_at: datetime
    extraction_method: ExtractionMethod
    source_interactions: tuple[InteractionRef, ...] = ()
    source_observations: tuple[ObservationRef, ...] = ()
    source_memories: tuple[MemoryRef, ...] = ()


@dataclass(frozen=True)
class Citation:
    """Consumer-facing reference returned alongside a memory.

    Contains enough information to locate and verify the original source
    material in the raw data store.
    """

    source_type: str
    source_id: str
    excerpt: str
    raw_data_uri: str
    span: str = ""


# ---------------------------------------------------------------------------
# Embedding metadata
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EmbeddingMetadata:
    """Describes the embedding associated with a stored entity (PRD §6)."""

    text: str
    model: str
    dimensions: int


# ---------------------------------------------------------------------------
# Input types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Interaction:
    """An event between a user and the product (PRD §1, §4).

    Represents a message, clickstream event, uploaded document, domain event,
    etc. that the memory system can learn from.
    """

    source_type: str
    content: dict[str, Any]
    id: str = field(default_factory=_new_id)
    timestamp: datetime = field(default_factory=_now)
    metadata: dict[str, Any] = field(default_factory=lambda: dict[str, Any]())


@dataclass(frozen=True)
class Observation:
    """Normalised internal type that all input sources are converted to (PRD §4).

    An Observation is the uniform representation fed into the extraction
    pipeline, regardless of the original source type.
    """

    interaction_ids: tuple[str, ...]
    content: dict[str, Any]
    id: str = field(default_factory=_new_id)
    timestamp: datetime = field(default_factory=_now)
    metadata: dict[str, Any] = field(default_factory=lambda: dict[str, Any]())


# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Memory:
    """A derived, persisted unit of knowledge (PRD §1, §5).

    Extracted from one or more interactions, intended to aid future task
    execution.  The ``memory_type`` field is a string so that users can
    define custom types through configuration.  The system ships default
    constants (``MEMORY_TYPE_SEMANTIC``, ``MEMORY_TYPE_EPISODIC``,
    ``MEMORY_TYPE_PROCEDURAL``) but does not restrict the set of allowed
    values at the model level.
    """

    content: str
    memory_type: str
    provenance: Provenance
    embedding_metadata: EmbeddingMetadata
    id: str = field(default_factory=_new_id)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    metadata: dict[str, Any] = field(default_factory=lambda: dict[str, Any]())
