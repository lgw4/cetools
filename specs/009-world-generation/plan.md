# Implementation Plan: World Generation

**Branch**: `009-world-generation` | **Date**: 2026-07-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/009-world-generation/spec.md`

## Summary

Add a world-generation domain to cetools that produces Cepheus Engine worlds from SRD Chapter 12:
a single world's Universal World Profile (UWP), a fully-described system (population modifier, bases,
gas giants, planetoid belts, trade codes, travel zone, allegiance), and an 8×10 subsector of such
systems. Worlds are named by default via a hybrid stem generator, unique within a subsector, and
callers may override any name. All rules run through the existing `Rolls` chance seam so generation
is reproducible from a seed. Logic lives in a new `engine/worlds/` subpackage (zero CLI dependency);
a thin `cetools world` Typer subcommand routes I/O.

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: Typer (CLI only); standard library `random`, `dataclasses`, `enum` for the
engine. No new third-party runtime dependencies.

**Storage**: N/A—generation is stateless and pure.

**Testing**: pytest with coverage (suite fails below 85% on `src/cetools`); the `Rolls` seam's
`ScriptedRolls` adapter drives deterministic rule tests.

**Target Platform**: Cross-platform CLI (macOS/Linux/Windows), Python library.

**Project Type**: Single project—engine library plus Typer CLI (existing layout).

**Performance Goals**: A single world is effectively instant; a full 8×10 subsector (80 presence
checks, ~40 worlds) generates in well under one second.

**Constraints**: Engine code MUST NOT import from `cli/`. Generation MUST be deterministic given a
seed (reproducibility via `RandomRolls(random.Random(seed))`). All SRD caps/floors/dependencies
enforced.

**Scale/Scope**: Bounded—the largest unit is one 8×10 subsector.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. SRD-Fidelity | ✅ PASS | Rules taken verbatim from `worlds.html` (Chapter 12), digested in [research.md](./research.md). No deliberate deviations. SRD referee-discretion steps (Red Zones, polity borders, trade/comm routes) are out of automated scope per the spec and are *not* invented. World naming has no SRD algorithm; the chosen hybrid generator is documented, not a rule change. |
| II. Library-First | ✅ PASS | All logic in `src/cetools/engine/worlds/`; importable and callable with no CLI. Engine has zero `cli/` imports. |
| III. CLI Interface | ✅ PASS | New `cetools world` sub-app is pure I/O routing: parse args → call engine → write stdout. Exit 0 on success. (World generation has no failure analogue like character death; malformed *user input*—e.g. bad `--density`—exits 1 to stderr.) |
| IV. Test-First | ✅ PASS | TDD red-green-refactor; every module gets `tests/test_*.py` before implementation. `ScriptedRolls` pins probabilistic rules to exact outcomes. |
| V. Data-Driven Extensibility | ✅ PASS | Every SRD table (size, atmosphere, hydro DMs, population DMs, starport, government, law, TL DM matrix, TL minimums, trade-code rules) is a data structure in `worlds/tables.py`; the generator reads them generically. Adding/adjusting a table entry needs no generator logic change. |

**Complexity**: A `worlds/` subpackage (not flat modules) is justified below. No other deviations.

**Result**: PASS—no unjustified violations. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/009-world-generation/
├── plan.md              # This file
├── spec.md              # Feature specification (clarified)
├── research.md          # Phase 0: SRD rules digest + design decisions
├── data-model.md        # Phase 1: entities, fields, validation, rendering
├── quickstart.md        # Phase 1: runnable validation guide
├── contracts/
│   ├── cli.md           # `cetools world` command schema
│   └── engine-api.md    # Engine public functions and types
├── checklists/
│   └── requirements.md  # Spec quality checklist (from /speckit-specify)
└── tasks.md             # Phase 2 output (/speckit-tasks—NOT created here)
```

### Source Code (repository root)

```text
src/cetools/
├── cli/
│   ├── main.py          # MODIFIED: register the world sub-app
│   ├── character.py     # (unchanged)
│   └── world.py         # NEW: `cetools world` Typer sub-app (I/O routing only)
├── engine/
│   ├── worlds/          # NEW subpackage—the world-generation domain
│   │   ├── __init__.py  # Public surface: generate_world/system/subsector, models
│   │   ├── tables.py    # SRD static data (all Chapter 12 tables as data)
│   │   ├── models.py    # World, System, Subsector, TravelZone, Density frozen dataclasses/enums
│   │   ├── generator.py # generate_world(), generate_system(), generate_subsector()
│   │   ├── naming.py    # generate_world_name(): hybrid stem assembler
│   │   └── profile.py   # render UWP profile string + full world-data line
│   ├── rolls.py         # MODIFIED: add world RollName members
│   ├── pseudohex.py     # REUSED: to_pseudohex/from_pseudohex for UWP digits
│   └── ...              # (all existing modules unchanged)
└── formatter.py         # (unchanged; world rendering lives in worlds/profile.py)

tests/
├── test_world_tables.py     # NEW: table invariants
├── test_world_models.py     # NEW: derived fields (base code, PBG, profile)
├── test_world_generator.py  # NEW: rule correctness via ScriptedRolls + statistical bounds
├── test_world_naming.py     # NEW: naming + subsector uniqueness
├── test_world_profile.py    # NEW: profile string + full line rendering
├── test_cli.py              # MODIFIED: add `cetools world` cases
└── ...
```

**Structure Decision**: A cohesive `engine/worlds/` subpackage, mirroring the existing
`engine/careers/` package precedent. World generation spans several concerns (static tables, models,
rule engine, naming, rendering) that belong together and read best namespaced. `worlds/__init__.py`
is the public surface, so callers import from `cetools.engine.worlds`, not from submodules—exactly
as `careers` works today. Docs note: `scripts/check_docs.py`'s module-map check globs only top-level
`engine/*.py`, so subpackage modules are not individually enforced; the `worlds/` package is still
added to CONTRIBUTING.md's module map for human readers.

## Complexity Tracking

| Choice | Why Needed | Simpler Alternative Rejected Because |
|--------|------------|-------------------------------------|
| `worlds/` subpackage (5 modules) vs. flat `world_*.py` modules | The domain has five distinct concerns (tables, models, generator, naming, rendering); a package namespaces them and matches the `careers/` precedent | Five top-level `world_*.py` modules add prefix noise to the engine root and to the module-map diagram; the domain is cohesive enough to warrant one package boundary |

*No constitution violations require justification; the table above records a structural choice only.*
