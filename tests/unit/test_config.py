"""Tests for the goldfishmem central config and type registry."""

from __future__ import annotations

from pathlib import Path

import pytest

from goldfishmem import (
    DEFAULT_CONFIG_FILE,
    DEFAULT_SETTINGS,
    DEFAULT_TYPE_REGISTRY,
    EmbeddingSettings,
    RetrievalSettings,
    Settings,
    StorageSettings,
    TypeDefinition,
    TypeRegistry,
    TypeRegistrySettings,
    load_settings,
    load_type_registry,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MINIMAL_CONFIG = """
type_registry:
  root: types
  source_types_dir: source_types
  memory_types_dir: memory_types
""".strip()


def _write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)


# ---------------------------------------------------------------------------
# Central config / Settings
# ---------------------------------------------------------------------------


class TestDefaultSettings:
    def test_default_config_file_ships_with_package(self) -> None:
        assert DEFAULT_CONFIG_FILE.is_file()
        assert DEFAULT_CONFIG_FILE.name == "goldfishmem.yaml"

    def test_default_settings_type(self) -> None:
        assert isinstance(DEFAULT_SETTINGS, Settings)
        assert isinstance(DEFAULT_SETTINGS.type_registry, TypeRegistrySettings)
        assert isinstance(DEFAULT_SETTINGS.embedding, EmbeddingSettings)
        assert isinstance(DEFAULT_SETTINGS.storage, StorageSettings)
        assert isinstance(DEFAULT_SETTINGS.retrieval, RetrievalSettings)

    def test_type_registry_root_resolved_relative_to_config(self) -> None:
        trs = DEFAULT_SETTINGS.type_registry
        assert trs.root.is_absolute()
        assert trs.root == DEFAULT_CONFIG_FILE.parent / "default_types"
        assert trs.source_types_dir == "source_types"
        assert trs.memory_types_dir == "memory_types"

    def test_unset_optional_settings_default_to_none(self) -> None:
        assert DEFAULT_SETTINGS.embedding.model is None
        assert DEFAULT_SETTINGS.embedding.dimensions is None
        assert DEFAULT_SETTINGS.storage.backend is None


class TestLoadSettings:
    def test_relative_root_resolved_against_config_dir(self, tmp_path: Path) -> None:
        _write(tmp_path / "goldfishmem.yaml", _MINIMAL_CONFIG)
        settings = load_settings(tmp_path / "goldfishmem.yaml")
        assert settings.type_registry.root == tmp_path / "types"

    def test_absolute_root_preserved(self, tmp_path: Path) -> None:
        abs_root = tmp_path / "elsewhere" / "types"
        _write(
            tmp_path / "goldfishmem.yaml",
            f"type_registry:\n  root: {abs_root}\n",
        )
        settings = load_settings(tmp_path / "goldfishmem.yaml")
        assert settings.type_registry.root == abs_root

    def test_subdir_names_are_config_driven(self, tmp_path: Path) -> None:
        _write(
            tmp_path / "goldfishmem.yaml",
            (
                "type_registry:\n"
                "  root: t\n"
                "  source_types_dir: sources\n"
                "  memory_types_dir: memories\n"
            ),
        )
        settings = load_settings(tmp_path / "goldfishmem.yaml")
        assert settings.type_registry.source_types_dir == "sources"
        assert settings.type_registry.memory_types_dir == "memories"

    def test_embedding_storage_retrieval_parsed(self, tmp_path: Path) -> None:
        _write(
            tmp_path / "goldfishmem.yaml",
            (
                "type_registry:\n  root: t\n"
                "embedding:\n  model: text-embedding-3-small\n  dimensions: 1536\n"
                "storage:\n  backend: postgres\n  options:\n    dsn: postgres://x\n"
                "retrieval:\n  options:\n    top_k: 10\n"
            ),
        )
        settings = load_settings(tmp_path / "goldfishmem.yaml")
        assert settings.embedding.model == "text-embedding-3-small"
        assert settings.embedding.dimensions == 1536
        assert settings.storage.backend == "postgres"
        assert settings.storage.options == {"dsn": "postgres://x"}
        assert settings.retrieval.options == {"top_k": 10}

    def test_defaults_when_sections_missing(self, tmp_path: Path) -> None:
        _write(tmp_path / "goldfishmem.yaml", "type_registry:\n  root: t\n")
        settings = load_settings(tmp_path / "goldfishmem.yaml")
        assert settings.type_registry.source_types_dir == "source_types"
        assert settings.type_registry.memory_types_dir == "memory_types"
        assert settings.embedding == EmbeddingSettings()
        assert settings.storage == StorageSettings()
        assert settings.retrieval == RetrievalSettings()

    def test_invalid_top_level_raises(self, tmp_path: Path) -> None:
        _write(tmp_path / "goldfishmem.yaml", "- not_a_mapping\n")
        with pytest.raises(ValueError, match="top level"):
            load_settings(tmp_path / "goldfishmem.yaml")

    def test_invalid_dimensions_raises(self, tmp_path: Path) -> None:
        _write(
            tmp_path / "goldfishmem.yaml",
            "type_registry:\n  root: t\nembedding:\n  dimensions: not_an_int\n",
        )
        with pytest.raises(ValueError, match="dimensions"):
            load_settings(tmp_path / "goldfishmem.yaml")

    def test_bool_rejected_as_dimensions(self, tmp_path: Path) -> None:
        _write(
            tmp_path / "goldfishmem.yaml",
            "type_registry:\n  root: t\nembedding:\n  dimensions: true\n",
        )
        with pytest.raises(ValueError, match="dimensions"):
            load_settings(tmp_path / "goldfishmem.yaml")


# ---------------------------------------------------------------------------
# Default type registry
# ---------------------------------------------------------------------------


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
        """Each default type ships as its own file under the registry root."""
        root = DEFAULT_SETTINGS.type_registry.root
        assert (root / "source_types" / "conversation.yaml").is_file()
        assert (root / "source_types" / "clickstream.yaml").is_file()
        assert (root / "source_types" / "document.yaml").is_file()
        assert (root / "source_types" / "domain_entity.yaml").is_file()
        assert (root / "memory_types" / "semantic.yaml").is_file()
        assert (root / "memory_types" / "episodic.yaml").is_file()
        assert (root / "memory_types" / "procedural.yaml").is_file()

    def test_returns_type_registry(self) -> None:
        assert isinstance(DEFAULT_TYPE_REGISTRY, TypeRegistry)


# ---------------------------------------------------------------------------
# load_type_registry (driven by Settings)
# ---------------------------------------------------------------------------


class TestLoadTypeRegistry:
    """Loading a registry in isolation (extend_defaults=False)."""

    def _settings_for(self, root: Path) -> Settings:
        return Settings(type_registry=TypeRegistrySettings(root=root))

    def test_custom_registry_with_attributes(self, tmp_path: Path) -> None:
        _write(
            tmp_path / "source_types" / "webhook.yaml",
            "attributes:\n  retention_days: 30\n",
        )
        _write(
            tmp_path / "memory_types" / "financial_insight.yaml",
            "attributes:\n  retrieval:\n    recency_weight: 0.4\n",
        )

        registry = load_type_registry(self._settings_for(tmp_path), extend_defaults=False)

        assert set(registry.source_types) == {"webhook"}
        assert registry.source_type("webhook").attributes == {"retention_days": 30}
        assert set(registry.memory_types) == {"financial_insight"}
        assert registry.memory_type("financial_insight").attributes == {
            "retrieval": {"recency_weight": 0.4}
        }

    def test_config_driven_subdir_names(self, tmp_path: Path) -> None:
        _write(tmp_path / "sources" / "webhook.yaml", "attributes: {}\n")
        _write(tmp_path / "memories" / "insight.yaml", "attributes: {}\n")
        settings = Settings(
            type_registry=TypeRegistrySettings(
                root=tmp_path, source_types_dir="sources", memory_types_dir="memories"
            )
        )
        registry = load_type_registry(settings, extend_defaults=False)
        assert set(registry.source_types) == {"webhook"}
        assert set(registry.memory_types) == {"insight"}

    def test_missing_subdir_is_empty(self, tmp_path: Path) -> None:
        _write(tmp_path / "source_types" / "only_source.yaml", "attributes: {}\n")
        registry = load_type_registry(self._settings_for(tmp_path), extend_defaults=False)
        assert set(registry.source_types) == {"only_source"}
        assert registry.memory_types == {}

    def test_filename_is_type_name(self, tmp_path: Path) -> None:
        _write(tmp_path / "memory_types" / "domain_specific.yaml", "attributes: {}\n")
        registry = load_type_registry(self._settings_for(tmp_path), extend_defaults=False)
        assert registry.memory_type("domain_specific").name == "domain_specific"

    def test_entry_without_attributes_key(self, tmp_path: Path) -> None:
        _write(tmp_path / "memory_types" / "bare.yaml", "{}\n")
        registry = load_type_registry(self._settings_for(tmp_path), extend_defaults=False)
        assert registry.memory_type("bare").attributes == {}

    def test_yml_extension_is_accepted(self, tmp_path: Path) -> None:
        _write(tmp_path / "source_types" / "legacy.yml", "attributes: {}\n")
        registry = load_type_registry(self._settings_for(tmp_path), extend_defaults=False)
        assert "legacy" in registry.source_types

    def test_non_yaml_files_ignored(self, tmp_path: Path) -> None:
        _write(tmp_path / "source_types" / "real.yaml", "attributes: {}\n")
        _write(tmp_path / "source_types" / "README.md", "ignore me\n")
        registry = load_type_registry(self._settings_for(tmp_path), extend_defaults=False)
        assert set(registry.source_types) == {"real"}

    def test_invalid_attributes_raises(self, tmp_path: Path) -> None:
        _write(tmp_path / "memory_types" / "oops.yaml", "attributes: not_a_mapping\n")
        with pytest.raises(ValueError, match="Attributes"):
            load_type_registry(self._settings_for(tmp_path), extend_defaults=False)

    def test_defaults_to_package_settings(self) -> None:
        registry = load_type_registry()
        assert set(registry.memory_types) == {"semantic", "episodic", "procedural"}

    def test_end_to_end_via_config_file(self, tmp_path: Path) -> None:
        """Loading a user config file and building a registry from it."""
        _write(
            tmp_path / "goldfishmem.yaml",
            "type_registry:\n  root: my_types\n",
        )
        _write(tmp_path / "my_types" / "source_types" / "sensor.yaml", "attributes: {}\n")
        settings = load_settings(tmp_path / "goldfishmem.yaml")
        registry = load_type_registry(settings, extend_defaults=False)
        assert set(registry.source_types) == {"sensor"}


# ---------------------------------------------------------------------------
# Registry layering: user types overlaid on shipped defaults
# ---------------------------------------------------------------------------


class TestRegistryLayering:
    def _settings_for(self, root: Path) -> Settings:
        return Settings(type_registry=TypeRegistrySettings(root=root))

    def test_user_types_extend_defaults(self, tmp_path: Path) -> None:
        """A custom type is added on top of the shipped defaults."""
        _write(tmp_path / "source_types" / "sensor.yaml", "attributes: {}\n")
        _write(tmp_path / "memory_types" / "financial_insight.yaml", "attributes: {}\n")

        registry = load_type_registry(self._settings_for(tmp_path))

        # Defaults still present...
        assert {"conversation", "clickstream", "document", "domain_entity"} <= set(
            registry.source_types
        )
        assert {"semantic", "episodic", "procedural"} <= set(registry.memory_types)
        # ...plus the user's own types.
        assert "sensor" in registry.source_types
        assert "financial_insight" in registry.memory_types

    def test_user_type_overrides_same_named_default(self, tmp_path: Path) -> None:
        """A user file named like a default replaces that default's definition."""
        _write(
            tmp_path / "memory_types" / "semantic.yaml",
            "attributes:\n  ttl_days: 90\n",
        )
        registry = load_type_registry(self._settings_for(tmp_path))
        # Overridden, not duplicated.
        assert registry.memory_type("semantic").attributes == {"ttl_days": 90}
        assert {"semantic", "episodic", "procedural"} <= set(registry.memory_types)

    def test_extend_defaults_false_isolates(self, tmp_path: Path) -> None:
        _write(tmp_path / "memory_types" / "only_mine.yaml", "attributes: {}\n")
        registry = load_type_registry(self._settings_for(tmp_path), extend_defaults=False)
        assert set(registry.memory_types) == {"only_mine"}

    def test_default_registry_unaffected_by_layering(self) -> None:
        """Building a layered registry must not mutate DEFAULT_TYPE_REGISTRY."""
        before = set(DEFAULT_TYPE_REGISTRY.memory_types)
        assert before == {"semantic", "episodic", "procedural"}


# ---------------------------------------------------------------------------
# Settings layering: user config merged over package defaults
# ---------------------------------------------------------------------------


class TestSettingsLayering:
    def test_omitted_keys_inherit_from_package_defaults(self, tmp_path: Path) -> None:
        """A user config that only sets embedding inherits the rest from defaults."""
        _write(
            tmp_path / "goldfishmem.yaml",
            "embedding:\n  model: my-model\n  dimensions: 768\n",
        )
        settings = load_settings(tmp_path / "goldfishmem.yaml")
        # Inherited from the shipped package config (points into the package).
        assert settings.type_registry.root == DEFAULT_SETTINGS.type_registry.root
        assert settings.type_registry.source_types_dir == "source_types"
        # Overridden by the user.
        assert settings.embedding.model == "my-model"
        assert settings.embedding.dimensions == 768

    def test_nested_partial_override_within_section(self, tmp_path: Path) -> None:
        """Overriding one key in a section keeps the section's other keys."""
        _write(
            tmp_path / "goldfishmem.yaml",
            "type_registry:\n  source_types_dir: sources\n",
        )
        settings = load_settings(tmp_path / "goldfishmem.yaml")
        # Overridden...
        assert settings.type_registry.source_types_dir == "sources"
        # ...while root + memory_types_dir are inherited from the base.
        assert settings.type_registry.root == DEFAULT_SETTINGS.type_registry.root
        assert settings.type_registry.memory_types_dir == "memory_types"

    def test_user_relative_root_resolves_against_user_file(self, tmp_path: Path) -> None:
        _write(tmp_path / "goldfishmem.yaml", "type_registry:\n  root: my_types\n")
        settings = load_settings(tmp_path / "goldfishmem.yaml")
        assert settings.type_registry.root == tmp_path / "my_types"

    def test_merge_defaults_false_isolates(self, tmp_path: Path) -> None:
        """With merge_defaults=False, omitted keys fall back to dataclass defaults."""
        _write(tmp_path / "goldfishmem.yaml", "type_registry:\n  root: standalone\n")
        settings = load_settings(tmp_path / "goldfishmem.yaml", merge_defaults=False)
        # Root resolves against the user file, NOT the package default location.
        assert settings.type_registry.root == tmp_path / "standalone"
        assert settings.type_registry.root != DEFAULT_SETTINGS.type_registry.root

    def test_end_to_end_layered_config_and_registry(self, tmp_path: Path) -> None:
        """User adds a type via a partial config that inherits everything else."""
        _write(tmp_path / "goldfishmem.yaml", "type_registry:\n  root: my_types\n")
        _write(tmp_path / "my_types" / "memory_types" / "insight.yaml", "attributes: {}\n")
        settings = load_settings(tmp_path / "goldfishmem.yaml")
        registry = load_type_registry(settings)
        # User's type plus the shipped defaults.
        assert "insight" in registry.memory_types
        assert {"semantic", "episodic", "procedural"} <= set(registry.memory_types)
