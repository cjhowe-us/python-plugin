"""In-process hook tests — exercise each hook's `main()` directly so coverage
is attributed (subprocess-spawned hooks otherwise show 0%).

Each test patches stdin / argv / env / cwd so the hook runs deterministically.
"""

from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path
from typing import Any

import pytest

_HOOKS_DIR = Path(__file__).resolve().parent.parent / "hooks"


def _load(name: str):
    """Import a hook module by its kebab-case filename."""
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), _HOOKS_DIR / f"{name}.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _patch_stdin(monkeypatch: pytest.MonkeyPatch, payload: dict[str, Any]) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))


# ---------- ruff hook ----------


def test_ruff_main_no_payload(monkeypatch):
    mod = _load("posttooluse-ruff")
    _patch_stdin(monkeypatch, {})
    assert mod.main() == 0


def test_ruff_main_disabled_flag(monkeypatch, project_dir):
    mod = _load("posttooluse-ruff")
    f = project_dir / "src" / "x.py"
    f.write_text("x = 1\n")
    _patch_stdin(monkeypatch, {"tool_name": "Edit", "tool_input": {"file_path": str(f)}})
    monkeypatch.setenv("PYTHON_PLUGIN_RUFF", "0")
    assert mod.main() == 0


def test_ruff_main_no_tools(monkeypatch, project_dir):
    mod = _load("posttooluse-ruff")
    f = project_dir / "src" / "x.py"
    f.write_text("x = 1\n")
    _patch_stdin(monkeypatch, {"tool_name": "Edit", "tool_input": {"file_path": str(f)}})
    monkeypatch.setenv("PATH", "/nonexistent")
    assert mod.main() == 0


def test_ruff_main_runs_against_real_file(monkeypatch, project_dir, capsys):
    mod = _load("posttooluse-ruff")
    f = project_dir / "src" / "bad.py"
    f.write_text("import os\n")  # F401
    _patch_stdin(monkeypatch, {"tool_name": "Edit", "tool_input": {"file_path": str(f)}})
    rc = mod.main()
    assert rc == 0
    err = capsys.readouterr().err
    # ruff present in dev/CI venv; if absent the hook silently no-ops
    if err:
        assert "ruff/check" in err


# ---------- mypy hook ----------


def test_mypy_main_no_payload(monkeypatch):
    mod = _load("posttooluse-mypy")
    _patch_stdin(monkeypatch, {})
    assert mod.main() == 0


def test_mypy_main_disabled(monkeypatch, project_dir):
    mod = _load("posttooluse-mypy")
    f = project_dir / "x.py"
    f.write_text("")
    _patch_stdin(monkeypatch, {"tool_name": "Edit", "tool_input": {"file_path": str(f)}})
    monkeypatch.setenv("PYTHON_PLUGIN_MYPY", "0")
    assert mod.main() == 0


def test_mypy_main_no_tool(monkeypatch, project_dir):
    mod = _load("posttooluse-mypy")
    f = project_dir / "x.py"
    f.write_text("")
    _patch_stdin(monkeypatch, {"tool_name": "Edit", "tool_input": {"file_path": str(f)}})
    monkeypatch.setenv("PATH", "/nonexistent")
    assert mod.main() == 0


def test_mypy_main_real_file(monkeypatch, project_dir):
    mod = _load("posttooluse-mypy")
    f = project_dir / "src" / "x.py"
    f.write_text("from __future__ import annotations\nx: int = 1\n")
    _patch_stdin(monkeypatch, {"tool_name": "Edit", "tool_input": {"file_path": str(f)}})
    assert mod.main() == 0


def test_mypy_cmd_uses_venv_when_present(monkeypatch, project_dir):
    mod = _load("posttooluse-mypy")
    venv_bin = project_dir / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    fake = venv_bin / "mypy"
    fake.write_text("#!/bin/sh\nexit 0\n")
    fake.chmod(0o755)
    cmd = mod._mypy_cmd(project_dir)
    assert cmd == [str(fake)]


def test_mypy_cmd_returns_none_when_nothing_available(monkeypatch, project_dir):
    mod = _load("posttooluse-mypy")
    monkeypatch.setenv("PATH", "/nonexistent")
    assert mod._mypy_cmd(project_dir) is None


# ---------- pytest hook ----------


def test_pytest_main_no_payload(monkeypatch):
    mod = _load("posttooluse-pytest")
    _patch_stdin(monkeypatch, {})
    assert mod.main() == 0


def test_pytest_main_disabled(monkeypatch, project_dir):
    mod = _load("posttooluse-pytest")
    f = project_dir / "x.py"
    f.write_text("")
    _patch_stdin(monkeypatch, {"tool_name": "Edit", "tool_input": {"file_path": str(f)}})
    monkeypatch.setenv("PYTHON_PLUGIN_PYTEST", "0")
    assert mod.main() == 0


def test_pytest_main_no_tool(monkeypatch, project_dir):
    mod = _load("posttooluse-pytest")
    f = project_dir / "x.py"
    f.write_text("")
    _patch_stdin(monkeypatch, {"tool_name": "Edit", "tool_input": {"file_path": str(f)}})
    monkeypatch.setenv("PATH", "/nonexistent")
    assert mod.main() == 0


def test_pytest_main_runs_related_test(monkeypatch, project_dir):
    mod = _load("posttooluse-pytest")
    src = project_dir / "src" / "feature.py"
    src.parent.mkdir(exist_ok=True)
    src.write_text("def add(a, b):\n    return a + b\n")
    test = project_dir / "tests" / "test_feature.py"
    test.write_text("def test_passes():\n    assert True\n")
    _patch_stdin(monkeypatch, {"tool_name": "Edit", "tool_input": {"file_path": str(src)}})
    rc = mod.main()
    assert rc == 0


def test_pytest_main_falls_back_to_lf(monkeypatch, project_dir):
    mod = _load("posttooluse-pytest")
    src = project_dir / "src" / "lonely.py"
    src.parent.mkdir(exist_ok=True)
    src.write_text("")
    _patch_stdin(monkeypatch, {"tool_name": "Edit", "tool_input": {"file_path": str(src)}})
    rc = mod.main()
    assert rc == 0


def test_pytest_cmd_returns_none_without_tools(monkeypatch, project_dir):
    mod = _load("posttooluse-pytest")
    monkeypatch.setenv("PATH", "/nonexistent")
    assert mod._pytest_cmd(project_dir) is None


# ---------- test-required hook ----------


def test_required_main_no_payload(monkeypatch):
    mod = _load("posttooluse-test-required")
    _patch_stdin(monkeypatch, {})
    assert mod.main() == 0


def test_required_main_disabled(monkeypatch, project_dir, capsys):
    mod = _load("posttooluse-test-required")
    f = project_dir / "src" / "lonely.py"
    f.write_text("")
    _patch_stdin(monkeypatch, {"tool_name": "Write", "tool_input": {"file_path": str(f)}})
    monkeypatch.setenv("PYTHON_PLUGIN_REQUIRE_TESTS", "0")
    assert mod.main() == 0
    assert capsys.readouterr().err == ""


def test_required_main_warns(monkeypatch, project_dir, capsys):
    mod = _load("posttooluse-test-required")
    f = project_dir / "src" / "lonely.py"
    f.write_text("")
    _patch_stdin(monkeypatch, {"tool_name": "Write", "tool_input": {"file_path": str(f)}})
    assert mod.main() == 0
    assert "lonely.py" in capsys.readouterr().err


def test_required_main_silent_with_test(monkeypatch, project_dir, capsys):
    mod = _load("posttooluse-test-required")
    f = project_dir / "src" / "good.py"
    f.write_text("")
    (project_dir / "tests" / "test_good.py").write_text("")
    _patch_stdin(monkeypatch, {"tool_name": "Write", "tool_input": {"file_path": str(f)}})
    assert mod.main() == 0
    assert capsys.readouterr().err == ""


def test_required_main_skips_edit(monkeypatch, project_dir, capsys):
    mod = _load("posttooluse-test-required")
    f = project_dir / "src" / "lonely.py"
    f.write_text("")
    _patch_stdin(monkeypatch, {"tool_name": "Edit", "tool_input": {"file_path": str(f)}})
    assert mod.main() == 0
    assert capsys.readouterr().err == ""


def test_required_main_skips_test_file(monkeypatch, project_dir, capsys):
    mod = _load("posttooluse-test-required")
    f = project_dir / "tests" / "test_x.py"
    f.write_text("")
    _patch_stdin(monkeypatch, {"tool_name": "Write", "tool_input": {"file_path": str(f)}})
    assert mod.main() == 0
    assert capsys.readouterr().err == ""


# ---------- uv-lock hook ----------


def test_uvlock_main_no_payload(monkeypatch):
    mod = _load("posttooluse-uv-lock")
    _patch_stdin(monkeypatch, {})
    assert mod.main() == 0


def test_uvlock_main_disabled(monkeypatch, project_dir):
    mod = _load("posttooluse-uv-lock")
    pp = project_dir / "pyproject.toml"
    _patch_stdin(monkeypatch, {"tool_name": "Edit", "tool_input": {"file_path": str(pp)}})
    monkeypatch.setenv("PYTHON_PLUGIN_UV_LOCK", "0")
    assert mod.main() == 0


def test_uvlock_main_no_uv(monkeypatch, project_dir):
    mod = _load("posttooluse-uv-lock")
    pp = project_dir / "pyproject.toml"
    _patch_stdin(monkeypatch, {"tool_name": "Edit", "tool_input": {"file_path": str(pp)}})
    monkeypatch.setenv("PATH", "/nonexistent")
    assert mod.main() == 0


def test_uvlock_main_skips_non_pyproject(monkeypatch, project_dir):
    mod = _load("posttooluse-uv-lock")
    f = project_dir / "src.py"
    f.write_text("")
    _patch_stdin(monkeypatch, {"tool_name": "Edit", "tool_input": {"file_path": str(f)}})
    assert mod.main() == 0


def test_uvlock_main_runs_against_pyproject(monkeypatch, project_dir):
    mod = _load("posttooluse-uv-lock")
    pp = project_dir / "pyproject.toml"
    pp.write_text('[project]\nname = "x"\nversion = "0.0.0"\nrequires-python = ">=3.11"\n')
    _patch_stdin(monkeypatch, {"tool_name": "Edit", "tool_input": {"file_path": str(pp)}})
    assert mod.main() == 0
