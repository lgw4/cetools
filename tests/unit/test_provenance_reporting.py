"""Provenance reporting through a real load: identical content fingerprints
identically regardless of where it was read from, differing content
fingerprints differently, the reported value is reproducible with
`shasum -a 256`, and the reported version is the installed package version
itself rather than a value only ever checked through a placeholder
(SC-008, FR-036).
"""

import shutil
import subprocess
from importlib.metadata import version
from pathlib import Path

import pytest

from cetools.rules import load_rules

NAVY = Path(__file__).resolve().parents[2] / "src" / "cetools" / "data" / "careers" / "navy.toml"


def test_identical_content_at_two_different_locations_fingerprints_identically(tmp_path):
    content = NAVY.read_bytes()

    first = tmp_path / "first"
    first.mkdir()
    (first / "scouts.toml").write_bytes(content.replace(b'name = "Navy"', b'name = "Scouts"'))

    second = tmp_path / "second"
    second.mkdir()
    (second / "scouts.toml").write_bytes(content.replace(b'name = "Navy"', b'name = "Scouts"'))

    first_fingerprint = load_rules(first).provenance.files[0].fingerprint
    second_fingerprint = load_rules(second).provenance.files[0].fingerprint
    assert first_fingerprint == second_fingerprint


def test_differing_content_fingerprints_differently(tmp_path):
    content = NAVY.read_bytes().replace(b'name = "Navy"', b'name = "Scouts"')

    one = tmp_path / "one"
    one.mkdir()
    (one / "scouts.toml").write_bytes(content.replace(b"target = 5", b"target = 9", 1))

    other = tmp_path / "other"
    other.mkdir()
    (other / "scouts.toml").write_bytes(content.replace(b"target = 5", b"target = 8", 1))

    one_fingerprint = load_rules(one).provenance.files[0].fingerprint
    other_fingerprint = load_rules(other).provenance.files[0].fingerprint
    assert one_fingerprint != other_fingerprint


# SC-008 is about an *outside* tool agreeing with the reported value, so it
# cannot be checked where that tool does not exist; Windows runners ship no
# `shasum`. The fingerprint is still covered there by the two tests above,
# which pin content-addressing without leaving the process.
@pytest.mark.skipif(shutil.which("shasum") is None, reason="shasum is not on PATH")
def test_the_reported_fingerprint_is_reproducible_with_shasum(tmp_path):
    override = tmp_path / "scouts.toml"
    override.write_bytes(NAVY.read_bytes().replace(b'name = "Navy"', b'name = "Scouts"'))

    reported = load_rules(tmp_path).provenance.files[0].fingerprint

    shasum = subprocess.run(
        ["shasum", "-a", "256", str(override)], capture_output=True, text=True, check=True
    )
    expected_hex = shasum.stdout.split()[0]
    assert reported == f"sha256:{expected_hex}"


def test_the_reported_version_equals_the_installed_package_version():
    rules = load_rules()
    assert rules.provenance.version == version("cetools")
