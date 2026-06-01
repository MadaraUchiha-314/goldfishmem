# goldfishmem

A production grade memory system for agents.

The Python import name matches the distribution name:
> `from goldfishmem import ...`.

## Install

```bash
pip install goldfishmem
# or with uv
uv add goldfishmem
```

## Quick start

goldfishmem is config-driven. Load the shipped defaults (or your own
`goldfishmem.yaml`) and build the type registry:

```python
from goldfishmem import DEFAULT_SETTINGS, load_type_registry

registry = load_type_registry(DEFAULT_SETTINGS)
print(sorted(registry.memory_types))   # ['episodic', 'procedural', 'semantic']
print(sorted(registry.source_types))   # ['clickstream', 'conversation', 'document', 'domain_entity']
```

See [Configuration](./configuration.md) for custom types and config layering.

## Documentation

- [Configuration](./configuration.md) — the central config file, type definitions, and layering.
- [Architecture](./architecture.md) — how goldfishmem is structured internally.

## Project links

- Source: https://github.com/MadaraUchiha-314/goldfishmem
- Issues: https://github.com/MadaraUchiha-314/goldfishmem/issues
- PyPI: https://pypi.org/project/goldfishmem/
