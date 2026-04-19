#!/usr/bin/env python3
"""Run pytest tests related to any .py the agent just edited.

Strategy:
- For an edited test file: run that file directly.
- For an edited source file: discover companion test by best-effort filename
  match (`test_<basename>.py` or `<basename>_test.py`) under any `tests/` dir
  in the project; if none, fall back to running pytest on the project's
  configured testpaths but constrained by `--lf` (last-failed) to keep it
  fast.

Disable per-shell with `PYTHON_PLUGIN_PYTEST=0`.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import emit, is_disabled, project_root, python_paths, read_payload, run, which


def _pytest_cmd(cwd: Path) -> list[str] | None:
    venv = cwd / ".venv" / "bin" / "pytest"
    if venv.is_file():
        return [str(venv)]
    if which("pytest"):
        return ["pytest"]
    if which("uvx"):
        return ["uvx", "--from", "pytest", "pytest"]
    return None


def _is_test_file(p: Path) -> bool:
    n = p.name
    return n.startswith("test_") or n.endswith("_test.py")


def _find_related_tests(target: Path, root: Path) -> list[Path]:
    if _is_test_file(target):
        return [target]
    stem = target.stem
    candidates = [f"test_{stem}.py", f"{stem}_test.py"]
    found: list[Path] = []
    for tests_dir in root.rglob("tests"):
        if not tests_dir.is_dir():
            continue
        for name in candidates:
            for hit in tests_dir.rglob(name):
                if hit.is_file():
                    found.append(hit)
    return found


def main() -> int:
    if is_disabled("PYTHON_PLUGIN_PYTEST"):
        return 0
    payload = read_payload()
    targets = python_paths(payload)
    if not targets:
        return 0
    # Group by project root so we run pytest at most once per project.
    by_root: dict[Path, list[Path]] = {}
    for t in targets:
        by_root.setdefault(project_root(t), []).append(t)

    for root, files in by_root.items():
        cmd = _pytest_cmd(root)
        if cmd is None:
            return 0
        related: list[Path] = []
        for f in files:
            related.extend(_find_related_tests(f, root))
        # Dedupe + relativize.
        seen: set[Path] = set()
        rel_args: list[str] = []
        for r in related:
            if r in seen:
                continue
            seen.add(r)
            rel_args.append(str(r.relative_to(root)) if root in r.parents else str(r))

        if rel_args:
            full = [*cmd, "-q", "--no-header", *rel_args]
            label = f"pytest ({len(rel_args)} file{'s' if len(rel_args) > 1 else ''})"
        else:
            full = [*cmd, "-q", "--no-header", "--lf"]
            label = "pytest (--lf, no related)"
        code, out = run(full, cwd=root, timeout=120)
        emit(label, files[0], code, out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
