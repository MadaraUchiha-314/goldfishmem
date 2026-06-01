"""Tests for the goldfishmem config-driven type registry."""

from __future__ import annotations

from pathlib import Path

import pytest

from goldfishmem import (
    DEFAULT_TYPE_REGISTRY,
    DEFAULT_TYPES_DIR,
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

    def test_default_types_dir_layout(self) -> None:
        """Each default type ships as its own file under the directory tree."""
        assert (DEFAULT_TYPES_DIR / "source_types" / "conversation.yaml").is_file()
        assert (DEFAULT_TYPES_DIR / "source_types" / "clickstream.yaml").is_file()
        assert (DEFAULT_TYPES_DIR / "source_types" / "document.yaml").is_file()
        assert (DEFAULT_TYPES_DIR / "source_types" / "domain_entity.yaml").is_file()
        assert (DEFAULT_TYPES_DIR / "memory_types" / "semantic.yaml").is_file()
        assert (DEFAULT_TYPES_DIR / "memory_types" / "episodic.yaml").is_file()
        assert (DEFAULT_TYPES_DIR / "memory_types" / "procedural.yaml").is_file()


class TestLoadTypeRegistry:
    def _write(self, path: Path, body: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)

    def test_custom_registry_with_attributes(self, tmp_path: Path) -> None:
        self._write(
            tmp_path / "source_types" / "webhook.yaml",
            "attributes:\n  retention_days: 30\n",
        )
        self._write(
            tmp_path / "memory_types" / "financial_insight.yaml",
            "attributes:\n  retrieval:\n    recency_weight: 0.4\n",
        )

        registry = load_type_registry(tmp_path)

        assert set(registry.source_types) == {"webhook"}
        assert registry.source_type("webhook").attributes == {"retention_days": 30}

        assert set(registry.memory_types) == {"financial_insight"}
        assert registry.memory_type("financial_insight").attributes == {
            "retrieval": {"recency_weight": 0.4}
        }

    def test_missing_subdir_is_empty(self, tmp_path: Path) -> None:
        self._write(tmp_path / "source_types" / "only_source.yaml", "attributes: {}\n")
        registry = load_type_registry(tmp_path)
        assert set(registry.source_types) == {"only_source"}
        assert registry.memory_types == {}

    def test_filename_is_type_name(self, tmp_path: Path) -> None:
        self._write(tmp_path / "memory_types" / "domain_specific.yaml", "attributes: {}\n")
        registry = load_type_registry(tmp_path)
        assert registry.memory_type("domain_specific").name == "domain_specific"

    def test_entry_without_attributes_key(self, tmp_path: Path) -> None:
        self._write(tmp_path / "memory_types" / "bare.yaml", "{}\n")
        registry = load_type_registry(tmp_path)
        assert registry.memory_type("bare").attributes == {}

    def test_yml_extension_is_accepted(self, tmp_path: Path) -> None:
        self._write(tmp_path / "source_types" / "legacy.yml", "attributes: {}\n")
        registry = load_type_registry(tmp_path)
        assert "legacy" in registry.source_types

    def test_non_yaml_files_ignored(self, tmp_path: Path) -> None:
        self._write(tmp_path / "source_types" / "real.yaml", "attributes: {}\n")
        self._write(tmp_path / "source_types" / "README.md", "ignore me\n")
        registry = load_type_registry(tmp_path)
        assert set(registry.source_types) == {"real"}

    def test_invalid_top_level_raises(self, tmp_path: Path) -> None:
        self._write(tmp_path / "source_types" / "bad.yaml", "- not_a_mapping\n")
        with pytest.raises(ValueError, match="mapping"):
            load_type_registry(tmp_path)

    def test_invalid_attributes_raises(self, tmp_path: Path) -> None:
        self._write(
            tmp_path / "memory_types" / "oops.yaml",
            "attributes: not_a_mapping\n",
        )
        with pytest.raises(ValueError, match="Attributes"):
            load_type_registry(tmp_path)

    def test_nonexistent_path_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="must be a directory"):
            load_type_registry(tmp_path / "does_not_exist")

    def test_returns_type_registry(self) -> None:
        assert isinstance(DEFAULT_TYPE_REGISTRY, TypeRegistry)
