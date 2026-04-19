---
name: python-uv
description: >
  Deep guidance for uv as the Python env + dep + tool runner. Use when
  setting up a venv, declaring dependencies in pyproject.toml,
  maintaining uv.lock, choosing between `uv run` / `uv tool` / `uvx`,
  pinning Python versions, debugging resolver conflicts, or migrating
  from pip / pip-tools / poetry. Pairs with the unified `python` skill.
---

# python-uv

uv is the only Python toolchain manager in this workspace. No pyenv, no
poetry, no pip-tools, no virtualenv-wrapper.

## Project layout

```text
project/
  pyproject.toml      # source of truth for deps + tool config
  uv.lock             # committed, machine-managed
  .venv/              # gitignored, recreated on demand
```

## Day-to-day commands

| Goal                                 | Command                              |
| ------------------------------------ | ------------------------------------ |
| Create venv with project Python      | `uv venv`                            |
| Install everything from lock         | `uv sync`                            |
| Install with dev extras              | `uv sync --extra dev`                |
| Add a dependency                     | `uv add httpx`                       |
| Add a dev dependency                 | `uv add --dev pytest`                |
| Run a script in the venv             | `uv run python script.py`            |
| Run a tool ephemerally               | `uvx ruff check .`                   |
| Install a tool globally              | `uv tool install ruff`               |
| Pin Python version                   | `uv python pin 3.12`                 |
| Re-lock without upgrading            | `uv lock`                            |
| Re-lock and upgrade everything       | `uv lock --upgrade`                  |
| Re-lock and upgrade one dep          | `uv lock --upgrade-package httpx`    |
| Build wheel + sdist                  | `uv build`                           |
| Publish to PyPI                      | `uv publish`                         |

## When to use which command

- `uv run <cmd>` — run from the project's venv. Equivalent to activating
  the venv first, but stateless.
- `uvx <cmd>` — run an ephemeral isolated tool. Doesn't pollute the
  project's deps. Right for one-off `ruff`, `mypy`, `bumpver`.
- `uv tool install` — install a tool to the user's global tool dir.
  Right for things you call from any cwd: `ruff`, `pre-commit`.

## pyproject.toml dependency syntax

```toml
[project]
dependencies = [
  "httpx>=0.27,<1",
  "pydantic>=2",
]

[project.optional-dependencies]
dev = ["pytest>=8", "ruff>=0.7", "mypy>=1.11"]

[tool.uv]
dev-dependencies = ["ipython"]   # not exposed as an extra
```

`[tool.uv].dev-dependencies` is the modern home for dev-only deps. The
older `[project.optional-dependencies].dev` still works and is more
portable across non-uv tools (pip).

## Lockfile

- Always commit `uv.lock`. Reproducible installs depend on it.
- `uv lock` is non-destructive: it preserves existing pins.
- Re-lock when `pyproject.toml` changes (the
  `posttooluse-uv-lock` hook does this automatically).
- CI uses `uv sync --frozen` to fail on drift.

## Resolver conflicts

When `uv add` reports a conflict:

1. Read the printed graph — it identifies the incompatible spec.
2. Loosen one constraint (`>=` rather than `==`), or drop the offender.
3. If a transitive dep is the problem, add an explicit constraint on it
   to your `[project].dependencies` to override.

## Python versions

- `requires-python = ">=3.11"` in `[project]`.
- `uv python install 3.12` to fetch a managed interpreter.
- `uv python pin 3.12` to record the project's default; uv writes
  `.python-version`.

## Migration

- pip + requirements.txt -> `uv add` each line, delete requirements.txt.
- poetry -> `uv init --bare`, copy `[tool.poetry.dependencies]` into
  `[project].dependencies`, delete `poetry.lock`.
- pip-tools -> drop `requirements.in` / `requirements.txt`; use uv.lock.
