# CLAUDE.md

Guidance for Claude (and other coding agents) when working in this repository.

## Project

`goldfishmem` is a production grade memory system for agents. The PyPI
distribution and the Python import name match: `from goldfishmem import ...`.

## Tech stack

- **Language**: Python 3.12+
- **Build / packaging**: [hatchling](https://hatch.pypa.io/) via `pyproject.toml`
- **Package manager**: [uv](https://docs.astral.sh/uv/)
- **Linter / formatter**: [ruff](https://docs.astral.sh/ruff/)
- **Type checker**: [pyright](https://microsoft.github.io/pyright/) (strict mode)
- **Tests**: [pytest](https://docs.pytest.org/)
- **Pre-commit**: [pre-commit](https://pre-commit.com/)
- **Commit linting**: [commitizen](https://commitizen-tools.github.io/commitizen/) (Conventional Commits)
- **Docs**: Markdown under `docs/`, with [mermaid](https://mermaid.js.org/) for diagrams
- **CI/CD**: GitHub Actions

## Repository layout

```
goldfishmem/      # Python package (all source code lives here; import as `goldfishmem`)
tests/            # pytest suite (unit + integration)
docs/             # Consumer-facing documentation
.claude/          # Claude Code settings, skills, plugins
.mcp.json         # MCP server registrations
.github/workflows # CI/CD pipelines
```

All source code must live under the `goldfishmem/` folder. All imports look like
`from goldfishmem import ...`.

## Local development

```bash
# Install uv (one-time)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create the virtualenv and install dependencies (including dev tools)
uv sync

# Install pre-commit git hooks
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg

# Run the dev loop
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
```

The virtualenv is created at `.venv/` in the repo root.

## Conventions and rules

1. **Plan first, implement after approval.** For any non-trivial work, post the
   implementation plan as a comment on the relevant GitHub Issue or project work
   item **before** writing code. Prefix the comment with `**[Plan by Claude]**`
   (or `[Plan by <agent name>]` for other agents) so reviewers can identify it.
   Wait for the user to review and approve the plan before implementing. Only
   skip this for clearly trivial changes (typo fixes, one-line config tweaks).
2. **Conventional Commits / semantic commits — always.** Commit messages MUST use
   the conventional-commits prefix: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`,
   `test:`, `build:`, `ci:`, `perf:`, `style:`, `revert:`. This is enforced by
   commitizen via the `commit-msg` pre-commit hook.
3. **Pull-request titles MUST also follow Conventional Commits.** PRs are
   squash-merged onto `main`, and the squash commit takes the PR title. Because
   `release.yml` runs `cz bump` to compute the next semver from commit messages
   on `main`, a non-conventional PR title will break automated semantic
   releases. Pick the prefix that reflects the PR's user-visible impact:
   `feat:` (minor bump), `fix:` (patch bump), `feat!:`/`fix!:` or a
   `BREAKING CHANGE:` footer (major bump), and `chore:`/`docs:`/`test:`/`ci:`/
   `build:`/`refactor:`/`style:`/`perf:`/`revert:` for no version bump.
4. **GitHub Projects** is the source of truth for features, bugs, and the project
   roadmap. Track all work there.
5. **Community contributions** are welcome — feature requests and bug reports
   should be filed as GitHub Issues.
6. **Type checking is strict.** New code must pass `pyright` in strict mode.
7. **Tests are required.** New functionality must come with unit tests in `tests/`.
   Integration tests should be marked with `@pytest.mark.integration`.
8. **Docs in `docs/` are consumer-facing.** Developer docs live in the root
   `README.md`.
9. **Don't create files** (especially Markdown docs) unless they are necessary for
   the task. Prefer editing existing files.

## Agent support

This repo is set up to work out-of-the-box with the following coding agents:

- **Claude Code** — configured via `.claude/settings.json` and this `CLAUDE.md`
- **Cursor** — configured via `AGENTS.md` (a symlink/alias of `AGENT.md`)

MCP servers used by the project are declared in `.mcp.json` so any agent that
honors the standard MCP config will pick them up.

The repository is intended to be self-contained: every skill, plugin, and MCP
needed to develop on it is declared inside the repo itself.
