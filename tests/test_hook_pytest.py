"""Tests for hooks/posttooluse-pytest.py."""

from __future__ import annotations

import os
import sys

import pytest

# Make hook helpers importable for unit-level tests.
HOOK_NAME = "posttooluse-pytest"


def _env(extra: dict[str, str] | None = None) -> dict[str, str]:
    e = os.environ.copy()
    if extra:
        e.update(extra)
    return e


def test_pytest_empty_stdin(hook_runner):
    rc, _, err = hook_runner("posttooluse-pytest.py", {})
    assert rc == 0
    assert err == ""


def test_pytest_disabled(hook_runner, project_dir, write_payload):
    f = project_dir / "x.py"
    f.write_text("x = 1\n")
    rc, _, err = hook_runner(
        "posttooluse-pytest.py",
        write_payload(f),
        env=_env({"PYTHON_PLUGIN_PYTEST": "0"}),
    )
    assert rc == 0
    assert err == ""


def test_pytest_skips_unknown_tool(hook_runner):
    rc, _, err = hook_runner("posttooluse-pytest.py", {"tool_name": "Bash", "tool_input": {}})
    assert rc == 0


def test_pytest_no_tool_available(hook_runner, project_dir, write_payload):
    f = project_dir / "x.py"
    f.write_text("x = 1\n")
    rc, _, err = hook_runner(
        "posttooluse-pytest.py",
        write_payload(f),
        env=_env({"PATH": "/nonexistent"}),
    )
    assert rc == 0
    assert err == ""


# ---------- unit-level: helpers via direct import ----------


# Reload required because conftest already inserted the hooks dir on sys.path.
def _import_hook():
    sys.path.insert(0, str(__import__("conftest").HOOKS_DIR))
    import importlib

    return importlib.import_module("posttooluse-pytest".replace("-", "_"))


# Hook filename has a dash so we exercise it via direct path import:
import importlib.util
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parent.parent / "hooks"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), _HOOKS_DIR / f"{name}.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def hook_module():
    return _load("posttooluse-pytest")


def test_is_test_file_recognizes_test_prefix(hook_module):
    assert hook_module._is_test_file(Path("tests/test_x.py"))


def test_is_test_file_recognizes_test_suffix(hook_module):
    assert hook_module._is_test_file(Path("tests/x_test.py"))


def test_is_test_file_rejects_normal_module(hook_module):
    assert not hook_module._is_test_file(Path("src/x.py"))


def test_find_related_tests_finds_companion(hook_module, tmp_path):
    src = tmp_path / "src" / "foo.py"
    src.parent.mkdir()
    src.write_text("")
    tests = tmp_path / "tests"
    tests.mkdir()
    test_file = tests / "test_foo.py"
    test_file.write_text("")
    found = hook_module._find_related_tests(src, tmp_path)
    assert test_file in found


def test_find_related_tests_returns_self_for_test_file(hook_module, tmp_path):
    test_file = tmp_path / "tests" / "test_foo.py"
    test_file.parent.mkdir()
    test_file.write_text("")
    assert hook_module._find_related_tests(test_file, tmp_path) == [test_file]


def test_find_related_tests_returns_empty_when_no_match(hook_module, tmp_path):
    src = tmp_path / "src" / "lonely.py"
    src.parent.mkdir()
    src.write_text("")
    (tmp_path / "tests").mkdir()
    assert hook_module._find_related_tests(src, tmp_path) == []
