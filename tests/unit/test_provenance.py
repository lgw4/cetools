import hashlib

from cetools.provenance import (
    Disposition,
    FileProvenance,
    Provenance,
    fingerprint,
    package_version,
)


class TestDisposition:
    def test_replaced_serializes_to_replaced(self):
        assert Disposition.REPLACED == "replaced"
        assert str(Disposition.REPLACED) == "replaced"

    def test_added_serializes_to_added(self):
        assert Disposition.ADDED == "added"
        assert str(Disposition.ADDED) == "added"


class TestFingerprint:
    def test_sha256_over_raw_bytes(self):
        data = b'schema = "career"\n'
        expected = f"sha256:{hashlib.sha256(data).hexdigest()}"
        assert fingerprint(data) == expected

    def test_reproducible_with_shasum_format(self):
        digest = fingerprint(b"content")
        assert digest.startswith("sha256:")
        hex_part = digest.removeprefix("sha256:")
        assert len(hex_part) == 64
        assert hex_part == hex_part.lower()
        int(hex_part, 16)  # raises ValueError if not valid hex

    def test_identical_content_fingerprints_identically(self):
        assert fingerprint(b"same content") == fingerprint(b"same content")

    def test_differing_content_fingerprints_differently(self):
        assert fingerprint(b"content a") != fingerprint(b"content b")

    def test_does_not_decode_bytes_first(self):
        # A byte sequence that is not valid UTF-8 must still hash; decoding
        # first would raise instead.
        data = b"\xff\xfe\x00\x01"
        assert fingerprint(data) == f"sha256:{hashlib.sha256(data).hexdigest()}"

    def test_content_differing_only_in_line_endings_fingerprints_differently(self):
        assert fingerprint(b"a\nb") != fingerprint(b"a\r\nb")


class TestFileProvenance:
    def test_fields(self):
        fp = FileProvenance(
            file="navy.toml", disposition=Disposition.REPLACED, fingerprint="sha256:abc"
        )
        assert fp.file == "navy.toml"
        assert fp.disposition is Disposition.REPLACED
        assert fp.fingerprint == "sha256:abc"


class TestProvenance:
    def test_is_packaged_when_no_files_overridden(self):
        provenance = Provenance(version="2026.08.1", files=(), ignored=())
        assert provenance.is_packaged is True

    def test_not_packaged_when_a_file_took_effect(self):
        provenance = Provenance(
            version="2026.08.1",
            files=(
                FileProvenance(
                    file="navy.toml", disposition=Disposition.REPLACED, fingerprint="sha256:x"
                ),
            ),
            ignored=(),
        )
        assert provenance.is_packaged is False

    def test_ignored_is_independent_of_is_packaged(self):
        # An override location holding only a README leaves the data
        # packaged and the README named (FR-032a).
        provenance = Provenance(version="2026.08.1", files=(), ignored=("README.md",))
        assert provenance.is_packaged is True
        assert provenance.ignored == ("README.md",)

    def test_version_field(self):
        provenance = Provenance(version="2026.08.1", files=(), ignored=())
        assert provenance.version == "2026.08.1"


class TestPackageVersion:
    def test_matches_installed_package_metadata(self):
        from importlib.metadata import version

        assert package_version() == version("cetools")
