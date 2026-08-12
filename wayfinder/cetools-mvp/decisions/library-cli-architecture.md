---
title: Library and CLI architecture
status: resolved
type: grilling
blocked-by: [ratify-constitution, pypi-package-name]
---

## Question

How is the package structured? One distribution containing a core
library plus a CLI entry point, or multiple distributions? What is the
CLI's command shape (single `cetools` command with subcommands per
generator?), which CLI framework (if any), and where is the boundary
between library API and CLI concerns (output formatting, seeds as
arguments, JSON vs human output)? Blocked by the constitution (whose
principles this must respect) and the package name research (which fixes
naming).

## Resolution

Resolved 2026-08-11 via grilling. Decided:

- **One distribution.** A single `cetools` package contains the
  importable library and its CLI entry point. A future web UI would be
  a separate package depending on this one. Splitting core from CLI now
  fails YAGNI (Principle VI).
- **`cetools` everywhere**: PyPI distribution name, import name, and
  CLI command are all `cetools`. Available on PyPI per
  [PyPI package name](pypi-package-name.md), and contains no Product
  Identity string per [SRD licensing](srd-licensing.md).
- **CLI framework: typer**, a deliberate exception to stdlib-first,
  justified under Principle VI as follows: typer derives the CLI from
  typed function signatures, keeping the CLI layer declarative and
  nearly logic-free (reinforcing Principle I), with generated help and
  shell completion; argparse would reimplement this as hand-written
  boilerplate that grows with every subcommand.
- **Command shape**: one `cetools` entry point with verb subcommands
  (`cetools npc`, `cetools roll`; later `cetools world`), matching
  typer's app/sub-app model.
- **Library/CLI boundary**: the library owns the data model, JSON
  serialization, and human-readable text rendering (character sheets as
  text); the CLI only parses arguments, calls the library, prints, and
  sets exit codes. Rendering is thus TDD-testable and reusable by any
  future consumer.
- **Seeds at the boundary** (consequence of Principle IV): every
  generator subcommand accepts `--seed`; when omitted, the
  freshly-drawn seed is included in both human and JSON output so any
  result can be regenerated.
