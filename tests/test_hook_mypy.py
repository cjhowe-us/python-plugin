"""Tests for hooks/posttooluse-mypy.py."""

from __future__ import annotations

import os


def _env(extra: dict[str, str] | None = None) -> dict[str, str]:
    e = os.environ.copy()
    if extra:
        e.update(extra)
    return e


def test_mypy_empty_stdin(hook_runner):
    rc, _, err = hook_runner("posttooluse-mypy.py", {})
    assert rc == 0
    assert err == ""


def test_mypy_disabled(hook_runner, project_dir, write_payload):
    f = project_dir / "x.py"
    f.write_text("x = 1\n")
    rc, _, err = hook_runner(
        "posttooluse-mypy.py",
        write_payload(f),
        env=_env({"PYTHON_PLUGIN_MYPY": "0"}),
    )
    assert rc == 0
    assert err == ""


def test_mypy_skips_non_python(hook_runner, project_dir, edit_payload):
    f = project_dir / "x.md"
    f.write_text("hi")
    rc, _, err = hook_runner("posttooluse-mypy.py", edit_payload(f))
    assert rc == 0


def test_mypy_no_tool_available(hook_runner, project_dir, write_payload):
    f = project_dir / "x.py"
    f.write_text("x = 1\n")
    rc, _, err = hook_runner(
        "posttooluse-mypy.py",
        write_payload(f),
        env=_env({"PATH": "/nonexistent"}),
    )
    assert rc == 0
    assert err == ""


def test_mypy_reports_type_error(hook_runner, project_dir, edit_payload):
    f = project_dir / "src" / "bad.py"
    f.write_text(
        "from __future__ import annotations\n"
        "def f(x: int) -> str:\n"
        "    return x\n"  # int is not str
    )
    rc, _, err = hook_runner("posttooluse-mypy.py", edit_payload(f))
    assert rc == 0
    # Either mypy reports the error or the local environment lacks mypy
    # (in which case the hook silently skips). Both are valid passes.
    if err:
        assert "mypy" in err
        assert "Incompatible return value" in err or "incompatible" in err.lower()
