"""Provenance reporting through a real load: identical content fingerprints
identically regardless of where it was read from, differing content
fingerprints differently, the reported value is reproducible with
`shasum -a 256`, and the reported version is the installed package version
itself rather than a value only ever checked through a placeholder
(SC-008, FR-036).
"""

import hashlib
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


def test_the_reported_fingerprint_is_reproducible_with_shasum(tmp_path):
    override = tmp_path / "scouts.toml"
    override.write_bytes(NAVY.read_bytes().replace(b'name = "Navy"', b'name = "Scouts"'))

    reported = load_rules(tmp_path).provenance.files[0].fingerprint

    # SC-008 is about an *outside* tool agreeing with the reported value, so it
    # cannot be checked where that tool cannot be run. Skipping on the attempt
    # rather than on `shutil.which` is deliberate: Git for Windows puts an
    # extensionless Perl `shasum` on PATH, so `which` finds one the OS then
    # refuses to execute. Only `OSError` is caught, so a `shasum` that does run
    # and disagrees still fails; the two tests above keep content-addressing
    # covered wherever this is skipped.
    try:
        shasum = subprocess.run(
            ["shasum", "-a", "256", str(override)], capture_output=True, text=True, check=True
        )
    except OSError as exc:
        pytest.skip(f"shasum cannot be executed here: {exc}")

    expected_hex = shasum.stdout.split()[0]
    assert reported == f"sha256:{expected_hex}"


def test_the_reported_version_equals_the_installed_package_version():
    rules = load_rules()
    assert rules.provenance.version == version("cetools")


def test_the_reported_version_equals_the_installed_package_version_when_overridden(tmp_path):
    # The sibling assertion above reaches only the packaged branch's
    # `Provenance(version=package_version(), ...)` construction; the
    # overridden branch is a second, independent call site, and this is
    # precisely the case where a reader needs both halves of the
    # reproduction key (FR-033a, SC-008).
    override = tmp_path / "scouts.toml"
    override.write_bytes(NAVY.read_bytes().replace(b'name = "Navy"', b'name = "Scouts"'))
    rules = load_rules(tmp_path)
    assert not rules.provenance.is_packaged
    assert rules.provenance.version == version("cetools")


def test_an_override_load_is_not_cached_editing_and_reloading_sees_new_content(tmp_path):
    # `load_rules`' own docstring states the override call is not cached,
    # "since a caller may edit a file and reload in the same process" — the
    # authoring loop plan.md's Performance Goals describe. A naive
    # memoization keyed on the override path would leave every fingerprint
    # test above passing, since none of them loads the same path twice
    # (FR-036, FR-024, SC-008).
    override = tmp_path / "scouts.toml"
    first_content = (
        NAVY.read_bytes()
        .replace(b'name = "Navy"', b'name = "Scouts"')
        .replace(b"target = 5", b"target = 8", 1)
    )
    override.write_bytes(first_content)
    first_fingerprint = load_rules(tmp_path).provenance.files[0].fingerprint

    second_content = first_content.replace(b"target = 8", b"target = 9", 1)
    override.write_bytes(second_content)
    second_fingerprint = load_rules(tmp_path).provenance.files[0].fingerprint

    assert first_fingerprint != second_fingerprint
    assert first_fingerprint == f"sha256:{hashlib.sha256(first_content).hexdigest()}"
    assert second_fingerprint == f"sha256:{hashlib.sha256(second_content).hexdigest()}"


def test_fingerprint_reflects_the_raw_bytes_with_no_line_ending_normalization(tmp_path):
    # research R4 and `fingerprint`'s own docstring name this transformation
    # specifically: decoding or normalizing line endings before hashing
    # would make the reported value irreproducible with `shasum -a 256`,
    # which is FR-036's "MUST NOT vary with ... anything else outside the
    # content itself". The sibling test above proving `shasum` agreement
    # uses whatever line endings the shipped file already has (LF), so it
    # cannot see a normalization step that treats CRLF and LF as equal.
    content = (
        NAVY.read_bytes().replace(b'name = "Navy"', b'name = "Scouts"').replace(b"\n", b"\r\n")
    )
    assert b"\r\n" in content
    override = tmp_path / "scouts.toml"
    override.write_bytes(content)

    reported = load_rules(tmp_path).provenance.files[0].fingerprint

    assert reported == f"sha256:{hashlib.sha256(content).hexdigest()}"
