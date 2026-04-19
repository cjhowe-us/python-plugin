#!/usr/bin/env python3
"""Warn when a newly-added .py file lacks a matching test.

Companion to `posttooluse-test-required.py` (the Claude Code PostToolUse
variant): this one runs at ``git commit`` time via the pre-commit framework
or a direct ``.git/hooks/pre-commit`` install.

Scans files in the index that are being *added* (diff-filter=A), ignores
files under ``tests/``/``test/`` and anything matching ``test_*.py`` /
``*_test.py``, then looks for a sibling test (same stem) anywhere in the
working tree. Missing-test situations are printed to stderr; exit code is
always 0 so the commit isn't blocked — the point is a visible warning, not
enforcement.

Disable per-shell with ``PYTHON_PLUGIN_REQUIRE_TESTS=0``.

Invocations:

    # pre-commit framework (preferred):
    .pre-commit-config.yaml hook id: new-file-tests

    # direct install of a .git/hooks/pre-commit:
    python3 hooks/pre-commit-new-file-tests.py [<path>…]

When run via the pre-commit framework, the framework passes the filenames
as positional args. When run as a raw git hook, no args are passed and we
fall back to reading the staged file set via ``git diff --cached``.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

WARN_LABEL = "[python-plugin/new-file-tests]"


def _disabled() -> bool:
    return os.environ.get("PYTHON_PLUGIN_REQUIRE_TESTS", "").lower() in {
        "0",
        "false",
        "no",
        "off",
        "disabled",
    }


def _repo_root() -> Path:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], stderr=subprocess.DEVNULL
        )
        return Path(out.decode().strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return Path.cwd()


def _staged_added_files(root: Path) -> list[Path]:
    """Return files newly added in the index (diff-filter=A)."""
    try:
        out = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=A", "-z"],
            cwd=str(root),
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    names = [n for n in out.decode().split("\x00") if n]
    return [root / n for n in names]


def _is_test_path(p: Path) -> bool:
    if p.name.startswith("test_") or p.name.endswith("_test.py"):
        return True
    parts = {part.lower() for part in p.parts}
    return bool(parts & {"tests", "test"})


def _has_sibling_test(target: Path, root: Path) -> bool:
    stem = target.stem
    needles = {f"test_{stem}.py", f"{stem}_test.py"}
    for name in needles:
        if any(root.rglob(name)):
            return True
    return False


def _candidates(root: Path, argv_files: list[str]) -> list[Path]:
    """Resolve input files to absolute Paths filtered to existing .py files."""
    if argv_files:
        raw = [root / f if not Path(f).is_absolute() else Path(f) for f in argv_files]
    else:
        raw = _staged_added_files(root)
    out = []
    for p in raw:
        if p.suffix != ".py":
            continue
        if not p.is_file():
            # pre-commit framework passes already-committed paths; staged
            # files should exist. Fall back to skip silently.
            continue
        out.append(p)
    return out


def main(argv: list[str] | None = None) -> int:
    if _disabled():
        return 0
    args = list(argv if argv is not None else sys.argv[1:])
    root = _repo_root()
    missing: list[Path] = []
    for target in _candidates(root, args):
        if _is_test_path(target):
            continue
        if _has_sibling_test(target, root):
            continue
        try:
            rel = target.relative_to(root)
        except ValueError:
            rel = target
        missing.append(rel)
    for rel in missing:
        print(
            f"{WARN_LABEL} {rel}: new module without a matching "
            f"`test_{rel.stem}.py`/`{rel.stem}_test.py` — add tests before merging.",
            file=sys.stderr,
        )
    # Always exit 0: this is a warning, not a gate.
    return 0


if __name__ == "__main__":
    sys.exit(main())
