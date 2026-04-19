"""Tests for hooks/pre-commit-new-file-tests.py."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent.parent / "hooks" / "pre-commit-new-file-tests.py"


def _load():
    spec = importlib.util.spec_from_file_location("_nft", HOOK)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.email", "x@y"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "t"], check=True)
    return tmp_path


def _stage(repo: Path, name: str, body: str = "") -> Path:
    p = repo / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body)
    subprocess.run(["git", "-C", str(repo), "add", name], check=True)
    return p


def test_disabled_returns_zero(monkeypatch: pytest.MonkeyPatch):
    mod = _load()
    monkeypatch.setenv("PYTHON_PLUGIN_REQUIRE_TESTS", "0")
    assert mod.main([]) == 0


def test_new_file_without_test_warns(
    git_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    mod = _load()
    monkeypatch.chdir(git_repo)
    _stage(git_repo, "src/widget.py")
    assert mod.main([]) == 0
    err = capsys.readouterr().err
    assert "widget.py" in err
    assert "new module without a matching" in err


def test_new_file_with_sibling_test_passes_silent(
    git_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    mod = _load()
    monkeypatch.chdir(git_repo)
    _stage(git_repo, "src/widget.py")
    _stage(git_repo, "tests/test_widget.py", "def test_ok(): pass\n")
    assert mod.main([]) == 0
    assert capsys.readouterr().err == ""


def test_argv_filenames_preferred_over_staged(
    git_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    """pre-commit framework passes filenames as argv — they override `git diff --cached`."""
    mod = _load()
    monkeypatch.chdir(git_repo)
    # Create + stage a file that *does* have a sibling test.
    _stage(git_repo, "src/ok.py")
    _stage(git_repo, "tests/test_ok.py", "def test_ok(): pass\n")
    # Also create a file without a test and pass it on argv.
    orphan = _stage(git_repo, "src/orphan.py")
    assert mod.main([str(orphan)]) == 0
    err = capsys.readouterr().err
    assert "orphan.py" in err
    assert "ok.py" not in err


def test_excludes_test_files_themselves(
    git_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    mod = _load()
    monkeypatch.chdir(git_repo)
    # A test file is staged — no warning even without a sibling test.
    t = _stage(git_repo, "tests/test_only_me.py", "def test_ok(): pass\n")
    assert mod.main([str(t)]) == 0
    assert capsys.replayfile if False else capsys.readouterr().err == ""


def test_ignores_non_python_files(
    git_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    mod = _load()
    monkeypatch.chdir(git_repo)
    _stage(git_repo, "docs/readme.md", "# hi")
    assert mod.main([]) == 0
    assert capsys.readouterr().err == ""


def test_outside_git_repo_does_not_crash(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """When `git rev-parse` fails the hook still exits 0 silently."""
    mod = _load()
    monkeypatch.chdir(tmp_path)
    assert mod.main([]) == 0


def test_argv_files_skipped_if_missing(
    git_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    mod = _load()
    monkeypatch.chdir(git_repo)
    assert mod.main(["does/not/exist.py"]) == 0
    assert capsys.readouterr().err == ""


def test_ignored_when_under_tests_dir(
    git_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    """Any path containing a tests/ segment is treated as a test module."""
    mod = _load()
    monkeypatch.chdir(git_repo)
    t = _stage(git_repo, "tests/helpers/util.py")  # no test_ prefix but under tests/
    assert mod.main([str(t)]) == 0
    assert capsys.readouterr().err == ""
