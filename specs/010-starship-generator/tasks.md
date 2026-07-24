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

- [ ] T049 [P] [US4] Write failing `BAYS` and `SCREENS` table tests (each row is 50 t with its SRD cost; bays carry the +1 t fire-control rule) in `tests/test_ship_tables.py`
- [ ] T050 [P] [US4] Add a bay-and-screen-equipped golden design `specs/010-starship-generator/examples/heavy-cruiser.toml` with its hand-worked expected figures in a comment header
- [ ] T051 [US4] Write failing bay/screen builder tests (golden figures; 50 t + 1 t fire control and one hardpoint per bay; screen tonnage and cost; `Crew.gunners` counts one per bay and `Crew.screen_operators` one per screen; bay rejected when hardpoints are exhausted; bay rejected when free tonnage is under 50; bay on a small craft rejected with `small craft cannot mount a weapon bay`) in `tests/test_ship_builder.py`
- [ ] T052 [P] [US4] Write failing design I/O tests for the `[[bays]]` and `[[screens]]` sections (load, dump, round-trip, unknown `kind` rejected at load as a shape error; a bay on a small-craft hull *loads* cleanly and is rejected by `build_ship`, not at load) in `tests/test_ship_design.py`
- [ ] T053 [P] [US4] Write failing sheet tests asserting bays and screens appear in the armaments section and screen operators appear in the crew section in `tests/test_ship_sheet.py`
- [ ] T054 [P] [US4] Write failing generator tests asserting bays/screens only ever appear on hulls with the hardpoints and free tonnage to hold them, never on small craft, in `tests/test_ship_generator.py`

### Implementation for User Story 4

- [ ] T055 [US4] Add the `BAYS` and `SCREENS` tables from research.md Part H to `src/cetools/engine/ships/tables.py`
- [ ] T056 [US4] Implement bay and screen allocation in `src/cetools/engine/ships/builder.py`: 50 t plus 1 t fire control per bay, one hardpoint per bay counted against the hull limit, screen tonnage and cost, the small-craft bay rejection, one gunner per bay in `Crew.gunners` and one operator per screen in `Crew.screen_operators`
- [ ] T057 [P] [US4] Add the `[[bays]]` and `[[screens]]` sections to `loads_design` and `dump_design` in `src/cetools/engine/ships/design.py`
- [ ] T058 [P] [US4] Render bays and screens in the armaments section, and screen operators in the crew section, in `src/cetools/engine/ships/sheet.py`
- [ ] T059 [P] [US4] Implement bay and screen selection (using `SHIP_BAY` and `SHIP_SCREEN`), gated on available hardpoints and free tonnage and disabled for small craft, in `src/cetools/engine/ships/generator.py`

**Checkpoint**: All four user stories are independently functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, doc-check compliance, the remaining success-criteria assertions (SC-006,
SC-007), and the full quality gate.

- [ ] T060 [P] Add the `engine/ships/` package (and its seven modules) to the module map in `CONTRIBUTING.md`
- [ ] T061 [P] Document the `cetools ship build` and `cetools ship generate` commands with a runnable example in `README.md`
- [ ] T062 [P] Record the ship-design domain and its SRD source in `CONTEXT.md`, including the FR-002 note that referee-discretion steps (crew role assignment beyond the SRD minimum, mission-specific fittings) are deliberately omitted
- [ ] T063 Run `uv run python scripts/check_docs.py` and fix any broken backticked symbol, non-running README example, or spaced dash introduced by T060–T062
- [ ] T064 Add a performance assertion that a single build and a single generation each complete in under 0.1 seconds (SC-007) in `tests/test_ship_generator.py`
- [ ] T065 [P] Add a data-driven-extensibility test (SC-006) in `tests/test_ship_tables.py`: insert a synthetic row into a copy of a table (a new hull size, a new turret weapon, a new fitting), build a design that uses it, and assert it costs and allocates correctly—proving a new SRD entry needs no change to `builder.py` or `generator.py`
- [ ] T066 Execute every command in [quickstart.md](./quickstart.md) and confirm the stated expected output for Stories 1–4
- [ ] T067 Run the full quality gate `uv run black . && uv run flake8 src tests && uv run pytest && uv run python scripts/check_docs.py` and confirm `src/cetools` coverage stays at or above 85%

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
