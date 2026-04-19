#!/usr/bin/env python3
"""Re-lock when pyproject.toml changes so uv.lock never drifts.

Triggers on Edit/Write to `pyproject.toml`. Runs `uv lock` (no upgrade) and
emits stderr only if the command fails. Disable per-shell with
`PYTHON_PLUGIN_UV_LOCK=0`.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import edited_paths, emit, is_disabled, read_payload, run, which


def main() -> int:
    if is_disabled("PYTHON_PLUGIN_UV_LOCK"):
        return 0
    if not which("uv"):
        return 0
    payload = read_payload()
    seen_roots: set[Path] = set()
    for target in edited_paths(payload):
        if target.name != "pyproject.toml":
            continue
        root = target.parent
        if root in seen_roots:
            continue
        seen_roots.add(root)
        code, out = run(["uv", "lock"], cwd=root, timeout=30)
        # Per docstring: only surface stderr when the lock command fails.
        emit("uv lock", target, code, out if code else "")
    return 0


if __name__ == "__main__":
    sys.exit(main())
