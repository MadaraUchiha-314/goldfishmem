# AGENT.md

Guidance for coding agents (Cursor, Claude, Aider, etc.) working in this repository.
This file mirrors `CLAUDE.md`; either may be consulted depending on the agent.

## Project

`goldfishmem` is a production grade memory system for agents. The PyPI
distribution and the Python import name match: `from goldfishmem import ...`.

## Tech stack

- **Language**: Python 3.12+
- **Build / packaging**: hatchling via `pyproject.toml`
- **Package manager**: uv
- **Linter / formatter**: ruff
- **Type checker**: pyright (strict mode)
- **Tests**: pytest
- **Pre-commit**: pre-commit
- **Commit linting**: commitizen (Conventional Commits)
- **Docs**: Markdown under `docs/`, mermaid for diagrams
- **CI/CD**: GitHub Actions

## Repository layout

```
goldfishmem/      # Python package (all source code; import as `goldfishmem`)
tests/            # pytest suite (unit + integration)
docs/             # Consumer-facing documentation
.claude/          # Claude Code settings, skills, plugins
.mcp.json         # MCP server registrations
.github/workflows # CI/CD pipelines
```

All source code lives under `goldfishmem/`. All imports look like
`from goldfishmem import ...`.

## Local development

```bash
uv sync
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
```

## Conventions and rules

1. **Plan first, implement after approval.** For any non-trivial work, post the
   implementation plan as a comment on the relevant GitHub Issue or project work
   item **before** writing code. Wait for the user to review and approve the
   plan before implementing. Only skip this for clearly trivial changes (typo
   fixes, one-line config tweaks).
1a. **Agent comment prefix — always.** All comments posted by a coding agent on
   GitHub Issues, PRs, or any other platform must be prefixed with a title line:
   `**Comment by: <Agent Name>-<Model Name>**`. For example:
   `**Comment by: Claude Code-claude-opus-4-6**` or
   `**Comment by: Cursor-gpt-4o**`. This makes it easy to identify which agent
   (and which model) authored each comment.
2. **Conventional Commits / semantic commits — always.** Commit messages MUST start
   with one of: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`, `build:`,
   `ci:`, `perf:`, `style:`, `revert:`. Enforced by commitizen on `commit-msg`.
3. **PR titles MUST follow Conventional Commits too.** PRs are squash-merged
   onto `main`, so the squash commit inherits the PR title. `release.yml` runs
   `cz bump` to derive the next semver from commits on `main`; a non-conventional
   PR title will break the semantic release. Use `feat:` (minor), `fix:` (patch),
   `feat!:` / `fix!:` or a `BREAKING CHANGE:` footer (major), or
   `chore:`/`docs:`/`test:`/`ci:`/`build:`/`refactor:`/`style:`/`perf:`/`revert:`
   for no version bump.
4. **GitHub Projects** is the source of truth for features, bugs, and the roadmap.
5. **Community** can submit GitHub Issues for feature requests and bug reports.
6. **Strict type-checking.** New code must pass `pyright` strict.
7. **Tests required.** Add unit tests under `tests/` for every new function.
   Integration tests use the `@pytest.mark.integration` marker.
8. `docs/` is for consumers of the package; developer docs live in `README.md`.
9. Prefer editing existing files. Avoid creating new files (especially docs) unless
   necessary.

## MCPs and self-containment

MCP servers used by the project are declared in `.mcp.json`. Claude-specific
permissions, skills, and plugins are declared under `.claude/`. The repository is
intended to be self-contained: every skill, plugin, and MCP needed to develop on
it is declared inside the repo itself.
