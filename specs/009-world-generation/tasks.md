---
description: "Task list for World Generation implementation"
---

# Tasks: World Generation

**Input**: Design documents from `/specs/009-world-generation/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md, contracts/engine-api.md, quickstart.md

**Tests**: INCLUDED. The plan's Constitution Check mandates Test-First (Principle IV, TDD
red-green-refactor); every module gets a `tests/test_*.py` before implementation, and `ScriptedRolls`
pins probabilistic rules to exact outcomes.

**Organization**: Tasks are grouped by user story (P1 → P2 → P3) so each story can be implemented,
tested, and delivered as an independent increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story the task belongs to (US1, US2, US3)
- Every task lists an exact file path

## Path Conventions

Single project (existing layout): engine at `src/cetools/engine/`, CLI at `src/cetools/cli/`, tests
at `tests/`. The world domain lives in a new `src/cetools/engine/worlds/` subpackage (mirrors
`engine/careers/`); callers import from `cetools.engine.worlds`, never from submodules.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the subpackage skeleton so every later module has a home.

- [X] T001 Create the `src/cetools/engine/worlds/` subpackage skeleton: empty `__init__.py`,
  `tables.py`, `models.py`, `generator.py`, `naming.py`, and `profile.py` module files (each with a
  one-line module docstring), so imports resolve as the domain is filled in.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Wire the chance seam so all three stories can drive deterministic rolls. MUST complete
before any user-story work.

**⚠️ CRITICAL**: No user story can be implemented until this phase is complete.

- [X] T002 Add the world `RollName` members to `src/cetools/engine/rolls.py` (additive only):
  `WORLD_SIZE`, `WORLD_ATMOSPHERE`, `WORLD_HYDROGRAPHICS`, `WORLD_POPULATION`, `WORLD_GOVERNMENT`,
  `WORLD_LAW_LEVEL`, `WORLD_STARPORT`, `WORLD_TECH_LEVEL`, `POPULATION_MODIFIER`,
  `PLANETOID_BELT_PRESENCE`, `PLANETOID_BELT_COUNT`, `GAS_GIANT_PRESENCE`, `GAS_GIANT_COUNT`,
  `NAVAL_BASE`, `SCOUT_BASE`, `PIRATE_BASE`, `WORLD_PRESENCE`, `WORLD_NAME_STEM` (research.md D2).

**Checkpoint**: Foundation ready — user-story implementation can begin.

---

## Phase 3: User Story 1 - Generate a single world profile (Priority: P1) 🎯 MVP

**Goal**: `generate_world(rolls)` produces a `World` whose Starport, Size, Atmosphere, Hydrographics,
Population, Government, Law Level, and Technology Level obey every SRD dice rule, DM, cap, floor, and
inter-characteristic dependency, and renders as the classic pseudo-hex UWP string (e.g. `A867A9C-F`).

**Independent Test**: Generate a batch of worlds; every UWP falls in its SRD range (SC-001), every
dependency holds (Size-0 ⇒ Atmo 0 & Hydro 0; Pop-0 ⇒ Gov/Law/TL 0; TL raised to mandated minimum)
(SC-002), and the profile string round-trips to the same values.

### Tests for User Story 1 ⚠️ (write first, ensure they FAIL)

- [X] T003 [P] [US1] Table-invariant tests in `tests/test_world_tables.py`: `STARPORT_BY_ROLL` maps
  every clamped roll to `X/E/D/C/B/A` per the Primary Starport table; `TL_DM_BY_VALUE` matches
  research.md Appendix C1 (including the Hydrographics-0 `+1` entry); `TL_MINIMUMS` matches C2;
  `HYDRO_DM_BY_ATMOSPHERE`, `POPULATION_DMS`, `GOVERNMENT_TYPES`, `LAW_LEVELS` have the SRD shapes.
- [X] T004 [P] [US1] `World` model tests in `tests/test_world_models.py`: `profile` renders SRD order
  with the hyphen before TL; `head_count == population_modifier * 10**population`; the frozen
  dataclass enforces SC-001 ranges and SC-002 dependencies for hand-built instances.
- [X] T005 [P] [US1] `generate_world` rule tests in `tests/test_world_generator.py` using
  `ScriptedRolls`: pin each characteristic (Size `2D6−2`; Atmosphere `2D6−7+Size` with Size-0 → 0 and
  cap 15; Hydrographics DMs and Size-0/1 → 0; Population DMs and clamp; Government/Law Level zeroing;
  Starport lookup; TL DM sum, `≥0` floor, minimum overrides, and Population-0 → TL 0). Add a
  statistical-bounds pass over ≥2000 unseeded worlds asserting SC-001/SC-002 (mirrors quickstart).
  Add a determinism assertion: `generate_world` under two freshly-seeded `RandomRolls(random.Random(n))`
  produces identical worlds (FR-022, SC-005).
- [X] T006 [P] [US1] Profile-rendering tests in `tests/test_world_profile.py`: the UWP string uses
  pseudo-hex for values >9 (letters), literal Starport letter, and the `-TL` suffix (e.g. `A867A9C-F`).
- [X] T007 [P] [US1] Naming tests in `tests/test_world_naming.py`: `generate_world_name(rolls)`
  returns a non-empty title-cased pronounceable string, is deterministic under a seeded `rolls`, and
  a large sample yields ≥10,000 distinct names (FR-026).

### Implementation for User Story 1

- [X] T008 [P] [US1] Encode the P1 SRD tables as data in `src/cetools/engine/worlds/tables.py`:
  `SIZE_DESCRIPTIONS`, `ATMOSPHERE_DESCRIPTIONS`, `HYDRO_DM_BY_ATMOSPHERE`, `POPULATION_DMS`
  (per-field predicate data), `STARPORT_BY_ROLL`, `GOVERNMENT_TYPES`, `LAW_LEVELS`, `TL_DM_BY_VALUE`,
  and `TL_MINIMUMS` (research.md Appendix C1/C2, Principle V — no logic).
- [X] T009 [P] [US1] Define `TravelZone` enum and the `World` frozen dataclass in
  `src/cetools/engine/worlds/models.py`, with `profile` and `head_count` derived properties
  (data-model.md World section).
- [X] T010 [P] [US1] Implement the curated stem pool and `generate_world_name(rolls=None)` in
  `src/cetools/engine/worlds/naming.py`, assembling 2–3 stems via `rolls.choose(..., WORLD_NAME_STEM)`
  and title-casing (research.md D4; ≥10,000 distinct names).
- [X] T011 [P] [US1] Implement the UWP profile-string renderer in
  `src/cetools/engine/worlds/profile.py`, reusing `engine/pseudohex.to_pseudohex` for the 0–15 digits
  and the literal Starport letter (research.md D5).
- [X] T012 [US1] Implement `generate_world(rolls=None, *, name=None, travel_zone_red=False)` in
  `src/cetools/engine/worlds/generator.py`, running the SRD order size → atmosphere → hydrographics →
  population → government → law_level → starport → tech_level, applying all DMs/caps/floors/zeroing
  and TL minimums, and defaulting the name via `generate_world_name` (depends on T008–T011).
- [X] T013 [US1] Export `generate_world`, `generate_world_name`, `World`, and `TravelZone` from
  `src/cetools/engine/worlds/__init__.py` as the public surface (contracts/engine-api.md).

**Checkpoint**: `generate_world` is fully functional and independently testable (MVP). The engine
produces a correct, reproducible single UWP with a default name.

---

## Phase 4: User Story 2 - Complete system data and full profile line (Priority: P2)

**Goal**: `generate_system(rolls)` wraps a `World` with Population Modifier, planetoid belts, gas
giants, bases (reduced to a base code), trade codes, travel zone, and allegiance, and renders the
full SRD world-data line. A `cetools world generate` CLI command prints it.

**Independent Test**: Generate fully-described systems; Population Modifier and head-count are
consistent (FR-011), base presence/exclusions hold (SC-004), trade codes match the C3 table exactly
(SC-003), the Amber rule flags correctly, and the rendered line contains name, hex, profile, base
code, trade codes, travel-zone code, PBG triple, and allegiance (FR-018).

### Tests for User Story 2 ⚠️ (write first, ensure they FAIL)

- [ ] T014 [P] [US2] Trade-code table tests in `tests/test_world_tables.py`: `TRADE_CODES` reproduces
  research.md Appendix C3 for all 18 classifications (Ag, As, Ba, De, Fl, Ga, Hi, Ht, Ic, In, Lo, Lt,
  Na, Ni, Po, Ri, Wa, Va) as per-field allowed-value sets.
- [ ] T015 [P] [US2] `System` model tests in `tests/test_world_models.py`: `base_code` mapping
  (`A`/`N`/`S`/`G`/`P`/blank); `pbg` renders each slot via `pseudohex` (assert a Population Modifier
  of 10 renders `A`, e.g. `pbg == "A10"`-style, not a broken 4-char string); and the base-exclusion
  invariants (`size==0 ⇒ belts>=1`, no scout on E/X, no pirate with A or a naval base).
- [ ] T016 [P] [US2] `generate_system` rule tests in `tests/test_world_generator.py` via
  `ScriptedRolls`: Population Modifier (`2D6−2`, min 1 when pop>0 else 0); belt presence `2D6≥4` and
  count `1D6−3` min 1 with Size-0 guarantee; gas-giant presence `2D6≥5` and count `1D6−2` min 1;
  naval/scout/pirate rolls with the scout DMs and all exclusions; trade-code assignment against a
  reference fixture with ≥1 world per classification plus a multi-code and a no-code world (SC-003);
  Amber flagging for Atmo≥10 / Gov∈{0,7,10} / Law∈{0,9+} (FR-016). Add a statistical-bounds pass over
  ≥10,000 unseeded systems asserting belt presence ≈92%, gas-giant presence ≈83%, and naval-base
  presence ≈42% (given a Class-A/B starport) each within ±2pp, and that the base-exclusion rules are
  never violated (SC-004). Add a determinism assertion: `generate_system` under two freshly-seeded
  `RandomRolls(random.Random(n))` produces identical systems (FR-022, SC-005).
- [ ] T017 [P] [US2] Data-line rendering tests in `tests/test_world_profile.py`: `System.data_line`
  emits name, `CCRR` (or blanks), profile, base code, trade codes/remarks, travel-zone code, PBG
  triple, and allegiance with blanks preserved for absent fields (research.md D5). Assert an
  unspecified allegiance defaults to and renders `Na` (FR-017), and that a Population-Modifier-10
  system renders its PBG slot as `A` (I1).
- [ ] T018 [P] [US2] CLI tests in `tests/test_cli.py`: `cetools world generate --seed 42` prints one
  data line and exits 0; `--name Terra` names the world; `--count 2` prints two lines; `--name` with
  `--count > 1` exits 1 with the usage message (contracts/cli.md).

### Implementation for User Story 2

- [ ] T019 [US2] Add `TRADE_CODES` (per-field allowed-value sets, table order) to
  `src/cetools/engine/worlds/tables.py` (research.md Appendix C3).
- [ ] T020 [US2] Add the `System` frozen dataclass to `src/cetools/engine/worlds/models.py` with
  `base_code`, `pbg` (each of `population_modifier`/`planetoid_belts`/`gas_giants` rendered via
  `pseudohex.to_pseudohex`, so a modifier of 10 → `A`), and `data_line` derived members
  (data-model.md System section).
- [ ] T021 [US2] Extend `src/cetools/engine/worlds/generator.py` with the trade-code matcher, Amber
  travel-zone rule, and `generate_system(rolls=None, *, name=None, hex=None, allegiance="Na",
  travel_zone_red=False)` computing Population Modifier, belts, gas giants, and bases in the SRD
  exclusion order (depends on T012, T019, T020).
- [ ] T022 [US2] Add the full world-data line renderer to `src/cetools/engine/worlds/profile.py`
  (name, hex, profile, base code, trade codes, travel-zone code, PBG, allegiance).
- [ ] T023 [US2] Export `generate_system` and `System` from
  `src/cetools/engine/worlds/__init__.py` (contracts/engine-api.md).
- [ ] T024 [US2] Create the `cetools world` Typer sub-app in `src/cetools/cli/world.py` with the
  `generate` command (`--name`, `--count/-n`, `--allegiance`, `--seed`), building
  `RandomRolls(random.Random(seed))` when seeded, printing one data line per system, and erroring on
  `--name` with `--count > 1` (contracts/cli.md — pure I/O routing).
- [ ] T025 [US2] Register the world sub-app in `src/cetools/cli/main.py`
  (`app.add_typer(world.app, name="world")`) and update the root callback help text.

**Checkpoint**: A referee can generate a full system data line in one command; US1 and US2 both work.

---

## Phase 5: User Story 3 - Generate a subsector of worlds (Priority: P3)

**Goal**: `generate_subsector(rolls)` walks the 8×10 hex grid, checks each hex for presence at the
configured density, generates a full `System` per occupied hex with a unique auto-name, and a
`cetools world subsector` command prints the listing.

**Independent Test**: Generate a subsector; the grid is 8×10, each hex is independently checked at
the density (SC-007), every occupied hex carries a valid system whose `CCRR` matches its position,
and all auto-generated names are unique within the subsector (SC-008).

### Tests for User Story 3 ⚠️ (write first, ensure they FAIL)

- [ ] T026 [P] [US3] `Subsector` model tests in `tests/test_world_models.py`: `Density` DMs
  (rift −2, sparse −1, standard 0, dense +1); every `system.hex` is within columns 01–08 / rows 01–10
  and unique.
- [ ] T027 [P] [US3] `generate_subsector` tests in `tests/test_world_generator.py`: per-hex presence
  `1D6 + density.dm >= 4` with statistical occupancy within ±2pp per density (SC-007); each occupied
  hex is a valid system with a matching `CCRR`; auto-generated names are unique across the subsector
  and collisions regenerate (bounded max-attempts guard raises `ValueError` when exhausted) (SC-008).
  Add a determinism assertion: `generate_subsector` under two freshly-seeded
  `RandomRolls(random.Random(n))` produces an identical subsector (FR-022, SC-005).
- [ ] T028 [P] [US3] Subsector CLI tests in `tests/test_cli.py`: `cetools world subsector --seed 7`
  prints hex-prefixed lines and exits 0; `--density dense` yields more occupied hexes than default;
  an invalid `--density` value exits 1 (contracts/cli.md).

### Implementation for User Story 3

- [ ] T029 [US3] Add the `Density` enum and the `Subsector` frozen dataclass to
  `src/cetools/engine/worlds/models.py` (data-model.md Subsector section).
- [ ] T030 [US3] Implement `generate_subsector(rolls=None, *, density=Density.STANDARD)` in
  `src/cetools/engine/worlds/generator.py`: walk 80 hexes, presence via `d6()` + density DM ≥ 4,
  `generate_system(..., hex="CCRR")` per occupied hex, and enforce per-subsector name uniqueness by
  regenerating on collision with a bounded max-attempts guard (research.md D4, depends on T021).
- [ ] T031 [US3] Export `generate_subsector`, `Subsector`, and `Density` from
  `src/cetools/engine/worlds/__init__.py` (contracts/engine-api.md).
- [ ] T032 [US3] Add the `subsector` command (`--density`, `--seed`) to `src/cetools/cli/world.py`,
  printing one `CCRR`-prefixed data line per occupied hex ordered by coordinate (contracts/cli.md).

**Checkpoint**: All three user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, docs-check compliance, and the full quality gate.

- [ ] T033 [P] Add the `engine/worlds/` package (and its modules) to the module map in
  `CONTRIBUTING.md` for human readers (plan.md notes `check_docs.py` globs only top-level
  `engine/*.py`, so subpackage modules are not auto-enforced).
- [ ] T034 [P] Document the `cetools world` commands and world generation in `README.md` (backtick
  every referenced symbol so `scripts/check_docs.py` resolves it; keep dashes tight).
- [ ] T035 Run `uv run python scripts/check_docs.py` and fix any unresolved symbols, missing
  module-map entries, or spaced dashes in the touched docs.
- [ ] T036 Run the quickstart.md validation (library, CLI, subsector, and SRD-invariant snippets) and
  confirm each prints its expected success output.
- [ ] T037 Run the full quality gate — `uv run black . && uv run flake8 src tests && uv run pytest &&
  uv run python scripts/check_docs.py` — and confirm Black clean, flake8 zero warnings, pytest green
  with `src/cetools` coverage ≥ 85%, and docs check passing.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies — start immediately.
- **Foundational (Phase 2)**: depends on Setup — BLOCKS all user stories.
- **User Stories (Phase 3–5)**: all depend on Foundational. They share `tables.py`, `models.py`,
  `generator.py`, `profile.py`, and `__init__.py`, so they are naturally sequential (P1 → P2 → P3);
  each nonetheless remains independently testable at its checkpoint.
- **Polish (Phase 6)**: depends on the stories being delivered.

### User Story Dependencies

- **US1 (P1)**: only Foundational. The MVP — no dependency on other stories.
- **US2 (P2)**: builds on the US1 `World`/`generator` but is independently testable via
  `generate_system`.
- **US3 (P3)**: builds on the US2 `generate_system` (each hex is a full system) but is independently
  testable via `generate_subsector`.

### Within Each User Story

- Tests are written first and must FAIL before implementation (Principle IV).
- Tables and models before the generator; generator before the public `__init__.py` export; engine
  before the CLI.

### Parallel Opportunities

- Setup is a single task.
- Within a story, the `[P]` test tasks (different `tests/test_*.py`) run together, and the `[P]`
  implementation tasks touching **different** files (`tables.py`, `models.py`, `naming.py`,
  `profile.py` in US1) run together; the generator task then depends on them.
- Cross-story `[P]` is limited because the stories edit the same engine files sequentially.
- Polish doc tasks T033 and T034 (different files) run in parallel.

---

## Parallel Example: User Story 1

```bash
# Write all US1 tests together (they share no files):
Task: "Table-invariant tests in tests/test_world_tables.py"      # T003
Task: "World model tests in tests/test_world_models.py"          # T004
Task: "generate_world rule tests in tests/test_world_generator.py"  # T005
Task: "Profile-rendering tests in tests/test_world_profile.py"   # T006
Task: "Naming tests in tests/test_world_naming.py"               # T007

# Then build the independent US1 modules together:
Task: "P1 SRD tables in src/cetools/engine/worlds/tables.py"     # T008
Task: "TravelZone + World model in src/cetools/engine/worlds/models.py"  # T009
Task: "generate_world_name in src/cetools/engine/worlds/naming.py"       # T010
Task: "UWP profile renderer in src/cetools/engine/worlds/profile.py"     # T011
# T012 (generator) waits on all four; T013 (__init__) waits on T012.
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 Setup → Phase 2 Foundational.
2. Phase 3 US1 (tests red → green).
3. **STOP and VALIDATE**: run the SRD-invariant quickstart snippet over ≥2000 worlds (SC-001, SC-002).
4. The single correct, reproducible, named UWP is a shippable MVP.

### Incremental Delivery

1. Setup + Foundational → foundation ready.
2. US1 → test → the atomic UWP (MVP).
3. US2 → test → full system data line + `cetools world generate`.
4. US3 → test → 8×10 subsector + `cetools world subsector`.
5. Polish → docs + full quality gate.

---

## Notes

- `[P]` = different files, no dependency on an incomplete task.
- `[Story]` label maps each task to its user story for traceability.
- Every rule test uses `ScriptedRolls` to pin the dice; statistical-bounds tests use unseeded runs.
- Verify tests fail before implementing; commit after each task or logical group.
- Engine code MUST NOT import from `cli/` (Principle II); the CLI is pure I/O routing (Principle III).
