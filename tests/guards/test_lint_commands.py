"""The lint commands CONTRIBUTING.md's Style and tooling section documents
must actually run clean at the scope it documents (T140).

At repository scope, `flake8` reports thousands of errors out of
`.venv/lib/`, and `black --check` finds six vendored Spec Kit scripts under
`.specify/` that would be reformatted; neither tool nor `isort` is configured
to exclude those trees. Every convergence note from Phase 9 onward has
silently meant `src tests` when it claimed the tree lints clean, so this
guard derives the commands from CONTRIBUTING.md rather than restating them,
and pins that narrowed scope to what it actually is.

Run with `--check`/`--check-only` rather than the literal commands the doc
shows: this guard verifies the scope is clean, it does not rewrite files as
a side effect of running the test suite.
"""

import re
import shutil
import subprocess
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]

_FENCE = re.compile(r"## Style and tooling\n.*?```sh\n(.*?)```", re.DOTALL)

# Each tool's flag for reporting without rewriting files.
_CHECK_ONLY_FLAG = {"black": "--check", "isort": "--check-only", "flake8": None}


def _documented_lint_commands() -> list[str]:
    text = (_ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    match = _FENCE.search(text)
    assert match, "CONTRIBUTING.md no longer documents the lint commands the same way"
    return [line.strip() for line in match.group(1).splitlines() if line.strip()]


def test_the_documented_lint_commands_have_something_to_check():
    """A pattern that matched nothing would make every case below vacuous."""
    commands = _documented_lint_commands()
    assert {c.split()[2] for c in commands} == {"black", "isort", "flake8"}


@pytest.mark.parametrize("command", _documented_lint_commands())
def test_a_documented_lint_command_reports_clean(command):
    if shutil.which("uv") is None:
        pytest.skip("uv is not on PATH, so the documented commands cannot be run here")
    parts = command.split()
    assert parts[:2] == ["uv", "run"], parts
    tool, scope = parts[2], parts[3:]
    flag = _CHECK_ONLY_FLAG[tool]
    args = ["uv", "run", tool, *([flag] if flag else []), *scope]
    result = subprocess.run(args, cwd=_ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
