"""goldfishmem: a production grade memory system for agents."""

from goldfishmem.config import (
    DEFAULT_TYPE_REGISTRY,
    TypeDefinition,
    TypeRegistry,
    load_type_registry,
)
from goldfishmem.models import (
    MEMORY_TYPE_EPISODIC,
    MEMORY_TYPE_PROCEDURAL,
    MEMORY_TYPE_SEMANTIC,
    SOURCE_TYPE_CLICKSTREAM,
    SOURCE_TYPE_CONVERSATION,
    SOURCE_TYPE_DOCUMENT,
    SOURCE_TYPE_DOMAIN_ENTITY,
    Citation,
    EmbeddingMetadata,
    ExtractionMethod,
    Interaction,
    InteractionRef,
    Memory,
    MemoryRef,
    Observation,
    ObservationRef,
    Provenance,
)

__version__ = "0.1.0"
__all__ = [
    "DEFAULT_TYPE_REGISTRY",
    "MEMORY_TYPE_EPISODIC",
    "MEMORY_TYPE_PROCEDURAL",
    "MEMORY_TYPE_SEMANTIC",
    "SOURCE_TYPE_CLICKSTREAM",
    "SOURCE_TYPE_CONVERSATION",
    "SOURCE_TYPE_DOCUMENT",
    "SOURCE_TYPE_DOMAIN_ENTITY",
    "Citation",
    "EmbeddingMetadata",
    "ExtractionMethod",
    "Interaction",
    "InteractionRef",
    "Memory",
    "MemoryRef",
    "Observation",
    "ObservationRef",
    "Provenance",
    "TypeDefinition",
    "TypeRegistry",
    "__version__",
    "load_type_registry",
]
