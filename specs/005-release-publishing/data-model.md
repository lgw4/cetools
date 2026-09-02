# Phase 1 Data Model: Release Publishing

This feature adds no runtime types and no rules data. Its entities are build
and publication artifacts, so this document describes what each one is, what
identifies it, what it must contain, and which rule refuses it. Nothing here
becomes a Python class.

## Version

The project's single declared identifier for a release.

| Field | Value | Authority |
| --- | --- | --- |
| Declared form | `2026.08.1` | `pyproject.toml` `project.version` |
| Reported form | `2026.8.1` | PEP 440 normalization, read back via `importlib.metadata` |
| Tag form | `v2026.08.1` | The declared form with a `v` prefix |

**Shape**: `YYYY.0M.INC1`, pinned by `_CALVER` in
`tests/guards/test_documented_version.py`: a four-digit year beginning `20`, a
zero-padded month `01` through `12`, and an increment of one or more digits
with no leading zero.

**Relationships**: exactly one Changelog entry, exactly one Release tag,
exactly one Release, exactly one source commit.

**Validation**:

- The declared form matches `_CALVER` (existing guard).
- The declared form normalizes to the reported form (existing guard).
- The tag form is the declared form with exactly one leading `v` (preflight).
- Each form appears only in its own position across documented outputs
  (extended drift guard; see research.md R13).

**State**: `declared` → `dated` (its changelog heading carries a date) →
`published` → `spent`. There is no transition out of `spent`; a defect ships as
the next increment. A release attempt that aborts before publishing leaves the
version in its prior state, which is why a retry is legitimate.

## Release tag

The deliberate trigger, and the only one.

- **Identity**: the git tag name, `v` plus the declared form.
- **Points at**: one commit, which is what the release job checks out. Not a
  branch tip.
- **Refused when**: the name does not parse as `v` plus a `_CALVER` string
  (the `v*` trigger filter, then the preflight), or the stripped remainder does
  not equal `project.version` at that commit (FR-007).

A tag is not evidence that a release exists. The already-published check asks
about the Release, not the tag, because the tag necessarily exists by the time
the workflow runs (research.md R18).

## Changelog entry

The curated per-version section of `CHANGELOG.md` that doubles as the public
announcement text.

- **Identity**: a `## <declared form>` heading.
- **Body**: everything after the heading line, up to the next `## ` heading or
  end of file, blank-line-trimmed at both ends.
- **Undated state**: the heading carries `(unreleased)`.
- **Dated state**: the heading carries an ISO date.

**Validation**:

- A heading for the declared version exists (existing guard, and preflight
  check 2).
- The heading is dated rather than marked unreleased (preflight check 3, and
  only there; a suite guard would fail every working branch).
- The section body is non-empty (preflight check 4; a dated heading over
  nothing is not an announcement).
- The heading matches that version and not a longer one whose prefix it is:
  `## 2026.08.1` never selects `## 2026.08.10`.
- No section other than `### Breaking changes` cites FR-056b (existing guard).

**Note for the first release**: `CHANGELOG.md` currently holds exactly one
`## ` section, so the extractor's "runs to end of file" branch is the one the
first release exercises.

## Release

A published, immutable bundle on `lgw4/cetools`.

- **Identity**: the Release tag.
- **Title**: the tag form.
- **Body**: the Changelog entry body, verbatim, followed by the Release footer.
  Nothing else (FR-002).
- **Assets**: exactly four things, described below.
- **Bound to**: one source commit, through both the tag and the Provenance
  records.

**Immutability**: never republished, never edited, never added to. The workflow
holds this structurally: it calls `gh release create` once and never
`gh release edit`, `gh release upload`, or `--clobber`.

## Distribution artifact

Two per release, both platform-independent.

| Artifact | Filename | Built by |
| --- | --- | --- |
| Source distribution | `cetools-2026.8.1.tar.gz` | `uv build` (hatchling sdist target) |
| Built distribution | `cetools-2026.8.1-py3-none-any.whl` | `uv build` (hatchling wheel target) |

Filenames carry the **reported** form, because that is what the build backend
writes.

**Each must contain** (all already guarded except the last two):

- Every `.toml` under `src/cetools/data/`, at its full relative path
  (tightened; FR-015).
- Exactly one of the OGC or the GPL designation per rules-data file.
- No Product Identity string inside any shipped Open Game Content file.
- The full OGL 1.0a text with its complete Section 15 chain, and the GPL text.
- No file outside the sdist `include` list.
- The `py.typed` marker: `cetools/py.typed` in the wheel,
  `src/cetools/py.typed` in the sdist (new; FR-020).
- The descriptive metadata of the Package metadata entity below (new; FR-019).

## Checksum manifest

- **Identity**: `SHA256SUMS.txt`, one per release.
- **Content**: one line per Distribution artifact, in `sha256sum` output
  format, generated over the two files in `dist/`.
- **Covers**: both artifacts, and only them. It does not list itself.
- **Verified by**: `sha256sum -c SHA256SUMS.txt` on Linux,
  `shasum -a 256 -c SHA256SUMS.txt` on macOS, `Get-FileHash` on Windows.

It exists as an asset and nowhere else; the release body carries no checksums
(research.md R7).

## Provenance record

One per Distribution artifact.

- **Produced by**: `actions/attest-build-provenance`, run after the build and
  before publication.
- **Binds**: the artifact's digest to the workflow run, the workflow file, and
  the source commit.
- **Verified by**: `gh attestation verify <file> --repo lgw4/cetools`.
- **Stored by**: GitHub, alongside the release, rather than as a file this
  project uploads.

## Release footer

The fixed text FR-021 requires below every release body.

- **Identity**: `.github/release-footer.md`. One file, not per version.
- **Must contain**: the exact attribution string
  `Cepheus Engine and Samardan Press are the trademarks of Jason 'Flynn' Kemp`,
  and a statement of non-affiliation matching one of the phrases
  `tests/unit/test_licensing.py` already recognizes.
- **Guarded by**: `tests/unit/test_licensing.py`, using the constants that
  module already defines, so the footer cannot drift away from the wording
  every other surface is checked against.

## Package metadata

The `[project]` fields the built distributions carry. Not a runtime entity;
listed here because FR-019 and SC-002 bind its contents.

| Field | Status |
| --- | --- |
| `name`, `version`, `description`, `readme`, `requires-python` | Existing, unchanged |
| `license`, `license-files` | Existing, unchanged (SPDX expression, plus both texts) |
| `dependencies`, `[project.scripts]` | Existing, unchanged |
| `keywords` | New. Descriptive terms; must not name the trademark |
| `classifiers` | New. Includes `Typing :: Typed`; no `License ::` classifier |
| `authors` | New. Name only (research.md R22) |
| `[project.urls]` | New. `Homepage`, `Repository`, `Changelog`, `Issues` |

See [contracts/package-metadata.md](./contracts/package-metadata.md) for the
exact field contract.
