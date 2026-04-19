---
name: python
description: >
  Unified Python coding standard for projects in this workspace. Use this
  skill whenever reading, writing, editing, reviewing, or creating any
  `.py` file. Covers types (mypy --strict), lint/format (ruff), env +
  packaging (uv), tests (pytest), and publishing (PyPI). Per-tool deep
  dives live in sibling skills (`python-ruff`, `python-mypy`, `python-uv`,
  `python-pypi`, `python-pytest`) — load those for fine-grained guidance.
---

# Python Coding Standard

## Scope

All Python code in projects that opt into the `python-plugin`. Hooks
auto-run ruff + mypy + pytest after every `.py` edit; this skill is the
guidance the agent reads before writing the code in the first place.

## Tooling

| Concern                  | Tool        | Sibling skill   |
| ------------------------ | ----------- | --------------- |
| Lint + format            | ruff        | `python-ruff`   |
| Static types             | mypy strict | `python-mypy`   |
| Env + deps + lockfile    | uv          | `python-uv`     |
| Test runner + discovery  | pytest      | `python-pytest` |
| Distribution + publish   | uv / twine  | `python-pypi`   |

## Universal rules

### Types are mandatory

- Every function/method has annotated parameters and return type.
  `-> None` for procedures.
- Module-level globals get an annotation when type isn't obvious from
  the literal.
- Prefer concrete types over `Any`; use `Any` only at JSON / external
  boundaries and document why.
- Use `from __future__ import annotations` in every module; type
  expressions become strings, allowing forward references and Py3.9-style
  `dict[str, X]` on older runtimes.
- Generic containers always parameterized: `list[str]`, `dict[str, int]`,
  `tuple[int, ...]`. `dict[str, Any]` is acceptable for parsed JSON.

### Lint + format

- ruff is the only formatter. No black, no isort, no autopep8.
- ruff config in `pyproject.toml` under `[tool.ruff]` and
  `[tool.ruff.lint]`. Project owns the rule set; defaults: `E`, `F`, `I`,
  `UP`, `ANN`.
- Line length 100 unless project sets otherwise.
- Auto-fix locally: `ruff check --fix && ruff format`.

### Env + deps

- uv-managed venv at `.venv/` per project.
- Dependencies declared in `pyproject.toml`; `uv.lock` committed.
- Install: `uv sync` for normal work, `uv pip install -e ".[dev]"` for
  legacy editable workflows.
- Never `pip install` ad-hoc; if a dep is needed, add it to `pyproject`
  and re-lock.

### Tests

- Every non-trivial module has a `tests/test_<module>.py`. The
  `posttooluse-test-required` hook warns when a new module ships without
  one.
- Use `pytest` (no unittest classes unless inheriting from a fixture
  framework that requires it).
- Tests live in `tests/`, mirror source layout where feasible.
- Fixtures in `tests/conftest.py`; use scoped fixtures over module
  globals.

### Layout

- Source under `scripts/`, `src/<pkg>/`, or top-level package — match
  project convention.
- Hooks/agents/skills/workflows belong to Claude-Code plugins, not
  Python packages — exclude from `setuptools` discovery.

## Imports

- Group: stdlib, third-party, local — separated by blank lines (ruff `I`
  enforces).
- No relative imports across top-level packages; intra-package relative
  imports OK.
- No wildcard imports.

## Errors

- Raise specific exceptions. Catch the narrowest type that handles the
  case.
- `raise ... from e` to preserve cause when wrapping.
- Don't silently `except: pass`.

## Concurrency

- Default to sync code. Reach for `asyncio` only when the I/O concurrency
  is the bottleneck.
- `subprocess.run(..., check=False)` + explicit returncode check beats
  `try/except CalledProcessError` for control flow.

## Reference: per-tool skills

- `python-ruff` — rule selection, per-file ignores, format-on-save.
- `python-mypy` — strict-mode escape hatches, stubs, `cast()` patterns.
- `python-uv` — venvs, lockfile workflow, `uv run`, `uv tool`.
- `python-pytest` — fixtures, parametrize, async tests, plugins.
- `python-pypi` — building, `uv publish`, version bumping, trusted publishers.
