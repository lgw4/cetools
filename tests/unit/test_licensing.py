import tomllib
from pathlib import Path

ATTRIBUTION = "Cepheus Engine and Samardan Press are the trademarks of Jason 'Flynn' Kemp"
NON_AFFILIATION_PHRASES = ("not affiliated", "no affiliation")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _normalized(text: str) -> str:
    return " ".join(text.split())


def _assert_claim_carries_attribution(text: str, where: str) -> None:
    """Assert `text` either makes no compatibility claim or attributes it.

    The constitution's Compatibility-Statement clause and FR-035 allow either
    route; what they forbid is naming the trademark without the attribution
    and the statement of non-affiliation.
    """
    if "Cepheus Engine" not in text:
        return
    assert ATTRIBUTION in text, f"{where} names Cepheus Engine without the attribution"
    assert any(
        phrase in text.lower() for phrase in NON_AFFILIATION_PHRASES
    ), f"{where} names Cepheus Engine without a statement of non-affiliation"


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


def test_readme_makes_no_unattributed_compatibility_claim():
    text = _normalized((_repo_root() / "README.md").read_text(encoding="utf-8"))
    _assert_claim_carries_attribution(text, "README.md")


def test_package_description_makes_no_unattributed_compatibility_claim():
    pyproject = tomllib.loads((_repo_root() / "pyproject.toml").read_text(encoding="utf-8"))
    _assert_claim_carries_attribution(
        _normalized(pyproject["project"]["description"]), "the pyproject description"
    )


def test_packaged_tasks_toml_opens_with_ogc_designation_and_omits_pi_strings():
    from importlib import resources

    text = resources.files("cetools.data").joinpath("tasks.toml").read_text(encoding="utf-8")
    assert "Open Game Content" in text
    assert "Cepheus Engine" not in text
    assert "Samardan Press" not in text
