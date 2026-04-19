"""Shared fixtures for python-plugin tests.

Hooks live in `hooks/` (a flat directory of scripts, not a package).
Importing them under test requires putting that directory on sys.path so
`from _common import ...` resolves.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOKS_DIR = REPO / "hooks"

if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))


def run_hook(
    name: str, payload: dict[str, Any], env: dict[str, str] | None = None
) -> tuple[int, str, str]:
    """Spawn a hook script with payload on stdin; return (rc, stdout, stderr)."""
    proc = subprocess.run(
        [sys.executable, str(HOOKS_DIR / name)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


@pytest.fixture
def hook_runner():
    return run_hook


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """An empty project rooted at tmp_path with a pyproject.toml."""
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\nversion = "0"\n')
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    return tmp_path


@pytest.fixture
def write_payload():
    """Build a Write tool payload for a given file_path."""

    def _make(file_path: Path | str) -> dict[str, Any]:
        return {"tool_name": "Write", "tool_input": {"file_path": str(file_path)}}

    return _make


@pytest.fixture
def edit_payload():
    def _make(file_path: Path | str) -> dict[str, Any]:
        return {"tool_name": "Edit", "tool_input": {"file_path": str(file_path)}}

    return _make
