# Implementation Plan: Aerospace System Defense Career

**Branch**: `003-aerospace-system-defense` | **Date**: 2026-06-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-aerospace-system-defense-career/spec.md`

## Summary

Add the Aerospace System Defense career to cetools by defining a new `Career` dataclass instance
(`AEROSPACE_CAREER`) in the engine, registering it in the career registry, fixing the draft
table so roll 1 assigns Aerospace, and updating the CLI with hyphen-to-space normalization,
"did you mean" error suggestions, and enumerated help text — all without touching engine logic.

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: typer (CLI), dataclasses (stdlib), difflib (stdlib — `get_close_matches`
for "did you mean" suggestions)

**Storage**: N/A

**Testing**: pytest with `--cov`, minimum 85% coverage

**Target Platform**: macOS/Linux CLI

**Project Type**: Library (`src/cetools/engine/`) + CLI (`src/cetools/cli/`)

**Performance Goals**: N/A (interactive single-character generation)

**Constraints**: Coverage ≥ 85%; zero changes to engine generation logic (Constitution §V)

**Scale/Scope**: One new module, three file edits, test additions

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| §I SRD-Fidelity | PASS | All tables in FR-002–FR-005 match SRD exactly; one deviation documented in research.md (material benefit table length) |
| §II Library-First | PASS | `AEROSPACE_CAREER` lives in `engine/careers/aerospace.py`; no game logic enters CLI code |
| §III CLI Interface | PASS | CLI changes are I/O-only: hyphen normalization, error message, help text — all pure string manipulation with no game logic |
| §IV Test-First | MANDATORY | All new code requires failing tests before implementation; full suite must be green before PR |
| §V Data-Driven Extensibility | PASS | Adding Aerospace requires only a new `Career` instance and a registry key — zero engine changes |

**Complexity Tracking**: No violations requiring justification. The "did you mean" logic
(`difflib.get_close_matches`) is a single stdlib call in the CLI error path.

## Project Structure

### Documentation (this feature)

```text
specs/003-aerospace-system-defense-career/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── cli-career-flag.md
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/cetools/
├── engine/
│   └── careers/
│       ├── base.py          # unchanged — Career + RankEntry dataclasses
│       ├── navy.py          # unchanged
│       ├── scout.py         # unchanged
│       ├── aerospace.py     # NEW — AEROSPACE_CAREER instance
│       └── registry.py      # EDIT — add aerospace key, fix DRAFT_TABLE index 0
└── cli/
    └── character.py         # EDIT — hyphen normalization, "did you mean", help text

tests/
├── test_aerospace_career.py # NEW — field-level validation of AEROSPACE_CAREER
├── test_careers.py          # EDIT — update test_draft_table_other_entries_are_navy
└── test_cli.py              # EDIT — update exact error message test + add Aerospace tests
```

**Structure Decision**: Single-project layout (Option 1). The engine/careers/ subdirectory
already houses per-career modules; `aerospace.py` is an exact peer of `navy.py` and `scout.py`.

## Implementation Notes

### Draft table correction

The current `DRAFT_TABLE` in `registry.py` is:

```python
("navy", "navy", "navy", "navy", "scout", "navy")
```

The SRD assigns roll 1 (index 0) to Aerospace System Defense. Index 0 must be changed to
`"aerospace system defense"`. The existing test `test_draft_table_other_entries_are_navy`
asserts that all non-index-4 entries are "navy" — it must be updated to allow index 0 to be
`"aerospace system defense"` while indices 1, 2, 3, and 5 remain "navy".

### CLI changes scope

Three targeted changes to `cli/character.py`, all I/O-only (Constitution §III):

1. **Hyphen normalization** (FR-007): `career.strip().lower().replace("-", " ")` before lookup.
2. **"Did you mean" error** (FR-009): Use `difflib.get_close_matches(normalized, CAREER_REGISTRY, n=1, cutoff=0.6)`. If a match is found, emit `"Unknown career '<input>'. Did you mean: <canonical name>?"`. If no match, emit `"Unknown career '<input>'. Valid careers: <comma-separated list>"`.
3. **Help text** (FR-010): Pass `help=` to `typer.Option` to enumerate valid canonical career names derived from the registry, e.g., `"Aerospace System Defense, Navy, Scout"`.

The exact error-message test in `test_cli.py` (`test_career_unknown_stderr_message_exact`)
currently asserts the old format; it will be updated to match the new "did you mean" format.

### Material benefits table length

The Aerospace material benefits table has 7 entries (rolls 1–7 including the rank 5+ DM).
`SCOUT_CAREER.material_benefits` has only 6 entries (no 7th row in the Scout SRD table).
The Aerospace table matches `NAVY_CAREER` in length (7). No engine change is needed —
`_muster_out` uses `len(career.material_benefits) - 1` as the cap, which handles variable lengths.
