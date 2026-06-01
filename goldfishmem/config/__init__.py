"""Configuration for goldfishmem.

goldfishmem is driven by a central config file (default:
``goldfishmem/config/goldfishmem.yaml``).  It is the single entry point
that defines where type definitions live and holds settings for
embedding, storage, and retrieval — nothing about the system's layout
(directory names, etc.) is hard-coded in Python.

Type definitions themselves live in their own YAML files under a
directory tree whose location and subdirectory names come from the
config file::

    <type_registry.root>/
        <source_types_dir>/
            conversation.yaml
            ...
        <memory_types_dir>/
            semantic.yaml
            ...

The filename (without extension) is the type name; each file's body is a
mapping with an ``attributes`` key so per-type extraction / retrieval
settings can grow without changing this module.

Users override the defaults by passing their own config file to
:func:`load_settings`, then building a registry with
:func:`load_type_registry`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib.resources import files
from pathlib import Path
from typing import Any, cast

import yaml

__all__ = [
    "DEFAULT_CONFIG_FILE",
    "DEFAULT_SETTINGS",
    "DEFAULT_TYPE_REGISTRY",
    "EmbeddingSettings",
    "RetrievalSettings",
    "Settings",
    "StorageSettings",
    "TypeDefinition",
    "TypeRegistry",
    "TypeRegistrySettings",
    "load_settings",
    "load_type_registry",
]


DEFAULT_CONFIG_FILE: Path = Path(str(files("goldfishmem.config").joinpath("goldfishmem.yaml")))


# ---------------------------------------------------------------------------
# Settings (central config)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TypeRegistrySettings:
    """Where type definitions live and how their directories are named."""

    root: Path
    source_types_dir: str = "source_types"
    memory_types_dir: str = "memory_types"


@dataclass(frozen=True)
class EmbeddingSettings:
    """Embedding model configuration (PRD §6). Unset fields are ``None``."""

    model: str | None = None
    dimensions: int | None = None


@dataclass(frozen=True)
class StorageSettings:
    """Storage backend configuration. ``options`` is backend-specific."""

    backend: str | None = None
    options: dict[str, Any] = field(default_factory=lambda: dict[str, Any]())


@dataclass(frozen=True)
class RetrievalSettings:
    """Retrieval configuration. ``options`` is strategy-specific."""

    options: dict[str, Any] = field(default_factory=lambda: dict[str, Any]())


@dataclass(frozen=True)
class Settings:
    """Top-level goldfishmem configuration loaded from the central file."""

    type_registry: TypeRegistrySettings
    embedding: EmbeddingSettings = field(default_factory=EmbeddingSettings)
    storage: StorageSettings = field(default_factory=StorageSettings)
    retrieval: RetrievalSettings = field(default_factory=RetrievalSettings)
    source: Path | None = None


# ---------------------------------------------------------------------------
# Type registry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TypeDefinition:
    """A single source-type or memory-type entry from configuration.

    ``attributes`` is intentionally an opaque mapping: new fields
    (extraction config, retrieval config, embedding hints, ...) can be
    added through configuration without changing this dataclass.
    """

    name: str
    attributes: dict[str, Any]


@dataclass(frozen=True)
class TypeRegistry:
    """All source and memory types known to a goldfishmem instance."""

    source_types: dict[str, TypeDefinition]
    memory_types: dict[str, TypeDefinition]

    def source_type(self, name: str) -> TypeDefinition:
        return self.source_types[name]

    def memory_type(self, name: str) -> TypeDefinition:
        return self.memory_types[name]


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def _require_mapping(value: object, ctx: str) -> dict[Any, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{ctx} must be a mapping")
    return cast(dict[Any, Any], value)


def _opt_str(value: object, ctx: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{ctx} must be a string")
    return value


def _str_or_default(value: object, default: str, ctx: str) -> str:
    if value is None:
        return default
    if not isinstance(value, str):
        raise ValueError(f"{ctx} must be a string")
    return value


def _opt_int(value: object, ctx: str) -> int | None:
    if value is None:
        return None
    # bool is a subclass of int; reject it explicitly.
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{ctx} must be an integer")
    return value


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def load_settings(path: Path | str = DEFAULT_CONFIG_FILE) -> Settings:
    """Load :class:`Settings` from the central config file.

    Relative paths inside the file (e.g. ``type_registry.root``) are
    resolved relative to the config file's own directory.  Missing
    sections fall back to the dataclass defaults.
    """

    config_path = Path(path)
    text = config_path.read_text(encoding="utf-8")
    raw: object = yaml.safe_load(text) or {}
    data = _require_mapping(raw, f"top level of {config_path}")

    tr = _require_mapping(data.get("type_registry"), "type_registry")
    root = Path(_str_or_default(tr.get("root"), "default_types", "type_registry.root"))
    if not root.is_absolute():
        root = config_path.parent / root
    type_registry = TypeRegistrySettings(
        root=root,
        source_types_dir=_str_or_default(
            tr.get("source_types_dir"), "source_types", "type_registry.source_types_dir"
        ),
        memory_types_dir=_str_or_default(
            tr.get("memory_types_dir"), "memory_types", "type_registry.memory_types_dir"
        ),
    )

    emb = _require_mapping(data.get("embedding"), "embedding")
    embedding = EmbeddingSettings(
        model=_opt_str(emb.get("model"), "embedding.model"),
        dimensions=_opt_int(emb.get("dimensions"), "embedding.dimensions"),
    )

    sto = _require_mapping(data.get("storage"), "storage")
    storage = StorageSettings(
        backend=_opt_str(sto.get("backend"), "storage.backend"),
        options=dict(_require_mapping(sto.get("options"), "storage.options")),
    )

    ret = _require_mapping(data.get("retrieval"), "retrieval")
    retrieval = RetrievalSettings(
        options=dict(_require_mapping(ret.get("options"), "retrieval.options")),
    )

    return Settings(
        type_registry=type_registry,
        embedding=embedding,
        storage=storage,
        retrieval=retrieval,
        source=config_path,
    )


def _load_type_file(path: Path) -> TypeDefinition:
    name = path.stem
    text = path.read_text(encoding="utf-8")
    raw: object = yaml.safe_load(text) or {}
    data = _require_mapping(raw, f"top level of {path}")
    raw_attrs: object = data.get("attributes", {})
    if raw_attrs is None:
        attributes: dict[str, Any] = {}
    elif isinstance(raw_attrs, dict):
        attributes = dict(cast(dict[Any, Any], raw_attrs))
    else:
        raise ValueError(f"Attributes for {name!r} in {path} must be a mapping")
    return TypeDefinition(name=name, attributes=attributes)


def _load_type_dir(directory: Path) -> dict[str, TypeDefinition]:
    if not directory.is_dir():
        return {}
    result: dict[str, TypeDefinition] = {}
    for entry in sorted(directory.iterdir()):
        if entry.suffix not in {".yaml", ".yml"} or not entry.is_file():
            continue
        definition = _load_type_file(entry)
        if definition.name in result:
            raise ValueError(f"Duplicate type {definition.name!r} in {directory}")
        result[definition.name] = definition
    return result


def load_type_registry(settings: Settings | None = None) -> TypeRegistry:
    """Build a :class:`TypeRegistry` from ``settings``.

    The directory tree and subdirectory names come from
    ``settings.type_registry`` (loaded from the central config file), so
    no layout is hard-coded here.  When ``settings`` is omitted the
    package defaults (:data:`DEFAULT_SETTINGS`) are used.
    """

    if settings is None:
        settings = DEFAULT_SETTINGS
    trs = settings.type_registry
    return TypeRegistry(
        source_types=_load_type_dir(trs.root / trs.source_types_dir),
        memory_types=_load_type_dir(trs.root / trs.memory_types_dir),
    )


DEFAULT_SETTINGS: Settings = load_settings()
DEFAULT_TYPE_REGISTRY: TypeRegistry = load_type_registry(DEFAULT_SETTINGS)
