# Implementation Plan: Release Publishing

**Branch**: `005-release-publishing` | **Date**: 2026-09-01 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/005-release-publishing/spec.md`

## Summary

cetools has never cut a release. Version `2026.08.1` sits declared in
`pyproject.toml` and unreleased, no tag exists, and the only automation is the
merge-time test matrix. This feature makes a release a tag-triggered,
fully automatic publication on GitHub Releases: pushing `v2026.08.1` runs a
preflight that refuses a wrong release, runs the full suite on a clean
`ubuntu-latest` runner at the tagged commit, builds the hatchling sdist and
wheel, attests their provenance, and publishes them with a combined SHA-256
manifest and the version's changelog section as the release notes.

Around that mechanism sit the things a publicly distributed artifact is
expected to carry and the mechanical guards that keep the recurring failure
modes from shipping: descriptive `[project]` metadata and repository links, a
`py.typed` marker, a README installation command that points at the published
artifact instead of a package index that has never carried this package, a
drift guard extended to cover that command in both of the version's spellings,
and a packaging guard tightened to compare full relative paths so a flattened
rules-data layout fails at build-inspection time.

The technical approach is deliberately thin: one new workflow file, two small
pure-Bourne-shell scripts with pytest coverage, an empty marker file, edits to
`pyproject.toml`, `README.md`, and `CONTRIBUTING.md`, and extensions to two
guards that already exist. No new runtime dependency, and no new shipped code.

## Technical Context

**Language/Version**: Python 3.13+ (release job pins 3.13, the supported
floor); release scripting in pure Bourne shell (`/usr/bin/env sh`)

**Primary Dependencies**: no new runtime dependency. Build backend stays
`hatchling`. Dev group gains `mypy` (optional, gates nothing). Release
automation uses `actions/checkout`, `astral-sh/setup-uv`,
`actions/attest-build-provenance`, and the `gh` CLI preinstalled on GitHub
runners.

**Storage**: N/A. Release state lives in GitHub Releases; the version is
declared statically in `pyproject.toml`, which stays the single authority.

**Testing**: pytest. New coverage lands in `tests/guards/` (the shell scripts,
the release footer, the extended drift and packaging guards) and reuses the
existing `tests/conftest.py` skip machinery for tools that may be absent.

**Target Platform**: the published artifacts are platform-independent
(`py3-none-any`). The release job runs on `ubuntu-latest` only; the existing
merge-time workflow keeps the three-platform, two-interpreter matrix.

**Project Type**: single Python project (library plus CLI), packaged as an
sdist and a wheel.

**Performance Goals**: N/A. The release job's wall-clock time is not a
constraint; it runs `uv build` twice (once inside the packaging guard, once for
the artifacts), which is accepted rather than optimized away.

**Constraints**:

- Nothing is published unless every preflight check and the full suite pass, so
  a failed attempt leaves the version number available for a retry.
- A published version number is spent (constitution, Development Workflow), so
  the workflow refuses a tag whose version already has a release.
- The version has three spellings that must each appear in the right position:
  declared `2026.08.1`, PEP 440 normalized `2026.8.1`, and tag `v2026.08.1`.
- The release body is the changelog section verbatim plus a fixed footer, and
  nothing else (FR-002, resolved in the spec's clarifications).

**Scale/Scope**: one workflow, two shell scripts, one marker file, four edited
documents, two extended guards. 42 shipped rules-data files whose paths the
tightened packaging guard now compares in full.

## Constitution Check

*GATE: passed before Phase 0 research; re-checked after Phase 1 design.*

| Principle / clause | Bearing on this feature | Status |
| --- | --- | --- |
| I. Library-First | No library capability is added. `py.typed` and the `[project]` metadata are packaging, not game logic. | Not engaged |
| II. CLI Text I/O Protocol | No CLI surface changes. The release scripts are build tooling, not a library capability, so they owe no `--json` mode. | Not engaged |
| III. Test-First (NON-NEGOTIABLE) | Engaged. Every guard extension and both shell scripts get a failing test first. mypy is added as an optional tool and gates nothing, which is what this principle's own "no mandated tooling gates beyond tests" sentence requires. | Pass |
| IV. Seed-Reproducible Generation | No generator changes. The relevant clause is the *other* direction: the constitution's never-reuse rule exists because a reused version number would falsify the seed-and-version promise, and FR-025's already-published check is what enforces it mechanically. | Pass |
| V. Data-Driven Rules Content | No rules data changes. The tightened packaging guard strengthens this principle: it fails a build whose data files sit at paths the loader could not read. | Pass |
| VI. Simplicity | Two shell scripts, one workflow, no new runtime dependency, no release module inside the shipped package. Discussed below. | Pass |
| Licensing: compatibility claims carry attribution | The published release page is now a surface the constitution names. Discharged by a fixed footer file appended by the workflow, guarded in `tests/unit/test_licensing.py`, rather than by per-version text a maintainer could forget. | Pass |
| Licensing: every distribution bundles OGL 1.0a and Section 15 | Already discharged by `tests/guards/test_packaging.py`; unchanged here except that the artifacts are now published rather than discarded. | Pass |
| Distribution: a release is a tagged, immutable bundle on the public source repository | This feature is the implementation of that clause, amended for exactly this purpose in constitution 2026.08.2. | Pass |
| Development Workflow: CalVer `YYYY.0M.INC1` | Already guarded. The tag adds a `v` prefix over the declared form; the workflow strips one leading `v` before comparing. | Pass |
| Governance: complexity justified against VI | See below. | Pass |

**Principle VI, the one call worth stating.** Two pure-Bourne-shell scripts do
the changelog extraction and the preflight checks rather than a Python module.
The simpler-looking alternative, a `cetools release` subcommand or a
`scripts/release.py`, was rejected on two grounds: the preflight has to run and
abort *before* the package is necessarily installable, and release machinery
inside `src/cetools/` would ship in every distribution to serve nobody who
installed it. Shell also matches the repository's stated tooling preference.
The cost is that shell is harder to test than Python, which is why both scripts
are invoked from pytest with fixture changelogs rather than trusted on sight.

**No entries in Complexity Tracking.** Nothing here exceeds the simplest
adequate solution.

### Post-design re-check

Re-evaluated after Phase 1. No new violations. Two things the design surfaced
that are worth recording rather than leaving implicit:

1. **The release body carries no checksums.** The planning input asked for
   SHA-256 checksums in the release body; FR-002, as resolved in the spec's
   clarification session, fixes the body as the changelog section verbatim
   followed by the fixed footer, with "nothing else may be added". The
   checksums therefore live only in the `SHA256SUMS.txt` asset, which is what
   FR-006 and SC-002 actually require ("published as a single combined file",
   "verifiable in one command"). Recorded as R7 in research.md.
2. **mypy is not required to report clean.** FR-022 forbids it from gating
   anything, and Principle III forbids mandating it. Making a clean run a
   deliverable would be that mandate arriving by the back door.

## Project Structure

### Documentation (this feature)

```text
specs/005-release-publishing/
├── plan.md              # This file
├── spec.md              # Already written
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── release-workflow.md    # The tag trigger, abort conditions, published asset set
│   ├── release-scripts.md     # The two shell scripts' argument, stdout, and exit-code contract
│   └── package-metadata.md    # The [project] fields the built distributions must carry
└── tasks.md             # Phase 2 output (/speckit-tasks; NOT created here)
```

### Source Code (repository root)

```text
.github/
├── workflows/
│   ├── ci.yaml               # Existing merge-time matrix; unchanged
│   └── release.yaml          # NEW: tag-triggered release job
└── release-footer.md         # NEW: the fixed attribution/non-affiliation footer

scripts/                      # NEW directory (repo-root tooling, not shipped)
├── changelog-section.sh      # NEW: extract the `## <version>` section body
└── release-preflight.sh      # NEW: the four abort checks

src/cetools/
└── py.typed                  # NEW: empty PEP 561 marker

tests/
├── guards/
│   ├── test_documented_version.py   # EXTENDED: install-command coverage, both spellings
│   ├── test_packaging.py            # EXTENDED: full-path comparison, py.typed, metadata
│   ├── test_python_support.py       # EXTENDED: Python trove classifiers track ci.yaml's matrix
│   ├── test_release_scripts.py      # NEW: the two shell scripts, against fixture changelogs
│   └── test_release_workflow.py     # NEW: release.yaml's required steps and its prohibitions
└── unit/
    └── test_licensing.py            # EXTENDED: the release footer carries the attribution

pyproject.toml                # EDITED: classifiers, keywords, authors, [project.urls],
                              #         mypy in the dev group, [tool.mypy]
README.md                     # EDITED: installation section (FR-016, FR-017, FR-018, FR-026)
CONTRIBUTING.md               # EDITED: release procedure, mypy, the superseded PyPI clauses
CHANGELOG.md                  # EDITED: entries for this feature; dated at release time
```

**Structure Decision**: the existing single-project layout is kept unchanged.
Everything this feature adds sits outside `src/`, because none of it ships:
release automation in `.github/`, release scripting in a new repo-root
`scripts/` directory, and coverage in the existing `tests/guards/` tree. The
one exception is `src/cetools/py.typed`, which exists precisely in order to
ship. `scripts/` is deliberately not added to the sdist `include` list; it is
maintainer tooling, not part of a distribution.

## Complexity Tracking

No Constitution Check violations. This table is intentionally empty.
