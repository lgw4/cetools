# Implementation Plan: Scout Career & Career Selection Flag

**Branch**: `002-scout-career-character` | **Date**: 2026-06-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-scout-career-character/spec.md`

## Summary

Add the Scout career as a pure data structure and wire the `--career` CLI flag with a qualification re-roll loop (engine) and a draft fallback (engine). Per-career term-processing logic in `generate_character` requires zero changes for Scout; the existing `commission_stat=None` path already yields two skill rolls per term.

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: typer ≥0.15 (CLI); pytest ≥8, black, flake8 (dev)

**Storage**: N/A — stateless generation, no persistence

**Testing**: pytest with branch coverage (85% floor), black (line-length 99), flake8

**Target Platform**: Cross-platform CLI (macOS/Linux)

**Project Type**: Library + CLI

**Performance Goals**: N/A — single-character generation runs in milliseconds

**Constraints**: No new `Career` dataclass fields (FR-001); no per-career term-processing logic changes (FR-001); 85% coverage floor enforced by CI

**Scale/Scope**: Two careers (Navy, Scout); six-entry draft table; extensible registry for future careers

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| §I SRD-Fidelity | **PASS with documented deviation** | Scout data matches SRD. FR-015 imposes a hard 7-term cap where the SRD allows forced re-enlistment on a natural-12; deviation documented in spec clarification CHK043 and in Complexity Tracking below. |
| §II Library-First | **PASS** | Re-roll loop, draft table, career registry, and all Scout data live in `src/cetools/engine/`. CLI contains only I/O routing. |
| §III CLI Interface | **PASS** | `character.py` adds `--career` flag: strip/lowercase → validate → call engine → write stdout/stderr. Exit codes 0 and 1 only. |
| §IV Test-First | **PASS** | SC-004 mandates red-first tests for three functions before any implementation is committed. Tasks enforce this sequence. |
| §V Data-Driven Extensibility | **PASS** | Scout is a pure `Career` data structure instance. The engine processes it generically. `registry.py` provides the extensible career map; adding a new career requires only a new data structure and a registry entry. |

## Project Structure

### Documentation (this feature)

```text
specs/002-scout-career-character/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── cli.md           # CLI command contract
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/cetools/
├── engine/
│   ├── careers/
│   │   ├── __init__.py        (update: re-export registry symbols)
│   │   ├── base.py            (unchanged)
│   │   ├── navy.py            (unchanged)
│   │   ├── scout.py           (NEW: SCOUT_CAREER data structure)
│   │   └── registry.py        (NEW: CAREER_REGISTRY dict + DRAFT_TABLE tuple)
│   ├── generator.py           (update: add roll_until_qualified, generate_career_character,
│   │                                   draft_character; add hard_max_terms param)
│   └── models.py              (update: add drafted: bool = False to Character)
├── cli/
│   └── character.py           (update: add --career option, call new engine entry points)
└── formatter.py               (update: render "(Drafted)" when character.drafted is True)

tests/
├── test_careers.py            (update: add Scout career data validation tests)
├── test_generator.py          (update: add roll_until_qualified, generate_career_character,
│                                        draft_character, hard_max_terms tests)
├── test_cli.py                (update: add --career flag tests, draft default tests)
├── test_formatter.py          (update: add drafted=True rendering test)
└── test_models.py             (update: add Character.drafted default test)
```

**Structure Decision**: Single-project layout (existing). New source files are two new modules in `src/cetools/engine/careers/` (scout.py, registry.py). All engine additions live in the engine package; CLI and formatter receive minimal updates. No new test files are required; all new tests slot into existing mirror files.

## Complexity Tracking

| Item | Why Needed | Simpler Alternative Rejected Because |
|------|------------|--------------------------------------|
| `hard_max_terms: bool = False` param on `generate_character` | FR-015 requires Scout to enforce a hard 7-term cap; natural-12 re-enlistment at term 7 must not grant an 8th term. | Adding a `Career` field would violate FR-001. Duplicating `generate_character` for Scout would violate §V Data-Driven Extensibility. Inferring from `commission_stat is None` would be an undocumented side-channel. A named boolean parameter is the simplest explicit solution that keeps the engine generic. |
| `preset_characteristics` + `bypass_qualification` params on `generate_character` | The re-roll loop in `roll_until_qualified` generates qualifying characteristics externally; `generate_character` must accept them and skip the enlistment roll. | The alternative (re-implementing the full term loop in a separate function) would duplicate ~100 lines of logic. |
| `drafted: bool = False` field on `Character` | The formatter and output contract require `"(Drafted)"` in the career line for draft-assigned characters (FR-011). | The alternative (pass drafted as a separate parameter to the formatter) would break the `Character` value-object contract and leak presentation decisions into call sites. |
