import re
import tomllib
from pathlib import Path

import pytest

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

    The constitution's Compatibility-Statement clause and FR-035 allow either
    route; what they forbid is claiming compatibility without the attribution
    and the statement of non-affiliation.
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


# FR-035 binds "any text this feature writes", and CONTRIBUTING.md tells
# contributors the rule applies "anywhere (README, PyPI description, CLI help)".
# Guarding two of those surfaces left the other two documented and unenforced.
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


def test_section_15_game_data_line_covers_every_data_file_actually_present(
    repo_root, section_15_notices
):
    # FR-047, SC-016: derive what the game-data notice must cover from the data
    # files actually present rather than comparing the chain against a fixed
    # expected text. A check written the latter way passes unchanged when a
    # file is added, which is exactly the failure this test exists to catch.
    game_data_line = section_15_notices[-1]
    covered_prefix = "src/cetools/data/"
    assert (
        covered_prefix in game_data_line
    ), "the game-data notice must name the directory every shipped data file lives under"

    data_dir = repo_root / "src" / "cetools" / "data"
    data_files = sorted(p.relative_to(repo_root) for p in data_dir.rglob("*.toml"))
    assert data_files, "no data files found to derive coverage from"
    for data_file in data_files:
        # `as_posix`, not `str`: the notice names a POSIX path, and a Windows
        # `str()` renders separators as backslashes, so this compares the
        # notice against the same shape on every platform.
        assert data_file.as_posix().startswith(
            covered_prefix
        ), f"{data_file} is not under the directory the game-data notice covers"

    text = " ".join((repo_root / "LICENSE-OGL.txt").read_text(encoding="utf-8").split())
    assert game_data_line in text


def test_packaged_tasks_toml_opens_with_ogc_designation_and_omits_pi_strings():
    from importlib import resources

    text = resources.files("cetools.data").joinpath("tasks.toml").read_text(encoding="utf-8")
    assert "Open Game Content" in text
    assert "Cepheus Engine" not in text
    assert "Samardan Press" not in text
