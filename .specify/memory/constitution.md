# cetools Constitution

## Core Principles

### I. Library-First
Every capability lives in the importable `cetools` library. The CLI is a
thin consumer of the library API and contains no game logic of its own; a
future web UI would be another consumer of the same API. Library modules
are self-contained, independently testable, and documented.

### II. CLI Text I/O Protocol
Every library capability is reachable from the CLI. Input arrives via
arguments and stdin; results go to stdout; errors and diagnostics go to
stderr. Every command supports both human-readable output and JSON
(machine-readable) output. Exit codes are meaningful: zero on success,
non-zero on failure.

### III. Test-First (NON-NEGOTIABLE)
TDD is mandatory: tests are written first, confirmed to fail, and only
then is the implementation written. Red-Green-Refactor is strictly
enforced for all library code. No mandated tooling gates beyond tests;
lint, format, and type-check tooling may be used but is not
constitutionally required.

### IV. Seed-Reproducible Generation
Every generator accepts a seed, and the same seed with the same package
version produces the same output. No generator draws randomness from any
source outside its seeded generator. Reproducibility is a feature (share
and regenerate results) and the testing strategy (deterministic
assertions), and it is designed in from day one, never retrofitted.

### V. Data-Driven Rules Content
Rules content from the Cepheus Engine SRD (career tables, skill lists,
task parameters, and the like) lives in data files shipped with the
package; engine code interprets the data and contains no hard-coded
table content. House rules and future expansion happen by editing or
swapping data, not by forking code.

### VI. Simplicity
YAGNI governs: build the simplest thing that solves the actual problem;
speculative abstraction is rejected in review. Prefer the Python
standard library; every third-party runtime dependency must be justified
by a concrete need the standard library cannot meet.

## Licensing & Distribution Constraints

- Source code is licensed under **GPL-3.0**.
- Shipped rules data derived from the Cepheus Engine SRD is **Open Game
  Content under OGL 1.0a** and cannot be sublicensed under the GPL; the
  repository and package must clearly designate which files are OGC and
  which are GPL-licensed code.
- Every distribution (sdist and wheel) bundles the full OGL 1.0a text
  and reproduces the SRD's complete Section 15 copyright-notice chain
  verbatim, extended with this project's own game-data copyright line.
- The Product Identity strings "Cepheus Engine" and "Samardan Press"
  must not appear in the package name or inside shipped Open Game
  Content data files.
- Wherever compatibility with Cepheus Engine is claimed (README, PyPI
  description), include the Compatibility-Statement License attribution
  ("Cepheus Engine and Samardan Press are the trademarks of Jason
  'Flynn' Kemp") and a statement of non-affiliation.

## Development Workflow

- **Python 3.13+** is the supported floor.
- Versioning is **CalVer in `YYYY.0M.INC1` format** (e.g. `2026.08.1`
  for the first release cut in August 2026, `2026.08.2` for the
  second). Because CalVer does not signal breaking changes, every
  release ships a changelog entry and breaking changes are flagged
  prominently there.
- Releases are published to PyPI.

## Governance

This constitution supersedes all other practices. All PRs and reviews
verify compliance with its principles; complexity beyond the simplest
adequate solution must be justified against Principle VI. Amendments are
made via `/speckit-constitution`, documented with a version bump, the
amendment date, and a rationale. The constitution itself is versioned
with the same CalVer `YYYY.0M.INC1` scheme the project uses.

**Version**: 2026.08.1 | **Ratified**: 2026-08-11 | **Last Amended**: 2026-08-11
