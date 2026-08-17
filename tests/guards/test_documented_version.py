"""Every package version written into a documented output must be the one
the tool actually reports.

`pyproject.toml` declares the constitution's CalVer form, `2026.08.1`, but
PEP 440 normalizes a zero-padded month away, so `importlib.metadata` and
therefore every rendered result carry `2026.8.1`. Documenting the declared
form leaves a reader comparing what they ran against a string the tool never
prints. This guard pins the documented outputs to the reported value, and so
fails on the release that changes it (FR-033a).

Only documented *outputs* are scanned: the README and, per feature, the
quickstart and the contracts. Prose that discusses a version, such as a
`tasks.md` entry or a changelog heading, is deliberately out of scope.
"""

import re
from pathlib import Path

import pytest

from cetools.provenance import package_version

_ROOT = Path(__file__).resolve().parents[2]

# `Rules: packaged (cetools X)` in a text block, and `"version": "X"` in a
# JSON block, are the two places a version reaches documented output.
_PATTERNS = (re.compile(r"\(cetools ([^)]+)\)"), re.compile(r'"version": "([^"]+)"'))


def _documented_outputs() -> list[Path]:
    paths = [_ROOT / "README.md"]
    paths.extend(sorted(_ROOT.glob("specs/*/quickstart.md")))
    paths.extend(sorted(_ROOT.glob("specs/*/contracts/*.md")))
    return [path for path in paths if path.is_file()]


@pytest.mark.parametrize("path", _documented_outputs(), ids=lambda path: path.name)
def test_documented_versions_match_the_reported_version(path):
    text = path.read_text(encoding="utf-8")
    found = {match for pattern in _PATTERNS for match in pattern.findall(text)}
    stale = sorted(version for version in found if version != package_version())
    assert not stale, (
        f"{path.relative_to(_ROOT)} documents {stale}, "
        f"but the tool reports {package_version()!r}"
    )


def test_the_guard_has_something_to_check():
    """A glob that matched nothing would pass silently."""
    documented = {
        match
        for path in _documented_outputs()
        for pattern in _PATTERNS
        for match in pattern.findall(path.read_text(encoding="utf-8"))
    }
    assert documented == {package_version()}
