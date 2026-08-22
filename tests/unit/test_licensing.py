import re
import tomllib
from pathlib import Path

import pytest

from tests.conftest import DESIGNATION, _uncovered

ATTRIBUTION = "Cepheus Engine and Samardan Press are the trademarks of Jason 'Flynn' Kemp"
NON_AFFILIATION_PHRASES = ("not affiliated", "no affiliation")
TRADEMARK = "Cepheus Engine"

# A compatibility claim says this software *works with* the named rules. A
# connective immediately before the trademark is what makes the difference:
# "an engine for Cepheus Engine" claims, "content derived from the Cepheus
# Engine SRD" does not.
_CLAIM_BEFORE = re.compile(
    r"\b(?:for|with|compatible with|compatibility with|works with|supports|"
    r"supporting|designed for|built for|targets|targeting)\s*$",
    re.IGNORECASE,
)
_CLAIM_AFTER = re.compile(r"^\s*-\s*(?:based|compatible|ready|native)\b", re.IGNORECASE)
# Rich draws the help screens inside a box and wraps inside it, so the borders
# have to go before the text can be read as prose. Spelled as an explicit
# codepoint range: written literally as `[─-╿|]` it reads like three separate
# characters including an ASCII hyphen, and a reviewer took it for one. It is
# the Box Drawing block (U+2500-U+257F) plus the pipe, and it must NOT touch
# U+002D, or the hyphen in "Cepheus Engine-based" would vanish and the claim
# would stop being detected. `test_normalizing_preserves_the_hyphen_a_claim_
# suffix_needs` pins that.
_BOX_DRAWING = re.compile(r"[\u2500-\u257F|]")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _normalized(text: str) -> str:
    return " ".join(_BOX_DRAWING.sub(" ", text).split())


def _claims_compatibility(text: str) -> bool:
    """Report whether `text` claims compatibility with the named rules.

    **The rule, decided deliberately (T087).** Naming a trademark is not
    claiming compatibility with it. The Compatibility-Statement License
    governs claims that this software *works with* the source rules; the OGL,
    separately, *requires* disclosing that content is derived from Open Game
    Content, and the constitution requires the Product Identity strings to be
    named in order to state where they may not appear. Demanding trademark
    attribution from every mention would therefore make the licensing
    documentation unwritable while catching nothing a claim-shaped test does
    not.

    So a claim is the trademark standing as the object of a connective that
    makes it the thing this software works with ("an engine for Cepheus
    Engine", "compatible with Cepheus Engine"), or carrying a hyphenated
    suffix that says the same thing ("Cepheus Engine-based"). Provenance
    wording ("derived from the Cepheus Engine SRD"), quoted mentions of the
    string itself, and the attribution text are mentions, not claims.
    """
    for match in re.finditer(re.escape(TRADEMARK), text):
        before = text[max(0, match.start() - 40) : match.start()]
        after = text[match.end() : match.end() + 16]
        if _CLAIM_BEFORE.search(before) or _CLAIM_AFTER.match(after):
            return True
    return False


def _assert_claim_carries_attribution(text: str, where: str) -> None:
    """Assert `text` either makes no compatibility claim or attributes it.

    The constitution's Compatibility-Statement clause and 001-dice-task-engine
    FR-035 allow either route; what they forbid is claiming compatibility
    without the attribution and the statement of non-affiliation.
    """
    if not _claims_compatibility(text):
        return
    assert ATTRIBUTION in text, f"{where} claims compatibility without the attribution"
    assert any(
        phrase in text.lower() for phrase in NON_AFFILIATION_PHRASES
    ), f"{where} claims compatibility without a statement of non-affiliation"


def test_license_exists_and_is_non_empty():
    license_path = _repo_root() / "LICENSE"
    assert license_path.is_file()
    assert license_path.read_text(encoding="utf-8").strip()


def test_license_ogl_exists_and_is_non_empty():
    ogl_path = _repo_root() / "LICENSE-OGL.txt"
    assert ogl_path.is_file()
    assert ogl_path.read_text(encoding="utf-8").strip()


def test_license_ogl_contains_title_and_section_15():
    text = (_repo_root() / "LICENSE-OGL.txt").read_text(encoding="utf-8")
    assert "OPEN GAME LICENSE Version 1.0a" in text
    assert "15." in text
    assert "Section 15" in text or "COPYRIGHT NOTICE" in text


def test_license_ogl_carries_the_whole_copyright_notice_chain(assert_section_15_chain):
    # The heading check above would pass with every notice under it deleted.
    # The constitution requires the chain verbatim and complete, extended with
    # this project's own game-data line, so each notice is asserted by name.
    text = (_repo_root() / "LICENSE-OGL.txt").read_text(encoding="utf-8")
    assert_section_15_chain(text, "LICENSE-OGL.txt")


def test_pyproject_lists_both_licenses_in_license_files():
    pyproject = tomllib.loads((_repo_root() / "pyproject.toml").read_text(encoding="utf-8"))
    license_files = pyproject["project"]["license-files"]
    assert "LICENSE" in license_files
    assert "LICENSE-OGL.txt" in license_files


def test_pyproject_declares_the_source_code_license_as_a_machine_readable_expression():
    # `license-files` ships the texts; it says nothing about which licence
    # governs the code, so PyPI and `pip show` reported the package as
    # unlicensed. The constitution states outright that source code is
    # GPL-3.0 and that the package must clearly designate what is GPL
    # code, and a licence a tool cannot read is not a designation a tool
    # can act on. `-only`, not `-or-later`: nothing in this repository
    # offers a later version.
    pyproject = tomllib.loads((_repo_root() / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["license"] == "GPL-3.0-only"


def test_readme_contains_ogc_gpl_designation():
    text = " ".join((_repo_root() / "README.md").read_text(encoding="utf-8").split())
    assert "Open Game Content" in text
    assert "Open Game License" in text
    assert "GNU General Public License" in text


def _package_description() -> str:
    pyproject = tomllib.loads((_repo_root() / "pyproject.toml").read_text(encoding="utf-8"))
    return pyproject["project"]["description"]


def _cli_help() -> str:
    from typer.testing import CliRunner

    from cetools.cli import app

    runner = CliRunner()
    # Every command's help, not a hand-kept subset: a new subcommand's help is
    # a new claim surface, and `validate` shipped without reaching this guard.
    screens = (["--help"], ["roll", "--help"], ["check", "--help"], ["validate", "--help"])
    return "\n".join(runner.invoke(app, args).stdout for args in screens)


# 001-dice-task-engine FR-035 binds "any text this feature writes", and
# CONTRIBUTING.md tells contributors the rule applies "anywhere (README, PyPI
# description, CLI help)". Guarding two of those surfaces left the other two
# documented and unenforced.
CLAIM_SURFACES = {
    "README.md": lambda: (_repo_root() / "README.md").read_text(encoding="utf-8"),
    "CHANGELOG.md": lambda: (_repo_root() / "CHANGELOG.md").read_text(encoding="utf-8"),
    "CONTRIBUTING.md": lambda: (_repo_root() / "CONTRIBUTING.md").read_text(encoding="utf-8"),
    "the pyproject description": _package_description,
    "the CLI help screens": _cli_help,
}


@pytest.mark.parametrize("where", sorted(CLAIM_SURFACES))
def test_no_surface_makes_an_unattributed_compatibility_claim(where, strip_ansi):
    # `strip_ansi` before normalizing: the help screens arrive styled under CI,
    # and Rich splits a phrase with escapes, so a claim could sit in the output
    # while the search for it found nothing. A guard that colour codes can
    # disarm is worse than no guard, because it reports success.
    _assert_claim_carries_attribution(_normalized(strip_ansi(CLAIM_SURFACES[where]())), where)


def test_the_guard_reads_provenance_and_quoted_mentions_as_mentions_not_claims():
    # The rule this guard runs on, stated as cases. Without these, a later
    # tightening that demanded attribution from every mention would look correct
    # while making CONTRIBUTING.md's own licensing section unwritable.
    assert not _claims_compatibility("content derived from the Cepheus Engine SRD is also OGC")
    assert not _claims_compatibility('The strings "Cepheus Engine" and "Samardan Press"')
    assert not _claims_compatibility(ATTRIBUTION)


def test_normalizing_preserves_the_hyphen_a_claim_suffix_needs():
    # `_BOX_DRAWING` strips the Box Drawing block, and it must not reach the
    # ASCII hyphen: a reviewer read `[─-╿|]` as three literals including `-`
    # and concluded the `-based` form could slip through unattributed. It
    # cannot, and this pins that it stays so — the guard runs on normalized
    # text, so a class that widened to U+002D would silently disarm the
    # hyphen-suffix half of the rule on every surface.
    assert _BOX_DRAWING.match("-") is None
    claim = "│ A Cepheus Engine-based toolkit │"
    assert "-based" in _normalized(claim)
    assert _claims_compatibility(_normalized(claim))


def test_the_guard_reads_a_compatibility_claim_as_a_claim():
    for claim in (
        "A dice and task-check engine for Cepheus Engine SRD-based games",
        "cetools is compatible with Cepheus Engine",
        "A Cepheus Engine-based toolkit",
    ):
        assert _claims_compatibility(claim), claim
        with pytest.raises(AssertionError):
            _assert_claim_carries_attribution(claim, "a synthetic claim")


# Never shipped, whatever `rglob` finds: hatchling's sdist honours the VCS
# ignore list, and a compiled cache holds this module's own constants — which
# would reintroduce the self-match the split literal above avoids.
_NOT_SHIPPED = ("__pycache__", ".pytest_cache", ".hypothesis")


def _shipped_files(repo_root: Path) -> list[Path]:
    """Every file a source distribution would carry, read out of the build
    configuration rather than assumed.

    Scoped to what ships because that is what the notice must cover: FR-047
    binds "every data file this feature adds" to the chain "that travels with
    the shipped Open Game Content". Deriving the scope from a hard-coded
    `src/` prefix is what left an Open Game Content file under `tests/` — a
    directory the sdist really does ship — covered by no check at all, while
    an OGC-designated file that was not a `.toml` was covered by none either.
    """
    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    includes = pyproject["tool"]["hatch"]["build"]["targets"]["sdist"]["include"]
    assert includes, "the sdist ships nothing, so the scan would be vacuous"
    files: list[Path] = []
    for entry in includes:
        # A leading slash anchors the pattern to the sdist root rather than
        # matching at any depth; joined onto `repo_root` unstripped it would
        # discard `repo_root` entirely, since `Path` treats a leading-slash
        # right operand as absolute.
        target = repo_root / entry.lstrip("/")
        if target.is_dir():
            files.extend(
                path
                for path in target.rglob("*")
                if path.is_file() and not set(path.parts) & set(_NOT_SHIPPED)
            )
        elif target.is_file():
            files.append(target)
    return files


def _designated_in_tree(repo_root: Path) -> list[str]:
    # `as_posix`, not `str`: the notice names POSIX paths, and a Windows
    # `str()` renders separators as backslashes, so this compares the notice
    # against the same shape on every platform. Bytes, not decoded text: the
    # scan reaches every shipped file, and not all of them are text.
    return sorted(
        path.relative_to(repo_root).as_posix()
        for path in _shipped_files(repo_root)
        if DESIGNATION in path.read_bytes()
    )


def test_section_15_game_data_line_covers_every_open_game_content_file_present(
    repo_root, section_15_notices, game_data_covered_paths, game_data_covered_suffix
):
    # 002-rules-data-loading FR-047 and SC-016: derive what the game-data
    # notice must cover from the files actually shipped rather than comparing
    # the chain against a fixed expected text, and derive it from the
    # designation rather than from a directory prefix and an extension.
    designated = _designated_in_tree(repo_root)
    assert designated, "no Open Game Content files found to derive coverage from"
    uncovered = _uncovered(designated, game_data_covered_paths, game_data_covered_suffix)
    assert not uncovered, (
        f"{uncovered} carry the Open Game Content designation but fall under none of the "
        f"paths the game-data notice names: {list(game_data_covered_paths)}"
    )

    text = " ".join((repo_root / "LICENSE-OGL.txt").read_text(encoding="utf-8").split())
    assert section_15_notices[-1] in text


def test_the_coverage_check_can_fail(repo_root, game_data_covered_paths, game_data_covered_suffix):
    # The rule this guard runs on, stated as a case, for the same reason the
    # compatibility-claim guard states its own: an earlier form of the check
    # was a tautology, and a tautology reports success. Narrowing the notice
    # back to the single file that shipped before this feature must fail it.
    narrowed = ("src/cetools/data/tasks.toml",)
    designated = _designated_in_tree(repo_root)
    uncovered = _uncovered(designated, narrowed, game_data_covered_suffix)
    assert uncovered, "a narrowed notice must leave files uncovered"
    assert not _uncovered(designated, game_data_covered_paths, game_data_covered_suffix)


@pytest.mark.parametrize(
    ("relative", "name"),
    [("tests", "fixtures_ogc.toml"), ("src/cetools/data", "tables.md")],
    ids=["outside-src", "not-a-toml"],
)
def test_the_coverage_check_sees_a_designated_file_the_old_scan_missed(
    repo_root, game_data_covered_paths, game_data_covered_suffix, relative, name
):
    """The two cases the previous scan could not fail on, each written into
    the tree and then removed.

    `tests/` really does ship — it is in the sdist's `include` list — and the
    old scan filtered on a `src/` prefix; a designated file that is not a
    `.toml` sits inside the covered directory and the old scan filtered on the
    extension. Both left an Open Game Content file travelling outside the
    notice that grants the right to redistribute it (FR-047, SC-016).
    """
    planted = repo_root / relative / name
    assert not planted.exists()
    planted.write_bytes(b"# " + DESIGNATION + b"; see LICENSE-OGL.txt\n")
    try:
        designated = _designated_in_tree(repo_root)
        assert planted.relative_to(repo_root).as_posix() in designated
        assert _uncovered(designated, game_data_covered_paths, game_data_covered_suffix)
    finally:
        planted.unlink()


def test_shipped_files_still_finds_a_root_level_include_anchored_with_a_leading_slash(repo_root):
    # T138 anchored `"README.md"` and `"CHANGELOG.md"` to `"/README.md"` and
    # `"/CHANGELOG.md"` in the sdist `include` list, so hatchling stops
    # matching the pattern at any depth. `repo_root / "/README.md"` is not
    # `repo_root/README.md`: a `pathlib` join discards the left operand
    # entirely when the right one looks absolute, so `_shipped_files` silently
    # dropped both files, contradicting its own docstring's promise of "every
    # file a source distribution would carry".
    shipped = {path.name for path in _shipped_files(repo_root)}
    assert "README.md" in shipped
    assert "CHANGELOG.md" in shipped


def test_packaged_tasks_toml_opens_with_ogc_designation_and_omits_pi_strings():
    from importlib import resources

    text = resources.files("cetools.data").joinpath("tasks.toml").read_text(encoding="utf-8")
    assert "Open Game Content" in text
    assert "Cepheus Engine" not in text
    assert "Samardan Press" not in text
