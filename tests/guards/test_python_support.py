"""Guard the runtime-support claim FR-007 rests on.

FR-007 binds identical results across "every version of the underlying language
runtime that the package declares itself to support", and is careful to add that
the declared set is what makes the requirement dischargeable rather than
open-ended. `requires-python` is deliberately left unbounded (plan.md, Technical
Context), so the declared set only stays honest if something notices when the CI
matrix falls behind it.

The check keys off the interpreter the suite is running on rather than a
hard-coded list of Python releases: that needs no network and no periodic
maintenance, and it fires on the first run under a Python the matrix does not
cover, which is the moment the claim would otherwise start being untrue.
"""

import re
import sys
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

_LOWER_BOUND = re.compile(r">=\s*(\d+)\.(\d+)")
_MATRIX_VERSIONS = re.compile(r"python-version:\s*\[([^\]]*)\]")
_VERSION = re.compile(r"(\d+)\.(\d+)")


def _declared_floor() -> tuple[int, int]:
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    requires_python = pyproject["project"]["requires-python"]
    match = _LOWER_BOUND.search(requires_python)
    assert match is not None, f"no lower bound in requires-python: {requires_python!r}"
    return int(match.group(1)), int(match.group(2))


def _matrix_versions() -> set[tuple[int, int]]:
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yaml").read_text(encoding="utf-8")
    match = _MATRIX_VERSIONS.search(workflow)
    assert match is not None, "no python-version matrix in .github/workflows/ci.yaml"
    versions = {(int(major), int(minor)) for major, minor in _VERSION.findall(match.group(1))}
    assert versions, "the python-version matrix is empty"
    return versions


def test_the_matrix_covers_every_python_from_the_declared_floor_to_the_one_in_use():
    floor = _declared_floor()
    running = sys.version_info[:2]
    if running[0] != floor[0] or running < floor:
        pytest.skip(f"running on {running}, which is outside the declared floor {floor}")

    expected = {(floor[0], minor) for minor in range(floor[1], running[1] + 1)}
    missing = sorted(expected - _matrix_versions())
    assert not missing, (
        "requires-python declares support for "
        + ", ".join(f"{major}.{minor}" for major, minor in missing)
        + " but .github/workflows/ci.yaml does not verify it. Either add the version to "
        "the matrix or narrow requires-python; FR-007 binds every version in the "
        "declared set."
    )


def test_the_matrix_verifies_no_python_the_package_declares_unsupported():
    floor = _declared_floor()
    stray = sorted(version for version in _matrix_versions() if version < floor)
    assert not stray, (
        "the CI matrix verifies "
        + ", ".join(f"{major}.{minor}" for major, minor in stray)
        + " but requires-python refuses to install there"
    )
