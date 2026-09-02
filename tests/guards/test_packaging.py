"""Guard the packaging promise SC-012 makes about the built artifacts.

`uv sync` installs this project editable, so `importlib.resources` resolves to
the working tree and every other test would stay green if the wheel target
stopped shipping `data/tasks.toml`. This module is the one place that inspects
what a build actually produces.

The constitution's bundling clause is written against *every* distribution, so
both the wheel and the sdist are inspected here: the sdist has its own
`include` list in `pyproject.toml` and can lose a license without the wheel
noticing.
"""

import re
import shutil
import subprocess
import tarfile
import zipfile
from pathlib import Path

import pytest

from tests.conftest import DESIGNATION, GPL_DESIGNATION, _uncovered, _wrongly_covered

REPO_ROOT = Path(__file__).resolve().parents[2]

# Decoded once, rather than written contiguously below: this module ships in
# the sdist, and the two designation constants are already split for exactly
# this reason.
_OGC_MARKER = DESIGNATION.decode()
_GPL_MARKER = GPL_DESIGNATION.decode()


def _build(tmp_path_factory, flag: str, suffix: str) -> Path:
    if shutil.which("uv") is None:
        pytest.skip("uv is not on PATH, so the distribution cannot be built here")
    out_dir = tmp_path_factory.mktemp("dist")
    subprocess.run(
        ["uv", "build", flag, "--out-dir", str(out_dir)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    built = list(out_dir.glob(f"*{suffix}"))
    assert len(built) == 1, f"expected exactly one {suffix}, got {built}"
    return built[0]


@pytest.fixture(scope="module")
def wheel(tmp_path_factory) -> zipfile.ZipFile:
    return zipfile.ZipFile(_build(tmp_path_factory, "--wheel", ".whl"))


@pytest.fixture(scope="module")
def sdist(tmp_path_factory) -> tarfile.TarFile:
    return tarfile.open(_build(tmp_path_factory, "--sdist", ".tar.gz"))


def _assert_shipped_rules_data(text: str, where: str) -> None:
    """Assert the rules data as *shipped* satisfies SC-012, both halves.

    SC-012 binds the file "as read from the installed package". The
    designation half was already checked here; the Product Identity half
    lived only in a test reading through `importlib.resources`, which under
    an editable install resolves into the working tree and so verifies
    nothing about a distribution.

    Widened to an exactly-one-of-two check (FR-042a): 003-npc-generator's
    name tables carry the GPL-3.0 designation instead of the OGC one, and a
    file carrying both, or neither, is a labeling error the check must catch
    rather than pass on the strength of the one designation it used to look
    for.
    """
    has_ogc = _OGC_MARKER in text
    has_gpl = _GPL_MARKER in text
    assert has_ogc or has_gpl, f"{where} carries neither the OGC nor the GPL designation"
    assert not (has_ogc and has_gpl), f"{where} carries both the OGC and GPL designations"
    assert "Cepheus Engine" not in text, f"{where} carries a Product Identity string"
    assert "Samardan Press" not in text, f"{where} carries a Product Identity string"


def _wheel_data_files(wheel: zipfile.ZipFile) -> list[str]:
    return sorted(
        name
        for name in wheel.namelist()
        if name.startswith("cetools/data/") and name.endswith(".toml")
    )


def _path_set_difference(expected: set[str], actual: set[str]) -> str | None:
    """None if the two sets are equal; otherwise a message naming exactly
    which paths differ, in both directions, rather than a bare set
    inequality.
    """
    missing = expected - actual
    extra = actual - expected
    if not missing and not extra:
        return None
    return f"missing: {sorted(missing)}, unexpected: {sorted(extra)}"


def test_the_set_difference_helper_reports_a_flattened_layout():
    """A synthetic flattened build: every basename present, every path
    different. FR-015's whole point is that a full-path comparison reports
    this rather than passing on basename equality (SC-010).
    """
    source = {"careers/scout.toml", "chargen/aging.toml"}
    flattened = {"scout.toml", "aging.toml"}
    diff = _path_set_difference(source, flattened)
    assert diff is not None
    assert "careers/scout.toml" in diff
    assert "chargen/aging.toml" in diff


def _source_data_paths(repo_root: Path) -> set[str]:
    base = repo_root / "src" / "cetools"
    return {p.relative_to(base).as_posix() for p in (base / "data").rglob("*.toml")}


def test_wheel_contains_every_packaged_data_file(wheel, repo_root):
    source_paths = _source_data_paths(repo_root)
    wheel_paths = {name.removeprefix("cetools/") for name in _wheel_data_files(wheel)}
    diff = _path_set_difference(source_paths, wheel_paths)
    assert diff is None, diff


def test_every_data_file_in_the_wheel_carries_its_ogc_designation(wheel):
    data_files = _wheel_data_files(wheel)
    assert data_files
    for name in data_files:
        _assert_shipped_rules_data(wheel.read(name).decode("utf-8"), f"the wheel's {name}")


def test_the_data_set_read_from_the_wheel_validates_without_a_problem(wheel, tmp_path):
    from cetools.rules import validate_rules

    for name in _wheel_data_files(wheel):
        basename = name.rsplit("/", 1)[-1]
        (tmp_path / basename).write_bytes(wheel.read(name))
    report = validate_rules(tmp_path)
    assert report.valid, report.problems


def test_the_notice_covers_every_open_game_content_file_in_the_wheel(
    wheel, game_data_covered_paths, game_data_covered_suffix
):
    # SC-016 requires the coverage obligation to be derived from what is
    # actually shipped, and SC-014 binds the built artifacts rather than the
    # working tree, so the two belong together here.
    #
    # Every member, and keyed on the designation rather than on the `.toml`
    # extension: filtering by extension left an Open Game Content file that is
    # not a `.toml` covered by no check at all. No path translation either —
    # the notice now names `cetools/data/` alongside `src/cetools/data/`,
    # because a wheel holds no `src/` and the fabricated `f"src/{name}"`
    # prefix this check used to build was papering over that.
    designated = sorted(name for name in wheel.namelist() if DESIGNATION in wheel.read(name))
    assert designated, "the wheel carries no Open Game Content file to derive coverage from"
    uncovered = _uncovered(designated, game_data_covered_paths, game_data_covered_suffix)
    assert not uncovered, (
        f"the wheel ships {uncovered} as Open Game Content, outside the paths the game-data "
        f"notice names: {list(game_data_covered_paths)}"
    )


def test_the_notice_does_not_wrongly_cover_a_gpl_file_in_the_wheel(
    wheel, game_data_covered_paths, game_data_covered_suffix
):
    # The mirror of the OGC coverage check above (T167): a name table that
    # drifted into an OGC subtree would still be a `.toml` under a covered
    # path — `test_wheel_contains_every_packaged_data_file` and the
    # basename-uniqueness guard would both pass it — so this is the one
    # check that would catch it shipping under a notice its own
    # GPL-3.0 designation contradicts.
    designated = sorted(name for name in wheel.namelist() if GPL_DESIGNATION in wheel.read(name))
    assert designated, "the wheel carries no GPL-3.0-designated file to check"
    wrongly_covered = _wrongly_covered(
        designated, game_data_covered_paths, game_data_covered_suffix
    )
    assert not wrongly_covered, (
        f"the wheel ships {wrongly_covered} as GPL-3.0 content under a path the OGC "
        f"game-data notice names: {list(game_data_covered_paths)}"
    )


def _license_in_wheel(wheel: zipfile.ZipFile, name: str) -> str:
    matches = [n for n in wheel.namelist() if n.endswith(f".dist-info/licenses/{name}")]
    assert matches, f"{name} is missing from the wheel"
    return wheel.read(matches[0]).decode("utf-8")


def test_wheel_carries_the_source_code_license(wheel):
    assert _license_in_wheel(wheel, "LICENSE").strip()


def test_wheel_carries_the_ogl_text_with_its_section_15_chain(wheel, assert_section_15_chain):
    text = _license_in_wheel(wheel, "LICENSE-OGL.txt")
    assert "OPEN GAME LICENSE Version 1.0a" in text
    assert_section_15_chain(text, "the wheel's LICENSE-OGL.txt")


def _read_from_sdist(sdist: tarfile.TarFile, relative: str) -> str:
    # Every member sits under a single `{name}-{version}/` prefix directory.
    matches = [n for n in sdist.getnames() if n.split("/", 1)[-1] == relative]
    assert matches, f"{relative} is missing from the sdist"
    handle = sdist.extractfile(matches[0])
    assert handle is not None
    return handle.read().decode("utf-8")


def _sdist_data_files(sdist: tarfile.TarFile) -> list[str]:
    return sorted(
        name.split("/", 1)[-1]
        for name in sdist.getnames()
        if name.split("/", 1)[-1].startswith("src/cetools/data/")
        and name.split("/", 1)[-1].endswith(".toml")
    )


def test_sdist_contains_every_packaged_data_file(sdist, repo_root):
    source_paths = _source_data_paths(repo_root)
    sdist_paths = {name.removeprefix("src/cetools/") for name in _sdist_data_files(sdist)}
    diff = _path_set_difference(source_paths, sdist_paths)
    assert diff is None, diff


def test_every_data_file_in_the_sdist_carries_its_ogc_designation(sdist):
    data_files = _sdist_data_files(sdist)
    assert data_files
    for relative in data_files:
        _assert_shipped_rules_data(_read_from_sdist(sdist, relative), f"the sdist's {relative}")


def test_the_data_set_read_from_the_sdist_validates_without_a_problem(sdist, tmp_path):
    from cetools.rules import validate_rules

    for relative in _sdist_data_files(sdist):
        basename = relative.rsplit("/", 1)[-1]
        # `newline=""`: the sdist's bytes are already whatever they are, and the
        # default translation rewrites every "\n" to os.linesep. On Windows a
        # file that already carried CRLF comes back out as "\r\r\n", which is
        # not valid TOML, so the guard would fail on the write rather than on
        # anything the sdist actually contains.
        (tmp_path / basename).write_text(
            _read_from_sdist(sdist, relative), encoding="utf-8", newline=""
        )
    report = validate_rules(tmp_path)
    assert report.valid, report.problems


def _sdist_bytes(sdist: tarfile.TarFile, name: str) -> bytes:
    handle = sdist.extractfile(name)
    return b"" if handle is None else handle.read()


def test_the_notice_covers_every_open_game_content_file_in_the_sdist(
    sdist, game_data_covered_paths, game_data_covered_suffix
):
    # The sdist's member paths, once the single `{name}-{version}/` prefix is
    # stripped, are exactly the source paths the notice names, so no
    # translation is needed here.
    #
    # Every member, keyed on the designation. Filtering on a `src/` prefix left
    # a designated file under `tests/` — which this sdist really does ship, per
    # the `include` list in pyproject.toml — covered by no check at all, and
    # filtering on the extension left a designated non-`.toml` uncovered too.
    designated = sorted(
        name.split("/", 1)[-1]
        for name in sdist.getnames()
        if DESIGNATION in _sdist_bytes(sdist, name)
    )
    assert designated, "the sdist carries no Open Game Content file to derive coverage from"
    uncovered = _uncovered(designated, game_data_covered_paths, game_data_covered_suffix)
    assert not uncovered, (
        f"the sdist ships {uncovered} as Open Game Content, outside the paths the game-data "
        f"notice names: {list(game_data_covered_paths)}"
    )


def test_the_notice_does_not_wrongly_cover_a_gpl_file_in_the_sdist(
    sdist, game_data_covered_paths, game_data_covered_suffix
):
    # The sdist counterpart of the wheel check above (T167).
    designated = sorted(
        name.split("/", 1)[-1]
        for name in sdist.getnames()
        if GPL_DESIGNATION in _sdist_bytes(sdist, name)
    )
    assert designated, "the sdist carries no GPL-3.0-designated file to check"
    wrongly_covered = _wrongly_covered(
        designated, game_data_covered_paths, game_data_covered_suffix
    )
    assert not wrongly_covered, (
        f"the sdist ships {wrongly_covered} as GPL-3.0 content under a path the OGC "
        f"game-data notice names: {list(game_data_covered_paths)}"
    )


def test_sdist_carries_the_source_code_license(sdist):
    assert _read_from_sdist(sdist, "LICENSE").strip()


def test_sdist_ships_no_file_outside_its_own_include_list(sdist):
    # Neither `"README.md"` nor `"CHANGELOG.md"` in pyproject.toml's sdist
    # `include` list carried a leading slash, and hatchling treats a
    # slash-free pattern as matching at any depth, so both also picked up
    # `.specify/extensions/git/README.md` — a vendored Spec Kit file that is
    # neither this project's code nor its rules data, and that the include
    # list does not name (T138).
    members = {name.split("/", 1)[-1] for name in sdist.getnames()}
    assert not any(name.startswith(".specify") for name in members), members


def test_sdist_carries_the_ogl_text_with_its_section_15_chain(sdist, assert_section_15_chain):
    text = _read_from_sdist(sdist, "LICENSE-OGL.txt")
    assert "OPEN GAME LICENSE Version 1.0a" in text
    assert_section_15_chain(text, "the sdist's LICENSE-OGL.txt")


# --- 005-release-publishing: the py.typed marker and descriptive metadata --


def test_wheel_contains_the_py_typed_marker(wheel):
    assert "cetools/py.typed" in wheel.namelist()


def test_sdist_contains_the_py_typed_marker(sdist):
    matches = [n for n in sdist.getnames() if n.split("/", 1)[-1] == "src/cetools/py.typed"]
    assert matches, "src/cetools/py.typed is missing from the sdist"


def _wheel_metadata(wheel: zipfile.ZipFile) -> str:
    matches = [n for n in wheel.namelist() if n.endswith(".dist-info/METADATA")]
    assert len(matches) == 1, matches
    return wheel.read(matches[0]).decode("utf-8")


def _assert_descriptive_metadata(text: str, where: str) -> None:
    assert re.search(r"^Keywords: \S", text, re.MULTILINE), f"{where} carries no Keywords line"
    assert re.search(r"^Classifier: ", text, re.MULTILINE), f"{where} carries no Classifier line"
    for name in ("Homepage", "Repository", "Changelog", "Issues"):
        assert re.search(
            rf"^Project-URL: {name},", text, re.MULTILINE
        ), f"{where} carries no Project-URL entry for {name}"
    assert not re.search(
        r"^Classifier: License ::", text, re.MULTILINE
    ), f"{where} carries a redundant License :: classifier"

    keywords_line = re.search(r"^Keywords: (.*)$", text, re.MULTILINE)
    classifier_lines = re.findall(r"^Classifier: (.*)$", text, re.MULTILINE)
    for marker in ("Cepheus Engine", "Samardan Press"):
        assert marker not in keywords_line.group(1), f"{where} names {marker} in Keywords"
        assert not any(
            marker in line for line in classifier_lines
        ), f"{where} names {marker} in a Classifier"


def test_wheel_metadata_carries_the_descriptive_fields(wheel):
    _assert_descriptive_metadata(_wheel_metadata(wheel), "the wheel's METADATA")


def test_sdist_metadata_carries_the_descriptive_fields(sdist):
    _assert_descriptive_metadata(_read_from_sdist(sdist, "PKG-INFO"), "the sdist's PKG-INFO")
