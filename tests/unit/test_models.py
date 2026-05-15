"""Tests for goldfishmem core data models and memory type taxonomy."""

from datetime import UTC, datetime

import pytest

from goldfishmem import (
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

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_provenance() -> Provenance:
    return Provenance(
        extraction_run_id="run-001",
        extracted_at=datetime(2026, 5, 15, tzinfo=UTC),
        extraction_method=ExtractionMethod.LLM_EXTRACTION,
        source_interactions=(InteractionRef(id="int-1", source_type=SourceType.CONVERSATION),),
        source_observations=(ObservationRef(id="obs-1"),),
    )


@pytest.fixture()
def sample_embedding() -> EmbeddingMetadata:
    return EmbeddingMetadata(
        text="user prefers dark mode", model="text-embedding-3-small", dimensions=1536
    )


# ---------------------------------------------------------------------------
# Enum tests
# ---------------------------------------------------------------------------


class TestSourceType:
    def test_values(self) -> None:
        assert SourceType.CONVERSATION.value == "conversation"
        assert SourceType.CLICKSTREAM.value == "clickstream"
        assert SourceType.DOCUMENT.value == "document"
        assert SourceType.DOMAIN_ENTITY.value == "domain_entity"

    def test_membership(self) -> None:
        assert len(SourceType) == 4


class TestMemoryType:
    def test_values(self) -> None:
        assert MemoryType.SEMANTIC.value == "semantic"
        assert MemoryType.EPISODIC.value == "episodic"
        assert MemoryType.PROCEDURAL.value == "procedural"
        assert MemoryType.CUSTOM.value == "custom"

    def test_membership(self) -> None:
        assert len(MemoryType) == 4


class TestExtractionMethod:
    def test_values(self) -> None:
        assert ExtractionMethod.LLM_EXTRACTION.value == "llm_extraction"
        assert ExtractionMethod.REFLECTION.value == "reflection"
        assert ExtractionMethod.CONSOLIDATION.value == "consolidation"

    def test_membership(self) -> None:
        assert len(ExtractionMethod) == 3


# ---------------------------------------------------------------------------
# Reference type tests
# ---------------------------------------------------------------------------


class TestInteractionRef:
    def test_construction(self) -> None:
        ref = InteractionRef(id="int-1", source_type=SourceType.CONVERSATION)
        assert ref.id == "int-1"
        assert ref.source_type == SourceType.CONVERSATION

    def test_immutable(self) -> None:
        ref = InteractionRef(id="int-1", source_type=SourceType.CONVERSATION)
        with pytest.raises(AttributeError):
            ref.id = "changed"  # type: ignore[misc]


class TestObservationRef:
    def test_construction(self) -> None:
        ref = ObservationRef(id="obs-1")
        assert ref.id == "obs-1"

    def test_immutable(self) -> None:
        ref = ObservationRef(id="obs-1")
        with pytest.raises(AttributeError):
            ref.id = "changed"  # type: ignore[misc]


class TestMemoryRef:
    def test_construction(self) -> None:
        ref = MemoryRef(id="mem-1", memory_type=MemoryType.SEMANTIC)
        assert ref.id == "mem-1"
        assert ref.memory_type == MemoryType.SEMANTIC


# ---------------------------------------------------------------------------
# Provenance tests
# ---------------------------------------------------------------------------


class TestProvenance:
    def test_construction(self, sample_provenance: Provenance) -> None:
        assert sample_provenance.extraction_run_id == "run-001"
        assert sample_provenance.extraction_method == ExtractionMethod.LLM_EXTRACTION
        assert len(sample_provenance.source_interactions) == 1
        assert len(sample_provenance.source_observations) == 1
        assert len(sample_provenance.source_memories) == 0

    def test_immutable(self, sample_provenance: Provenance) -> None:
        with pytest.raises(AttributeError):
            sample_provenance.extraction_run_id = "changed"  # type: ignore[misc]

    def test_reflection_provenance(self) -> None:
        prov = Provenance(
            extraction_run_id="run-002",
            extracted_at=datetime(2026, 5, 15, tzinfo=UTC),
            extraction_method=ExtractionMethod.REFLECTION,
            source_memories=(
                MemoryRef(id="mem-1", memory_type=MemoryType.SEMANTIC),
                MemoryRef(id="mem-2", memory_type=MemoryType.EPISODIC),
            ),
        )
        assert prov.extraction_method == ExtractionMethod.REFLECTION
        assert len(prov.source_memories) == 2
        assert len(prov.source_interactions) == 0

    def test_defaults_empty_tuples(self) -> None:
        prov = Provenance(
            extraction_run_id="run-003",
            extracted_at=datetime(2026, 5, 15, tzinfo=UTC),
            extraction_method=ExtractionMethod.LLM_EXTRACTION,
        )
        assert prov.source_interactions == ()
        assert prov.source_observations == ()
        assert prov.source_memories == ()


# ---------------------------------------------------------------------------
# Citation tests
# ---------------------------------------------------------------------------


class TestCitation:
    def test_construction(self) -> None:
        citation = Citation(
            source_type=SourceType.CONVERSATION,
            source_id="conv-123",
            excerpt="I prefer dark mode",
            raw_data_uri="s3://bucket/conversations/conv-123",
            span="messages[2].content",
        )
        assert citation.source_type == SourceType.CONVERSATION
        assert citation.source_id == "conv-123"
        assert citation.span == "messages[2].content"

    def test_span_defaults_empty(self) -> None:
        citation = Citation(
            source_type=SourceType.DOCUMENT,
            source_id="doc-1",
            excerpt="section content",
            raw_data_uri="s3://bucket/docs/doc-1",
        )
        assert citation.span == ""


# ---------------------------------------------------------------------------
# EmbeddingMetadata tests
# ---------------------------------------------------------------------------


class TestEmbeddingMetadata:
    def test_construction(self, sample_embedding: EmbeddingMetadata) -> None:
        assert sample_embedding.text == "user prefers dark mode"
        assert sample_embedding.model == "text-embedding-3-small"
        assert sample_embedding.dimensions == 1536


# ---------------------------------------------------------------------------
# Interaction tests
# ---------------------------------------------------------------------------


class TestInteraction:
    def test_construction(self) -> None:
        interaction = Interaction(
            source_type=SourceType.CONVERSATION,
            content={"messages": [{"role": "user", "text": "hello"}]},
        )
        assert interaction.source_type == SourceType.CONVERSATION
        assert interaction.content["messages"][0]["text"] == "hello"
        assert interaction.id  # auto-generated UUID
        assert interaction.timestamp  # auto-generated

    def test_custom_id_and_timestamp(self) -> None:
        ts = datetime(2026, 1, 1, tzinfo=UTC)
        interaction = Interaction(
            source_type=SourceType.CLICKSTREAM,
            content={"event": "click"},
            id="custom-id",
            timestamp=ts,
        )
        assert interaction.id == "custom-id"
        assert interaction.timestamp == ts

    def test_metadata_defaults_empty(self) -> None:
        interaction = Interaction(
            source_type=SourceType.DOCUMENT,
            content={"text": "doc content"},
        )
        assert interaction.metadata == {}


# ---------------------------------------------------------------------------
# Observation tests
# ---------------------------------------------------------------------------


class TestObservation:
    def test_construction(self) -> None:
        obs = Observation(
            interaction_ids=("int-1", "int-2"),
            content={"normalized": "data"},
        )
        assert obs.interaction_ids == ("int-1", "int-2")
        assert obs.content["normalized"] == "data"
        assert obs.id  # auto-generated

    def test_immutable(self) -> None:
        obs = Observation(interaction_ids=("int-1",), content={"data": "value"})
        with pytest.raises(AttributeError):
            obs.id = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Memory base class tests
# ---------------------------------------------------------------------------


class TestMemory:
    def test_construction(
        self, sample_provenance: Provenance, sample_embedding: EmbeddingMetadata
    ) -> None:
        mem = Memory(
            content="The user prefers dark mode",
            memory_type=MemoryType.SEMANTIC,
            provenance=sample_provenance,
            embedding_metadata=sample_embedding,
        )
        assert mem.content == "The user prefers dark mode"
        assert mem.memory_type == MemoryType.SEMANTIC
        assert mem.provenance.extraction_run_id == "run-001"
        assert mem.embedding_metadata.dimensions == 1536
        assert mem.id  # auto-generated
        assert mem.metadata == {}

    def test_immutable(
        self, sample_provenance: Provenance, sample_embedding: EmbeddingMetadata
    ) -> None:
        mem = Memory(
            content="fact",
            memory_type=MemoryType.SEMANTIC,
            provenance=sample_provenance,
            embedding_metadata=sample_embedding,
        )
        with pytest.raises(AttributeError):
            mem.content = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Memory subtype tests
# ---------------------------------------------------------------------------


class TestSemanticMemory:
    def test_construction(
        self, sample_provenance: Provenance, sample_embedding: EmbeddingMetadata
    ) -> None:
        mem = SemanticMemory(
            content="Python 3.12 supports type parameter syntax",
            memory_type=MemoryType.SEMANTIC,
            provenance=sample_provenance,
            embedding_metadata=sample_embedding,
            confidence=0.95,
        )
        assert mem.confidence == 0.95
        assert isinstance(mem, Memory)

    def test_default_confidence(
        self, sample_provenance: Provenance, sample_embedding: EmbeddingMetadata
    ) -> None:
        mem = SemanticMemory(
            content="fact",
            memory_type=MemoryType.SEMANTIC,
            provenance=sample_provenance,
            embedding_metadata=sample_embedding,
        )
        assert mem.confidence == 1.0


class TestEpisodicMemory:
    def test_construction(
        self, sample_provenance: Provenance, sample_embedding: EmbeddingMetadata
    ) -> None:
        event_ts = datetime(2026, 3, 1, tzinfo=UTC)
        mem = EpisodicMemory(
            content="User reported a login bug on 2026-03-01",
            memory_type=MemoryType.EPISODIC,
            provenance=sample_provenance,
            embedding_metadata=sample_embedding,
            event_timestamp=event_ts,
            participants=("user-42", "support-agent-7"),
        )
        assert mem.event_timestamp == event_ts
        assert mem.participants == ("user-42", "support-agent-7")
        assert isinstance(mem, Memory)

    def test_defaults(
        self, sample_provenance: Provenance, sample_embedding: EmbeddingMetadata
    ) -> None:
        mem = EpisodicMemory(
            content="event",
            memory_type=MemoryType.EPISODIC,
            provenance=sample_provenance,
            embedding_metadata=sample_embedding,
        )
        assert mem.participants == ()


class TestProceduralMemory:
    def test_construction(
        self, sample_provenance: Provenance, sample_embedding: EmbeddingMetadata
    ) -> None:
        mem = ProceduralMemory(
            content="Always review PRs before merging",
            memory_type=MemoryType.PROCEDURAL,
            provenance=sample_provenance,
            embedding_metadata=sample_embedding,
            trigger_context="When a PR is opened",
        )
        assert mem.trigger_context == "When a PR is opened"
        assert isinstance(mem, Memory)

    def test_default_trigger_context(
        self, sample_provenance: Provenance, sample_embedding: EmbeddingMetadata
    ) -> None:
        mem = ProceduralMemory(
            content="procedure",
            memory_type=MemoryType.PROCEDURAL,
            provenance=sample_provenance,
            embedding_metadata=sample_embedding,
        )
        assert mem.trigger_context == ""


class TestCustomMemory:
    def test_construction(
        self, sample_provenance: Provenance, sample_embedding: EmbeddingMetadata
    ) -> None:
        mem = CustomMemory(
            content="Monthly budget is $5000",
            memory_type=MemoryType.CUSTOM,
            provenance=sample_provenance,
            embedding_metadata=sample_embedding,
            custom_type="financial_insight",
        )
        assert mem.custom_type == "financial_insight"
        assert isinstance(mem, Memory)

    def test_default_custom_type(
        self, sample_provenance: Provenance, sample_embedding: EmbeddingMetadata
    ) -> None:
        mem = CustomMemory(
            content="custom",
            memory_type=MemoryType.CUSTOM,
            provenance=sample_provenance,
            embedding_metadata=sample_embedding,
        )
        assert mem.custom_type == ""
