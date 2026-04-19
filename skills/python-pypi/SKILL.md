---
name: python-pypi
description: >
  Deep guidance for publishing Python packages to PyPI. Use when
  preparing a release, configuring `[project]` metadata for distribution,
  building wheels with `uv build`, publishing with `uv publish`, setting
  up Trusted Publishers / OIDC in GitHub Actions, picking version bump
  strategy, dealing with name collisions, or recovering from a botched
  release. Pairs with the unified `python` skill.
---

# python-pypi

Use uv for build + publish. No twine, no flit-publish, no setup.py
upload.

## Pre-flight checklist

`pyproject.toml` must declare:

```toml
[project]
name = "your-package"           # PyPI-unique; check availability first
version = "0.1.0"               # PEP 440
description = "..."             # one line, shown on PyPI listing
readme = "README.md"
requires-python = ">=3.11"
license = { text = "Apache-2.0" }
authors = [{ name = "...", email = "..." }]
keywords = ["..."]
classifiers = [
  "License :: OSI Approved :: Apache Software License",
  "Programming Language :: Python :: 3.11",
  "Programming Language :: Python :: 3.12",
]

[project.urls]
Homepage = "https://github.com/owner/repo"
Source   = "https://github.com/owner/repo"
Issues   = "https://github.com/owner/repo/issues"

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"
```

## Build

```bash
uv build               # writes wheel + sdist to dist/
ls dist/               # sanity-check filenames
unzip -l dist/*.whl    # eyeball wheel contents
```

## Publish

### Manual (token-based)

```bash
uv publish             # reads UV_PUBLISH_TOKEN or --token
```

Get a project-scoped token at <https://pypi.org/manage/account/token/>.
Store as `UV_PUBLISH_TOKEN` in your shell, never commit.

### CI (Trusted Publishers / OIDC) — preferred

1. PyPI: Project -> Settings -> Publishing -> "Add a new publisher"
   (GitHub Actions). Fill owner / repo / workflow filename / env name.
2. Workflow:

```yaml
jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv build
      - run: uv publish --trusted-publishing always
```

No tokens, no secrets. OIDC handshake authenticates the runner.

## Versioning

- Bump in `[project].version` and tag the commit `vX.Y.Z`.
- SemVer: `MAJOR.MINOR.PATCH`. Pre-releases: `0.1.0a1`, `0.1.0rc1`.
- Don't reuse a version — PyPI rejects re-uploads even after deletion.
- Use `bumpver` or `hatch version` if manual bumping gets tedious.

## Name conflicts

PyPI names are globally unique and case-insensitive. Check availability
*before* you write the package:

```bash
curl -s https://pypi.org/pypi/<name>/json | head -c 200
```

If 404 the name is free. Common collision: anything resembling a
well-known framework. Pick a distinctive prefix
(`<org>-<thing>`, `claude-<thing>`).

## Recovery

- Wrong file uploaded: bump version and re-publish. PyPI never lets you
  overwrite.
- Sensitive data in a release: yank it (`pypi.org -> Manage -> Yank`)
  and publish a clean bump. Yank ≠ delete; the file remains downloadable
  for users who pinned it.
- Compromised token: revoke at <https://pypi.org/manage/account/token/>
  immediately, rotate.

## Checklist before pushing the tag

- `uv build` succeeds, wheel + sdist look right.
- `uv run python -m pytest` green.
- `uv run python -m mypy` green.
- README renders on PyPI's preview tool (or local: `python -m readme_renderer`).
- Version bumped, CHANGELOG updated.
- Tag matches `v<version>`.
