#!/usr/bin/env python3
"""Warn (don't block) when a new non-test .py is created without a sibling test.

Heuristic: PostToolUse with `Write` of a brand-new file under a directory
that isn't `tests/`, `test/`, or already a test module. Looks for a
`test_<stem>.py` or `<stem>_test.py` anywhere in the project; if none
exist, prints a warning to stderr.

Disable per-shell with `PYTHON_PLUGIN_REQUIRE_TESTS=0`.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import is_disabled, project_root, python_paths, read_payload


def _is_test_path(p: Path) -> bool:
    if p.name.startswith("test_") or p.name.endswith("_test.py"):
        return True
    parts = {part.lower() for part in p.parts}
    return bool(parts & {"tests", "test"})


def _has_sibling_test(target: Path, root: Path) -> bool:
    stem = target.stem
    needles = {f"test_{stem}.py", f"{stem}_test.py"}
    for name in needles:
        if list(root.rglob(name)):
            return True
    return False


def main() -> int:
    if is_disabled("PYTHON_PLUGIN_REQUIRE_TESTS"):
        return 0
    payload = read_payload()
    if payload.get("tool_name") != "Write":
        return 0
    for target in python_paths(payload):
        if _is_test_path(target):
            continue
        root = project_root(target)
        if _has_sibling_test(target, root):
            continue
        rel = target.relative_to(root) if root in target.parents else target
        print(
            f"[python-plugin/test-required] {rel}: new module without a test_*.py "
            f"sibling — add tests in tests/ before merging.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
