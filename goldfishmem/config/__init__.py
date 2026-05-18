"""Configuration loaders for goldfishmem.

Source and memory types are config-driven (PRD §4, §5).  The defaults
shipped with the package live in ``default_types.yaml``; users register
custom types by loading additional YAML files through
:func:`load_type_registry`.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any, cast

import yaml

__all__ = [
    "DEFAULT_TYPE_REGISTRY",
    "DEFAULT_TYPES_YAML",
    "TypeDefinition",
    "TypeRegistry",
    "load_type_registry",
]


DEFAULT_TYPES_YAML: Path = Path(str(files("goldfishmem.config").joinpath("default_types.yaml")))


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


def _parse_section(raw: object) -> dict[str, TypeDefinition]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError("Type section must be a mapping of name -> entry")
    entries = cast(dict[Any, Any], raw)
    result: dict[str, TypeDefinition] = {}
    for name, entry in entries.items():
        if not isinstance(name, str):
            raise ValueError(f"Type name must be a string, got {type(name).__name__}")
        attributes: dict[str, Any] = {}
        if entry is not None:
            if not isinstance(entry, dict):
                raise ValueError(f"Entry for {name!r} must be a mapping")
            entry_map = cast(dict[Any, Any], entry)
            raw_attrs: object = entry_map.get("attributes", {})
            if raw_attrs is None:
                attributes = {}
            elif isinstance(raw_attrs, dict):
                attributes = dict(cast(dict[Any, Any], raw_attrs))
            else:
                raise ValueError(f"Attributes for {name!r} must be a mapping")
        result[name] = TypeDefinition(name=name, attributes=attributes)
    return result


def load_type_registry(path: Path | str = DEFAULT_TYPES_YAML) -> TypeRegistry:
    """Load a :class:`TypeRegistry` from a YAML file.

    The file must contain ``source_types`` and/or ``memory_types`` keys,
    each mapping a type name to an entry of the shape
    ``{attributes: {...}}``.  Missing sections produce an empty mapping.
    """

    text = Path(path).read_text(encoding="utf-8")
    data: object = yaml.safe_load(text) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping at top level of {path}")
    data_map = cast(dict[Any, Any], data)
    return TypeRegistry(
        source_types=_parse_section(data_map.get("source_types")),
        memory_types=_parse_section(data_map.get("memory_types")),
    )


DEFAULT_TYPE_REGISTRY: TypeRegistry = load_type_registry()
