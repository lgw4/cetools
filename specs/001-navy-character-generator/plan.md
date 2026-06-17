# Implementation Plan: Navy Character Generator

**Branch**: `001-navy-character-generator` | **Date**: 2026-06-17 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-navy-character-generator/spec.md`

## Summary

Generate complete Cepheus Engine Navy characters from the CLI using a TDD-built library that faithfully implements every Navy career table from the CE SRD. The CLI command `cetools navy` is a thin Typer binding over a pure-Python library in `src/cetools/navy/`; all generation logic lives in that library and is fully testable in isolation.

## Technical Context

**Language/Version**: Python 3.11+ (per `pyproject.toml`; `uv` managed)

**Primary Dependencies**: Typer (CLI binding), standard library `random` (dice simulation)

**Storage**: N/A (no persistence; output to stdout only)

**Testing**: pytest via `uv run pytest`

**Target Platform**: macOS/Linux CLI

**Project Type**: CLI tool + library (logic fully decoupled per Constitution Principle I)

**Performance Goals**: Single character in under 5 seconds end-to-end (SC-001); 100 characters in one invocation without error (SC-003)

**Constraints**: No characteristic modification tracking complexity; max UPP hex digit is C (12) at initial roll, potentially D–F after Personal Development stat increases (see research.md §1)

**Scale/Scope**: Single-user CLI; no concurrency, no persistence

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Status | Evidence |
|---|---|---|
| I. CLI First, Logic Decoupled | **PASS** | All generation logic in `src/cetools/navy/`; Typer command in `src/cetools/cli.py` calls library functions only (FR-012) |
| II. Test-First (TDD) | **PASS** | Plan specifies red-green-refactor loop; all SRD tables in `tables.py` are independently importable and testable without CLI invocation |
| III. Code Quality | **PASS** | Black + flake8 required before every commit per AGENTS.md |
| IV. Simplicity | **PASS** | No patterns beyond what the spec requires; one module per concern; no abstract base classes or plugin registries |

**Result**: All gates pass. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/001-navy-character-generator/
├── plan.md              # This file
├── research.md          # Phase 0 output — SRD constants + resolved ambiguities
├── data-model.md        # Phase 1 output — entity definitions
├── quickstart.md        # Phase 1 output — validation guide
├── contracts/
│   └── cli.md           # Phase 1 output — CLI interface contract
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created by /speckit-plan)
```

### Source Code

```text
src/cetools/
├── cli.py               # Typer app — thin CLI binding only, no business logic
└── navy/
    ├── __init__.py
    ├── tables.py         # All SRD constants: checks, skill tables, rank titles, benefits
    ├── character.py      # Dataclasses: Character, CareerTerm, Benefit
    ├── generator.py      # Career simulation: roll characteristics, run terms, muster out
    └── formatter.py      # Human-readable and JSON output

tests/
├── navy/
│   ├── test_tables.py    # Verifies SRD constants are correct and well-formed
│   ├── test_character.py # UPP formatting, skill merging, to_json_dict
│   ├── test_generator.py # Career simulation with seeded RNG
│   └── test_formatter.py # Human-readable output format, JSON validity
└── test_cli.py           # CLI integration: exit codes, --count, --json flag
```

**Structure Decision**: Single-project layout (Option 1). The `navy/` subpackage isolates all Navy-specific logic so future careers can be added as sibling subpackages without touching existing code.

## Complexity Tracking

> No Constitution violations. Section left intentionally empty.
