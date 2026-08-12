import tomllib
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


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


def test_packaged_tasks_toml_opens_with_ogc_designation_and_omits_pi_strings():
    from importlib import resources

    text = resources.files("cetools.data").joinpath("tasks.toml").read_text(encoding="utf-8")
    assert "Open Game Content" in text
    assert "Cepheus Engine" not in text
    assert "Samardan Press" not in text
