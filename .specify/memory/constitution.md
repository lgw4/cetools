<!--
SYNC IMPACT REPORT
==================
Version change: 0.0.0 (unfilled template) → 1.0.0 (initial ratification)

New sections added:
  - I. SRD-Fidelity (new)
  - II. Library-First (new)
  - III. CLI Interface (new)
  - IV. Test-First (new)
  - V. Data-Driven Extensibility (new)
  - Code Quality Standards (new)
  - Development Workflow (new)
  - Governance (populated)

Modified principles: N/A (initial ratification, no prior principles)
Removed sections: N/A

Templates reviewed:
  - .specify/templates/plan-template.md ✅ — Constitution Check section aligns with all five principles; no changes required
  - .specify/templates/spec-template.md ✅ — Generic structure; no constitution-specific references to update
  - .specify/templates/tasks-template.md ✅ — Generic structure; task categories (test-first, setup, foundational) align with TDD principle; no changes required
  - No commands/ directory present in .specify/templates/ — skipped

Follow-up TODOs: None. All placeholders resolved.
-->

# cetools Constitution

## Core Principles

### I. SRD-Fidelity

The Cepheus Engine SRD at https://evolvedexperiment.github.io/cepheus-srd/index.html is the sole
authoritative source for all game rules, tables, and terminology. Where the SRD is ambiguous,
the most common community interpretation MUST be used and documented in the feature's research.md.
Any deliberate deviation from SRD rules MUST be recorded in the plan's Constitution Check section
with a clear rationale. No rule-bending is allowed merely for implementation convenience.

### II. Library-First

All game logic (character generation, rule resolution, dice mechanics, data tables) MUST be
implemented in the engine library under `src/cetools/engine/`, with zero dependency on any
delivery layer (CLI, HTTP API, or otherwise). Engine modules MUST be importable and callable
directly without invoking any CLI or server. The same engine code MUST serve every current and
future delivery layer without modification.

### III. CLI Interface

The CLI (under `src/cetools/cli/`) is the primary delivery layer for the MVP. CLI modules MUST
contain only I/O routing: parse arguments → call library → write result to stdout (success) or
stderr (failure). No game logic belongs in CLI code. Exit codes MUST be consistent:
0 for success, 1 for user-facing failures (e.g., enlistment failure, character death).

### IV. Test-First (NON-NEGOTIABLE)

TDD is mandatory on all new code. The Red-Green-Refactor cycle MUST be followed strictly:

- Write tests that express the desired behavior.
- Confirm tests fail (red) before writing any implementation.
- Implement until tests pass (green).
- Refactor under passing tests.

Tests live in `tests/`, mirroring the package structure. Every new module or function MUST have
corresponding tests before the implementation is committed. The full test suite (`uv run pytest`)
MUST pass before any PR is opened.

### V. Data-Driven Extensibility

Game content (careers, rank tables, skill tables, mustering-out tables, aging tables) MUST be
expressed as data structures (e.g., frozen dataclasses, typed dicts) rather than as hardcoded
logic in the engine. The generation engine MUST accept a career data structure and operate on it
generically. Adding a new career MUST require only defining a new data structure instance — zero
changes to engine logic are permitted.

## Code Quality Standards

All code MUST conform to the following before any commit is pushed:

- **Formatter**: Black (`uv run black .`) — zero tolerance for unformatted code.
- **Linter**: flake8 (`uv run flake8 src tests`) — zero warnings.
- **Test suite**: `uv run pytest` — all tests green.
- **Python version**: 3.13+.
- **Dependency management**: `uv` exclusively; `pyproject.toml` is the single source of truth
  for all dependencies and project metadata. No `requirements.txt` files.

Complexity MUST be justified in the plan's Constitution Check section. The default posture is
simplicity: no abstractions introduced until a second concrete use case exists.

## Development Workflow

Each feature follows this sequence:

1. Spec (`/speckit-specify`) → clarified requirements and acceptance scenarios.
2. Plan (`/speckit-plan`) → architecture, Constitution Check gate, project structure.
3. Tasks (`/speckit-tasks`) → dependency-ordered task list.
4. Implement following TDD (Principle IV): test → fail → implement → green → refactor.
5. Quality gate: `uv run black . && uv run flake8 src tests && uv run pytest`.
6. PR with a Conventional Commits title (e.g., `feat: add X`, `fix: correct Y`).

The Constitution Check in each plan.md is a mandatory gate. A feature may not proceed to
implementation if it cannot demonstrate compliance with all five principles, or provide an
explicit justification for any variance.

## Governance

This constitution supersedes all informal practices. Amendments require:

1. A pull request updating this file with an incremented version per semantic versioning:
   MAJOR for principle removal or redefinition, MINOR for new principles or material guidance
   additions, PATCH for clarifications or wording fixes.
2. Updated Sync Impact Report in the HTML comment at the top of this file.
3. Review of all plan templates, spec templates, and task templates for alignment.

All PRs and code reviews MUST verify compliance with the five Core Principles. Complexity MUST
be justified; unexplained complexity is a constitution violation.

**Version**: 1.0.0 | **Ratified**: 2026-06-17 | **Last Amended**: 2026-06-17
