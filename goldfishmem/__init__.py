"""goldfishmem: a production grade memory system for agents."""

from goldfishmem.hello import hello_world
from goldfishmem.models import (
    Citation,
    CustomMemory,
    EmbeddingMetadata,
    EpisodicMemory,
    ExtractionMethod,
    Interaction,
    InteractionRef,
    Memory,
    MemoryRef,
    MemoryType,
    Observation,
    ObservationRef,
    ProceduralMemory,
    Provenance,
    SemanticMemory,
    SourceType,
)

__version__ = "0.1.0"
__all__ = [
    "__version__",
    "hello_world",
    "Citation",
    "CustomMemory",
    "EmbeddingMetadata",
    "EpisodicMemory",
    "ExtractionMethod",
    "Interaction",
    "InteractionRef",
    "Memory",
    "MemoryRef",
    "MemoryType",
    "Observation",
    "ObservationRef",
    "ProceduralMemory",
    "Provenance",
    "SemanticMemory",
    "SourceType",
]
