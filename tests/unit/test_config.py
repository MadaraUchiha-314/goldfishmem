"""Tests for the goldfishmem config-driven type registry."""

from __future__ import annotations

from pathlib import Path

import pytest

from goldfishmem import (
    DEFAULT_TYPE_REGISTRY,
    TypeDefinition,
    TypeRegistry,
    load_type_registry,
)


class TestDefaultRegistry:
    def test_ships_default_source_types(self) -> None:
        names = set(DEFAULT_TYPE_REGISTRY.source_types)
        assert names == {"conversation", "clickstream", "document", "domain_entity"}

    def test_ships_default_memory_types(self) -> None:
        names = set(DEFAULT_TYPE_REGISTRY.memory_types)
        assert names == {"semantic", "episodic", "procedural"}

    def test_entries_carry_attributes_mapping(self) -> None:
        for entry in DEFAULT_TYPE_REGISTRY.source_types.values():
            assert isinstance(entry, TypeDefinition)
            assert isinstance(entry.attributes, dict)
        for entry in DEFAULT_TYPE_REGISTRY.memory_types.values():
            assert isinstance(entry, TypeDefinition)
            assert isinstance(entry.attributes, dict)

    def test_lookup_helpers(self) -> None:
        assert DEFAULT_TYPE_REGISTRY.source_type("document").name == "document"
        assert DEFAULT_TYPE_REGISTRY.memory_type("semantic").name == "semantic"


class TestLoadTypeRegistry:
    def test_custom_registry_with_attributes(self, tmp_path: Path) -> None:
        cfg = tmp_path / "custom.yaml"
        cfg.write_text(
            """
source_types:
  webhook:
    attributes:
      retention_days: 30
memory_types:
  financial_insight:
    attributes:
      retrieval:
        recency_weight: 0.4
""".strip()
        )

        registry = load_type_registry(cfg)

        assert set(registry.source_types) == {"webhook"}
        webhook = registry.source_type("webhook")
        assert webhook.attributes == {"retention_days": 30}

        assert set(registry.memory_types) == {"financial_insight"}
        fi = registry.memory_type("financial_insight")
        assert fi.attributes == {"retrieval": {"recency_weight": 0.4}}

    def test_missing_sections_are_empty(self, tmp_path: Path) -> None:
        cfg = tmp_path / "empty.yaml"
        cfg.write_text("source_types: {}\n")
        registry = load_type_registry(cfg)
        assert registry.source_types == {}
        assert registry.memory_types == {}

    def test_entry_without_attributes_key(self, tmp_path: Path) -> None:
        """Entries with no ``attributes`` key get an empty attribute map."""
        cfg = tmp_path / "no_attrs.yaml"
        cfg.write_text("memory_types:\n  bare: {}\n")
        registry = load_type_registry(cfg)
        assert registry.memory_type("bare").attributes == {}

    def test_invalid_top_level_raises(self, tmp_path: Path) -> None:
        cfg = tmp_path / "bad.yaml"
        cfg.write_text("- not_a_mapping\n")
        with pytest.raises(ValueError, match="mapping"):
            load_type_registry(cfg)

    def test_invalid_attributes_raises(self, tmp_path: Path) -> None:
        cfg = tmp_path / "bad_attrs.yaml"
        cfg.write_text("memory_types:\n  oops:\n    attributes: not_a_mapping\n")
        with pytest.raises(ValueError, match="Attributes"):
            load_type_registry(cfg)

    def test_returns_type_registry(self) -> None:
        assert isinstance(DEFAULT_TYPE_REGISTRY, TypeRegistry)
