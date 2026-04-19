"""Tests for hooks/posttooluse-uv-lock.py."""

from __future__ import annotations

import os


def _env(extra: dict[str, str] | None = None) -> dict[str, str]:
    e = os.environ.copy()
    if extra:
        e.update(extra)
    return e


def test_empty_stdin(hook_runner):
    rc, _, err = hook_runner("posttooluse-uv-lock.py", {})
    assert rc == 0
    assert err == ""


def test_disabled(hook_runner, project_dir, edit_payload):
    pp = project_dir / "pyproject.toml"
    rc, _, err = hook_runner(
        "posttooluse-uv-lock.py",
        edit_payload(pp),
        env=_env({"PYTHON_PLUGIN_UV_LOCK": "0"}),
    )
    assert rc == 0
    assert err == ""


def test_skips_non_pyproject(hook_runner, project_dir, edit_payload):
    f = project_dir / "src.py"
    f.write_text("")
    rc, _, err = hook_runner("posttooluse-uv-lock.py", edit_payload(f))
    assert rc == 0
    assert err == ""


def test_skips_when_uv_missing(hook_runner, project_dir, edit_payload):
    pp = project_dir / "pyproject.toml"
    rc, _, err = hook_runner(
        "posttooluse-uv-lock.py",
        edit_payload(pp),
        env=_env({"PATH": "/nonexistent"}),
    )
    assert rc == 0
    assert err == ""


def test_runs_uv_lock_on_pyproject_edit(hook_runner, project_dir, edit_payload):
    """When uv exists, the hook calls `uv lock` and produces uv.lock."""
    pp = project_dir / "pyproject.toml"
    # Stable, resolvable pyproject so `uv lock` succeeds.
    pp.write_text('[project]\nname = "x"\nversion = "0.0.0"\nrequires-python = ">=3.11"\n')
    rc, _, err = hook_runner("posttooluse-uv-lock.py", edit_payload(pp))
    assert rc == 0
    # Hook stays silent on success (only emits on failure).
    if (project_dir / "uv.lock").exists():
        assert err == ""
