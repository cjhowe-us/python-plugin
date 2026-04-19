---
name: python-mypy
description: >
  Deep guidance for mypy strict static typing. Use when configuring
  `[tool.mypy]`, debugging type errors, picking between `cast` /
  `assert isinstance` / TypeGuard, writing protocols vs ABCs, handling
  third-party libraries without stubs, dealing with pydantic plugin,
  silencing follow-imports for path-injected modules, or migrating an
  untyped codebase. Pairs with the unified `python` skill — load this
  one when the question is specifically about mypy.
---

# python-mypy

Strict mode is the default. Every project starts at `strict = true` and
adds per-module overrides only with a written reason.

## Config layout

```toml
[tool.mypy]
python_version = "3.11"
strict = true
files = ["src", "scripts", "hooks"]
explicit_package_bases = true
namespace_packages = true

[[tool.mypy.overrides]]
module = ["legacy.untyped.*"]
ignore_missing_imports = true
follow_imports = "skip"
```

## What `strict = true` enables

- `--disallow-untyped-defs` — every function annotated.
- `--disallow-any-generics` — `list`, `dict` must be parameterized.
- `--no-implicit-optional` — `Optional[T]` must be explicit.
- `--warn-unused-ignores` — dead `# type: ignore` flagged.
- `--warn-return-any` — function declared to return `T` can't actually
  return `Any`.

## Patterns for `Any`-leaking call sites

Wrap third-party returns:

```python
data: dict[str, Any] = json.loads(text)
return data
```

The local annotation pins the type so the function doesn't trip
`warn-return-any`.

For pydantic / msgspec models that mypy can't infer, install the
matching plugin (pydantic ships `pydantic.mypy`).

## Stubs

- First-party: write inline annotations.
- Third-party with stubs on PyPI: install `types-<package>`.
- Third-party without stubs: per-module override with
  `ignore_missing_imports = true`. Don't blanket-disable globally.

## Path-injected modules

If a module mutates `sys.path` to find a sibling package, mypy can't
resolve it. Two mitigations:

1. Set `mypy_path` in `[tool.mypy]` to the same dirs the runtime
   bootstrap finds.
2. Add an override silencing `import-untyped` and using
   `follow_imports = "skip"` for that package.

## Narrowing without `cast`

- `assert isinstance(x, T)` — runtime check, mypy narrows.
- `if x is not None:` — narrows `Optional[T]` to `T`.
- `match` statements with type patterns.
- `TypeGuard[T]` for custom predicates.

`cast(T, x)` is a last resort; prefer narrowing.

## Daemon mode

Use `dmypy run` (or the `mypy-type-checker` VS Code extension's
`preferDaemon: true`) to keep type state warm between checks. Cuts
incremental check time from seconds to milliseconds.

## CI integration

Run `python -m mypy` (no args — `[tool.mypy].files` controls scope).
Single job, no matrix needed.
