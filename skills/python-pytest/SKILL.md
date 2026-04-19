---
name: python-pytest
description: >
  Deep guidance for pytest. Use when writing tests, designing fixtures,
  parametrizing, configuring `[tool.pytest.ini_options]`, organizing
  conftest.py, debugging collection errors, picking plugins
  (pytest-xdist, pytest-asyncio, pytest-cov), or optimizing slow
  suites. Pairs with the unified `python` skill.
---

# python-pytest

pytest is the only test runner. No unittest classes unless inheriting from
a fixture framework that requires it.

## Config

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src", "scripts"]
addopts = "-ra --strict-markers --strict-config"
xfail_strict = true
filterwarnings = ["error"]
```

`--strict-markers` + `--strict-config` catch typos in marker / option
names. `filterwarnings = ["error"]` makes warnings fail the suite (turn
specific ones into `default::CategoryName`).

## File + name conventions

- Files: `tests/test_<module>.py` mirroring source layout.
- Functions: `def test_<behavior>(...)`. No camelCase.
- Test classes: only when grouping setup/teardown — use class scope
  fixtures, not `setUp`/`tearDown`.

## Fixtures

- Define shared fixtures in `tests/conftest.py`.
- Scope deliberately: `function` (default), `module`, `session`. Wider
  scope == faster but more shared state.
- Yield fixtures for setup + teardown:

```python
@pytest.fixture
def tmp_db(tmp_path):
    db = make_db(tmp_path / "x.db")
    yield db
    db.close()
```

- `monkeypatch` for env / attribute swaps. `tmp_path` for isolated
  filesystem. `caplog` for log assertions.

## Parametrize

```python
@pytest.mark.parametrize(
    ("input_text", "expected"),
    [
        ("foo", 3),
        ("hello", 5),
        ("", 0),
    ],
    ids=["short", "word", "empty"],
)
def test_length(input_text: str, expected: int) -> None:
    assert len(input_text) == expected
```

Always provide explicit `ids` for non-trivial params — default repr is
unreadable in failure output.

## Marks

- `pytest.mark.skip` — never run.
- `pytest.mark.skipif(condition, reason=...)` — conditionally skip.
- `pytest.mark.xfail(strict=True)` — expected failure; will fail the
  suite if it unexpectedly passes (with `xfail_strict = true`).
- Custom marks: declare in `[tool.pytest.ini_options].markers` so
  `--strict-markers` accepts them.

## Async tests

- Add `pytest-asyncio>=0.23` to dev deps.
- Mark with `@pytest.mark.asyncio` or set
  `asyncio_mode = "auto"`.

## Parallel + coverage

- `pytest-xdist` for parallel: `pytest -n auto`. Tests must be isolated
  (no shared global state).
- `pytest-cov` for coverage: `pytest --cov=src --cov-report=term-missing`.

## CLI cheatsheet

| Goal                              | Command                                  |
| --------------------------------- | ---------------------------------------- |
| Run one test                      | `pytest tests/test_x.py::test_y`         |
| Re-run last failures              | `pytest --lf`                            |
| Stop on first failure             | `pytest -x`                              |
| Verbose w/ short tracebacks       | `pytest -v --tb=short`                   |
| Drop into pdb on failure          | `pytest --pdb`                           |
| Show slowest 10                   | `pytest --durations=10`                  |
| Filter by name                    | `pytest -k "auth and not slow"`          |
| Filter by marker                  | `pytest -m "not slow"`                   |

## Debugging collection errors

If `pytest` fails before running anything ("collection error"):

1. The file imported something that raised at import time. Run
   `python -c "import tests.test_x"` to reproduce.
2. Missing `pythonpath` entry — add to `[tool.pytest.ini_options]`.
3. Module name collision — two `test_x.py` in different dirs without
   `__init__.py` clash. Add `__init__.py` to one or use unique names.
