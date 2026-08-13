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

import shutil
import subprocess
import tarfile
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


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
    """
    assert "Open Game Content" in text, f"{where} lost its Open Game Content designation"
    assert "Cepheus Engine" not in text, f"{where} carries a Product Identity string"
    assert "Samardan Press" not in text, f"{where} carries a Product Identity string"


def test_wheel_contains_the_packaged_rules_data(wheel):
    assert "cetools/data/tasks.toml" in wheel.namelist()
    _assert_shipped_rules_data(wheel.read("cetools/data/tasks.toml").decode("utf-8"), "the wheel")


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


def test_sdist_contains_the_packaged_rules_data(sdist):
    _assert_shipped_rules_data(_read_from_sdist(sdist, "src/cetools/data/tasks.toml"), "the sdist")


def test_sdist_carries_the_source_code_license(sdist):
    assert _read_from_sdist(sdist, "LICENSE").strip()


def test_sdist_carries_the_ogl_text_with_its_section_15_chain(sdist, assert_section_15_chain):
    text = _read_from_sdist(sdist, "LICENSE-OGL.txt")
    assert "OPEN GAME LICENSE Version 1.0a" in text
    assert_section_15_chain(text, "the sdist's LICENSE-OGL.txt")
