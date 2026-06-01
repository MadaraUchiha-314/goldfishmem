# Configuration

goldfishmem is driven by a **central config file**. A single
`goldfishmem.yaml` defines where type definitions live and holds settings
for embedding, storage, and retrieval. Nothing about the system's layout
(directory names, etc.) is hard-coded in Python — it all flows from this
file.

The package ships a default config and a default set of types. You
customize behavior by providing your own `goldfishmem.yaml` and your own
type definitions; both **layer on top of the shipped defaults** so you
only specify what differs.

## The config file

The shipped `goldfishmem.yaml` looks like this:

```yaml
type_registry:
  root: default_types          # where type definitions live
  source_types_dir: source_types
  memory_types_dir: memory_types

embedding:
  model: null                  # wired up as the embedding pipeline lands
  dimensions: null

storage:
  backend: null
  options: {}

retrieval:
  options: {}
```

Load it into a `Settings` object:

```python
from goldfishmem import load_settings, DEFAULT_SETTINGS

settings = load_settings("path/to/goldfishmem.yaml")
# or use the shipped defaults directly:
settings = DEFAULT_SETTINGS
```

Relative paths inside the file (such as `type_registry.root`) are resolved
relative to **that file's own directory**.

## Type definitions

Each source type and memory type is its own YAML file under the registry
root. The filename (without extension) is the type name; the body is a
mapping with an `attributes` key:

```
<type_registry.root>/
    source_types/
        conversation.yaml
        clickstream.yaml
        ...
    memory_types/
        semantic.yaml
        episodic.yaml
        procedural.yaml
```

A type file (e.g. `memory_types/financial_insight.yaml`):

```yaml
attributes:
  retrieval:
    recency_weight: 0.4
  retention_days: 365
```

`attributes` is intentionally opaque to the core models — add
extraction/retrieval knobs there without any code changes. Build a
registry from settings:

```python
from goldfishmem import load_type_registry

registry = load_type_registry(settings)
registry.memory_type("semantic")          # -> TypeDefinition
registry.source_type("conversation").attributes
```

## Layering: defaults as a base

By default, both loaders treat the shipped package config as a base layer,
so a user config inherits everything it does not override.

### Settings inheritance

`load_settings(path)` deep-merges your file over the shipped
`goldfishmem.yaml`. Keys you omit are inherited; nested maps (like
`storage.options`) are merged rather than replaced wholesale.

```yaml
# my-config.yaml — only override the embedding model
embedding:
  model: text-embedding-3-large
  dimensions: 3072
```

```python
settings = load_settings("my-config.yaml")
settings.embedding.model            # "text-embedding-3-large"  (yours)
settings.type_registry.root         # inherited from the package defaults
```

Pass `merge_defaults=False` to load a fully standalone config with no
inheritance.

### Type registry overlay

`load_type_registry(settings)` overlays your types on top of the shipped
defaults: the built-in types (`semantic`, `episodic`, `procedural`,
`conversation`, ...) are always present, and a type file of yours that
shares a name with a default **overrides** it.

```python
registry = load_type_registry(settings)
# -> shipped defaults  +  your custom types
```

Pass `extend_defaults=False` to get only the types under your registry
root, with no defaults mixed in.

## Worked example

A complete, runnable example lives in
[`examples/custom_memory_type/`](../examples/custom_memory_type/). It
defines a custom `financial_insight` memory type purely through config and
builds a `Memory` of that type:

```bash
uv run python examples/custom_memory_type/run.py
```
