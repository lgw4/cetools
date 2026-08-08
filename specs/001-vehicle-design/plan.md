# Implementation Plan: Vehicle Design System

**Branch**: `001-vehicle-design` | **Date**: 2026-08-07 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-vehicle-design/spec.md`

## Summary

A new `vehicles` domain implementing the Cepheus Engine Vehicle Design System construction rules,
sibling to `ships` and importing nothing from it. The forty construction tables ship as data; one
builder applies them in the SRD's own order and is the single authority on the rules; a description
renderer prints the Universal Vehicle Description Format paragraph and, on request, the component
table beneath it. Fifteen published vehicles ship as authored TOML installed with the package,
addressable by name, and are re-derived by that same builder rather than transcribed. Every figure
the book prints for them is transcribed too, so a disagreement is caught by a test rather than by
a reader, and every disagreement is recorded on a new `DIVERGENCES.md` that joins the quality gate.
Generation rolls a role first and fills each category from that role's loadout profile, seeded
through the existing `Rolls` seam so a seed and a set of constraints reproduce byte for byte.

The technical approach is deliberately imitative: `ships` already solved the shape of this problem
across nine modules and about 6,300 lines, and every convention it settled—frozen dataclasses
validated from `__post_init__`, tables as annotated module constants with no logic, bare
`ValueError` with the offending value named, a slot-per-sentence description renderer, a mutable
budget ledger recording what it could not honor—carries over unchanged. Three things are genuinely
new: shipping data files with the package, a role-driven generator, and a documentation page inside
the docs check.

## Technical Context

**Language/Version**: Python 3.13 (`requires-python = ">=3.13"`)

**Primary Dependencies**: `typer>=0.15` (CLI only). Standard library otherwise: `tomllib` for
reading design files, `importlib.resources` for reading the installed catalog, `random` behind the
`Rolls` seam. No new third-party dependency.

**Storage**: Files. Design files are TOML the referee owns; the catalog is fifteen TOML files
installed under `src/cetools/engine/vehicles/catalog/`. No database, no state.

**Testing**: pytest with `pytest-cov` and `pytest-timeout`; `--cov-fail-under=85`, `--timeout=30`.
Tests mirror the source layout, one file per module. Determinism is tested with `ScriptedRolls` for
outcomes and `RecordingRolls` for arguments, plus a pinned seeded baseline in
`tests/data/baseline/vehicle_designs.json`.

**Target Platform**: Cross-platform CLI and importable library; no platform-specific code.

**Project Type**: Single project, library-first with a thin CLI over it.

**Performance Goals**: None stated and none needed. A build is table lookups and arithmetic over
tens of components; generation is one pass. The only figure worth watching is the suite's
30-second per-test timeout against multi-thousand-seed determinism sweeps, which ships already
lives inside.

**Constraints**: Determinism is a correctness property, not a convenience: one seed and one set of
constraints must give byte-identical output. Floats throughout, rounded only at the display edge.
The `vehicles` package must not import from `ships`. The five-command quality gate must pass, and
this change widens it by adding a fourth maintained document.

**Scale/Scope**: 40 tables; 15 catalog vehicles; ten engine modules plus one CLI module; three
commands. Comparable ships work is ~6,300 lines across nine modules, and `tables.py` alone is
expected at 2,000 to 2,500 lines because two 24×12 drive-performance matrices and a 76-row weapon
table dominate it. This is a large single pull request by explicit, reaffirmed decision in the spec.

## Constitution Check

*GATE: evaluated before Phase 0, re-evaluated after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I. SRD Fidelity | Rules tables transcribed as data, separate from consuming code, verified against the SRD text | **PASS.** `tables.py` holds all forty tables and no logic. Every table was inventoried against the raw SRD HTML in Phase 0, not from memory. |
| I. SRD Fidelity | Deliberate departures are a named, selectable policy, documented where a referee sees them | **PASS with a documented exception.** FR-019 declines the policy switch because these are errata in worked examples, not departures from the rules. The documentation obligation is discharged in full by `DIVERGENCES.md` and enforced by the gate. See Complexity Tracking. |
| II. Library-First, CLI-Thin | Every capability a library function; no game logic in `cli/` | **PASS.** `cli/vehicle.py` parses arguments, calls the engine, formats output, picks an exit code. FR-027's ban on a wizard is what keeps it near 200 lines. |
| II. Library-First, CLI-Thin | `engine/` must not import from `cli/`; a subpackage's `__init__.py` is its public surface | **PASS.** `vehicles/__init__.py` is imports and an explicit `__all__`, no logic, as ships is. |
| III. Test-First | Red-green TDD, tests mirror source layout, coverage floor of 85% treated as a floor | **PASS.** One test module per source module. SC-006 goes further than the floor: every table row no catalog vehicle and no generation path exercises needs a test that fails when that row's values are altered. |
| IV. Deterministic by Construction | Every random decision through `Rolls`, named in `RollName`; no bare `random` in engine code | **PASS.** Seventeen new `VEHICLE_*` members. The role draw goes first because it decides every later pool. |
| IV. Deterministic by Construction | Same seed and inputs give identical output; tests script rolls rather than seeding and asserting | **PASS.** `ScriptedRolls` for outcomes, `RecordingRolls` where the arguments are the rule under test, plus a pinned baseline. |
| V. Simplicity | No abstraction beyond what the task requires | **PASS with one justified addition.** The role and loadout-profile concept is new machinery ships explicitly declined. See Complexity Tracking. |
| Workflow | Five-command gate green before commit; Conventional Commits; one logical change per PR | **PASS.** The gate itself changes: `DIVERGENCES.md` joins the maintained documents and a rebuild check joins `scripts/check_docs.py`. |

**Post-Phase-1 re-evaluation**: unchanged; the design added no new violation. The one thing worth
re-stating after the data model was written is that `published.py` puts transcribed SRD figures in
the package rather than in `tests/`. That is Principle I applied consistently—transcribed data is
data—and it is also what lets the docs check import those figures without reaching into the test
tree.

## Project Structure

### Documentation (this feature)

```text
specs/001-vehicle-design/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── cli.md           # command surface, exit codes, stream discipline
│   ├── design-file.md   # the TOML design file schema
│   └── library.md       # the vehicles package public surface
├── checklists/
│   └── requirements.md  # spec quality checklist
└── tasks.md             # Phase 2 output (/speckit-tasks, not created here)
```

### Source Code (repository root)

```text
src/cetools/
├── cli/
│   ├── main.py                    # + one import, one add_typer, callback docstring
│   └── vehicle.py                 # NEW: build, generate, catalog
└── engine/
    ├── rolls.py                   # + seventeen VEHICLE_* RollName members
    └── vehicles/                  # NEW domain
        ├── __init__.py            # public surface, explicit __all__
        ├── tables.py              # the forty construction tables; no functions
        ├── models.py              # VehicleDesign, Vehicle, component fits, enums
        ├── design.py              # TOML load and dump; shape validation only
        ├── builder.py             # build_vehicle: the authority on the rules
        ├── prose.py               # number, list and article primitives
        ├── description.py         # UVDF paragraph and component table
        ├── generator.py           # roles, constraints, seeded generation
        ├── catalog.py             # the installed designs, by name
        ├── published.py           # the fifteen published stat blocks, transcribed
        └── catalog/               # fifteen authored TOML design files
            ├── air-raft.toml
            └── ...                # fourteen more

tests/
├── test_vehicle_tables.py
├── test_vehicle_models.py
├── test_vehicle_design.py
├── test_vehicle_builder.py
├── test_vehicle_prose.py
├── test_vehicle_description.py
├── test_vehicle_generator.py
├── test_vehicle_catalog.py        # builds all fifteen, compares every published figure
├── test_cli.py                    # + a `cetools vehicle` section
└── data/baseline/
    └── vehicle_designs.json       # pinned seeded output

scripts/check_docs.py              # + DIVERGENCES.md in the maintained set, + rebuild check
DIVERGENCES.md                     # NEW maintained document
README.md                          # + vehicle section and examples
CONTRIBUTING.md                    # + vehicles/ in the module map
AGENTS.md                          # + the docs check's description names the new page
```

**Structure Decision**: single project, mirroring the `engine/<domain>/` layout that `ships/` and
`worlds/` established. `vehicles/` is a subpackage rather than a top-level `engine/vehicles.py`,
which matches ships and keeps it out of the module-map check's mandatory set while still being
listed in CONTRIBUTING.md's tree by convention. The catalog is package data under the domain that
owns it; hatchling already includes non-Python files under `src/cetools`, so `pyproject.toml` needs
no change.

## Phase 0: Research

Complete. See [research.md](./research.md): thirteen decisions, plus three factual corrections to
the spec that surfaced while verifying it against the SRD.

The three corrections, because they matter to whoever reads the spec next:

- **C-001**: the fifteen published vehicles are in Chapters 2, 3, 4 and 6, not Chapter 1, which is
  the construction chapter and carries no worked examples. The count and the breakdown are right;
  only the attribution is wrong.
- **C-002**: the discount does not cover fuel or ammunition. FR-007 says it applies to the summed
  component price; the rule it cites exempts those two. cetools implements the rule, which puts it
  at odds with the published examples and generates a divergence.
- **C-003**: the Air/Raft's four quoted figures all check out, and a fifth defect is worth knowing:
  its spaces column does not balance, so cetools prints 29.68 spaces of cargo where the book prints
  24.57.

The decision with the widest blast radius is **R-003**: Chapter 1 contradicts *itself* in seven
places, which FR-017 does not anticipate because it names Chapter 1 as the single source of truth.
The rule adopted is to transcribe what the table prints unless prose in the same chapter contradicts
it, in which case take the prose and record the divergence. That gives `DIVERGENCES.md` a rules
section alongside its worked-examples section.

## Phase 1: Design and Contracts

Complete. See [data-model.md](./data-model.md), [contracts/](./contracts/) and
[quickstart.md](./quickstart.md).

## Implementation Sequencing

Not a task list—`/speckit-tasks` owns that. This is the dependency order the design implies, and why
each step sits where it does.

1. **`tables.py` and `test_vehicle_tables.py`.** Everything reads from here. SC-006 makes the table
   tests substantial in their own right: a row no catalog vehicle and no generation path touches
   still needs a test that fails when its values are altered.
2. **`prose.py`, `models.py`, `design.py`.** The record types and the TOML shape. `design.py` is
   where round-tripping is proved, so User Story 4's guarantee is established before anything
   depends on it.
3. **`builder.py`.** The rules, in the SRD's build order. This is User Story 1 and the feature's
   center of gravity.
4. **`description.py`** and the CLI's `build` command. User Story 1 is now deliverable end to end.
5. **`published.py` and `test_vehicle_catalog.py`, then the fifteen `catalog/*.toml`.** The
   comparison test is written first so authoring runs red to green against the published figures
   rather than being tuned until it passes. This is where the builder gets its real exercise, and
   where divergences are discovered rather than assumed.
6. **`DIVERGENCES.md`, the `check_docs.py` extension, and `catalog.py`** with the CLI's `--catalog`
   and the `catalog` listing. User Story 2 complete, gate widened.
7. **`generator.py`** with roles and constraints, the `VEHICLE_*` roll names, the CLI's `generate`,
   and the pinned baseline. User Story 3.
8. **`--table`, `--toml` and `--out` across both commands**, then README, CONTRIBUTING and AGENTS.
   User Story 4 and the documentation obligation.

Steps 1 through 4 are the minimum that delivers value and could in principle ship alone; the spec's
Assumptions section explains why they will not.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Roles and loadout profiles in the generator, machinery `ships/generator.py` explicitly declined | FR-026b, confirmed in clarification. A vehicle's spaces budget is small and Chapter 1's component list is wide relative to it, so an independently drawn component is often absurd rather than merely surprising: a turret on an ambulance, a wet bar on a grav bike. User Story 3 exists to hand a referee a vehicle they can use at the table. | Rolling every category independently, which is ships' position, produces legal vehicles a referee would not use; that fails the story rather than simplifying it. Rolling the structural spine only produces a chassis with no sensors or comms. The profiles stay in `generator.py`, never touch `builder.py`, and are documented as cetools policy so no reader mistakes them for SRD rules. |
| Divergences documented in prose rather than exposed as a selectable policy, as Principle I would otherwise require | FR-019. These are not departures from the SRD: cetools implements the construction rules, and the book's worked examples disagree with those rules. A policy switch would offer a referee the choice to be wrong. | Adding a policy value would mean maintaining a second, incorrect arithmetic path for every diverging figure. The documentation half of Principle I's obligation binds in full and is enforced by the gate rather than by review, which is stricter than the constitution asks. |
| The change touches `scripts/check_docs.py`, `README.md`, `CONTRIBUTING.md`, `AGENTS.md` and `cli/main.py` outside the new domain | FR-020a requires the divergence page inside the quality gate, and a new CLI group has to be registered somewhere. | Leaving the page outside the gate would make SC-002's "enforced by the check rather than by review" false. The other four are the irreducible registration cost of a new domain. |
| One pull request of roughly ships' size | Spec Assumptions, an explicit and reaffirmed decision. The catalog is what verifies the tables; a builder without it is a half-change whose correctness cannot be demonstrated. | Splitting the builder from the catalog would put unverified tables on `main`. Recorded here so a reviewer meets the size as a decision rather than as a surprise. |
