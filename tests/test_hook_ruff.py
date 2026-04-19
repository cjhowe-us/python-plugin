"""Tests for hooks/posttooluse-ruff.py."""

from __future__ import annotations

import os


def _env(extra: dict[str, str] | None = None) -> dict[str, str]:
    e = os.environ.copy()
    if extra:
        e.update(extra)
    return e


def test_ruff_empty_stdin_returns_zero(hook_runner):
    rc, _, err = hook_runner("posttooluse-ruff.py", {})
    assert rc == 0
    assert err == ""


def test_ruff_disabled_flag(hook_runner, project_dir, write_payload):
    f = project_dir / "src" / "x.py"
    f.write_text("x = 1\n")
    rc, _, err = hook_runner(
        "posttooluse-ruff.py",
        write_payload(f),
        env=_env({"PYTHON_PLUGIN_RUFF": "0", "PATH": ""}),  # PATH wiped → no tools either
    )
    assert rc == 0
    assert err == ""


def test_ruff_skips_non_python_file(hook_runner, project_dir, edit_payload):
    f = project_dir / "x.md"
    f.write_text("hi")
    rc, _, err = hook_runner("posttooluse-ruff.py", edit_payload(f))
    assert rc == 0
    assert err == ""


def test_ruff_skips_unknown_tool(hook_runner, project_dir):
    payload = {"tool_name": "Bash", "tool_input": {"command": "ls"}}
    rc, _, err = hook_runner("posttooluse-ruff.py", payload)
    assert rc == 0
    assert err == ""


def test_ruff_no_tools_available_returns_zero(hook_runner, project_dir, write_payload):
    f = project_dir / "src" / "x.py"
    f.write_text("x = 1\n")
    rc, _, err = hook_runner(
        "posttooluse-ruff.py",
        write_payload(f),
        env=_env({"PATH": "/nonexistent"}),
    )
    assert rc == 0
    assert err == ""


def test_ruff_reports_violation(hook_runner, project_dir, edit_payload):
    """Trigger a real ruff failure: import without use."""
    f = project_dir / "src" / "bad.py"
    f.write_text("import os\n")  # F401: unused import
    rc, _, err = hook_runner("posttooluse-ruff.py", edit_payload(f))
    assert rc == 0  # hook never blocks; surfaces stderr only
    assert "ruff/check" in err
    assert "F401" in err
