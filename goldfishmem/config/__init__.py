"""Configuration loaders for goldfishmem.

Source and memory types are config-driven (PRD §4, §5).  Each type lives
in its own YAML file under a directory tree:

::

    <root>/
        source_types/
            conversation.yaml
            clickstream.yaml
            ...
        memory_types/
            semantic.yaml
            episodic.yaml
            ...

The filename (without extension) is the type name; each file's body is a
mapping with an ``attributes`` key so per-type extraction / retrieval
settings can grow without changing this module.

The defaults shipped with the package live under
``goldfishmem/config/default_types/``.  Users register custom types by
pointing :func:`load_type_registry` at their own directory.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any, cast

import yaml

__all__ = [
    "DEFAULT_TYPES_DIR",
    "DEFAULT_TYPE_REGISTRY",
    "TypeDefinition",
    "TypeRegistry",
    "load_type_registry",
]


DEFAULT_TYPES_DIR: Path = Path(str(files("goldfishmem.config").joinpath("default_types")))

_SOURCE_TYPES_SUBDIR = "source_types"
_MEMORY_TYPES_SUBDIR = "memory_types"


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


def _load_type_file(path: Path) -> TypeDefinition:
    name = path.stem
    text = path.read_text(encoding="utf-8")
    data: object = yaml.safe_load(text) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping at top level of {path}")
    data_map = cast(dict[Any, Any], data)
    raw_attrs: object = data_map.get("attributes", {})
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


def load_type_registry(path: Path | str = DEFAULT_TYPES_DIR) -> TypeRegistry:
    """Load a :class:`TypeRegistry` from a directory of per-type YAML files.

    The directory is expected to contain ``source_types/`` and/or
    ``memory_types/`` subdirectories; each ``*.yaml`` (or ``*.yml``) file
    inside represents one type, with the filename (without extension) as
    the type name.  Missing subdirectories produce an empty mapping for
    that section.
    """

    root = Path(path)
    if not root.is_dir():
        raise ValueError(f"Type registry path must be a directory: {root}")
    return TypeRegistry(
        source_types=_load_type_dir(root / _SOURCE_TYPES_SUBDIR),
        memory_types=_load_type_dir(root / _MEMORY_TYPES_SUBDIR),
    )


DEFAULT_TYPE_REGISTRY: TypeRegistry = load_type_registry()
