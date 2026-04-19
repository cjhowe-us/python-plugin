"""Shared helpers for python-plugin PostToolUse hooks.

Hooks `from _common import ...` after inserting their own dir on sys.path.
Keeps each hook script small while avoiding copy-paste of payload parsing
and tool-discovery logic.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def read_payload() -> dict[str, Any]:
    """Parse the PostToolUse JSON payload from stdin. Empty -> {}."""
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        data: dict[str, Any] = json.loads(raw)
        return data
    except json.JSONDecodeError:
        return {}


def edited_paths(payload: dict[str, Any]) -> list[Path]:
    """Return absolute Paths the tool just wrote, filtered to existing files."""
    tool = payload.get("tool_name")
    raw = payload.get("tool_input")
    if not isinstance(raw, dict):
        return []
    out: list[str] = []
    if tool in {"Edit", "Write"}:
        p = raw.get("file_path")
        if isinstance(p, str):
            out.append(p)
    elif tool == "MultiEdit":
        p = raw.get("file_path")
        if isinstance(p, str):
            out.append(p)
        edits = raw.get("edits")
        if isinstance(edits, list):
            for e in edits:
                if isinstance(e, dict):
                    fp = e.get("file_path")
                    if isinstance(fp, str):
                        out.append(fp)
    paths = []
    seen: set[str] = set()
    for p in out:
        if p in seen:
            continue
        seen.add(p)
        path = Path(p)
        if path.is_file():
            paths.append(path.resolve())
    return paths


def python_paths(payload: dict[str, Any]) -> list[Path]:
    return [p for p in edited_paths(payload) if p.suffix == ".py"]


def find_pyproject(start: Path) -> Path | None:
    """Walk up from start to find the nearest pyproject.toml."""
    cur = start if start.is_dir() else start.parent
    for ancestor in [cur, *cur.parents]:
        cand = ancestor / "pyproject.toml"
        if cand.is_file():
            return cand
    return None


def project_root(path: Path) -> Path:
    """Project root for a path: nearest pyproject.toml's directory, else cwd."""
    pp = find_pyproject(path)
    return pp.parent if pp else Path.cwd()


def which(name: str) -> str | None:
    """Locate an executable, accepting `uvx <name>` if uvx is on PATH."""
    return shutil.which(name)


def run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    timeout: int = 60,
    input_text: str | None = None,
) -> tuple[int, str]:
    """Run cmd, capture combined output. Returns (rc, text). Never raises."""
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            input=input_text,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as e:
        return 0, f"  (skipped, exec failed: {e})"
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def emit(label: str, target: Path, code: int, out: str) -> None:
    """Write a human-readable hook report to stderr (only on failure/output)."""
    if code == 0 and not out:
        return
    print(f"[python-plugin/{label}] {target}:", file=sys.stderr)
    if out:
        print(out, file=sys.stderr)


def is_disabled(env_var: str) -> bool:
    """User-toggleable disable: env var set to a falsy value disables the hook."""
    val = os.environ.get(env_var, "").lower()
    return val in {"0", "false", "no", "off", "disabled"}
