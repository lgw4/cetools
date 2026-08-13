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


def test_wheel_contains_the_packaged_rules_data(wheel):
    assert "cetools/data/tasks.toml" in wheel.namelist()
    text = wheel.read("cetools/data/tasks.toml").decode("utf-8")
    assert "Open Game Content" in text


def _license_in_wheel(wheel: zipfile.ZipFile, name: str) -> str:
    matches = [n for n in wheel.namelist() if n.endswith(f".dist-info/licenses/{name}")]
    assert matches, f"{name} is missing from the wheel"
    return wheel.read(matches[0]).decode("utf-8")


def test_wheel_carries_the_source_code_license(wheel):
    assert _license_in_wheel(wheel, "LICENSE").strip()


def test_wheel_carries_the_ogl_text_with_its_section_15_chain(wheel):
    text = _license_in_wheel(wheel, "LICENSE-OGL.txt")
    assert "OPEN GAME LICENSE Version 1.0a" in text
    assert "Section 15" in text or "COPYRIGHT NOTICE" in text


def _read_from_sdist(sdist: tarfile.TarFile, relative: str) -> str:
    # Every member sits under a single `{name}-{version}/` prefix directory.
    matches = [n for n in sdist.getnames() if n.split("/", 1)[-1] == relative]
    assert matches, f"{relative} is missing from the sdist"
    handle = sdist.extractfile(matches[0])
    assert handle is not None
    return handle.read().decode("utf-8")


def test_sdist_contains_the_packaged_rules_data(sdist):
    text = _read_from_sdist(sdist, "src/cetools/data/tasks.toml")
    assert "Open Game Content" in text


def test_sdist_carries_the_source_code_license(sdist):
    assert _read_from_sdist(sdist, "LICENSE").strip()


def test_sdist_carries_the_ogl_text_with_its_section_15_chain(sdist):
    text = _read_from_sdist(sdist, "LICENSE-OGL.txt")
    assert "OPEN GAME LICENSE Version 1.0a" in text
    assert "Section 15" in text or "COPYRIGHT NOTICE" in text
