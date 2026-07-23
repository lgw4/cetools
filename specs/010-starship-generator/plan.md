# Implementation Plan: Starship Generator

**Branch**: `010-starship-generator` | **Date**: 2026-07-22 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/010-starship-generator/spec.md`

## Summary

Add a ship-design domain to cetools that implements the Cepheus Engine "Ship Design and
Construction" rules as a deterministic **builder** plus a seed-driven **random generator** layered on
top of it. A caller supplies a structured design (hull, configuration, drives, power plant, fuel,
bridge/cockpit, computer and software, electronics, armor, quarters, fittings, turrets, bays,
screens, standard-design flag); the builder allocates tonnage, costs every component, derives crew,
hull/structure points, fuel, and build time, and rejects rule violations with a specific message.
The random generator selects a rules-legal combination and runs it through the same builder, so every
generated ship passes the same validation and is reproducible from a seed via the existing `Rolls`
chance seam. All logic lives in a new `engine/ships/` subpackage (zero CLI dependency, mirroring
`engine/worlds/` and `engine/careers/`); a thin `cetools ship` Typer sub-app routes I/O. Designs are
read from TOML with stdlib `tomllib` and emitted as builder-compatible TOML by a small hand-rolled
serializer, so any ship—including a generated one—round-trips losslessly.

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: Typer (CLI only). Standard library `tomllib` for reading TOML design files
(no new runtime dependency); `dataclasses`, `enum`, `math` for the engine. TOML *emission* uses a
small in-repo serializer (stdlib has no TOML writer) over the bounded design schema.

**Storage**: N/A—the builder is pure and stateless. TOML design files are user-supplied inputs and
optional outputs, not managed storage.

**Testing**: pytest with coverage (suite fails below 85% on `src/cetools`); the `Rolls` seam's
`ScriptedRolls` adapter drives deterministic rule tests, `RandomRolls(random.Random(seed))` drives
reproducibility tests, and Typer's `CliRunner` drives CLI tests.

**Target Platform**: Cross-platform CLI (macOS/Linux/Windows), Python library.

**Project Type**: Single project—engine library plus Typer CLI (existing layout).

**Performance Goals**: Building or generating a single ship is effectively instant, well under one
second (SC-007).

**Constraints**: Engine code MUST NOT import from `cli/`. Generation MUST be deterministic given a
seed (reproducibility via `RandomRolls.seeded(seed)`). The random generator MUST reuse the builder so
it cannot produce a rules-illegal ship (SC-003). Design TOML round-trips losslessly (SC-008). All SRD
tonnage budgets, caps, floors, and dependencies enforced.

**Scale/Scope**: Bounded—the largest unit is a single 5,000-ton ship with a fixed component set.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. SRD-Fidelity | ✅ PASS | Rules taken verbatim from the SRD "Ship Design and Construction" page, digested in [research.md](./research.md). No deliberate deviations. Referee-discretion steps (crew role assignment beyond the SRD minimum, mission-specific fittings) are out of automated scope per FR-002 and are documented as omitted, not invented. Two ambiguities (minimum-crew composition, small-craft power-plant fuel rounding) are resolved to the SRD's literal text in research.md, not house-ruled. |
| II. Library-First | ✅ PASS | All logic in `src/cetools/engine/ships/`; importable and callable with no CLI. Engine has zero `cli/` imports. The builder is the sole authority for costing/validation; the generator and CLI both call it. |
| III. CLI Interface | ✅ PASS | New `cetools ship` sub-app is pure I/O routing: parse args / read TOML → call engine → write stdout. Exit 0 on success; exit 1 (stderr) for a user-facing failure—an invalid design or malformed/schema-invalid TOML—analogous to enlistment failure/character death. |
| IV. Test-First | ✅ PASS | TDD red-green-refactor; every module gets `tests/test_*.py` before implementation. `ScriptedRolls` pins random selection to exact outcomes; hand-worked SRD reference designs (SC-002) are golden tests for the builder. |
| V. Data-Driven Extensibility | ✅ PASS | Every SRD table (hull, drive-performance matrix, drive costs, armor, bridge, computer, software, electronics, quarters, fittings, turrets, weapons, bays, screens, small-craft hull/cockpit) is a data structure in `ships/tables.py`; the builder reads them generically. Adding or adjusting a hull size, weapon, or fitting requires only changing data (SC-006), with no builder-logic change. |

**Complexity**: A `ships/` subpackage (not flat modules) and a small in-repo TOML serializer are the
only structural choices; both are justified in Complexity Tracking below. No constitution deviations.

**Result**: PASS—no unjustified violations. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/010-starship-generator/
├── plan.md              # This file
├── spec.md              # Feature specification (clarified)
├── research.md          # Phase 0: SRD rules digest + design decisions
├── data-model.md        # Phase 1: entities, fields, validation, rendering
├── quickstart.md        # Phase 1: runnable validation guide
├── contracts/
│   ├── cli.md           # `cetools ship` command schema
│   ├── engine-api.md    # Engine public functions and types
│   └── design-schema.md # TOML design-file schema (builder input / round-trip output)
└── tasks.md             # Phase 2 output (/speckit-tasks—NOT created here)
```

### Source Code (repository root)

```text
src/cetools/
├── cli/
│   ├── main.py          # MODIFIED: register the ship sub-app
│   ├── character.py     # (unchanged)
│   ├── world.py         # (unchanged)
│   └── ship.py          # NEW: `cetools ship` Typer sub-app (I/O routing only)
├── engine/
│   ├── ships/           # NEW subpackage—the ship-design domain
│   │   ├── __init__.py  # Public surface: build_ship, generate_ship, load_design, dump_design, models
│   │   ├── tables.py    # SRD static data (all ship-construction tables as data)
│   │   ├── models.py    # ShipDesign (input) + Ship (output) + component value objects, frozen
│   │   ├── builder.py   # build_ship(design) -> Ship: deterministic allocation, costing, validation
│   │   ├── generator.py # generate_ship(rolls, *, hull_size=None, small_craft=False) -> Ship
│   │   ├── design.py    # load_design() via tomllib; dump_design() TOML serializer (round-trip)
│   │   └── sheet.py     # render_sheet(ship) -> human-readable ship sheet
│   ├── rolls.py         # MODIFIED: add SHIP_* RollName members
│   └── ...              # (all existing modules unchanged)
└── formatter.py         # (unchanged; ship rendering lives in ships/sheet.py)

tests/
├── test_ship_tables.py     # NEW: table invariants (monotonic hulls, matrix shape, cost keys)
├── test_ship_models.py     # NEW: value-object validation + derived fields
├── test_ship_builder.py    # NEW: SRD reference designs (SC-002) + every rejection path (SC-005)
├── test_ship_generator.py  # NEW: legality (SC-003) + reproducibility (SC-004) via Scripted/RandomRolls
├── test_ship_design.py     # NEW: TOML load + dump round-trip (SC-008) + malformed-file errors
├── test_ship_sheet.py      # NEW: ship-sheet rendering is total and stable
├── test_cli.py             # MODIFIED: add `cetools ship build`/`generate` cases
└── ...
```

**Structure Decision**: A cohesive `engine/ships/` subpackage, mirroring the existing
`engine/worlds/` and `engine/careers/` packages. Ship design spans several distinct concerns (static
tables, models, the deterministic builder, the random generator, TOML design I/O, sheet rendering)
that belong together and read best namespaced. `ships/__init__.py` is the public surface, so callers
import from `cetools.engine.ships`, not from submodules—exactly as `worlds` and `careers` work today.
Docs note: `scripts/check_docs.py`'s module-map check globs only top-level `engine/*.py`, so
subpackage modules are not individually enforced; the `ships/` package is still added to
CONTRIBUTING.md's module map for human readers.

## Complexity Tracking

| Choice | Why Needed | Simpler Alternative Rejected Because |
|--------|------------|-------------------------------------|
| `ships/` subpackage (7 modules) vs. flat `ship_*.py` modules | The domain has distinct concerns (tables, models, builder, generator, design I/O, sheet); a package namespaces them and matches the `worlds/`/`careers/` precedent | Seven top-level `ship_*.py` modules add prefix noise to the engine root and to the module-map diagram; the domain is cohesive enough to warrant one package boundary |
| Hand-rolled TOML serializer in `design.py` (`dump_design`) | Round-tripping a generated ship to editable TOML (FR-022, FR-023, SC-008) requires *writing* TOML; the stdlib `tomllib` is read-only and the constitution/spec forbid a new runtime dependency | A third-party writer (`tomli-w`, `toml`) would add a runtime dependency (violates the spec's dependency-free assumption); the design schema is small and fully controlled, so a ~30-line serializer over known types is simpler than taking on a dependency |
| Split `ShipDesign` (input) from `Ship` (computed output) | The builder is a pure function `design → ship`; a separate input record makes round-trip lossless (emit `ship.design`, rebuild, compare) and keeps the TOML schema decoupled from derived numbers | A single mutable model conflating inputs and derived totals would make "same design in ⇒ same sheet out" (SC-008) unverifiable and blur what the TOML file must carry |

*No constitution violations require justification; the table above records structural choices only.*
