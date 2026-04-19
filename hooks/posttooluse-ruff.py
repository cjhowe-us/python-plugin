#!/usr/bin/env python3
"""Run ruff check + format on any .py the agent just edited.

Best-effort: if neither `ruff` nor `uvx` is on PATH the hook returns 0 silently.
Disable per-shell with `PYTHON_PLUGIN_RUFF=0`.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import emit, is_disabled, project_root, python_paths, read_payload, run, which


def _ruff_cmd() -> list[str] | None:
    if which("ruff"):
        return ["ruff"]
    if which("uvx"):
        return ["uvx", "ruff"]
    return None


def main() -> int:
    if is_disabled("PYTHON_PLUGIN_RUFF"):
        return 0
    base = _ruff_cmd()
    if base is None:
        return 0
    payload = read_payload()
    for target in python_paths(payload):
        cwd = project_root(target)
        rel = str(target.relative_to(cwd)) if cwd in target.parents else str(target)
        code, out = run([*base, "check", rel], cwd=cwd, timeout=30)
        emit("ruff/check", target, code, out)
        code, out = run([*base, "format", "--check", rel], cwd=cwd, timeout=30)
        emit("ruff/format", target, code, out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
