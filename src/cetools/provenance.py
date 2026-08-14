"""Provenance: what produced a loaded data set, and what (if anything) an
override changed (contracts/data-files.md, data-model.md).
"""

import hashlib
from dataclasses import dataclass
from enum import StrEnum
from importlib.metadata import version


class Disposition(StrEnum):
    """How an overridden file relates to the packaged data set it composed
    with. An ignored file is not a third member here (research, data-model.md):
    it carries no fingerprint and lives in `Provenance.ignored` instead.
    """

    REPLACED = "replaced"
    ADDED = "added"


@dataclass(frozen=True, slots=True)
class FileProvenance:
    """One overridden file's composition key, disposition, and fingerprint."""

    file: str
    disposition: Disposition
    fingerprint: str


@dataclass(frozen=True, slots=True)
class Provenance:
    """What produced a `RulesData`: the package version, and what an
    override changed, if anything.
    """

    version: str
    files: tuple[FileProvenance, ...]
    ignored: tuple[str, ...]

    @property
    def is_packaged(self) -> bool:
        return not self.files


def fingerprint(data: bytes) -> str:
    """`"sha256:"` plus the lowercase hex digest of `data`, hashed as read.

    Never decode first: that would make the value unreproducible with
    `shasum -a 256` and would silently normalize line endings (research R4).
    """
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def package_version() -> str:
    """The installed `cetools` version, read once from package metadata so a
    result cannot report a version other than the one that produced it.
    """
    return version("cetools")
