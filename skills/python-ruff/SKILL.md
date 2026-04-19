---
name: python-ruff
description: >
  Deep guidance for ruff lint + format in Python projects. Use when
  configuring `[tool.ruff]` in pyproject.toml, picking rule sets, adding
  per-file ignores, debugging ruff diagnostics, wiring format-on-save,
  resolving conflicts between ruff format and ruff check, or migrating
  from black/isort/flake8. Pairs with the unified `python` skill — load
  this one when the question is specifically about ruff.
---

# python-ruff

Ruff is the only linter and formatter for Python in this workspace. No black, no isort, no
autopep8, no flake8.

## Config layout

```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
extend-select = ["I", "UP", "ANN"]
ignore = ["ANN101", "ANN102", "ANN401"]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["ANN"]
"scripts/bootstrap.py" = ["E402"]
```

## Rule sets we enable

- `E`, `F` — pycodestyle errors + pyflakes (ruff defaults).
- `I` — import sorting. Replaces isort.
- `UP` — pyupgrade. Surfaces stale `typing.List` / `datetime.timezone.utc`
  patterns automatically.
- `ANN` — flake8-annotations. Required for the universal-types policy.
- Optional add-ons project-by-project: `B` (bugbear), `SIM` (simplify),
  `TCH` (type-checking-only imports), `RUF` (ruff-specific).

## Rules we always ignore

- `ANN101` / `ANN102` — `self` and `cls` annotations are noise.
- `ANN401` — `Any` is allowed; mypy enforces the substantive coverage.
- `E501` is *not* in this list: we honor line-length. Use ruff format
  to wrap, or break the expression.

## Per-file ignores

- `tests/**` — disable `ANN` group (pytest fixtures rarely benefit from
  explicit annotation noise).
- Bootstrap modules that mutate `sys.path` before importing: `E402`.

## CLI workflow

- Local: `ruff check --fix && ruff format`.
- CI: `ruff check` then `ruff format --check` (separate steps so format
  drift is its own failure signal).
- Pre-commit-equivalent: the `posttooluse-ruff` hook runs both on every
  agent edit.

## ruff vs ruff format

`ruff format` is the formatter (black-compatible). `ruff check` runs lint
rules including some that auto-fix style. Run `format` *after* `check
--fix` so structural fixes land before whitespace normalization.

## VS Code

```json
"[python]": {
  "editor.defaultFormatter": "charliermarsh.ruff",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.ruff": "explicit",
    "source.organizeImports.ruff": "explicit"
  }
}
```

`ruff.importStrategy = "fromEnvironment"` makes the extension use the
project venv's ruff so VS Code matches CI exactly.

## Migrating

- `black` -> remove from deps; ruff format is wire-compatible.
- `isort` -> add `I` to ruff lint extend-select; delete isort config.
- `flake8` -> add `E,F,W` (W via `extend-select`); migrate plugins to
  ruff's built-in rule families.
