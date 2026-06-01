"""Tests for goldfishmem core data models."""

from datetime import UTC, datetime

import pytest

from goldfishmem import (
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

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_provenance() -> Provenance:
    return Provenance(
        extraction_run_id="run-001",
        extracted_at=datetime(2026, 5, 15, tzinfo=UTC),
        extraction_method=ExtractionMethod.LLM_EXTRACTION,
        source_interactions=(InteractionRef(id="int-1", source_type=SOURCE_TYPE_CONVERSATION),),
        source_observations=(ObservationRef(id="obs-1"),),
    )


@pytest.fixture()
def sample_embedding() -> EmbeddingMetadata:
    return EmbeddingMetadata(
        text="user prefers dark mode", model="text-embedding-3-small", dimensions=1536
    )


# ---------------------------------------------------------------------------
# Default type constants
# ---------------------------------------------------------------------------


class TestDefaultConstants:
    def test_source_type_constants(self) -> None:
        assert SOURCE_TYPE_CONVERSATION == "conversation"
        assert SOURCE_TYPE_CLICKSTREAM == "clickstream"
        assert SOURCE_TYPE_DOCUMENT == "document"
        assert SOURCE_TYPE_DOMAIN_ENTITY == "domain_entity"

    def test_memory_type_constants(self) -> None:
        assert MEMORY_TYPE_SEMANTIC == "semantic"
        assert MEMORY_TYPE_EPISODIC == "episodic"
        assert MEMORY_TYPE_PROCEDURAL == "procedural"

    def test_custom_source_type_is_just_a_string(self) -> None:
        interaction = Interaction(
            source_type="custom_iot_sensor",
            content={"reading": 42},
        )
        assert interaction.source_type == "custom_iot_sensor"

    def test_custom_memory_type_is_just_a_string(
        self, sample_provenance: Provenance, sample_embedding: EmbeddingMetadata
    ) -> None:
        mem = Memory(
            content="financial insight",
            memory_type="financial_insight",
            provenance=sample_provenance,
            embedding_metadata=sample_embedding,
        )
        assert mem.memory_type == "financial_insight"


# ---------------------------------------------------------------------------
# ExtractionMethod enum
# ---------------------------------------------------------------------------


class TestExtractionMethod:
    def test_values(self) -> None:
        assert ExtractionMethod.LLM_EXTRACTION.value == "llm_extraction"
        assert ExtractionMethod.REFLECTION.value == "reflection"
        assert ExtractionMethod.CONSOLIDATION.value == "consolidation"
        assert ExtractionMethod.DIRECT_UPDATE.value == "direct_update"

    def test_membership(self) -> None:
        assert len(ExtractionMethod) == 4

    def test_direct_update_provenance(self) -> None:
        """Memories written directly by an external caller use DIRECT_UPDATE."""
        prov = Provenance(
            extraction_run_id="manual-001",
            extracted_at=datetime(2026, 5, 18, tzinfo=UTC),
            extraction_method=ExtractionMethod.DIRECT_UPDATE,
        )
        assert prov.extraction_method == ExtractionMethod.DIRECT_UPDATE
        assert prov.source_interactions == ()
        assert prov.source_observations == ()
        assert prov.source_memories == ()


# ---------------------------------------------------------------------------
# Reference type tests
# ---------------------------------------------------------------------------


class TestInteractionRef:
    def test_construction(self) -> None:
        ref = InteractionRef(id="int-1", source_type=SOURCE_TYPE_CONVERSATION)
        assert ref.id == "int-1"
        assert ref.source_type == SOURCE_TYPE_CONVERSATION

    def test_immutable(self) -> None:
        ref = InteractionRef(id="int-1", source_type=SOURCE_TYPE_CONVERSATION)
        with pytest.raises(AttributeError):
            ref.id = "changed"  # type: ignore[misc]

    def test_custom_source_type(self) -> None:
        ref = InteractionRef(id="int-2", source_type="custom_webhook")
        assert ref.source_type == "custom_webhook"


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
        ref = MemoryRef(id="mem-1", memory_type=MEMORY_TYPE_SEMANTIC)
        assert ref.id == "mem-1"
        assert ref.memory_type == MEMORY_TYPE_SEMANTIC

    def test_custom_memory_type(self) -> None:
        ref = MemoryRef(id="mem-2", memory_type="domain_specific")
        assert ref.memory_type == "domain_specific"


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
                MemoryRef(id="mem-1", memory_type=MEMORY_TYPE_SEMANTIC),
                MemoryRef(id="mem-2", memory_type=MEMORY_TYPE_EPISODIC),
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
            source_type=SOURCE_TYPE_CONVERSATION,
            source_id="conv-123",
            excerpt="I prefer dark mode",
            raw_data_uri="s3://bucket/conversations/conv-123",
            span="messages[2].content",
        )
        assert citation.source_type == SOURCE_TYPE_CONVERSATION
        assert citation.source_id == "conv-123"
        assert citation.span == "messages[2].content"

    def test_span_defaults_empty(self) -> None:
        citation = Citation(
            source_type=SOURCE_TYPE_DOCUMENT,
            source_id="doc-1",
            excerpt="section content",
            raw_data_uri="s3://bucket/docs/doc-1",
        )
        assert citation.span == ""

    def test_custom_source_type(self) -> None:
        citation = Citation(
            source_type="custom_audio",
            source_id="audio-1",
            excerpt="transcribed segment",
            raw_data_uri="s3://bucket/audio/audio-1",
        )
        assert citation.source_type == "custom_audio"


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
            source_type=SOURCE_TYPE_CONVERSATION,
            content={"messages": [{"role": "user", "text": "hello"}]},
        )
        assert interaction.source_type == SOURCE_TYPE_CONVERSATION
        assert interaction.content["messages"][0]["text"] == "hello"
        assert interaction.id  # auto-generated UUID
        assert interaction.timestamp  # auto-generated

    def test_custom_id_and_timestamp(self) -> None:
        ts = datetime(2026, 1, 1, tzinfo=UTC)
        interaction = Interaction(
            source_type=SOURCE_TYPE_CLICKSTREAM,
            content={"event": "click"},
            id="custom-id",
            timestamp=ts,
        )
        assert interaction.id == "custom-id"
        assert interaction.timestamp == ts

    def test_metadata_defaults_empty(self) -> None:
        interaction = Interaction(
            source_type=SOURCE_TYPE_DOCUMENT,
            content={"text": "doc content"},
        )
        assert interaction.metadata == {}

    def test_immutable(self) -> None:
        interaction = Interaction(
            source_type=SOURCE_TYPE_CONVERSATION,
            content={"data": "value"},
        )
        with pytest.raises(AttributeError):
            interaction.id = "changed"  # type: ignore[misc]


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
# Memory tests
# ---------------------------------------------------------------------------


class TestMemory:
    def test_construction(
        self, sample_provenance: Provenance, sample_embedding: EmbeddingMetadata
    ) -> None:
        mem = Memory(
            content="The user prefers dark mode",
            memory_type=MEMORY_TYPE_SEMANTIC,
            provenance=sample_provenance,
            embedding_metadata=sample_embedding,
        )
        assert mem.content == "The user prefers dark mode"
        assert mem.memory_type == MEMORY_TYPE_SEMANTIC
        assert mem.provenance.extraction_run_id == "run-001"
        assert mem.embedding_metadata.dimensions == 1536
        assert mem.id  # auto-generated
        assert mem.metadata == {}

    def test_immutable(
        self, sample_provenance: Provenance, sample_embedding: EmbeddingMetadata
    ) -> None:
        mem = Memory(
            content="fact",
            memory_type=MEMORY_TYPE_SEMANTIC,
            provenance=sample_provenance,
            embedding_metadata=sample_embedding,
        )
        with pytest.raises(AttributeError):
            mem.content = "changed"  # type: ignore[misc]

    def test_episodic_memory(
        self, sample_provenance: Provenance, sample_embedding: EmbeddingMetadata
    ) -> None:
        mem = Memory(
            content="User reported a login bug on 2026-03-01",
            memory_type=MEMORY_TYPE_EPISODIC,
            provenance=sample_provenance,
            embedding_metadata=sample_embedding,
        )
        assert mem.memory_type == MEMORY_TYPE_EPISODIC

    def test_procedural_memory(
        self, sample_provenance: Provenance, sample_embedding: EmbeddingMetadata
    ) -> None:
        mem = Memory(
            content="Always review PRs before merging",
            memory_type=MEMORY_TYPE_PROCEDURAL,
            provenance=sample_provenance,
            embedding_metadata=sample_embedding,
        )
        assert mem.memory_type == MEMORY_TYPE_PROCEDURAL

    def test_custom_memory_type(
        self, sample_provenance: Provenance, sample_embedding: EmbeddingMetadata
    ) -> None:
        mem = Memory(
            content="Monthly budget is $5000",
            memory_type="financial_insight",
            provenance=sample_provenance,
            embedding_metadata=sample_embedding,
        )
        assert mem.memory_type == "financial_insight"

    def test_metadata_field(
        self, sample_provenance: Provenance, sample_embedding: EmbeddingMetadata
    ) -> None:
        mem = Memory(
            content="fact",
            memory_type=MEMORY_TYPE_SEMANTIC,
            provenance=sample_provenance,
            embedding_metadata=sample_embedding,
            metadata={"importance": "high", "domain": "finance"},
        )
        assert mem.metadata["importance"] == "high"
        assert mem.metadata["domain"] == "finance"
