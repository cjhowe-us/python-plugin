# python-plugin

Claude Code plugin that wires the modern Python toolchain into every agent
session: ruff for lint + format, mypy for strict static types, uv for
envs and lockfile, pytest for related-test execution, and a missing-test
warning for new modules.

Ships:

- **Hooks** (`PostToolUse` after `Edit | Write | MultiEdit`):
  - `posttooluse-ruff` — `ruff check` + `ruff format --check` on edited `.py`.
  - `posttooluse-mypy` — type-check edited `.py` against the project's mypy config.
  - `posttooluse-pytest` — run pytest tests related to edited `.py` (companion `test_<name>.py` discovery; falls back to `--lf`).
  - `posttouse-test-required` — warn on new non-test `.py` without a sibling `test_<name>.py`.
  - `posttooluse-uv-lock` — re-lock `pyproject.toml` changes via `uv lock`.
- **Skills**:
  - `python` — unified Python coding standard (load on any `.py` interaction).
  - `python-ruff`, `python-mypy`, `python-uv`, `python-pytest`, `python-pypi` —
    per-tool deep dives for fine-grained enablement.

## Install

Add to your Claude Code marketplace plugins, or symlink the repo into
`~/.claude/plugins/`.

## Per-shell toggles

Each hook honors a `PYTHON_PLUGIN_<NAME>=0` env var to disable it:

- `PYTHON_PLUGIN_RUFF`
- `PYTHON_PLUGIN_MYPY`
- `PYTHON_PLUGIN_PYTEST`
- `PYTHON_PLUGIN_REQUIRE_TESTS`
- `PYTHON_PLUGIN_UV_LOCK`

## Requirements

- `python3` on PATH (3.11+).
- One of `ruff`, `mypy`, `pytest`, `uv` available — either project-local
  in `.venv/bin/`, globally installed, or invocable via `uvx`. Hooks
  skip silently when their tool isn't reachable; CI is the source of
  truth.

## License

Apache-2.0.
