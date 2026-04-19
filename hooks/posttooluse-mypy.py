#!/usr/bin/env python3
"""Run mypy on any .py the agent just edited.

Uses the project's mypy config (nearest pyproject.toml). Best-effort: skips
silently if mypy isn't installed in the project venv. Disable per-shell with
`PYTHON_PLUGIN_MYPY=0`.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import emit, is_disabled, project_root, python_paths, read_payload, run, which


def _mypy_cmd(cwd: Path) -> list[str] | None:
    """Prefer venv-local mypy so it sees project deps + stubs; fallback to uvx."""
    venv = cwd / ".venv" / "bin" / "mypy"
    if venv.is_file():
        return [str(venv)]
    if which("mypy"):
        return ["mypy"]
    if which("uvx"):
        return ["uvx", "mypy"]
    return None


def main() -> int:
    if is_disabled("PYTHON_PLUGIN_MYPY"):
        return 0
    payload = read_payload()
    for target in python_paths(payload):
        cwd = project_root(target)
        cmd = _mypy_cmd(cwd)
        if cmd is None:
            return 0
        rel = str(target.relative_to(cwd)) if cwd in target.parents else str(target)
        code, out = run([*cmd, rel], cwd=cwd, timeout=60)
        emit("mypy", target, code, out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
