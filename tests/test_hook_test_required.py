"""Tests for hooks/posttooluse-test-required.py."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).resolve().parent.parent / "hooks"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), _HOOKS_DIR / f"{name}.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def hook_module():
    return _load("posttooluse-test-required")


def _env(extra: dict[str, str] | None = None) -> dict[str, str]:
    e = os.environ.copy()
    if extra:
        e.update(extra)
    return e


# ---------- subprocess-level ----------


def test_empty_stdin(hook_runner):
    rc, _, err = hook_runner("posttooluse-test-required.py", {})
    assert rc == 0
    assert err == ""


def test_disabled(hook_runner, project_dir, write_payload):
    f = project_dir / "src" / "lonely.py"
    f.write_text("")
    rc, _, err = hook_runner(
        "posttooluse-test-required.py",
        write_payload(f),
        env=_env({"PYTHON_PLUGIN_REQUIRE_TESTS": "0"}),
    )
    assert rc == 0
    assert err == ""


def test_warns_for_new_module_without_test(hook_runner, project_dir, write_payload):
    f = project_dir / "src" / "lonely.py"
    f.write_text("")
    rc, _, err = hook_runner("posttooluse-test-required.py", write_payload(f))
    assert rc == 0
    assert "test-required" in err
    assert "lonely.py" in err


def test_silent_when_sibling_test_exists(hook_runner, project_dir, write_payload):
    f = project_dir / "src" / "good.py"
    f.write_text("")
    test = project_dir / "tests" / "test_good.py"
    test.write_text("")
    rc, _, err = hook_runner("posttooluse-test-required.py", write_payload(f))
    assert rc == 0
    assert err == ""


def test_silent_for_test_file_itself(hook_runner, project_dir, write_payload):
    f = project_dir / "tests" / "test_x.py"
    f.write_text("")
    rc, _, err = hook_runner("posttooluse-test-required.py", write_payload(f))
    assert rc == 0
    assert err == ""


def test_only_fires_on_write_not_edit(hook_runner, project_dir, edit_payload):
    f = project_dir / "src" / "lonely.py"
    f.write_text("")
    rc, _, err = hook_runner("posttooluse-test-required.py", edit_payload(f))
    assert rc == 0
    assert err == ""  # Edit means file already existed; only Write is checked


# ---------- unit-level ----------


def test_is_test_path_by_filename(hook_module):
    assert hook_module._is_test_path(Path("anywhere/test_x.py"))
    assert hook_module._is_test_path(Path("anywhere/x_test.py"))


def test_is_test_path_by_directory(hook_module):
    assert hook_module._is_test_path(Path("/p/tests/sub/x.py"))
    assert hook_module._is_test_path(Path("/p/test/x.py"))


def test_is_test_path_negative(hook_module):
    assert not hook_module._is_test_path(Path("/p/src/foo.py"))


def test_has_sibling_test_finds_test_prefix(hook_module, tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_foo.py").write_text("")
    assert hook_module._has_sibling_test(Path("src/foo.py"), tmp_path)


def test_has_sibling_test_finds_underscore_suffix(hook_module, tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "foo_test.py").write_text("")
    assert hook_module._has_sibling_test(Path("src/foo.py"), tmp_path)


def test_has_sibling_test_negative(hook_module, tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    assert not hook_module._has_sibling_test(Path("src/foo.py"), tmp_path)
