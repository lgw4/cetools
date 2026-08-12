---
title: Ratify the constitution
status: resolved
type: grilling
blocked-by: []
---

## Question

Fill in and ratify `.specify/memory/constitution.md`, currently an
unfilled template. The charting session already settled likely
principles to encode: library-first (CLI as thin consumer), text/JSON
in-out, data-file-driven rules content, seed-reproducible generation.
Open with the user: testing discipline (is TDD non-negotiable?),
versioning policy, and simplicity/YAGNI stance. Run
`/speckit-constitution` with the user to produce it.

## Resolution

Ratified 2026-08-11 as
[`.specify/memory/constitution.md`](../../../.specify/memory/constitution.md)
version 2026.08.1, via a grilling session. The constitution itself is
versioned with the same CalVer scheme as the project. Decided:

- **Six core principles**: Library-First (CLI as thin consumer), CLI
  Text I/O Protocol (args/stdin to stdout, errors to stderr, human +
  JSON output), Test-First (TDD non-negotiable, red-green-refactor),
  Seed-Reproducible Generation, Data-Driven Rules Content, and
  Simplicity (YAGNI plus stdlib-first dependency minimalism).
- **No quality gates beyond tests**: lint/format/type-check tooling is
  permitted but not constitutionally mandated.
- **Code license: GPL-3.0.** Shipped SRD-derived data remains OGL 1.0a
  Open Game Content (it cannot be sublicensed); the constitution's
  Licensing & Distribution Constraints section encodes the OGL
  obligations from [SRD licensing](srd-licensing.md).
- **Versioning: CalVer `YYYY.0M.INC1`** (e.g. `2026.08.1`); breaking
  changes flagged in the changelog since CalVer does not signal them.
- **Python floor: 3.13+.** Releases publish to PyPI.

This unblocks [Library and CLI architecture](library-cli-architecture.md),
whose other blocker ([PyPI package name](pypi-package-name.md)) was
already resolved.
