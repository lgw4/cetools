<!--
Sync Impact Report: amendment 2026-08-31

Version change: 2026.08.1 → 2026.08.2

Bump rationale: the constitution is versioned with the project's own CalVer
`YYYY.0M.INC1` scheme (see Governance), not semantic versioning. This is the
second amendment cut in August 2026, so the increment advances and the month
stays. Under the semantic scheme the command's default guidance names, this
would be a MAJOR change: a ratified distribution clause is redefined, not
clarified. The CalVer scheme the project chose carries no such signal, which
is precisely why every change ships a changelog entry.

Modified principles: none. All six Core Principles are unchanged in title and
text.

Modified sections:
- Licensing & Distribution Constraints: the compatibility-statement clause
  named "README, PyPI description" as the places compatibility is claimed.
  Since no PyPI description exists and the public release page now does, the
  clause names the release page and the built package's description instead.
- Development Workflow: "Releases are published to PyPI." is replaced by a
  definition of what a release is for this project, plus a never-reuse rule
  for published version numbers.

Added sections: none.

Removed sections: none.

Amendment rationale (Development Workflow, distribution channel):

  The clause "Releases are published to PyPI" was ratified on 2026-08-11 and
  has never been satisfied: no account exists on the index, no credential has
  been provisioned, and the project has cut no release at all. Version
  2026.08.1 sits declared and unreleased. Specification 005-release-publishing
  establishes a release process that publishes to the project's public source
  repository instead. Rather than let the ratified clause sit quietly
  contradicted by the way the project actually ships, it is amended.

  Publishing to a package index remains the intended future channel, and the
  package name intended for it is `cetools`, the name the project's own
  distribution metadata already declares, and which no other channel is
  permitted to change without a further amendment. Adding the index as a
  publication step today would mean committing untested automation that
  guesses at configuration values which do not yet exist; that step belongs
  in the feature that provisions the account, not in this amendment.

  The never-reuse rule is not administrative tidiness. Principle IV promises
  that a seed and a package version together determine the output. A reused
  version number makes that promise false in a way no user could detect: two
  different artifacts would answer to the same version, and the referee who
  shares a seed would have no way to tell which one their reader ran.

Follow-up TODOs: none deferred within the constitution. Documents outside it
that repeat the superseded clause are tracked as FR-024 of
specs/005-release-publishing/spec.md.
-->

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
- Wherever compatibility with Cepheus Engine is claimed (the README, the
  public release page, the built package's own description), include the
  Compatibility-Statement License attribution ("Cepheus Engine and Samardan
  Press are the trademarks of Jason 'Flynn' Kemp") and a statement of
  non-affiliation. The obligation follows the claim, so any future
  publication surface that repeats the claim inherits it.

## Development Workflow

- **Python 3.13+** is the supported floor.
- Versioning is **CalVer in `YYYY.0M.INC1` format** (e.g. `2026.08.1`
  for the first release cut in August 2026, `2026.08.2` for the
  second). Because CalVer does not signal breaking changes, every
  release ships a changelog entry and breaking changes are flagged
  prominently there.
- A **release** is a tagged, immutable bundle published on the project's
  public source repository. It is triggered by pushing a version tag that
  agrees with the version declared in the project metadata, which remains
  the single authority; a disagreement aborts the release rather than
  shipping. The build and the full test run happen on a clean machine
  checked out at the tagged commit, never on a maintainer's working tree,
  and nothing is published unless the suite passes there. Each release
  carries both distribution formats, a plain checksum for each artifact, a
  signed provenance record binding each artifact to the commit and build
  that produced it, and the version's changelog entry as its announcement
  text. Publishing to a package index is the intended future channel; it is
  not the current one, and adding it requires a further amendment.
- A published version number is **spent and never reused**. A defect in a
  released version ships as the next increment, with a changelog entry
  stating what was wrong. The sole exception is a release attempt that
  failed before publishing anything, which by definition published nothing.
  This follows from Principle IV rather than from convention: a reused
  version number would make the seed-and-version promise false in a way no
  user could detect.

## Governance

This constitution supersedes all other practices. All PRs and reviews
verify compliance with its principles; complexity beyond the simplest
adequate solution must be justified against Principle VI. Amendments are
made via `/speckit-constitution`, documented with a version bump, the
amendment date, and a rationale. The constitution itself is versioned
with the same CalVer `YYYY.0M.INC1` scheme the project uses.

**Version**: 2026.08.2 | **Ratified**: 2026-08-11 | **Last Amended**: 2026-08-31
