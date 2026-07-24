---
description: "Task list for the Starship Generator feature"
---

# Tasks: Starship Generator

**Input**: Design documents from `/specs/010-starship-generator/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Tests**: Test tasks ARE included. Constitution Principle IV (Test-First) is non-negotiable and
plan.md commits to red-green-refactor, so every implementation task is preceded by a failing-test
task in the same phase.

**Organization**: Tasks are grouped by user story so each story can be implemented, tested, and
delivered independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story the task belongs to (US1–US4)
- Every description names the exact file path

## Path Conventions

Single project (existing layout): engine library in `src/cetools/engine/`, CLI in `src/cetools/cli/`,
tests in `tests/` mirroring the package. New ship domain lives in `src/cetools/engine/ships/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the new subpackage and confirm a clean baseline before any behaviour changes.

- [X] T001 Create the ships subpackage skeleton at `src/cetools/engine/ships/__init__.py` with a module docstring and an empty `__all__`, and confirm `uv run python -c "import cetools.engine.ships"` succeeds
- [X] T002 [P] Confirm the baseline quality gate is green before changes: `uv run black . && uv run flake8 src tests && uv run pytest && uv run python scripts/check_docs.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The SRD data tables, the value objects, and the new chance names that every user story
reads from. Story-specific table data (small craft in US3, bays/screens in US4) is added in its own
story phase; this phase carries only what US1 needs plus the record shapes shared by all stories.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 [P] Write failing tests asserting the new `SHIP_*` `RollName` members exist and are unique in `tests/test_rolls.py`
- [X] T004 Add the `SHIP_*` members to `RollName` in `src/cetools/engine/rolls.py`, covering every selection the generator makes across all four stories: `SHIP_HULL_SIZE`, `SHIP_CONFIGURATION`, `SHIP_JUMP_CODE`, `SHIP_MANEUVER_CODE`, `SHIP_POWER_CODE`, `SHIP_ARMOR`, `SHIP_COMPUTER`, `SHIP_ELECTRONICS`, `SHIP_STATEROOMS`, `SHIP_FITTING`, `SHIP_TURRET_COUNT`, `SHIP_TURRET_MOUNT`, `SHIP_WEAPON`, plus `SHIP_COCKPIT` (US3, T047), `SHIP_BAY` and `SHIP_SCREEN` (US4, T059)—all added here so Phases 5 and 6 never have to reopen `rolls.py`
- [X] T005 [P] Write failing table-invariant tests (`HULLS` keys match the research Part B set exactly and are monotonically ordered—the table is deliberately sparse above 1,000 t, so do not assert every 100-ton step; every `DRIVE_COSTS` code present in `DRIVE_PERFORMANCE`; matrix cells are `int` or absent; bridge steps ordered; every row dataclass field typed) in `tests/test_ship_tables.py`
- [X] T006 Implement the row dataclasses and the core starship tables (`HULLS`, `CONFIG_MODIFIERS`, `DRIVE_COSTS`, `DRIVE_PERFORMANCE`, `ARMOR`, `BRIDGE_SIZES`, `COMPUTERS`, `SOFTWARE`, `ELECTRONICS`, `QUARTERS`, `FITTINGS`, `TURRET_MOUNTS`, `TURRET_WEAPONS`) from research.md Parts B–H in `src/cetools/engine/ships/tables.py`
- [X] T007 [P] Write failing model tests (enum members and `Configuration.cost_modifier`; each `_validate_*` rejection message; `Crew.total` including `screen_operators`; `LineItem` fields; frozen/immutable behaviour; and that shape-only validation lets a *rules-illegal but well-formed* design be constructed, e.g. a small craft with a `jump_code`, so the builder can be the one to reject it) in `tests/test_ship_models.py`
- [X] T008 Implement the `Configuration`, `ArmorType`, and `HullClass` enums in `src/cetools/engine/ships/models.py`
- [X] T009 Implement the frozen component-fit records `ArmorFit`, `SoftwareFit`, `ComputerFit`, `FittingFit`, `AmmoFit`, `TurretFit`, `BayFit`, `ScreenFit` with their `_validate_*` functions in `src/cetools/engine/ships/models.py`
- [X] T010 Implement the frozen `ShipDesign` input record with all fields and **shape-only** validation—field types and ranges, enum membership, drive codes being letters in the SRD sequence, and `bridge` XOR `cockpit`. Per data-model.md "Validation—shape only", SRD rule checks (tabulated `hull_tons`, required systems, small-craft jump drive/bays, 5% armor increments) do **not** live here; they belong to the builder so FR-015's build-order reporting has a single authority. In `src/cetools/engine/ships/models.py`
- [X] T011 Implement the frozen output records `Crew` (with `gunners` = turrets + bays, a separate `screen_operators`, the conditional medic rule—0 when there are no high/middle passengers—and `total`), `LineItem`, and `Ship` (holding its originating `design`; no rendering method, so `models.py` never imports `sheet.py`) in `src/cetools/engine/ships/models.py`
- [X] T012 Export the foundational public names (`ShipDesign`, `Ship`, `Crew`, `LineItem`, `Configuration`, `ArmorType`, `HullClass`, and the component fits `ArmorFit`, `SoftwareFit`, `ComputerFit`, `FittingFit`, `AmmoFit`, `TurretFit`, `BayFit`, `ScreenFit`) from `src/cetools/engine/ships/__init__.py`

**Checkpoint**: Tables and value objects import cleanly; user story implementation can begin.

---

## Phase 3: User Story 1 - Design a custom ship deterministically (Priority: P1) 🎯 MVP

**Goal**: `build_ship(design) -> Ship` allocates tonnage, costs every component, derives crew,
fuel, hull/structure points and build time for a standard 100–5,000-ton hull, and rejects a
rules-illegal design with a message naming the violated rule. A design is read from and written to
TOML, rendered as a ship sheet, and driven by `cetools ship build`.

**Independent Test**: `uv run cetools ship build specs/010-starship-generator/examples/free-trader.toml`
prints a sheet whose tonnage, cargo, cost, crew, hull/structure points, fuel and build weeks match the
hand-worked SRD figures (SC-002); a design with a power plant below the jump drive exits 1 with
`power plant rating ... below required ...` (SC-005).

### Tests for User Story 1 ⚠️

> Write these first and confirm they FAIL before implementing.

- [X] T013 [P] [US1] Add three golden SRD reference designs (small starship, mid-size trader/scout, larger turret-armed warship) as `specs/010-starship-generator/examples/free-trader.toml`, `examples/scout-courier.toml`, and `examples/warship.toml`, each with its hand-worked expected figures recorded in a comment header
- [X] T014 [US1] Write failing golden-design builder tests asserting exact tonnage, cargo, cost, crew breakdown (every `Crew` field individually, not just `total`—a passenger-free design must show `medic == 0`), jump/power fuel, hull/structure points and build weeks for the three reference designs (SC-002) in `tests/test_ship_builder.py`
- [X] T015 [US1] Write failing rejection tests, one per constraint in the data-model.md "Builder-enforced constraints" table and asserting the message names the rule (unknown hull size, armor increment, drive not available on hull, missing jump drive, missing power plant, power plant below drives, software over computer rating, fuel scoops on a distributed hull, hardpoint limit, over-allocation), plus multi-violation designs proving the first violation in SRD build order is the one reported—including a design with both a bad armor increment and an illegal drive code, which must report the *armor* error because armor precedes drives (FR-015, SC-005)—in `tests/test_ship_builder.py`
- [X] T016 [P] [US1] Write failing design I/O tests (parse the schema in contracts/design-schema.md; `loads_design(dump_design(d)) == d`; `build_ship(loads_design(dump_design(ship.design))) == ship` for each golden design, SC-008; `load_design(path)` reads a file and agrees with `loads_design(text)`; `ValueError` for malformed TOML, unknown key, wrong type, unknown enum string, missing `hull_tons`; and that a well-formed but rules-illegal design *loads* cleanly and is rejected only by `build_ship`) in `tests/test_ship_design.py`
- [X] T017 [P] [US1] Write failing `render_sheet` tests (every FR-022 section present—including the assumed jump range on the fuel line, FR-006; total for any valid `Ship`; byte-identical for equal ships; no seed anywhere in the output) in `tests/test_ship_sheet.py`
- [X] T018 [P] [US1] Write failing CLI tests for `cetools ship build` (sheet on stdout exit 0; `--toml` emits round-trippable TOML; `--out` writes the file; `--out` without `--toml` exits 1; missing file, malformed TOML and rules-illegal design each exit 1 with the message on stderr) in `tests/test_cli.py`

### Implementation for User Story 1

- [X] T019 [US1] Implement hull and configuration costing (rejecting a hull size that is not tabulated), armor allocation (rejecting a non-5% increment), hull points (⌊tons÷50⌋), structure points (⌈tons÷50⌉) and hardpoints (⌊tons÷100⌋) as the first `LineItem`s in `src/cetools/engine/ships/builder.py`. These are the first two steps of the SRD build order, so their checks run before every other rule check (FR-015)
- [X] T020 [US1] Implement maneuver drive, jump drive and power plant allocation from `DRIVE_COSTS`/`DRIVE_PERFORMANCE`, the power-plant ≥ higher-drive-rating check, the required-system checks, and jump/power fuel (0.1 × hull × distance; ⌊power tons ÷ 3⌋ × weeks with a 2-week starship floor) including the reported `assumed_jump_distance` in `src/cetools/engine/ships/builder.py`
- [X] T021 [US1] Implement bridge sizing from `BRIDGE_SIZES`, computer model with jump-control/hardened cost options, software with the total-rating-≤-computer-rating check, and the electronics package in `src/cetools/engine/ships/builder.py`
- [X] T022 [US1] Implement staterooms, low berths, emergency low berths, fittings (including the vault's +4 hull/structure points and the distributed-hull fuel-scoop prohibition, which rejects with `a distributed hull cannot mount fuel scoops`) and turrets with weapons, ammunition and the hardpoint limit in `src/cetools/engine/ships/builder.py`
- [X] T023 [US1] Implement the cargo remainder with the over-allocation check, `Crew` derivation (pilot; navigator unless Jump-Control software; engineers ⌈drive+plant tons÷35⌉; gunners = turrets + bays; `screen_operators` = one per screen; stewards per 4 high / 10 middle passengers; medic **0 when there are no high or middle passengers**, otherwise ⌈(crew+passengers)÷120⌉—a bare ceiling would give every ship a medic and contradict FR-012), total cost with the 10% standard-design discount excluding fuel and ammunition, build weeks from the hull table, and the public `build_ship(design) -> Ship` entry point in `src/cetools/engine/ships/builder.py`
- [X] T024 [P] [US1] Implement `loads_design(text)` parsing the contracts/design-schema.md sections with stdlib `tomllib` into a well-formed `ShipDesign`, plus the thin `load_design(path)` wrapper that reads the file and delegates (a `str` is always a path, never TOML text—the `json.load`/`json.loads` convention). Both raise `ValueError` with a clear message for malformed TOML, unknown keys, wrong types, or unknown enum strings, and neither checks SRD rules. In `src/cetools/engine/ships/design.py`
- [X] T025 [US1] Implement `dump_design(design) -> str`, the in-repo TOML writer emitting the canonical key order and omitting empty/default sections, in `src/cetools/engine/ships/design.py`
- [X] T026 [P] [US1] Implement `render_sheet(ship) -> str` covering hull/configuration, drives and ratings, power plant, fuel (with the assumed jump range the figure is based on, FR-006), computer and software, electronics, crew, quarters, fittings, armaments, tonnage used/cargo, hull/structure points, total cost and build time—reading only from the `Ship`, in `src/cetools/engine/ships/sheet.py`
- [X] T027 [US1] Export `build_ship`, `load_design`, `loads_design`, `dump_design` and `render_sheet` from `src/cetools/engine/ships/__init__.py`
- [X] T028 [US1] Implement the `cetools ship` Typer sub-app with the `build` command (`FILE`, `--toml`, `--out`) as pure I/O routing, catching `ValueError` (and `OSError`, reported as `cannot read design file: <path>`) and exiting 1 to stderr, in `src/cetools/cli/ship.py`
- [X] T029 [US1] Register the ship sub-app (`app.add_typer(ship.app, name="ship")`) and update the root callback help text in `src/cetools/cli/main.py`

**Checkpoint**: User Story 1 is fully functional. `cetools ship build` is a usable SRD ship-design
calculator with lossless TOML round-trip. This is the MVP.

---

## Phase 4: User Story 2 - Randomly generate a complete ship from a seed (Priority: P2)

**Goal**: `generate_ship(rolls=None, *, hull_size=None, small_craft=False)` selects rules-legal
components through the `Rolls` seam, assembles a `ShipDesign`, and returns `build_ship(design)` so no
generated ship can be illegal. The same seed always yields the same ship, and the CLI reports the seed
on stderr when none is given. (`small_craft=` is wired here; its behaviour lands in US3/T047.)

**Independent Test**: `uv run cetools ship generate --seed 42` twice produces byte-identical output;
`generate_ship(RandomRolls.seeded(42))` equals a second call with the same seed; `--hull 400` yields a
400-ton ship; every generated ship round-trips through `dump_design`/`load_design` unchanged.

### Tests for User Story 2 ⚠️

- [X] T030 [P] [US2] Write failing generator tests: `ScriptedRolls` pins a known component selection to an exact `Ship`; `RandomRolls.seeded(42)` twice yields equal ships (SC-004); a sweep of many seeds all produce ships (SC-003, no `ValueError`); `hull_size=` is honoured (FR-018); each generated ship satisfies `build_ship(loads_design(dump_design(ship.design))) == ship` (SC-008)—in `tests/test_ship_generator.py`
- [X] T031 [P] [US2] Write failing CLI tests for `cetools ship generate` (two `--seed 42` runs byte-identical on stdout; `--hull 400` reflected in the sheet; `--toml` and `--out`; the chosen seed reported on **stderr** when `--seed` is omitted, with stdout carrying the sheet alone and no seed in it; invalid `--hull` exits 1) in `tests/test_cli.py`

### Implementation for User Story 2

- [X] T032 [US2] Implement the component-selection helpers (hull size, configuration, drive codes constrained so the power plant meets the drive requirement, armor, computer and software, electronics, staterooms, fittings, turrets and weapons) reading the same `tables.py` data the builder validates against, each using a named `SHIP_*` roll, in `src/cetools/engine/ships/generator.py`
- [X] T033 [US2] Implement `generate_ship(rolls=None, *, hull_size=None, small_craft=False)`—defaulting `rolls` to `RandomRolls()`—assembling a `ShipDesign` that is legal by construction (tonnage budget respected before the build) and returning `build_ship(design)`, in `src/cetools/engine/ships/generator.py`
- [X] T034 [US2] Export `generate_ship` from `src/cetools/engine/ships/__init__.py`
- [X] T035 [US2] Add the `generate` command (`--hull`, `--seed`, `--toml`, `--out`) to `src/cetools/cli/ship.py`, seeding via `RandomRolls.seeded(seed)` and reporting the chosen seed on stderr when `--seed` is omitted

**Checkpoint**: User Stories 1 and 2 both work. Seeded generation is reproducible and always legal.

---

## Phase 5: User Story 3 - Design and generate small craft (Priority: P3)

**Goal**: Hulls of 10–95 tons build under the small-craft ruleset: cockpit instead of a bridge, no
jump drive, a one-week power-plant fuel minimum rounded to 0.1 ton, exactly one hardpoint, and the
power-plant energy-weapon cap. Both the builder and the generator support small craft.

**Independent Test**: `build_ship(load_design('specs/010-starship-generator/examples/fighter.toml'))`
matches the hand-worked small-craft figures with `jump_rating == 0`, a cockpit line and no jump-fuel
line on the sheet; a small-craft design carrying a jump drive is rejected;
`uv run cetools ship generate --hull 10 --small-craft --seed 7` produces a valid small craft.

### Tests for User Story 3 ⚠️

- [X] T036 [P] [US3] Write failing small-craft table tests (`SMALL_CRAFT_HULLS` covers 10–95 t with codes/cost/build weeks, `COCKPITS` holds exactly the two SRD cockpits `1_man` and `2_man` with their research Part K tonnage/cost, `SMALL_CRAFT_ENERGY_CAPS` bands are exhaustive over power-plant codes) in `tests/test_ship_tables.py`
- [X] T037 [P] [US3] Add the small-craft golden design `specs/010-starship-generator/examples/fighter.toml` with its hand-worked expected figures in a comment header
- [X] T038 [US3] Write failing small-craft builder tests (fighter golden figures; cockpit in place of bridge; one-week fuel floor rounded down to 0.1 t; exactly one hardpoint; jump drive rejected with `small craft cannot mount a jump drive`; energy-weapon count over the power-plant cap rejected) in `tests/test_ship_builder.py`
- [X] T039 [P] [US3] Write failing small-craft design I/O tests (`[bridge].cockpit` load and dump for both `1_man` and `2_man`; unknown cockpit string rejected at load; bridge-and-cockpit conflict rejected at load; a small craft carrying `[drives].jump` *loads* cleanly and is rejected by `build_ship`, not by `loads_design`; fighter round-trips losslessly) in `tests/test_ship_design.py`
- [X] T040 [P] [US3] Write failing small-craft sheet tests (cockpit line present, no jump-drive or jump-fuel lines) in `tests/test_ship_sheet.py`
- [X] T041 [P] [US3] Write failing small-craft generator tests (`small_craft=True` yields a 10–95 t ship with no jump drive, reproducible from a seed) in `tests/test_ship_generator.py`
- [X] T042 [P] [US3] Write failing CLI tests for `cetools ship generate --small-craft` (with and without `--hull`; `--hull 95` accepted; `--hull 100 --small-craft` is out of range and exits 1) in `tests/test_cli.py`

### Implementation for User Story 3

- [X] T043 [US3] Add `SMALL_CRAFT_HULLS`, `COCKPITS` (the two SRD cockpits only) and `SMALL_CRAFT_ENERGY_CAPS` from research.md Part K to `src/cetools/engine/ships/tables.py`
- [X] T044 [US3] Implement the small-craft branch in `src/cetools/engine/ships/builder.py`: `HullClass.SMALL_CRAFT` hull lookup, cockpit in place of the bridge, one-week power-fuel floor rounded down to 0.1 ton, exactly one hardpoint, jump-drive rejection, and the power-plant energy-weapon cap—each check placed at its SRD build-order step (FR-015)
- [X] T045 [P] [US3] Add the `[bridge].cockpit` key to `loads_design` and `dump_design` with the bridge/cockpit conflict check in `src/cetools/engine/ships/design.py`
- [X] T046 [P] [US3] Render the small-craft sheet variant (cockpit line, jump lines omitted) in `src/cetools/engine/ships/sheet.py`
- [X] T047 [P] [US3] Implement `small_craft=True` selection (small-craft hull sizes, cockpit chosen with `SHIP_COCKPIT`, no jump drive, energy-weapon cap respected) in `src/cetools/engine/ships/generator.py`
- [X] T048 [P] [US3] Add the `--small-craft` flag to the `generate` command, validating `--hull` against 10–95 when it is set, in `src/cetools/cli/ship.py`

**Checkpoint**: Small craft build and generate correctly alongside standard hulls.

---

## Phase 6: User Story 4 - Equip large ships with bay weapons and screens (Priority: P3)

**Goal**: 50-ton weapon bays (missile bank, particle, meson, fusion) and defensive screens (meson
screen, nuclear damper) are costed, consume tonnage, hardpoints and fire-control tonnage, add a gunner
per bay (`Crew.gunners`) and an operator per screen (`Crew.screen_operators`), and are rejected on
small craft.

**Independent Test**: A large hull with a 50-ton particle bay and a meson screen shows 50 t + 1 t fire
control and one hardpoint consumed for the bay, 50 t for the screen, both costs included, the bay
counted in `Crew.gunners` and the screen in `Crew.screen_operators`; a bay on a hull with no free
hardpoint or under 50 free tons is rejected; a bay on a small craft is rejected as disallowed.

### Tests for User Story 4 ⚠️

- [X] T049 [P] [US4] Write failing `BAYS` and `SCREENS` table tests (each row is 50 t with its SRD cost; bays carry the +1 t fire-control rule) in `tests/test_ship_tables.py`
- [X] T050 [P] [US4] Add a bay-and-screen-equipped golden design `specs/010-starship-generator/examples/heavy-cruiser.toml` with its hand-worked expected figures in a comment header
- [X] T051 [US4] Write failing bay/screen builder tests (golden figures; 50 t + 1 t fire control and one hardpoint per bay; screen tonnage and cost; `Crew.gunners` counts one per bay and `Crew.screen_operators` one per screen; bay rejected when hardpoints are exhausted; bay rejected when free tonnage is under 50; bay on a small craft rejected with `small craft cannot mount a weapon bay`) in `tests/test_ship_builder.py`
- [X] T052 [P] [US4] Write failing design I/O tests for the `[[bays]]` and `[[screens]]` sections (load, dump, round-trip, unknown `kind` rejected at load as a shape error; a bay on a small-craft hull *loads* cleanly and is rejected by `build_ship`, not at load) in `tests/test_ship_design.py`
- [X] T053 [P] [US4] Write failing sheet tests asserting bays and screens appear in the armaments section and screen operators appear in the crew section in `tests/test_ship_sheet.py`
- [X] T054 [P] [US4] Write failing generator tests asserting bays/screens only ever appear on hulls with the hardpoints and free tonnage to hold them, never on small craft, in `tests/test_ship_generator.py`

### Implementation for User Story 4

- [X] T055 [US4] Add the `BAYS` and `SCREENS` tables from research.md Part H to `src/cetools/engine/ships/tables.py`
- [X] T056 [US4] Implement bay and screen allocation in `src/cetools/engine/ships/builder.py`: 50 t plus 1 t fire control per bay, one hardpoint per bay counted against the hull limit, screen tonnage and cost, the small-craft bay rejection, one gunner per bay in `Crew.gunners` and one operator per screen in `Crew.screen_operators`
- [X] T057 [P] [US4] Add the `[[bays]]` and `[[screens]]` sections to `loads_design` and `dump_design` in `src/cetools/engine/ships/design.py`
- [X] T058 [P] [US4] Render bays and screens in the armaments section, and screen operators in the crew section, in `src/cetools/engine/ships/sheet.py`
- [X] T059 [P] [US4] Implement bay and screen selection (using `SHIP_BAY` and `SHIP_SCREEN`), gated on available hardpoints and free tonnage and disabled for small craft, in `src/cetools/engine/ships/generator.py`

**Checkpoint**: All four user stories are independently functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, doc-check compliance, the remaining success-criteria assertions (SC-006,
SC-007), and the full quality gate.

- [X] T060 [P] Add the `engine/ships/` package (and its seven modules) to the module map in `CONTRIBUTING.md`
- [X] T061 [P] Document the `cetools ship build` and `cetools ship generate` commands with a runnable example in `README.md`
- [X] T062 [P] Record the ship-design domain and its SRD source in `CONTEXT.md`, including the FR-002 note that referee-discretion steps (crew role assignment beyond the SRD minimum, mission-specific fittings) are deliberately omitted
- [X] T063 Run `uv run python scripts/check_docs.py` and fix any broken backticked symbol, non-running README example, or spaced dash introduced by T060–T062
- [X] T064 Add a performance assertion that a single build and a single generation each complete in under 0.1 seconds (SC-007) in `tests/test_ship_generator.py`
- [X] T065 [P] Add a data-driven-extensibility test (SC-006) in `tests/test_ship_tables.py`: insert a synthetic row into a copy of a table (a new hull size, a new turret weapon, a new fitting), build a design that uses it, and assert it costs and allocates correctly—proving a new SRD entry needs no change to `builder.py` or `generator.py`
- [X] T066 Execute every command in [quickstart.md](./quickstart.md) and confirm the stated expected output for Stories 1–4
- [X] T067 Run the full quality gate `uv run black . && uv run flake8 src tests && uv run pytest && uv run python scripts/check_docs.py` and confirm `src/cetools` coverage stays at or above 85%

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies; start immediately
- **Foundational (Phase 2)**: depends on Phase 1; BLOCKS all user stories
- **User Story 1 (Phase 3)**: depends on Phase 2 only
- **User Story 2 (Phase 4)**: depends on Phase 3 (`generate_ship` calls `build_ship`; FR-016)
- **User Story 3 (Phase 5)**: depends on Phase 3; its generator task (T047) also depends on Phase 4
- **User Story 4 (Phase 6)**: depends on Phase 3; its generator task (T059) also depends on Phase 4
- **Polish (Phase 7)**: depends on all desired stories being complete

### User Story Dependencies

- **US1 (P1)**: no dependencies on other stories—the MVP and the validation authority every other story reuses
- **US2 (P2)**: layered on US1 by design; independently testable via the generator API and `cetools ship generate`
- **US3 (P3)**: extends the builder with a second ruleset; independently testable against `fighter.toml`
- **US4 (P3)**: additive armaments; independently testable against `heavy-cruiser.toml`
- US3 and US4 are independent of each other in behaviour but both edit `tables.py`, `builder.py`, `design.py`, `sheet.py` and `generator.py`—run them sequentially, or on separate branches with a merge, not concurrently in one tree

### Within Each User Story

- Test tasks MUST be written and observed failing before the implementation tasks in the same phase
- Tables before models, models before builder, builder before design I/O and sheet, engine before CLI
- The builder implementation tasks (T019 → T023, T044, T056) all edit `builder.py` and are strictly sequential

### Parallel Opportunities

- Phase 2: T003, T005 and T007 (three different test files) run together; T004 and T006 run together once their tests exist; T008–T011 are sequential (one file)
- Phase 3: T013 and the test tasks T016, T017, T018 run together (four different files); T014 and T015 share `test_ship_builder.py` and are sequential; among the implementations, T024 and T026 run alongside the `builder.py` chain
- Phase 4: T030 and T031 run together
- Phase 5: T036, T037, T039, T040, T041 and T042 run together; then T043 (tables) must land before T044, and T044 joins the strictly sequential `builder.py` chain, so it is not marked [P]; T045–T048 each touch a different module and run together once T043 is in
- Phase 6: T049, T050, T052, T053 and T054 run together; T055 precedes T056, and T056 belongs to the sequential `builder.py` chain (not [P]); T057, T058 and T059 run together
- Phase 7: T060, T061, T062, T064 and T065 run together, then T063, then T066 and T067

---

## Parallel Example: User Story 1

```bash
# Fixtures and the failing tests in four different files, together:
Task: "Add three golden SRD reference designs in specs/010-starship-generator/examples/"
Task: "Write failing design I/O tests in tests/test_ship_design.py"
Task: "Write failing render_sheet tests in tests/test_ship_sheet.py"
Task: "Write failing CLI ship build tests in tests/test_cli.py"

# Then, while the builder.py chain (T019-T023) proceeds sequentially:
Task: "Implement loads_design/load_design in src/cetools/engine/ships/design.py"
Task: "Implement render_sheet in src/cetools/engine/ships/sheet.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 Setup (T001–T002)
2. Phase 2 Foundational (T003–T012)—blocks everything
3. Phase 3 User Story 1 (T013–T029)
4. **STOP and VALIDATE**: run the Story 1 quickstart commands; confirm the three golden designs match
   the hand-worked SRD figures and every rejection names its rule
5. `cetools ship build` is a shippable SRD ship-design calculator on its own

### Incremental Delivery

1. Setup + Foundational → tables and value objects ready
2. + US1 → deterministic builder, TOML round-trip, ship sheet, `ship build` (**MVP**)
3. + US2 → seeded random generation, `ship generate`
4. + US3 → small craft in both the builder and the generator
5. + US4 → bays and screens on large hulls
6. + Polish → docs, doc check, coverage, full quality gate

Each increment leaves the suite green and adds no regression to the previous ones.

---

## Notes

- The builder is the single validation authority: the generator and the CLI both route through
  `build_ship`, so a generated ship can never be rules-illegal (SC-003)
- That authority is exclusive. `ShipDesign.__post_init__` and `loads_design` reject only malformed
  *shape* (wrong type, unknown key, unknown enum string); every SRD *rule* check lives in
  `builder.py`, ordered by the SRD build order. Duplicating a rule check upstream would silently
  break FR-015's "first violation in build order" guarantee, because the upstream copy would fire
  first regardless of where the rule sits in that order
- `Crew.medic` is conditional, not a bare ceiling: a ship with no high or middle passengers has zero
  medics. `⌈(crew + passengers) ÷ 120⌉` alone would put a medic on every ship (FR-012)
- Every SRD number lives in `tables.py`; adding a hull, weapon or fitting must stay a data-only edit
  (SC-006)—if a story tempts you to branch on a table key in `builder.py`, add a table column instead
- Engine modules must never import from `cli/` (Constitution II)
- Commit after each task or logical group; stop at any checkpoint to validate a story independently

---

## Phase 8: Convergence

- [X] T068 Move the 5%-armor-increment rule out of `ArmorFit.__post_init__` in `src/cetools/engine/ships/models.py` and into the armor step of `build_ship` in `src/cetools/engine/ships/builder.py`, rejecting with the data-model message shape `armor must be added in 5% increments (min 1 ton)`, and add tests proving a design with both an untabulated hull size and a non-5% armor layer reports the *hull* error (hull precedes armor in build order) and that `loads_design` accepts a 7% armor layer without raising, per FR-015 / data-model.md "Builder-enforced constraints" #2 / contracts/design-schema.md "Rules enforced at load" (contradicts)
- [X] T069 Cost and allocate turret ammunition: add an ammunition table (missiles at 12 per ton with per-type cost, sand barrels) to `src/cetools/engine/ships/tables.py`, consume its tonnage and cost as `LineItem`s in `src/cetools/engine/ships/builder.py`, exclude fuel and ammunition line items from the 10% standard-design discount, render loaded ammunition in the armaments section of `src/cetools/engine/ships/sheet.py`, and add tests asserting that 120 missiles add 10 tons and that the discount leaves ammunition untouched, per FR-010 / FR-013 / FR-022 / research.md Part H (partial)
- [X] T070 Resolve the computer jump-control specialization's "+5 jump rating" from research.md Part E in `src/cetools/engine/ships/builder.py`: either add the rating bonus to the software-rating check with a covering test in `tests/test_ship_builder.py`, or record the cost-only reading as an explicit SRD-ambiguity resolution in `specs/010-starship-generator/research.md` Part E, per FR-007 (partial)
- [X] T071 Extend the FR-002 omissions note in `CONTEXT.md` to name the SRD entries left out because the source page never prices them — the beam laser named in FR-010 and any ammunition entry T069 cannot source — so every deliberate omission is documented where FR-002 requires rather than only in a `tables.py` docstring, per FR-002 / FR-010 (partial)

---

## Phase 9: Convergence

- [X] T072 Surface armor protection, which `ARMOR[...].protection_per_5_percent` in `src/cetools/engine/ships/tables.py` currently stores but nothing reads: sum each layer's protection (protection per 5% x increments) in the armor step of `src/cetools/engine/ships/builder.py`, carry the total as an `armor_protection` field on `Ship` in `src/cetools/engine/ships/models.py` (and in the data-model output-record table), render it on the armor line of `src/cetools/engine/ships/sheet.py`, and add tests asserting the figure for a single layer, for stacked layers of different types, and `0` for an unarmored ship, per FR-008 ("with the SRD protection and cost") / FR-022 (partial)
- [X] T073 Record the ammunition figures now hard-coded in `AMMO` in `src/cetools/engine/ships/tables.py` — sand barrels at 20 per ton and Cr500 per barrel, missiles at Cr1,250 / Cr2,500 / Cr3,750 for standard / smart / nuclear — in Part H of `specs/010-starship-generator/research.md`, which today lists only "12 per ton" and no ammunition cost; where the source page prices nothing, say so explicitly and extend the FR-002 omissions note in `CONTEXT.md` to name that entry rather than leaving an untraceable number in the table, per FR-001 / FR-002 / Constitution I (partial)
- [X] T074 Reconcile `TURRET_MOUNTS["fixed"]` in `src/cetools/engine/ships/tables.py`, which is `tons=1`, with research.md Part H's "fixed mounting (0t, x0.5 turret cost)": either set the row to 0 tons and update the golden fixtures and tests that consume it, or extend the `TURRET_MOUNTS` docstring and research.md Part H to justify the 1-ton reading the way the halved cost is already justified, per FR-010 / research.md Part H (contradicts)
- [X] T075 Resolve the armor sub-1-ton increment against spec.md Edge Cases ("armor requested ... below the 1-ton-per-5% minimum, is rejected as invalid ...; the builder does not silently normalize it"), which `_build_armor`'s `tons_per_increment = max(1.0, hull_tons * 0.05)` in `src/cetools/engine/ships/builder.py` contradicts by rounding 5% of a 10-ton hull from 0.5 t up to 1 t without comment: either reject such a layer with the 5%-increment message and cover it with a small-craft test in `tests/test_ship_builder.py`, or record the 1-ton-floor reading as an explicit SRD-ambiguity resolution in `specs/010-starship-generator/research.md` Part F (whose "rejected/normalized" wording is the source of the ambiguity), per FR-008 / spec.md Edge Cases (contradicts)
- [X] T076 Fix the SRD reference link in `README.md`, whose "Ship Design and Construction" URL `https://evolvedexperiment.github.io/cepheus-srd/ships.html` returns HTTP 404, to the authoritative page `https://evolvedexperiment.github.io/cepheus-srd/ship-design-and-construction.html` used by spec.md and research.md, and re-run `uv run python scripts/check_docs.py`, per FR-001 (contradicts)

---

## Phase 10: Convergence

- [X] T077 Decide the small-craft sheet variant from `design.hull_class`, not from `design.cockpit is not None`, in `src/cetools/engine/ships/sheet.py` (the `is_small_craft` line): today a 200-ton starship built with `cockpit="1_man"` carries a Jump-2 drive and 40 tons of jump fuel but renders neither a jump line nor a jump-fuel line, so 40 tons of the tonnage total appear nowhere on the sheet, while a 95-ton small craft built with `bridge=True` renders `Jump-0` and `Fuel: 0t jump (assumes range 0)` — the exact lines FR-022 says a small-craft sheet must omit. Add tests in `tests/test_ship_sheet.py` covering both mismatched pairings (`test_ship_sheet.py:23` only asserts the `"Jump-"` prefix today, so neither case is caught), per FR-022 / FR-019 (contradicts)
- [X] T078 Enforce the bridge/cockpit-to-hull-class pairing at the bridge step of `_build_bridge_or_cockpit` in `src/cetools/engine/ships/builder.py`, which currently accepts either on either hull class — a 95-ton small craft builds with a 10-ton bridge and a 200-ton starship builds with a 1.5-ton cockpit. Reject with messages naming the rule (`small craft requires a cockpit, not a bridge` / `a starship requires a bridge, not a cockpit`), place the checks at the bridge/cockpit step so FR-015's build-order reporting still holds, add the two rows to the "Builder-enforced constraints" table in `specs/010-starship-generator/data-model.md`, and add rejection tests in `tests/test_ship_builder.py`, per FR-019 ("cockpits in place of a bridge") / FR-007 (missing)
- [X] T079 Read `FittingRow.forbidden_on_distributed` in `_build_fittings` in `src/cetools/engine/ships/builder.py` instead of the hardcoded `fit.kind == "fuel_scoops"` comparison: the column is declared at `tables.py` `FittingRow` and set on the `fuel_scoops` row but is read nowhere, so adding a second SRD fitting forbidden on a distributed hull would require a builder change — contradicting SC-006 and the tasks.md note "if a story tempts you to branch on a table key in `builder.py`, add a table column instead". Keep the existing `a distributed hull cannot mount fuel scoops` message shape (name the fitting from the row key) and extend the SC-006 data-driven test in `tests/test_ship_tables.py` with a synthetic distributed-forbidden fitting, per SC-006 / Constitution V (contradicts)
- [X] T080 Render the drive codes and power-plant tonnage on the drives line of `src/cetools/engine/ships/sheet.py`, which today prints only `Jump-1 Maneuver-1 Power-1` while contracts/cli.md's example sheet shows `Drives: Jump-1 (A)  Maneuver-1 (A)  Power-1 (A)` and FR-022 lists "drives and performance" and "power plant" as separate sheet sections — a reader currently cannot tell which drive codes a built ship carries. Tighten the assertion in `tests/test_ship_sheet.py` (which only checks for the `"Jump-"` prefix) to name the codes, per FR-022 / contracts/cli.md (partial)
- [X] T081 Replace the name-suffix discount exemption in `_total_cost` in `src/cetools/engine/ships/builder.py` (`item.name.endswith(("fuel", "ammo"))`) with an explicit flag on `LineItem` in `src/cetools/engine/ships/models.py` (defaulting to discountable, set false on the jump-fuel, power-plant-fuel and ammunition items): coupling the FR-013 rule to line-item naming means a future SRD table entry whose name happens to end in "fuel" or "ammo" would silently escape the 10% standard-design discount as a data-only edit, which SC-006 forbids. Update the `LineItem` row in `specs/010-starship-generator/data-model.md` and add a test asserting a fitting whose name ends in "fuel" is still discounted, per FR-013 / SC-006 (partial)

---

## Phase 11: Convergence

- [X] T082 **CRITICAL** Resolve the turret fire-control deviation in `src/cetools/engine/ships/builder.py`: research.md Part H states "Fire control: 1 ton per weapon group" in the same bullet that governs "total turrets + bays", but `BAY_FIRE_CONTROL_TONS` is consumed only by `_build_bays` while `_build_turrets` allocates none, and the narrowing is recorded neither in research.md nor in plan.md's Constitution Check. Constitution I requires an ambiguity to be resolved in research.md and any deliberate SRD deviation to be recorded with a rationale, so either allocate a fire-control ton per turret weapon group (updating the golden fixtures in `specs/010-starship-generator/examples/` and their tonnage assertions in `tests/test_ship_builder.py`) or record the bays-only reading as an explicit SRD-ambiguity resolution in research.md Part H the way the armor and jump-control ambiguities already are, per Constitution I / research.md Part H / FR-010 / FR-020 (contradicts)
- [X] T083 Move the power-plant fuel-week floor out of `_validate_ship_design` in `src/cetools/engine/ships/models.py` (the `minimum_weeks = 2 if ... STARSHIP else 1` check) and into the fuel step of `build_ship` in `src/cetools/engine/ships/builder.py`: FR-015 states that "reading a design file rejects only malformed input (bad TOML, unknown key, wrong value type, unknown enum value), never a rule violation", yet `loads_design` on a design with `hull_tons = 999` and `[drives] power_weeks = 1` today raises `power_weeks must be >= 2 for a starship` and the untabulated-hull error — build-order step 1 — is never reported. This is the same defect T068 fixed for the 5%-armor rule. Keep the message shape, place the check at the fuel step, add the row to the "Builder-enforced constraints" table in `specs/010-starship-generator/data-model.md` (and correct that file's `power_weeks` field-range note plus contracts/design-schema.md's `power_weeks` comment, both of which currently present the floor as a load-time range), and add tests proving `loads_design` accepts `power_weeks = 1` on a starship and that the multi-violation design above reports the *hull* error, per FR-015 / FR-006 / contracts/design-schema.md "Rules enforced at load" (contradicts)
- [X] T084 Refresh the stale `cetools ship build` console block in `README.md`, which shows `Jump-1 Maneuver-1 Power-1` where the tool has printed `Drives: Jump-1 (A)  Maneuver-1 (A)  Power-1 (A), 4t power plant` since T080 changed the drives line: regenerate the block from the real output of `uv run cetools ship build specs/010-starship-generator/examples/free-trader.toml`, and extend `scripts/check_docs.py` to verify README `console` blocks whose command is a `cetools ship` invocation the same way it already runs README Python examples — the drift went unnoticed precisely because the doc check covers Python examples only, per FR-022 / T061 (contradicts)
- [X] T085 Render the hull code and the standard/custom marker on the sheet in `src/cetools/engine/ships/sheet.py`: contracts/cli.md's example sheet shows `Ship: Beowulf (custom)` and `Hull: 200 tons, streamlined (hull 2)`, but the hull line prints only tons and configuration, so `HullRow.code` in `src/cetools/engine/ships/tables.py` is stored on every row and read by no production code, and a sheet gives no indication that the 10% standard-design discount was applied to its cost — which spec.md Edge Cases ("Standard vs. custom cost") and FR-013 make a material distinction. Look the code up from `HULLS`/`SMALL_CRAFT_HULLS` and add assertions in `tests/test_ship_sheet.py` naming the code and both marker states, per FR-022 / FR-013 / contracts/cli.md (partial)
- [X] T086 Resolve the unread tech-level columns `ArmorRow.min_tl` and `ComputerRow.tl` in `src/cetools/engine/ships/tables.py`, which are set on every armor and computer row but read nowhere in `src/`: no functional requirement or success criterion in spec.md mentions tech level, so either drop them or extend each row's docstring to state that the column is retained for SRD-table fidelity and deliberately unenforced (no TL model exists in v1), so a reader does not mistake them for a live constraint the builder checks, per FR-002 / SC-006 (unrequested)

---

## Phase 12: Convergence

- [X] T087 **CRITICAL** Read the SRD catalog keys from their tables instead of from hardcoded duplicates: `_BAY_KINDS`, `_SCREEN_KINDS`, `_AMMO_KINDS`, `_MISSILE_TYPES` and `_ARMOR_OPTIONS` in `src/cetools/engine/ships/models.py` restate the keys of `BAYS`, `SCREENS` and `AMMO` (and the armor-option set) in a second place, while every other fit — `FittingFit`, `TurretFit`, `SoftwareFit`, `ComputerFit`, `cockpit`, `electronics` — validates against its `tables.py` table directly. Adding a fifth SRD bay to `BAYS` as a data-only edit therefore makes `BayFit(kind="…")` raise `unknown bay kind`, and the matching cost table `_ARMOR_OPTION_COST_PER_TON` in `src/cetools/engine/ships/builder.py` means repricing an armor option is a *logic* edit in a second module. Constitution V requires game content to live in data with zero engine-logic change to extend it, and SC-006 says the same. Derive the ammo/bay/screen validators from `AMMO`/`BAYS`/`SCREENS`, add an `ARMOR_OPTIONS` table (option -> MCr per ton) to `src/cetools/engine/ships/tables.py` that both `models.py` and `builder.py` read, and extend the SC-006 test block in `tests/test_ship_tables.py` with synthetic bay, screen and armor-option rows proving each is a data-only edit, per Constitution V / SC-006 / FR-020 (contradicts)
- [X] T088 **CRITICAL** Record the small-craft data tables in `specs/010-starship-generator/research.md` Part K: `SMALL_CRAFT_DRIVE_PERFORMANCE` in `src/cetools/engine/ships/tables.py` is a full 18-code x 18-hull matrix and `SMALL_CRAFT_HULLS` carries per-row cost (MCr 1.1-1.95) and build weeks (28-35), yet Part K states only "hull codes s1-sJ with their own (cost, build-time) table" and gives neither the figures nor any mention of a second performance matrix — while Part C2 positively asserts "**The same** matrix governs jump rating, maneuver-G, and power-plant rating", which the separate small-craft matrix contradicts. Constitution I makes the SRD the sole authority and requires ambiguities to be resolved in research.md and deliberate deviations to be recorded with a rationale; this is the same traceability defect T073 fixed for ammunition. Transcribe both tables (or the rule that generates them) into Part K, correct Part C2's "same matrix" claim to name the small-craft exception, and where the source page prices nothing say so explicitly and extend the FR-002 omissions note in `CONTEXT.md` rather than leaving untraceable numbers in `tables.py`, per Constitution I / FR-001 / FR-019 (contradicts)
- [X] T089 Reconcile `COCKPITS` with `specs/010-starship-generator/data-model.md`, whose static-table row documents it as `small-craft cockpit -> (tons, crew, cost)` while `CockpitRow` in `src/cetools/engine/ships/tables.py` carries only `tons`: nothing reads a cockpit's crew capacity, so `uv run cetools ship build specs/010-starship-generator/examples/fighter.toml` reports a 4-person crew for a craft whose `1_man` cockpit seats one. Either add the `crew` column and have `_build_crew` in `src/cetools/engine/ships/builder.py` cap or check the small-craft crew against it (with a covering test in `tests/test_ship_builder.py`), or correct the data-model row to `(tons)` and state in the `CockpitRow` docstring that cockpit seating is deliberately unenforced because no functional requirement asks for it. Add the missing `SMALL_CRAFT_DRIVE_PERFORMANCE` row to the same static-table list while there, per FR-019 / FR-012 / data-model.md "Static tables" (contradicts)
- [X] T090 Cover and de-hardcode the vehicle hangar, the one FR-009 fitting the builder sizes from the design: `builder.py:236-237` (the `fit.kind == "vehicle_hangar"` branch computing `vehicle_tons x 1.3` tons and `MCr 0.2/ton`) is the only uncovered production path in `src/cetools/engine/ships/`, so a named FR-009 component ships with no build-path test at all (Constitution IV). Add a builder test in `tests/test_ship_builder.py` asserting a 13-ton hangar allocates 16.9 tons at MCr 2.6 and round-trips, and replace the literal table-key comparison with per-vehicle-ton columns on `FittingRow` in `src/cetools/engine/ships/tables.py` — the same remedy T079 applied to `forbidden_on_distributed`, and what tasks.md's own note ("if a story tempts you to branch on a table key in `builder.py`, add a table column instead") requires, per FR-009 / SC-006 / Constitution IV (partial)
- [X] T091 Complete the SC-006 data-driven test that T065 specified as "a new hull size, a new turret weapon, a new fitting": `tests/test_ship_tables.py` currently inserts synthetic rows into `FITTINGS` only (`test_a_new_fitting_row_costs_and_allocates_correctly_with_no_code_change` and the distributed-forbidden case), so the claim that a new hull size or weapon is a data-only edit is asserted nowhere. Add the two missing cases — a synthetic `HULLS` row built and costed end-to-end, and a synthetic `TURRET_WEAPONS` row mounted in a turret and costed — proving neither needs a `builder.py` or `generator.py` change, per SC-006 / T065 (partial)
- [X] T092 Resolve the small-craft navigator in `_build_crew` in `src/cetools/engine/ships/builder.py`, which assigns `navigator = 1` to every craft without Jump-Control software including a `HullClass.SMALL_CRAFT` hull that by rule cannot mount a jump drive (FR-019), so `fighter.toml` reports a navigator on a jump-incapable fighter. research.md Part I documents the navigator rule only in terms of Jump-Control software and never addresses a hull with no jump capability at all. Either zero the navigator for small craft with a covering test in `tests/test_ship_builder.py`, or record the always-a-navigator reading as an explicit SRD-ambiguity resolution in research.md Part I the way the medic and jump-control ambiguities already are, per FR-012 / FR-019 / Constitution I (partial)

---

## Phase 13: Convergence

- [X] T093 Cover the design-schema sections no fixture exercises, so SC-008's lossless round-trip is verified for all of them rather than only the ones the golden designs happen to use: `_parse_ammo` (`src/cetools/engine/ships/design.py:193-207`) and `_dump_ammo` (`design.py:320-330`) are wholly uncovered — no example TOML and no test in `tests/test_ship_design.py` carries a `[[turrets]].ammo` entry — even though contracts/design-schema.md documents both ammo forms (`{ kind = "sand_barrels", count = 20 }` and `{ kind = "missile", type = "standard", count = 12 }`) and FR-010 names ammunition as a required component. The same holds for four `dump_design` branches: a non-default `power_weeks`, `present = false`, a fitting `quantity != 1`, and `vehicle_tons`. Load, dump and round-trip each in `tests/test_ship_design.py` (`loads_design(dump_design(d)) == d` and `build_ship(loads_design(dump_design(ship.design))) == ship`), and add loaded ammunition to a golden fixture in `specs/010-starship-generator/examples/` — `warship.toml`'s turrets are the natural home — updating its hand-worked header and the tonnage/cost assertions in `tests/test_ship_builder.py` to match, per FR-010 / FR-023 / SC-008 / Constitution IV (partial)
- [X] T094 Test the schema-invalid load errors that contracts/design-schema.md's "Rules enforced at load" promises but nothing exercises, leaving `src/cetools/engine/ships/design.py` the least-covered module in the ship package at 85% while every other one is at or above 98%: the untested branches are `[[armor]] entry requires 'type'`/`'percent'`, `[[fittings]] entry requires 'kind'` and its `vehicle_tons` type check, `[[turrets]] entry requires 'mount'`, `[[bays]]`/`[[screens]] entry requires 'kind'`, `[computer] requires 'model'`, the `computer.software[]` `name`/`level` requirements, and the `bridge.present` boolean check. FR-021 requires a clear error for a schema-invalid design file, so each of these messages is a promised behaviour with no test behind it; add one case per branch in `tests/test_ship_design.py` asserting the message names the offending section, per FR-021 / contracts/design-schema.md "Rules enforced at load" / Constitution IV (partial)

---

## Phase 14: Convergence

- [X] T095 Exercise the vault's +4 hull/structure bonus through `build_ship`, which no test does: no fixture in `specs/010-starship-generator/examples/` mounts a `vault` and it is absent from `_FITTING_CHOICES` in `src/cetools/engine/ships/generator.py`, so `hull_points = hull_tons // 50 + hull_structure_bonus` and `structure_points = ceil(hull_tons / 50) + hull_structure_bonus` in `src/cetools/engine/ships/builder.py` are evaluated with the bonus term at `0` in all 1167 tests — a wrong sign, a dropped term or a bad multiplier there would pass the entire suite. T022 called out "the vault's +4 hull/structure points" as required behaviour and `tests/test_ship_tables.py` asserts only the table value, never the built result. Add a test in `tests/test_ship_builder.py` building a design with a vault and asserting hull and structure points each rise by 4 over the same design without one, plus a second vault (quantity 2) proving the bonus multiplies by quantity, per FR-008 / T022 / Constitution IV (partial)
- [X] T096 Allocate low passage berths and emergency low berths in a builder test: FR-009 names four quarters types and `_build_quarters` in `src/cetools/engine/ships/builder.py` handles all four, but only staterooms are ever built. `low_berths` and `emergency_low_berths` appear solely in `tests/test_ship_design.py`'s `test_manually_constructed_design_round_trips`, which round-trips the design without ever calling `build_ship`, and `_select_staterooms` in `src/cetools/engine/ships/generator.py` never selects either, so no generated ship carries them. The loop's `continue` branch keeps line coverage at 100% while the allocation itself goes unverified. Add a test in `tests/test_ship_builder.py` asserting a design with low berths and emergency low berths produces the research Part G figures — 0.5 t / Cr50,000 per low berth and 1 t / Cr100,000 per emergency low berth — as their own `LineItem`s, per FR-009 / Constitution IV (partial)
- [X] T097 Pin spec.md's first Edge Case, "a design that exactly fills the hull yields zero cargo, which is valid", which nothing asserts: no test anywhere checks `cargo_tons == 0`, so the boundary between a legal exact fill and the over-allocation rejected one step beyond it is unverified, even though `build_ship` in `src/cetools/engine/ships/builder.py` distinguishes them with `if cargo_tons < 0`. Add a paired test in `tests/test_ship_builder.py`: a 100-ton hull with `jump_code="A"`, `power_code="A"`, 13 staterooms and 4 low berths builds to `tonnage_used == 100.0` and `cargo_tons == 0.0` without raising, while the same design with one more low berth is rejected with `components use 100.5 tons, hull holds 100`, per spec.md Edge Cases "Zero remaining tonnage" / FR-011 / FR-015 (partial)
