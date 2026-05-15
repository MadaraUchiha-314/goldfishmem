"""Core data models for the goldfishmem memory system.

Defines the foundational types referenced throughout the PRD:
- Input types: Interaction, Observation
- Memory types: Memory (base), SemanticMemory, EpisodicMemory, ProceduralMemory, CustomMemory
- Provenance types: Provenance, Citation, InteractionRef, ObservationRef, MemoryRef
- Supporting types: SourceType, MemoryType, ExtractionMethod, EmbeddingMetadata
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class SourceType(Enum):
    """Type of input data source (PRD §4)."""

    CONVERSATION = "conversation"
    CLICKSTREAM = "clickstream"
    DOCUMENT = "document"
    DOMAIN_ENTITY = "domain_entity"


class MemoryType(Enum):
    """Memory type taxonomy (PRD §5)."""

    SEMANTIC = "semantic"
    EPISODIC = "episodic"
    PROCEDURAL = "procedural"
    CUSTOM = "custom"


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
    source_type: SourceType


@dataclass(frozen=True)
class ObservationRef:
    """Lightweight reference to an Observation."""

    id: str


@dataclass(frozen=True)
class MemoryRef:
    """Lightweight reference to a Memory."""

    id: str
    memory_type: MemoryType


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

    source_type: SourceType
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

    source_type: SourceType
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
# Memory types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Memory:
    """Base class for all memory types (PRD §1, §5).

    A derived, persisted unit of knowledge extracted from one or more
    interactions, intended to aid future task execution.
    """

    content: str
    memory_type: MemoryType
    provenance: Provenance
    embedding_metadata: EmbeddingMetadata
    id: str = field(default_factory=_new_id)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    metadata: dict[str, Any] = field(default_factory=lambda: dict[str, Any]())


@dataclass(frozen=True)
class SemanticMemory(Memory):
    """Facts and conceptual knowledge (PRD §5).

    Examples: "The user prefers dark mode", "Company policy requires 2FA".
    """

    confidence: float = 1.0

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)


@dataclass(frozen=True)
class EpisodicMemory(Memory):
    """Specific past events and experiences (PRD §5).

    Examples: "On 2026-03-01 the user reported a login bug",
    "The deployment on Friday caused a 5-minute outage".
    """

    event_timestamp: datetime = field(default_factory=_now)
    participants: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProceduralMemory(Memory):
    """Preferences, behaviour patterns, and how-to knowledge (PRD §5).

    Examples: "The user always reviews PRs before merging",
    "When debugging, start with the error log".
    """

    trigger_context: str = ""


@dataclass(frozen=True)
class CustomMemory(Memory):
    """Extension point for domain-specific memory types (PRD §5).

    Use ``custom_type`` to identify the domain-specific subtype.  For richer
    domain models, subclass ``CustomMemory`` directly.
    """

    custom_type: str = ""
