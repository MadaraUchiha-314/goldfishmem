# Contributing to goldfishmem

Thanks for considering a contribution! This project is in its early days and
contributions, bug reports, and feature ideas are all welcome.

## How we manage work

- **GitHub Projects** is the source of truth for features, bugs, and the
  project roadmap.
- **GitHub Issues** is where the community files bug reports and feature
  requests. Please search existing issues before opening a new one.

## Getting set up

```bash
# 1. Install uv (one-time)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone & sync
git clone https://github.com/MadaraUchiha-314/goldfishmem.git
cd goldfishmem
uv sync

# 3. Install pre-commit hooks (covers commit-msg too)
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg
```

## The dev loop

```bash
uv run ruff check .              # lint
uv run ruff format .             # format
uv run pyright                   # type-check (strict)
uv run pytest tests/unit         # unit tests
uv run pytest tests/integration  # integration tests
```

`pre-commit` will run lint, format, type-check, and unit tests on every commit;
integration tests run in CI.

## Commit messages — Conventional Commits

All commit messages MUST follow the
[Conventional Commits](https://www.conventionalcommits.org/) format. This is
enforced by `commitizen` via a `commit-msg` hook.

Examples:

```
feat: add async memory.recall() method
fix(store): handle empty result set
docs: document the recall API
chore(deps): bump pyright to 1.1.395
refactor!: drop Python 3.11 support
```

Allowed types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `build`,
`ci`, `perf`, `style`, `revert`. A `!` after the type (or a `BREAKING CHANGE:`
footer) marks a breaking change and will trigger a major version bump.

If you prefer a guided prompt:

```bash
uv run cz commit
```

## Versioning & releases

Versioning is automated. When commits land on `main`, the release workflow
runs `cz bump`, which:

1. Computes the next semver from the conventional commits since the last tag.
2. Updates `pyproject.toml` and `goldfishmem/__init__.py`.
3. Writes/updates `CHANGELOG.md`.
4. Tags `vX.Y.Z` and publishes to PyPI via OIDC Trusted Publishing.

You do **not** need to bump versions in PRs — just write good commit messages.

## Pull requests

1. Open an issue first for anything non-trivial so we can agree on the approach.
   Coding agents (e.g. Claude, Cursor) are required to post a plan on the
   relevant issue with a `[Plan by <agent>]` prefix and wait for approval — see
   [`CLAUDE.md`](./CLAUDE.md) and [`AGENT.md`](./AGENT.md).
2. Branch off `main`.
3. Make your change with tests.
4. Ensure `pre-commit run --all-files` passes locally.
5. Open a PR; CI will run lint, type-check, unit tests, integration tests, and
   commit-message linting.

## Code of Conduct

Be kind. Assume good faith. Disagree on technical merits, not on people.
Harassment of any kind is not tolerated.
