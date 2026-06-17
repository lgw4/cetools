<!--
Sync Impact Report
Version change: new → 1.0.0
Added sections: Core Principles (I–IV), Development Toolchain, Project Structure, Governance
Removed sections: N/A (initial version)
Templates requiring updates:
  ✅ plan-template.md — Constitution Check gates are placeholder-driven per feature; no update needed
  ✅ spec-template.md — No constitution-specific references; no update needed
  ✅ tasks-template.md — "Tests are OPTIONAL" language updated to reflect mandatory TDD (Principle II)
Follow-up TODOs: None
-->

# cetools Constitution

## Core Principles

### I. CLI First, Logic Decoupled

All features MUST be accessible via a CLI interface. Application logic MUST reside
in standalone modules under `src/cetools/` that are fully independent of the CLI layer.
CLI entry points MUST act as thin bindings that call into library functions only;
no business logic is permitted in CLI handlers.

**Rationale**: Decoupling enables independent testing of logic, reuse across interfaces,
and flexibility to add new entry points (scripts, APIs) without refactoring core logic.

### II. Test-First (NON-NEGOTIABLE)

TDD is mandatory. Tests MUST be written before implementation code. The
Red-Green-Refactor cycle MUST be followed:

1. Write a failing test specifying the desired behavior.
2. Confirm the test fails.
3. Implement the minimum code to make it pass.
4. Refactor while keeping tests green.

All new code MUST have corresponding tests in `tests/`, mirroring the source
structure (e.g., `src/cetools/foo.py` → `tests/test_foo.py`). The full suite
MUST pass before any change is considered complete.

**Rationale**: Test-first development prevents regressions, documents intent, and
enforces the decoupling required by Principle I—logic that cannot be tested in
isolation violates both principles simultaneously.

### III. Code Quality

All code MUST be formatted with Black and MUST pass flake8 linting with zero
errors. Both checks MUST run and pass before finishing any change:

```bash
uv run black .
uv run flake8 src tests
```

**Rationale**: Consistent formatting eliminates style debates; static analysis
catches common errors early without a full test run.

### IV. Simplicity

No abstractions, features, or patterns MUST be introduced beyond what the current
task requires. YAGNI (You Aren't Gonna Need It) applies at every level. Three
similar lines is preferable to a premature abstraction. Design for the current
requirement, not hypothetical future ones.

**Rationale**: Premature abstractions accumulate complexity faster than they save
effort and make TDD harder by widening the surface under test.

## Development Toolchain

Dependencies and project metadata are managed with `uv` via `pyproject.toml`.

- **Setup**: `uv sync` (installs project and all dev dependencies into `.venv`)
- **Tests**: `uv run pytest`
- **Format**: `uv run black .`
- **Lint**: `uv run flake8 src tests`
- **Pre-commit gate**: `uv run black . && uv run flake8 src tests && uv run pytest`

All toolchain commands MUST pass before a change is committed.

## Project Structure

```
src/cetools/    Application logic modules (no CLI code permitted here)
tests/          Test suite mirroring src/cetools/ structure
```

CLI entry points live outside core logic modules. Any exception requires documented
justification in the Complexity Tracking section of the implementation plan.

## Governance

This constitution supersedes all other project conventions. Any practice that
conflicts with it MUST be updated to comply or have an explicit exception documented.

**Amendment procedure**:
1. Identify the principle or section to change.
2. Increment the version per the versioning policy below.
3. Update this file and propagate changes to dependent templates.
4. Record the amendment rationale in the Sync Impact Report comment.

**Versioning policy**:
- MAJOR: Backward-incompatible governance change (principle removed or fundamentally redefined).
- MINOR: New principle or section added, or materially expanded guidance.
- PATCH: Clarifications, wording fixes, non-semantic refinements.

**Compliance review**: All PRs and implementation plans MUST pass the Constitution
Check gate before proceeding to implementation.

**Version**: 1.0.0 | **Ratified**: 2026-06-17 | **Last Amended**: 2026-06-17
