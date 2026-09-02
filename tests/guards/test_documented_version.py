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
# JSON block, are the two places the *reported* (normalized) version reaches
# documented output. The declared (padded) group is extended in
# 005-release-publishing to cover the install command's tag segment.
_REPORTED_PATTERNS = (re.compile(r"\(cetools ([^)]+)\)"), re.compile(r'"version": "([^"]+)"'))
_DECLARED_PATTERNS: tuple[re.Pattern[str], ...] = ()


def _documented_outputs() -> list[Path]:
    paths = [_ROOT / "README.md"]
    paths.extend(sorted(_ROOT.glob("specs/*/quickstart.md")))
    paths.extend(sorted(_ROOT.glob("specs/*/contracts/*.md")))
    return [path for path in paths if path.is_file()]


def _matches(text: str, patterns: tuple[re.Pattern[str], ...]) -> set[str]:
    return {match for pattern in patterns for match in pattern.findall(text)}


@pytest.mark.parametrize("path", _documented_outputs(), ids=lambda path: path.name)
def test_documented_versions_match_the_reported_version(path):
    text = path.read_text(encoding="utf-8")
    found = _matches(text, _REPORTED_PATTERNS)
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
        for match in _matches(path.read_text(encoding="utf-8"), _REPORTED_PATTERNS)
    }
    assert documented == {package_version()}


# --- the constitution's two Development Workflow clauses ---------------------
#
# Neither was checkable. `version` could be changed from `2026.08.1` to
# `2026.8.1`, to `1.2.3`, or to `2026.13.1` with all 628 tests passing,
# because PEP 440 normalizes the padded and unpadded forms to one string and
# the drift guard above compares the *normalized* values — so nothing asserted
# the declared string carries the `YYYY.0M.INC1` shape the constitution fixes,
# which is the very distinction the rendered output had to reconcile. And the
# changelog heading could be renamed to anything at all, so a release cut
# without its entry shipped silently against the requirement that every
# release ship one.

_CALVER = re.compile(r"^(20\d\d)\.(0[1-9]|1[0-2])\.([1-9]\d*)$")


def _declared_version() -> str:
    import tomllib

    return tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"][
        "version"
    ]


def test_the_declared_version_carries_the_constitutions_calver_shape():
    declared = _declared_version()
    assert _CALVER.match(declared), (
        f"pyproject.toml declares version {declared!r}, which is not the "
        "constitution's YYYY.0M.INC1 CalVer form"
    )


@pytest.mark.parametrize("bad", ["2026.8.1", "1.2.3", "2026.13.1", "2026.08.0", "2026.08"])
def test_the_calver_shape_check_rejects_the_forms_it_must(bad):
    """The rule this guard runs on, stated as cases: an unpadded month, a
    semantic version, a thirteenth month, a zero increment, and a version with
    no increment at all. Without these the pattern could be loosened to
    something that accepts everything and still report success.
    """
    assert not _CALVER.match(bad)


def test_the_declared_version_normalizes_to_the_version_the_tool_reports():
    # The two halves have to be pinned together, or the shape check above and
    # the drift guard could pass while naming different releases.
    from importlib.metadata import version as _installed

    assert _installed("cetools") == package_version()
    padded, unpadded = _declared_version(), package_version()
    assert padded.replace(".0", ".", 1) == unpadded or padded == unpadded


def test_the_changelog_carries_an_entry_for_the_declared_version():
    # The constitution: "every release ships a changelog entry". Renaming the
    # heading to `## 9999.99.9 (unreleased)` left the suite green, so a
    # release could be cut with its entry missing or misnumbered.
    declared = _declared_version()
    headings = re.findall(
        r"^## (\S+)", (_ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), re.MULTILINE
    )
    assert (
        declared in headings
    ), f"CHANGELOG.md has no `## {declared}` heading; its headings are {headings}"


# --- T206: the changelog's own section-structure rule ------------------------
#
# T190 found eight entries that stated FR-056b's consequence — "changes every
# character a seed produces from this version forward" — in their own prose
# while sitting under `### Fixed` with only an inline marker or none at all,
# and moved them up to `### Breaking changes`, where the project's own stated
# rule (CHANGELOG.md's own preamble) says a breaking change belongs. T190's
# third clause, "add a guard so it stops drifting," was not done; this is
# that guard. FR-056b is the requirement that states a seed's output is a
# promise only within one package version — a bullet that cites it is
# claiming exactly the consequence `### Breaking changes` exists to hold, so
# one filed anywhere else is the same drift recurring.

_VERSION_HEADING = re.compile(r"^## \S.*$", re.MULTILINE)
_SUBSECTION_HEADING = re.compile(r"^### (.+)$", re.MULTILINE)


def _misplaced_fr056b_citations(text: str) -> list[str]:
    """Every `### <heading>` section, across every `## <version>` section,
    other than `### Breaking changes`, that cites FR-056b — each described
    by a short label for the assertion message.
    """
    misplaced = []
    version_starts = [m.start() for m in _VERSION_HEADING.finditer(text)] or [0]
    version_bounds = list(zip(version_starts, version_starts[1:] + [len(text)]))
    for start, end in version_bounds:
        version_text = text[start:end]
        version_heading = version_text.splitlines()[0].strip()
        subsection_matches = list(_SUBSECTION_HEADING.finditer(version_text))
        bounds = [m.end() for m in subsection_matches] + [len(version_text)]
        for match, section_end in zip(subsection_matches, bounds[1:]):
            name = match.group(1).strip()
            if name == "Breaking changes":
                continue
            body = version_text[match.end() : section_end]
            if "FR-056b" in body:
                misplaced.append(f"{version_heading} / ### {name}")
    return misplaced


def test_no_changelog_entry_citing_fr056b_sits_outside_breaking_changes():
    text = (_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    misplaced = _misplaced_fr056b_citations(text)
    assert not misplaced, (
        "these sections cite FR-056b — the seed's-output-is-a-version-scoped-"
        f"promise requirement — outside ### Breaking changes: {misplaced}"
    )


def test_the_fr056b_placement_check_can_fail():
    # Planted rather than read from the real file, so this case stands
    # before any drift exists to catch, the way the licensing guards' own
    # planted-file cases do.
    planted = (
        "## 9999.99.9 (unreleased)\n\n"
        "### Fixed\n\n"
        "- **A regression fixed.** Reorders a draw, which changes every "
        "character a seed produces from this version forward (FR-056b, "
        "T999).\n\n"
        "### Breaking changes\n\n"
        "- **An unrelated breaking change.** Also cites FR-056b, correctly, "
        "since this is the heading it belongs under.\n"
    )
    misplaced = _misplaced_fr056b_citations(planted)
    assert misplaced == ["## 9999.99.9 (unreleased) / ### Fixed"]
