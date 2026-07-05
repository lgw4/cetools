# Implementation Plan: Survival Mishaps Instead of Character Death

**Branch**: `007-survival-mishaps` | **Date**: 2026-07-05 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/007-survival-mishaps/spec.md`

## Summary

Today, a failed term survival roll returns a `GenerationFailure` ("character died")
and generation produces no character. This feature replaces that path with the
Cepheus Engine SRD's optional Survival Mishaps table: a new
`resolve_survival_mishap` engine function rolls 1D6 against a data-driven
`SURVIVAL_MISHAPS_TABLE`, applies an SRD `INJURY_TABLE` reduction where called for
(never allowing a characteristic to reach 0 without recovery — an injury crisis
converts that into debt instead), forces immediate career end for that term (2
years of age instead of 4, no reenlistment, no benefit roll for the term), and
forfeits mustering-out benefits and pension for the two dishonorable-discharge
outcomes. The resulting `MishapOutcome` and any incurred `debt` are attached to the
existing `Character` record so every generation path (direct, drafted) always
produces a complete, legible character — never an unrecoverable failure — and the
CLI's plain-text output gains one new conditional line describing the outcome.

## Technical Context

**Language/Version**: Python 3.13+ (existing project requirement, `pyproject.toml`)

**Primary Dependencies**: None new. Existing: `typer>=0.15` (CLI only); the engine
itself has zero runtime dependencies beyond the standard library.

**Storage**: N/A — in-memory dataclasses only, no persistence layer exists or is
needed.

**Testing**: `pytest` (existing), with `tests/conftest.py`'s deterministic roller
doubles (`ConstantRoller`, `SmartRoller`, `SequenceRoller`) for controlled outcomes,
plus one statistical test using `RandomDiceRoller` over a large sample for SC-004.

**Target Platform**: Cross-platform CLI (existing) — no platform-specific concerns
introduced.

**Project Type**: Single library + thin CLI (existing structure; no new project
type introduced).

**Performance Goals**: N/A beyond existing generation performance — mishap
resolution adds at most 2-3 extra dice rolls to a generation that already performs
many; no measurable performance requirement changes.

**Constraints**: Must not introduce a referee/interactive prompt (SRD gates this
rule behind referee approval; approval is always assumed per the spec's
Assumptions — this is the only behavior, not a toggle). Must not change the
behavior of enlistment/qualification failures (FR-012, `GenerationFailure` remains
for that path only).

**Scale/Scope**: One new engine module (`mishaps.py`, two static tables + one
resolver function + one result type), two new fields on `Character`, targeted
edits to the term loop in `generator.py`, and one new conditional output line in
`formatter.py`. No new CLI commands or flags.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design below.*

| Principle | Check | Status |
|---|---|---|
| I. SRD-Fidelity | Survival Mishaps and Injury tables sourced verbatim from the constitution's authoritative SRD URL (`research.md`). Every ambiguous point (D1–D6) is documented with rationale and the simplest/no-referee-context interpretation, per Principle I's requirement. | PASS |
| II. Library-First | All new logic (`resolve_survival_mishap`, `MishapEntry`, `InjuryEntry`, `MishapOutcome`) lives in `src/cetools/engine/`, zero dependency on `typer`/CLI. Directly importable/callable per `contracts/mishaps-engine-api.md`. | PASS |
| III. CLI Interface | `cli/character.py` requires **no logic change** — a mishap-affected character is still a `Character`, still routed through the existing `isinstance(result, Character)` success branch, still exit code 0. Only `formatter.py` (a library module, not CLI) gains the new output line. Note: Principle III's own text names "character death" as an exit-1 example; this is now stale and flagged as a required constitution wording follow-up (see `research.md`), not a code change of this feature. | PASS (with documented constitution follow-up) |
| IV. Test-First | Plan requires new failing tests before implementation: `tests/test_mishaps.py` (table correctness, injury resolution, crisis handling, SC-004 distribution) and updates to `tests/test_generator.py`, `tests/test_cli.py`, `tests/test_marine_career.py`/other career tests, and `tests/test_formatter.py` — written red before the corresponding implementation, per Principle IV. Enumerated in Phase 2 (`/speckit-tasks`). | PASS |
| V. Data-Driven Extensibility | Both new tables (`SURVIVAL_MISHAPS_TABLE`, `INJURY_TABLE`) are frozen-dataclass tuples indexed by roll, mirroring `Career`/`RankEntry` — explicitly *not* replicating `_apply_aging`'s hardcoded if/elif style. | PASS |

No violations requiring the Complexity Tracking table.

## Project Structure

### Documentation (this feature)

```text
specs/007-survival-mishaps/
├── plan.md              # This file
├── research.md          # Phase 0 output — SRD text + 7 documented decisions
├── data-model.md        # Phase 1 output — MishapEntry, InjuryEntry, MishapOutcome, Character extension
├── quickstart.md        # Phase 1 output — 7 runnable validation scenarios
├── contracts/
│   ├── mishaps-engine-api.md   # resolve_survival_mishap contract
│   └── mishap-output.md        # format_character output grammar extension
└── tasks.md             # Phase 2 output (/speckit-tasks — not created by /speckit-plan)
```

### Source Code (repository root)

```text
src/cetools/
├── engine/
│   ├── mishaps.py           # NEW: MishapEntry, InjuryEntry, SURVIVAL_MISHAPS_TABLE,
│   │                        #      INJURY_TABLE, resolve_survival_mishap()
│   ├── models.py            # MODIFIED: + MishapOutcome dataclass; Character gains
│   │                        #            `mishap` and `debt` fields
│   ├── generator.py         # MODIFIED: term loop's survival-failure branch now calls
│   │                        #            resolve_survival_mishap() instead of returning
│   │                        #            GenerationFailure; age/terms_served/benefit/
│   │                        #            pension bookkeeping per data-model.md
│   ├── dice.py               # UNCHANGED: DiceRoller protocol reused as-is
│   └── careers/              # UNCHANGED: no career-specific changes
├── formatter.py              # MODIFIED: + conditional "Mishap: ..." output line
└── cli/                      # UNCHANGED: no CLI logic changes required

tests/
├── test_mishaps.py           # NEW: table shape, injury resolution incl. "roll twice,
│                              #      take worse", crisis handling, SC-004 distribution
├── test_generator.py         # MODIFIED: replace death-path test with mishap-path
│                              #           assertions; add per-outcome integration tests
├── test_cli.py                # MODIFIED: repurpose the 3 stale "survival failure" tests
│                              #           to exercise enlistment-failure wording instead
├── test_marine_career.py      # MODIFIED: remove/replace "either Character or
│   (and similar career tests) #           GenerationFailure w/ 'survival check' reason"
│                              #           tolerant assertions — survival can no longer fail
└── test_formatter.py          # MODIFIED: + tests for the new Mishap output line
```

**Structure Decision**: No new projects or directories beyond one new engine
module (`src/cetools/engine/mishaps.py`) and its mirrored test file
(`tests/test_mishaps.py`), consistent with the existing single-package
library+CLI layout (`AGENTS.md`) and Principle II. This mirrors how career data
already lives in dedicated modules under `engine/careers/` — `mishaps.py` is the
non-career-specific SRD-table counterpart.

## Complexity Tracking

*No violations — table intentionally empty.*
