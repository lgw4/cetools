# Implementation Plan: Universal Character Format Output

**Branch**: `006-universal-character-format` | **Date**: 2026-07-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/006-universal-character-format/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Replace the current multi-section character printout with the community-standard Universal
Character Format (UCF): rank+name/UPP/age, career+terms+funds, alphabetical skills, and an
optional equipment line — nothing else. This requires one new piece of data (a randomly generated
character name, drawn from two new data tables) and a full rewrite of `format_character`; no
existing generation mechanics change (FR-010).

## Technical Context

**Language/Version**: Python 3.13+ (existing, per constitution)

**Primary Dependencies**: `typer` (existing CLI dependency; no new dependencies needed)

**Storage**: N/A — in-memory data tuples, same convention as existing career/skill tables

**Testing**: pytest + pytest-cov (existing; suite must stay ≥85% coverage on `src/cetools`)

**Target Platform**: Cross-platform CLI (local Python execution, existing `cetools` entry point)

**Project Type**: Single project — existing `src/cetools/{engine,cli}` + `formatter.py` layout

**Performance Goals**: N/A — in-memory list lookups and string formatting, no measurable
performance surface beyond the existing dice-roll-driven generator

**Constraints**: Must not alter any existing characteristic, career, or benefit mechanic
(FR-010); output must match the UCF grammar exactly (see contracts/ucf-output.md)

**Scale/Scope**: Small — one new data module (`engine/names.py`, two tuples), one new field on
`Character`, one new call in `generate_character`, a full rewrite of `format_character` (~40
lines → ~15 lines)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment |
|---|---|
| I. SRD-Fidelity | UCF field order/template verified directly against the cited SRD page (research.md). One ambiguous point (field delimiter within a line) resolved to tab-separated segments per the SRD's own template rendering, documented in research.md with rationale. PASS. |
| II. Library-First | Name generation lives in `engine/names.py` and is invoked from `engine/generator.py` (both under `src/cetools/engine/`), with zero CLI dependency. `formatter.py` remains a plain presentation function at `src/cetools/formatter.py` (not CLI code), callable directly — same location/shape as today. PASS. |
| III. CLI Interface | `cli/character.py` is untouched: still parse → call library → echo result/error. PASS. |
| IV. Test-First | Tasks phase will add failing tests first for `names.py`, the `Character.name` field, the `generate_character` name-assignment behavior, and the rewritten `format_character`, before any implementation. PASS (enforced at task level). |
| V. Data-Driven Extensibility | `FIRST_NAMES`/`LAST_NAMES` are plain data tuples in `names.py`; adding a name requires zero logic changes, mirroring `careers/*.py`. PASS. |

No violations — Complexity Tracking section is not needed.

## Project Structure

### Documentation (this feature)

```text
specs/006-universal-character-format/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/cetools/
├── engine/
│   ├── models.py          # MODIFIED: Character gains `name: str`
│   ├── generator.py       # MODIFIED: assigns character.name near the end of generate_character
│   ├── names.py           # NEW: FIRST_NAMES, LAST_NAMES tuples + generate_name(roller)
│   └── careers/           # unchanged
├── cli/
│   └── character.py       # unchanged
└── formatter.py           # MODIFIED: rewritten to emit the UCF line set

tests/
├── test_models.py         # MODIFIED: Character fixtures gain a name
├── test_generator.py      # MODIFIED: assert character.name is assigned
├── test_names.py          # NEW: generate_name unit tests
├── test_formatter.py       # MODIFIED: replaced with UCF-shape assertions
└── test_cli.py             # MODIFIED: fixtures/assertions updated for UCF output
```

**Structure Decision**: Existing single-project layout (`src/cetools/{engine,cli}` +
top-level `formatter.py`, tests mirroring under `tests/`) is unchanged. This feature adds one
new engine module (`names.py`) and modifies four existing files; no new top-level directories.

## Complexity Tracking

*No violations — table intentionally omitted.*
