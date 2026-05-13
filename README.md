# goldfishmem

> A production grade memory system for agents.

`goldfishmem` is published on PyPI under the same name. The Python import name
matches the distribution:

```python
from goldfishmem import hello_world
```

Consumer-facing documentation lives in [`docs/`](./docs/). This README is the
**developer** guide for working on the project.

## Tech stack

| Concern | Tool |
| --- | --- |
| Language | Python 3.12+ |
| Package manager | [uv](https://docs.astral.sh/uv/) |
| Build backend | [hatchling](https://hatch.pypa.io/) |
| Linter / formatter | [ruff](https://docs.astral.sh/ruff/) |
| Type checker | [pyright](https://microsoft.github.io/pyright/) (strict) |
| Tests | [pytest](https://docs.pytest.org/) + [pytest-cov](https://pytest-cov.readthedocs.io/) |
| Pre-commit | [pre-commit](https://pre-commit.com/) |
| Commit linting | [commitizen](https://commitizen-tools.github.io/commitizen/) (Conventional Commits) |
| Docs | Markdown + [mermaid](https://mermaid.js.org/) diagrams under `docs/` |
| CI/CD | GitHub Actions |
| PyPI publishing | OIDC Trusted Publishing (no API tokens) |

## Repository layout

```
goldfishmem/          # source package (all code lives here, import as `goldfishmem`)
tests/
  unit/               # fast unit tests
  integration/        # integration tests (also gated on the `integration` marker)
docs/                 # consumer-facing documentation
.claude/              # Claude Code permissions/skills/plugins
.mcp.json             # MCP server registrations (chrome-devtools, Lucid)
.github/workflows/    # ci.yml, release.yml
CLAUDE.md             # guidance for Claude
AGENT.md / AGENTS.md  # guidance for Cursor and other agents
CONTRIBUTING.md       # contributor guide
```

## Local development

### 1. Install uv (one-time)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and sync dependencies

```bash
git clone https://github.com/MadaraUchiha-314/goldfishmem.git
cd goldfishmem
uv sync
```

`uv sync` creates `.venv/` in the project root and installs runtime + dev
dependencies from `pyproject.toml`.

### 3. Install the pre-commit hooks

```bash
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg
```

This installs two hooks:

- **`pre-commit`** — runs `ruff check`, `ruff format`, `pyright`, and the unit
  test suite on every commit.
- **`commit-msg`** — runs `commitizen check` to enforce
  [Conventional Commits](https://www.conventionalcommits.org/).

You can also run the hooks ad-hoc:

```bash
uv run pre-commit run --all-files
```

### 4. The dev loop

```bash
uv run ruff check .              # lint
uv run ruff format .             # format
uv run pyright                   # type-check (strict)
uv run pytest tests/unit         # unit tests
uv run pytest tests/integration  # integration tests
```

### 5. Writing a commit

Either format the message yourself (`feat: ...`, `fix: ...`, etc.) or use the
interactive helper:

```bash
uv run cz commit
```

## CI/CD

- **`.github/workflows/ci.yml`** — runs on every PR and on push to `main`:
  - `ruff check` and `ruff format --check`
  - `pyright` (strict)
  - Unit tests against Python 3.12 and 3.13
  - Integration tests
  - Commit-message linting on PRs
- **`.github/workflows/release.yml`** — runs on push to `main` after CI passes:
  - `cz bump --yes --changelog` computes the next semver from the conventional
    commits since the last tag, updates `pyproject.toml` and
    `goldfishmem/__init__.py`, and updates `CHANGELOG.md`.
  - Pushes the version-bump commit and the new tag back to `main`.
  - Builds the sdist + wheel with `uv build`.
  - Publishes to PyPI via [OIDC Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
    (no `PYPI_API_TOKEN` secret needed — configure the PyPI project under
    `Settings → Publishing` to trust this GitHub repo + `release.yml`).
  - Creates a GitHub Release with the changelog and dist artifacts attached.

### One-time PyPI Trusted Publisher setup

Before the first release succeeds, configure PyPI:

1. Reserve the project name `goldfishmem` on https://pypi.org by uploading a
   first version manually, OR pre-create the project via "pending publisher"
   under your PyPI account → *Publishing* → *Add a new pending publisher*.
2. Add a trusted publisher with:
   - Owner: `MadaraUchiha-314`
   - Repository: `goldfishmem`
   - Workflow filename: `release.yml`
   - Environment name: `pypi`
3. In this repo's settings, create a GitHub Environment named `pypi`.

### One-time branch protection setup

`release.yml` pushes the version-bump commit and tag back to `main`. The
default `GITHUB_TOKEN` cannot bypass branch protection, so you must grant
the workflow's bot account explicit bypass rights:

1. Go to **Settings → Branches → Branch protection rules → `main`** (create
   the rule if you haven't yet).
2. Under **"Allow specified actors to bypass required pull requests"** (and
   "Allow force pushes" if that toggle is on), add **`github-actions[bot]`**.
3. If you use rulesets instead of classic protection: **Settings → Rules →
   Rulesets → your `main` ruleset → Bypass list →** add the
   `github-actions` role.

Without this, the release workflow will fail at the "Push version bump and
tag" step with a protected-branch rejection.

## Project management

- **Roadmap, features, bugs**: tracked on GitHub Projects.
- **Community feedback**: open a [GitHub Issue](https://github.com/MadaraUchiha-314/goldfishmem/issues).
- **Coding-agent contributions**: see [`CLAUDE.md`](./CLAUDE.md) and
  [`AGENT.md`](./AGENT.md). Agents must post a plan with a `[Plan by <agent>]`
  prefix on the relevant issue and wait for human approval before implementing.

## License

[MIT](./LICENSE)
