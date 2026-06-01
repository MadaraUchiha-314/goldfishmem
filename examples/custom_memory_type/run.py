"""Define a custom memory type through config and build a Memory with it.

Run from anywhere:

    uv run python examples/custom_memory_type/run.py

This example shows how goldfishmem is config-driven: a user supplies their
own ``goldfishmem.yaml`` (which inherits the shipped defaults) plus a
directory of type definitions. The resulting registry contains the
built-in default types *plus* the user's custom ``financial_insight``
type — no source changes required.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from goldfishmem import (
    EmbeddingMetadata,
    ExtractionMethod,
    Memory,
    Provenance,
    load_settings,
    load_type_registry,
)

HERE = Path(__file__).parent


def main() -> None:
    # 1. Load the user config. merge_defaults=True (the default) layers this
    #    file on top of the package's shipped goldfishmem.yaml, so we only
    #    had to specify `type_registry.root` in our file.
    settings = load_settings(HERE / "goldfishmem.yaml")
    print(f"Type registry root: {settings.type_registry.root}")

    # 2. Build the registry. extend_defaults=True (the default) overlays our
    #    custom types on top of the shipped defaults.
    registry = load_type_registry(settings)

    print("\nMemory types available:")
    for name in sorted(registry.memory_types):
        marker = "  (custom)" if name == "financial_insight" else ""
        print(f"  - {name}{marker}")

    custom = registry.memory_type("financial_insight")
    print(f"\nfinancial_insight attributes: {custom.attributes}")

    # 3. Construct a Memory of the custom type. The type name is just a
    #    string, validated against the registry the application maintains.
    memory = Memory(
        content="The user's monthly software budget is $5,000.",
        memory_type=custom.name,
        provenance=Provenance(
            extraction_run_id="example-run-001",
            extracted_at=datetime(2026, 6, 1, tzinfo=UTC),
            extraction_method=ExtractionMethod.LLM_EXTRACTION,
        ),
        embedding_metadata=EmbeddingMetadata(
            text="monthly software budget is $5,000",
            model="text-embedding-3-small",
            dimensions=1536,
        ),
    )
    print(f"\nBuilt memory {memory.id} of type {memory.memory_type!r}")


if __name__ == "__main__":
    main()
