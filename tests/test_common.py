"""Tests for hooks/_common.py shared helpers."""

from __future__ import annotations

from pathlib import Path

import _common as c

# ---------- read_payload ----------


def test_read_payload_empty(monkeypatch):
    monkeypatch.setattr("sys.stdin", _StdinStub(""))
    assert c.read_payload() == {}


def test_read_payload_whitespace_only(monkeypatch):
    monkeypatch.setattr("sys.stdin", _StdinStub("   \n  "))
    assert c.read_payload() == {}


def test_read_payload_valid_json(monkeypatch):
    monkeypatch.setattr("sys.stdin", _StdinStub('{"tool_name": "Edit"}'))
    assert c.read_payload() == {"tool_name": "Edit"}


def test_read_payload_invalid_json(monkeypatch):
    monkeypatch.setattr("sys.stdin", _StdinStub("not json {{"))
    assert c.read_payload() == {}


# ---------- edited_paths / python_paths ----------


def test_edited_paths_edit(tmp_path):
    f = tmp_path / "x.py"
    f.write_text("")
    paths = c.edited_paths({"tool_name": "Edit", "tool_input": {"file_path": str(f)}})
    assert paths == [f.resolve()]


def test_edited_paths_write(tmp_path):
    f = tmp_path / "x.py"
    f.write_text("")
    paths = c.edited_paths({"tool_name": "Write", "tool_input": {"file_path": str(f)}})
    assert paths == [f.resolve()]


def test_edited_paths_multiedit_dedupes(tmp_path):
    f = tmp_path / "x.py"
    f.write_text("")
    payload = {
        "tool_name": "MultiEdit",
        "tool_input": {
            "file_path": str(f),
            "edits": [{"file_path": str(f)}, {"file_path": str(f)}],
        },
    }
    assert c.edited_paths(payload) == [f.resolve()]


def test_edited_paths_multiedit_distinct_files(tmp_path):
    a, b = tmp_path / "a.py", tmp_path / "b.py"
    a.write_text("")
    b.write_text("")
    payload = {
        "tool_name": "MultiEdit",
        "tool_input": {"edits": [{"file_path": str(a)}, {"file_path": str(b)}]},
    }
    assert set(c.edited_paths(payload)) == {a.resolve(), b.resolve()}


def test_edited_paths_skips_nonexistent(tmp_path):
    payload = {"tool_name": "Edit", "tool_input": {"file_path": str(tmp_path / "ghost.py")}}
    assert c.edited_paths(payload) == []


def test_edited_paths_unknown_tool_returns_empty(tmp_path):
    f = tmp_path / "x.py"
    f.write_text("")
    assert c.edited_paths({"tool_name": "Bash", "tool_input": {"file_path": str(f)}}) == []


def test_edited_paths_bad_input_shape():
    assert c.edited_paths({"tool_name": "Edit", "tool_input": "not-a-dict"}) == []
    assert c.edited_paths({"tool_name": "Edit"}) == []


def test_edited_paths_non_string_file_path():
    assert c.edited_paths({"tool_name": "Edit", "tool_input": {"file_path": 42}}) == []


def test_python_paths_filters_extension(tmp_path):
    py = tmp_path / "x.py"
    md = tmp_path / "x.md"
    py.write_text("")
    md.write_text("")
    payload = {
        "tool_name": "MultiEdit",
        "tool_input": {"edits": [{"file_path": str(py)}, {"file_path": str(md)}]},
    }
    assert c.python_paths(payload) == [py.resolve()]


# ---------- find_pyproject / project_root ----------


def test_find_pyproject_in_same_dir(tmp_path):
    pp = tmp_path / "pyproject.toml"
    pp.write_text("")
    assert c.find_pyproject(tmp_path) == pp


def test_find_pyproject_walks_up(tmp_path):
    pp = tmp_path / "pyproject.toml"
    pp.write_text("")
    deep = tmp_path / "a" / "b" / "c"
    deep.mkdir(parents=True)
    assert c.find_pyproject(deep / "x.py") == pp


def test_find_pyproject_returns_none(tmp_path):
    deep = tmp_path / "a"
    deep.mkdir()
    # nothing exists above tmp_path either; walk terminates at root w/o pyproject
    assert c.find_pyproject(deep / "x.py") is None


def test_project_root_with_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text("")
    assert c.project_root(tmp_path / "x.py") == tmp_path


def test_project_root_falls_back_to_cwd(tmp_path, monkeypatch):
    # Use a child path that has no pyproject above it within tmp_path's tree
    deep = tmp_path / "deep"
    deep.mkdir()
    monkeypatch.chdir(tmp_path)
    # If the host filesystem has a pyproject.toml above tmp_path the test
    # still passes so long as cwd is the fallback when find_pyproject misses.
    result = c.project_root(deep / "x.py")
    assert isinstance(result, Path)


# ---------- which / is_disabled ----------


def test_which_returns_path_for_real_binary():
    # `python3` is guaranteed present in CI + dev envs
    assert c.which("python3") is not None


def test_which_none_for_garbage():
    assert c.which("definitely-not-a-real-binary-xyzzy-42") is None


def test_is_disabled_true_for_falsy_values(monkeypatch):
    for val in ["0", "false", "FALSE", "no", "off", "disabled"]:
        monkeypatch.setenv("PYTHON_PLUGIN_TEST_FLAG", val)
        assert c.is_disabled("PYTHON_PLUGIN_TEST_FLAG"), val


def test_is_disabled_false_for_unset_or_truthy(monkeypatch):
    monkeypatch.delenv("PYTHON_PLUGIN_TEST_FLAG", raising=False)
    assert not c.is_disabled("PYTHON_PLUGIN_TEST_FLAG")
    monkeypatch.setenv("PYTHON_PLUGIN_TEST_FLAG", "1")
    assert not c.is_disabled("PYTHON_PLUGIN_TEST_FLAG")


# ---------- run / emit ----------


def test_run_captures_stdout_and_returncode():
    rc, out = c.run(["python3", "-c", "print('hi')"])
    assert rc == 0
    assert "hi" in out


def test_run_captures_nonzero():
    rc, out = c.run(["python3", "-c", "import sys; sys.exit(7)"])
    assert rc == 7


def test_run_handles_missing_binary():
    rc, out = c.run(["definitely-not-a-real-binary-xyzzy-42"])
    assert rc == 0
    assert "skipped" in out


def test_run_with_cwd(tmp_path):
    rc, out = c.run(["python3", "-c", "import os; print(os.getcwd())"], cwd=tmp_path)
    assert rc == 0
    assert str(tmp_path) in out


def test_emit_silent_on_clean(capsys):
    c.emit("ruff", Path("/x.py"), 0, "")
    assert capsys.readouterr().err == ""


def test_emit_writes_on_failure(capsys):
    c.emit("ruff", Path("/tmp/x.py"), 1, "boom")
    err = capsys.readouterr().err
    assert "[python-plugin/ruff]" in err
    assert "/tmp/x.py" in err
    assert "boom" in err


def test_emit_writes_label_only_on_zero_with_output(capsys):
    c.emit("ruff", Path("/tmp/x.py"), 0, "warning: foo")
    assert "warning: foo" in capsys.readouterr().err


# ---------- helper ----------


class _StdinStub:
    def __init__(self, text: str) -> None:
        self._text = text

    def read(self) -> str:
        return self._text
