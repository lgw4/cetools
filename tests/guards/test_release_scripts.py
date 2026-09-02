"""Guard the two release scripts against
specs/005-release-publishing/contracts/release-scripts.md.

Both scripts are pure `/usr/bin/env sh` with no bashisms, invoked here via
`subprocess.run(["sh", ...])` against fixture files written into `tmp_path`,
following the missing-`uv` skip pattern already used in
`tests/guards/test_packaging.py`.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(shutil.which("sh") is None, reason="no sh on PATH")

REPO_ROOT = Path(__file__).resolve().parents[2]
CHANGELOG_SCRIPT = REPO_ROOT / "scripts" / "changelog-section.sh"
PREFLIGHT_SCRIPT = REPO_ROOT / "scripts" / "release-preflight.sh"


def _run(script: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["sh", str(script), *args],
        capture_output=True,
        text=True,
        env=env,
    )


def _write_changelog(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "CHANGELOG.md"
    path.write_text(text, encoding="utf-8")
    return path


# --- scripts/changelog-section.sh -------------------------------------------


def test_extractor_reproduces_a_section_that_runs_to_end_of_file(tmp_path):
    changelog = _write_changelog(
        tmp_path,
        "# Changelog\n\n## 2026.08.1 (unreleased)\n\nFirst line.\nSecond line.\n",
    )
    result = _run(CHANGELOG_SCRIPT, "2026.08.1", str(changelog))
    assert result.returncode == 0
    assert result.stdout == "First line.\nSecond line.\n"


def test_extractor_stops_at_the_next_heading(tmp_path):
    changelog = _write_changelog(
        tmp_path,
        "# Changelog\n\n"
        "## 2026.08.2 (unreleased)\n\nNewer entry.\n\n"
        "## 2026.08.1\n\n2026-08-01 body.\n",
    )
    result = _run(CHANGELOG_SCRIPT, "2026.08.2", str(changelog))
    assert result.returncode == 0
    assert result.stdout == "Newer entry.\n"


def test_extractor_reports_and_exits_1_when_the_section_is_absent(tmp_path):
    changelog = _write_changelog(tmp_path, "# Changelog\n\n## 2026.08.1\n\nBody.\n")
    result = _run(CHANGELOG_SCRIPT, "9999.99.9", str(changelog))
    assert result.returncode == 1
    assert result.stdout == ""
    assert "9999.99.9" in result.stderr
    assert str(changelog) in result.stderr


def test_extractor_finds_an_unreleased_heading(tmp_path):
    changelog = _write_changelog(tmp_path, "## 2026.08.1 (unreleased)\n\nBody.\n")
    result = _run(CHANGELOG_SCRIPT, "2026.08.1", str(changelog))
    assert result.returncode == 0
    assert result.stdout == "Body.\n"


def test_extractor_finds_a_dated_heading(tmp_path):
    changelog = _write_changelog(tmp_path, "## 2026.08.1 2026-08-31\n\nBody.\n")
    result = _run(CHANGELOG_SCRIPT, "2026.08.1", str(changelog))
    assert result.returncode == 0
    assert result.stdout == "Body.\n"


def test_extractor_preserves_subsection_headings(tmp_path):
    changelog = _write_changelog(
        tmp_path,
        "## 2026.08.1 (unreleased)\n\n### Added\n\n- A thing.\n",
    )
    result = _run(CHANGELOG_SCRIPT, "2026.08.1", str(changelog))
    assert result.returncode == 0
    assert result.stdout == "### Added\n\n- A thing.\n"


def test_extractor_trims_leading_and_trailing_blanks_but_not_interior_ones(tmp_path):
    changelog = _write_changelog(
        tmp_path,
        "## 2026.08.1 (unreleased)\n\n\nFirst.\n\nSecond.\n\n\n## 2026.08.0\n\nOlder.\n",
    )
    result = _run(CHANGELOG_SCRIPT, "2026.08.1", str(changelog))
    assert result.returncode == 0
    assert result.stdout == "First.\n\nSecond.\n"


def test_extractor_does_not_select_a_heading_it_is_a_prefix_of(tmp_path):
    changelog = _write_changelog(
        tmp_path,
        "## 2026.08.10 (unreleased)\n\nWrong section.\n\n## 2026.08.1\n\nRight section.\n",
    )
    result = _run(CHANGELOG_SCRIPT, "2026.08.1", str(changelog))
    assert result.returncode == 0
    assert result.stdout == "Right section.\n"


def test_extractor_usage_error_on_wrong_argument_count(tmp_path):
    changelog = _write_changelog(tmp_path, "## 2026.08.1\n\nBody.\n")
    result = _run(CHANGELOG_SCRIPT, "2026.08.1", str(changelog), "extra")
    assert result.returncode == 2
    assert result.stdout == ""


def test_extractor_usage_error_on_missing_changelog(tmp_path):
    result = _run(CHANGELOG_SCRIPT, "2026.08.1", str(tmp_path / "nope.md"))
    assert result.returncode == 2


# --- scripts/release-preflight.sh -------------------------------------------


def _write_pyproject(tmp_path: Path, version: str) -> Path:
    path = tmp_path / "pyproject.toml"
    path.write_text(
        "[tool.other]\n"
        'version = "9999.99.9"\n\n'
        "[project]\n"
        'name = "cetools"\n'
        f'version = "{version}"\n',
        encoding="utf-8",
    )
    return path


def _no_release_env(tmp_path: Path) -> dict:
    fake_gh = tmp_path / "fake-gh-not-found.sh"
    fake_gh.write_text("#!/usr/bin/env sh\necho 'release not found' >&2\nexit 1\n")
    fake_gh.chmod(0o755)
    return {**_base_env(), "RELEASE_PREFLIGHT_GH_RELEASE_VIEW": f"sh {fake_gh}"}


def _already_published_env(tmp_path: Path) -> dict:
    fake_gh = tmp_path / "fake-gh-found.sh"
    fake_gh.write_text("#!/usr/bin/env sh\necho '{}'\nexit 0\n")
    fake_gh.chmod(0o755)
    return {**_base_env(), "RELEASE_PREFLIGHT_GH_RELEASE_VIEW": f"sh {fake_gh}"}


def _unobtainable_env(tmp_path: Path) -> dict:
    fake_gh = tmp_path / "fake-gh-unobtainable.sh"
    fake_gh.write_text("#!/usr/bin/env sh\necho 'error connecting to github.com' >&2\nexit 1\n")
    fake_gh.chmod(0o755)
    return {**_base_env(), "RELEASE_PREFLIGHT_GH_RELEASE_VIEW": f"sh {fake_gh}"}


def _base_env() -> dict:
    import os

    return dict(os.environ)


def test_preflight_passes_a_well_formed_tag_over_a_dated_section(tmp_path):
    pyproject = _write_pyproject(tmp_path, "2026.08.1")
    changelog = _write_changelog(tmp_path, "## 2026.08.1 2026-08-31\n\nBody.\n")
    result = _run(
        PREFLIGHT_SCRIPT,
        "v2026.08.1",
        str(pyproject),
        str(changelog),
        env=_no_release_env(tmp_path),
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


def test_preflight_fails_when_the_tag_disagrees_with_the_declared_version(tmp_path):
    pyproject = _write_pyproject(tmp_path, "2026.08.1")
    changelog = _write_changelog(tmp_path, "## 2026.08.1 2026-08-31\n\nBody.\n")
    result = _run(
        PREFLIGHT_SCRIPT,
        "v2026.08.2",
        str(pyproject),
        str(changelog),
        env=_no_release_env(tmp_path),
    )
    assert result.returncode == 1
    assert "v2026.08.2" in result.stderr
    assert "2026.08.1" in result.stderr


@pytest.mark.parametrize(
    "tag", ["2026.08.1", "vv2026.08.1", "v2026.8.1", "v2026.13.1", "release-2026.08.1"]
)
def test_preflight_rejects_every_malformed_tag_shape(tmp_path, tag):
    pyproject = _write_pyproject(tmp_path, "2026.08.1")
    changelog = _write_changelog(tmp_path, "## 2026.08.1 2026-08-31\n\nBody.\n")
    result = _run(
        PREFLIGHT_SCRIPT, tag, str(pyproject), str(changelog), env=_no_release_env(tmp_path)
    )
    assert result.returncode == 1, (tag, result.stdout, result.stderr)


def test_preflight_fails_when_the_changelog_has_no_section(tmp_path):
    pyproject = _write_pyproject(tmp_path, "2026.08.1")
    changelog = _write_changelog(tmp_path, "## 2026.08.0\n\nOlder.\n")
    result = _run(
        PREFLIGHT_SCRIPT,
        "v2026.08.1",
        str(pyproject),
        str(changelog),
        env=_no_release_env(tmp_path),
    )
    assert result.returncode == 1


def test_preflight_fails_when_the_section_is_marked_unreleased(tmp_path):
    pyproject = _write_pyproject(tmp_path, "2026.08.1")
    changelog = _write_changelog(tmp_path, "## 2026.08.1 (unreleased)\n\nBody.\n")
    result = _run(
        PREFLIGHT_SCRIPT,
        "v2026.08.1",
        str(pyproject),
        str(changelog),
        env=_no_release_env(tmp_path),
    )
    assert result.returncode == 1
    assert "unreleased" in result.stderr


def test_preflight_passes_check_4_when_the_section_is_dated(tmp_path):
    pyproject = _write_pyproject(tmp_path, "2026.08.1")
    changelog = _write_changelog(tmp_path, "## 2026.08.1 2026-08-31\n\nBody.\n")
    result = _run(
        PREFLIGHT_SCRIPT,
        "v2026.08.1",
        str(pyproject),
        str(changelog),
        env=_no_release_env(tmp_path),
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("missing", ["pyproject", "changelog"])
def test_preflight_usage_error_on_a_missing_file(tmp_path, missing):
    pyproject = _write_pyproject(tmp_path, "2026.08.1")
    changelog = _write_changelog(tmp_path, "## 2026.08.1 2026-08-31\n\nBody.\n")
    pyproject_arg = str(tmp_path / "nope.toml") if missing == "pyproject" else str(pyproject)
    changelog_arg = str(tmp_path / "nope.md") if missing == "changelog" else str(changelog)
    result = _run(
        PREFLIGHT_SCRIPT,
        "v2026.08.1",
        pyproject_arg,
        changelog_arg,
        env=_no_release_env(tmp_path),
    )
    assert result.returncode == 2


def test_preflight_reads_project_version_over_a_same_named_tool_table_key(tmp_path):
    pyproject = _write_pyproject(tmp_path, "2026.08.1")
    assert '[tool.other]\nversion = "9999.99.9"' in pyproject.read_text()
    changelog = _write_changelog(tmp_path, "## 2026.08.1 2026-08-31\n\nBody.\n")
    result = _run(
        PREFLIGHT_SCRIPT,
        "v2026.08.1",
        str(pyproject),
        str(changelog),
        env=_no_release_env(tmp_path),
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "heading",
    [
        "## 2026.08.1 2026-08-31\n\n## 2026.08.0\n\nOlder.\n",
        "## 2026.08.1 2026-08-31\n\n\n\n",
    ],
)
def test_preflight_fails_when_the_dated_section_is_empty(tmp_path, heading):
    pyproject = _write_pyproject(tmp_path, "2026.08.1")
    changelog = _write_changelog(tmp_path, heading)
    result = _run(
        PREFLIGHT_SCRIPT,
        "v2026.08.1",
        str(pyproject),
        str(changelog),
        env=_no_release_env(tmp_path),
    )
    assert result.returncode == 1
    assert "empty" in result.stderr


def test_preflight_check_6_aborts_when_a_release_already_exists(tmp_path):
    pyproject = _write_pyproject(tmp_path, "2026.08.1")
    changelog = _write_changelog(tmp_path, "## 2026.08.1 2026-08-31\n\nBody.\n")
    result = _run(
        PREFLIGHT_SCRIPT,
        "v2026.08.1",
        str(pyproject),
        str(changelog),
        env=_already_published_env(tmp_path),
    )
    assert result.returncode == 1
    assert "2026.08.1" in result.stderr


def test_preflight_check_6_fails_closed_when_the_answer_is_unobtainable(tmp_path):
    pyproject = _write_pyproject(tmp_path, "2026.08.1")
    changelog = _write_changelog(tmp_path, "## 2026.08.1 2026-08-31\n\nBody.\n")
    result = _run(
        PREFLIGHT_SCRIPT,
        "v2026.08.1",
        str(pyproject),
        str(changelog),
        env=_unobtainable_env(tmp_path),
    )
    assert result.returncode == 1
