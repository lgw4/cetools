<!--
Sync Impact Report
Version change: 1.0.0 → 2026.07.1 (versioning scheme changed from SemVer to CalVer)

Modified principles:
  - I. CLI First, Logic Decoupled → II. CLI First, Logic Decoupled (renumbered; engine/cli
    import direction made explicit)
  - II. Test-First (NON-NEGOTIABLE) → III. Test-First (NON-NEGOTIABLE) (tightened: the failing
    test MUST be run and its failure observed before implementation)
  - IV. Simplicity → V. Simplicity (unchanged in substance)

Added sections:
  - I. Cepheus Engine SRD Fidelity (the domain authority and the HOUSE/SRD policy seam)
  - IV. Deterministic by Construction (the Rolls seam)
  - Versioning (CalVer YYYY.0M.INC1 for all artifacts, including this constitution)

Removed sections:
  - III. Code Quality (standalone principle): content preserved and expanded under
    Development Workflow and Quality Gates; pyflakes replaced by the real gate
    (isort, black, flake8, pytest, check_docs.py)
  - Development Toolchain, Project Structure: merged into Development Workflow and
    Quality Gates

Artifacts migrated with this amendment:
  - pyproject.toml: version 0.5.0 → 2026.07.1
  - uv.lock: relocked (records the PEP 440 normalized form, 2026.7.1)

Follow-up TODOs: None. No git tags existed at ratification, so pyproject.toml and uv.lock were
the only artifacts needing CalVer migration.
-->

# cetools Constitution

## Core Principles

### I. Cepheus Engine SRD Fidelity

The [Cepheus Engine SRD](https://evolvedexperiment.github.io/cepheus-srd/index.html) is the
authority on game rules. Rules tables MUST be transcribed as data, separate from the code that
consults them, and MUST be verified against the SRD text rather than against memory or another
implementation.

Any deliberate departure from the SRD MUST be a named, selectable policy rather than a silent
default: house rules live behind an explicit rules value (`HOUSE` versus `SRD`), and every
departure MUST be documented in user-facing prose where a referee will see it. An undocumented
divergence from the SRD is a defect.

**Rationale**: The value of this tool is that its output is trustworthy at the table. A referee
must be able to tell, for any surprising result, whether it came from the SRD or from cetools.

### II. CLI First, Logic Decoupled

Every capability MUST be reachable from the CLI, and the CLI MUST be a thin I/O binding: parse
arguments, call the engine, format output, choose an exit code. No game logic is permitted in
`src/cetools/cli/`.

The dependency direction is one-way and non-negotiable: `src/cetools/engine/` MUST NOT import
from `src/cetools/cli/`. Within the engine, a subpackage's `__init__.py` is its public surface,
and callers MUST import from the package rather than reaching into its modules.

**Rationale**: Decoupling keeps the engine usable as a library, keeps the logic testable without
a process boundary, and lets new front ends arrive without touching the rules.

### III. Test-First (NON-NEGOTIABLE)

Strict red-green TDD is mandatory. For every behavior change, in this order:

1. Write a test that specifies the desired behavior.
2. Run it and observe it fail, for the expected reason. A test that passes before the
   implementation exists is not evidence; diagnose it and fix the test.
3. Write the minimum implementation that makes it pass.
4. Run the suite green, then refactor with the suite still green.

Skipping step 2 is a violation even when the implementation is obvious. Tests MUST mirror the
source layout (`src/cetools/engine/foo.py` → `tests/test_foo.py`). Coverage of `src/cetools`
MUST NOT fall below 85%, and the full suite MUST pass before any change is considered complete.

**Rationale**: Observing the red is the only step that proves the test can fail, which is the
only thing that makes the green meaningful. In a rules engine, where an off-by-one in a table
produces plausible output, a test that never failed is indistinguishable from no test at all.

### IV. Deterministic by Construction

Every random decision the rules make MUST pass through the single `Rolls` seam in
`src/cetools/engine/rolls.py` and MUST be named in `RollName`. Direct use of the `random` module
outside that seam is prohibited in engine code.

Given the same seed and the same inputs, generation MUST produce identical output. Tests MUST
script rolls (`ScriptedRolls`) rather than seed a generator and assert on whatever emerges.

**Rationale**: One seam is what makes the rules both reproducible for users and specifiable by
tests. Reproducibility is a user-facing feature (`--seed`), so it is a correctness property
rather than a testing convenience.

### V. Simplicity

No abstraction, option, or pattern MUST be introduced beyond what the current task requires.
YAGNI applies at every level: three similar lines are preferable to a premature abstraction, and
a concrete function is preferable to a configurable one. Design for the requirement in hand, not
for a hypothetical successor.

**Rationale**: Premature abstraction accumulates complexity faster than it saves effort, and it
widens the surface under test, which makes Principle III more expensive to honour.

## Versioning

All versioned artifacts MUST use CalVer in `YYYY.0M.INC1` format:

- `YYYY` is the four-digit year.
- `0M` is the zero-padded month (`01` through `12`).
- `INC1` is an increment starting at `1`, resetting to `1` whenever the year or month changes.

Example progression: `2026.07.1`, `2026.07.2`, `2026.08.1`.

This applies to the package version in `pyproject.toml`, to release tags, and to this
constitution itself. Version numbers therefore carry no compatibility semantics: a breaking
change is communicated in the changelog and the commit history, not by the version number.
Amendments to this constitution are classified in the Sync Impact Report, which is where the
nature and scope of a change are recorded.

`YYYY.0M.INC1` is the authored form and is what MUST be written in `pyproject.toml`, in release
tags, and here. Python packaging will not preserve it: PEP 440 normalization strips leading
zeros from release segments, so `2026.07.1` and `2026.7.1` are the same version, and the
unpadded form is what appears in `uv.lock`, in wheel filenames, and from
`importlib.metadata.version`. This is expected and MUST NOT be "corrected" by unpadding the
authored version. Where a comparison must be exact, compare parsed versions rather than strings.

## Development Workflow and Quality Gates

Dependencies and project metadata are managed with `uv` via `pyproject.toml`. Setup is
`uv sync`, followed once per clone by `uv run pre-commit install --hook-type pre-push`.

The quality gate is these five commands, and all five MUST pass before a change is committed:

```bash
uv run isort . && uv run black . && uv run flake8 src tests && uv run pytest && uv run python scripts/check_docs.py
```

The pre-push hooks run the same gate, so a green local run and a green push are the same check.
`pytest` includes coverage measurement and fails below the 85% floor set by Principle III.

Documentation is part of the deliverable, not an afterthought. `scripts/check_docs.py` is the
only thing that tests the prose, which is why it is in the gate: it verifies that every
backticked symbol in the maintained docs resolves in the package, that the README's Python
examples still run, that the module map names every engine module, and that dashes are tight. A
rename MUST carry the docs that name it.

Commits and PR titles MUST follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).
A PR MUST contain one logical change and MUST be green on the gate before review.

## Governance

This constitution supersedes all other project conventions. A practice that conflicts with it
MUST be brought into compliance or carry an explicit, documented exception.

**Amendment procedure**:

1. Identify the principle or section to change and state the reason.
2. Assign the next CalVer version per the Versioning policy above.
3. Update this file and propagate the change to dependent templates and guidance files.
4. Record the change in the Sync Impact Report comment at the top of this file: version change,
   principles modified, sections added or removed, and any deferred follow-ups.

**Compliance review**: Every PR and every implementation plan MUST pass the Constitution Check
gate before implementation proceeds. Added complexity MUST be justified against Principle V in
the plan's Complexity Tracking section, and a rules change MUST cite the SRD passage it
implements per Principle I.

**Runtime guidance**: `AGENTS.md` (and `CLAUDE.md`, which includes it) carries the day-to-day
development guidance and MUST stay consistent with this constitution. Where the two disagree,
this constitution governs and `AGENTS.md` MUST be corrected.

**Version**: 2026.07.1 | **Ratified**: 2026-06-17 | **Last Amended**: 2026-07-29
