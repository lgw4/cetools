# Tasks: Vehicle Design System

**Input**: Design documents from `/specs/001-vehicle-design/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Tests**: Test tasks are **mandatory** here, not optional. Constitution Principle III makes strict
red-green TDD non-negotiable, and every test task below is written to fail first. Where a task pairs
a test with an implementation, the test task precedes it and must be observed red before the
implementation task begins.

**Organization**: Tasks are grouped by user story so each story can be implemented and tested
independently. The spec's Assumptions section records the deliberate decision to ship all four
stories in one pull request; the phase boundaries remain real checkpoints even so.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Every task names its exact file path

## Path Conventions

Single project, library-first: `src/cetools/engine/vehicles/` for the domain,
`src/cetools/cli/vehicle.py` for the binding, `tests/test_vehicle_*.py` mirroring the source layout.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Get the package skeleton and the deterministic seam in place so every later phase has
somewhere to land.

- [ ] T001 Create the vehicles package directory with a placeholder `src/cetools/engine/vehicles/__init__.py` containing a module docstring and an empty `__all__: tuple[str, ...] = ()`, plus an empty `src/cetools/engine/vehicles/catalog/` directory
- [ ] T002 Add a failing test in `tests/test_rolls.py` asserting the nineteen `VEHICLE_*` members exist on `RollName` with the exact snake-case values from research R-009 (`VEHICLE_ROLE`, `VEHICLE_TECH_LEVEL`, `VEHICLE_CHASSIS`, `VEHICLE_CONFIGURATION`, `VEHICLE_ARMOR`, `VEHICLE_PROPULSION`, `VEHICLE_POWER_PLANT`, `VEHICLE_DRIVE_CODE`, `VEHICLE_FUEL`, `VEHICLE_CONTROLS`, `VEHICLE_COMMUNICATIONS`, `VEHICLE_SENSORS`, `VEHICLE_COMPUTER`, `VEHICLE_CREW`, `VEHICLE_ACCOMMODATION`, `VEHICLE_COMPONENT`, `VEHICLE_MOUNT`, `VEHICLE_WEAPON`, `VEHICLE_AMMUNITION`), and asserting the count, so a name added later without a decision to draw it fails here
- [ ] T003 Add the nineteen `VEHICLE_*` members to the `RollName` `StrEnum` in `src/cetools/engine/rolls.py`, grouped as a block after the `SHIP_*` members and ordered as the build order draws them, turning T002 green (FR-030)

**Checkpoint**: `uv run pytest tests/test_rolls.py --no-cov` green; `import cetools.engine.vehicles` succeeds.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The thirty-seven transcribed table constants, the six prose option families, the prose
primitives, the record types and the design-file parser. Everything in every user story reads from
these.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

**Note on the table tasks**: all table tests live in one file and all table data lives in one file,
so the table tasks below are strictly sequential rather than parallel. Each pair is one SRD table
group from research R-001: write the test naming each row's key columns and expected values against
the SRD text, observe it red, then transcribe.

### Row types and the first tables

- [ ] T004 Write failing tests in `tests/test_vehicle_tables.py` for the chassis and configuration group: `CHASSIS` (24 rows, keys `"1"`–`"9"` and `"A"`–`"Q"` with no I and no O, columns tons, spaces, price, build hours, size, example) and `CONFIGURATIONS` (closed ×1, open ×0.9), including the assertion that `CHASSIS` stops at 20 tons and that every row's transcribed `spaces` equals its `tons` × 12, which is what makes FR-005's "computed at twelve to the ton" and the printed column the same number rather than two sources; record any row where they disagree as an FR-017a divergence instead of silently preferring one
- [ ] T005 Create `src/cetools/engine/vehicles/tables.py` with the `ChassisRow` and `ConfigurationRow` frozen dataclasses and the `CHASSIS` and `CONFIGURATIONS` annotated module constants, each followed by a bare docstring naming its SRD table and key columns, no functions and no in-package imports (FR-003)
- [ ] T006 Record the chassis code H transcription decision as a comment at the `CHASSIS` definition site in `src/cetools/engine/vehicles/tables.py`: Cr23,350 is transcribed as printed even though it breaks the F→G→J progression, because nothing in the chapter contradicts it (research R-003 defect 5, FR-017a)
- [ ] T006a Write failing tests in `tests/test_vehicle_tables.py` for `SUBMERSIBLE_DIVE_DEPTH` (6 rows keyed by tech level, columns safe dive depth and crush depth), including the assertion that nothing in the package reads it, since it is transcribed only to satisfy FR-003's completeness clause
- [ ] T006b Add `DiveDepthRow` and `SUBMERSIBLE_DIVE_DEPTH` to `src/cetools/engine/vehicles/tables.py` with a docstring recording that the table is watercraft-only, is transcribed because FR-003 requires watercraft rows ship and then be refused, and is read by nothing (FR-003, FR-013)

### Armor, structure, drives and fuel

- [ ] T007 Write failing tests in `tests/test_vehicle_tables.py` for `ARMOR` (7 rows: type, tl, base, additional protection, price, max armor) and `HULL_STRUCTURE` (8 rows keyed by tons band)
- [ ] T008 Add `ArmorRow`, `HullStructureRow`, `ARMOR` and `HULL_STRUCTURE` to `src/cetools/engine/vehicles/tables.py`
- [ ] T009 Write failing tests in `tests/test_vehicle_tables.py` for `POWER_PLANTS` (10), `PROPULSION` (16) and `DRIVE_COSTS` (24 codes `"A"`–`"Z"` with no I and no O), including the assertion that drive code D carries 0.75 spaces rather than the 0.4 the drive-cost table prints
- [ ] T010 Add `PowerPlantRow`, `PropulsionRow`, `DriveRow`, `POWER_PLANTS`, `PROPULSION` and `DRIVE_COSTS` to `src/cetools/engine/vehicles/tables.py`, taking the fuel table's 0.75 for drive code D and recording the decision at the definition site (research R-003 defect 1, FR-017a)
- [ ] T011 Write failing tests in `tests/test_vehicle_tables.py` for `DRIVE_PERFORMANCE` as one merged `dict[str, dict[str, int | None]]` keyed drive code → chassis code, asserting the full 24×24 key set, that `None` stands for the printed em-dash, and spot values from both of the book's two page-split tables
- [ ] T012 Add the merged `DRIVE_PERFORMANCE` constant to `src/cetools/engine/vehicles/tables.py` with a docstring recording that the book's two tables are merged because their split is a page-width artifact (research R-001)
- [ ] T013 Write failing tests in `tests/test_vehicle_tables.py` for `BASE_SPEED` (15 rows, tl plus speeds at performance 1–6 in kph), `POWER_PLANT_FUEL` (24 rows keyed by drive code), `FUEL_CONSUMPTION` (10 rows) and `AGILITY_MODIFIERS` (24 rows), including that the Mole's speeds are flagged as meters per hour and that antimatter is a special case rather than a multiplier
- [ ] T014 Add `SpeedRow`, `FuelRow`, `FuelModRow`, `AgilityRow`, `BASE_SPEED`, `POWER_PLANT_FUEL`, `FUEL_CONSUMPTION` and `AGILITY_MODIFIERS` to `src/cetools/engine/vehicles/tables.py`, transcribing the "Huge (20+ tons)" and "Gargantuan (100+ tons)" agility rows even though they are unreachable under the 20-ton cap (FR-003)

### Controls, electronics, crew and components

- [ ] T015 Write failing tests in `tests/test_vehicle_tables.py` for `CONTROLS` (5), `DRONE_CONTROLLERS` (5), `ROBOT_BRAINS` (3), `COMMUNICATIONS` (4), `ALTERNATIVE_COMMUNICATORS` (3), `SENSORS` (5) and `COMPUTERS` (6), asserting Primitive controls at TL2, that Primitive's price is a chassis-price modifier rather than a figure, that the standard sensor max range is transcribed as the printed "Very Long (500 km)", and that computer models 2 and up take no space
- [ ] T016 Add the control and electronics row types and constants to `src/cetools/engine/vehicles/tables.py`, taking the prose's TL2 for Primitive controls and recording both that decision and the untouched sensor-range transcription at their definition sites (research R-003 defects 2 and 4, FR-017a)
- [ ] T017 Write failing tests in `tests/test_vehicle_tables.py` for `ACCOMMODATIONS` (12), `LIFE_SUPPORT` (2), `CARGO_TRAILERS` (6), `MANIPULATOR_MAXIMUMS` (4 tech levels 5, 8, 11, 14) and `ADDITIONAL_COMPONENTS` (34 rows plus the Folding Wings/Rotors row recovered from prose), asserting the Wet Bar reads 1.5 spaces at Cr2,000 and that at least one component carries a negative price
- [ ] T018 Add the crew and component row types and constants to `src/cetools/engine/vehicles/tables.py`, un-shifting the Wet Bar row per its prose and adding the Folding Wings/Rotors (TL3) row from its prose entry, recording both at their definition sites (research R-003 defects 3 and 6, FR-017a)

### Armaments

- [ ] T019 Write failing tests in `tests/test_vehicle_tables.py` for `GUN_PORT_WEAPONS` (24), `WEAPON_MOUNTS` (6, with Gun Shield priced per point of armor and carrying no `tl`) and `TURRETS` (3, carrying formula coefficients rather than figures)
- [ ] T020 Add `GunPortWeaponRow`, `MountRow`, `TurretRow` and their constants to `src/cetools/engine/vehicles/tables.py`
- [ ] T021 Write failing tests in `tests/test_vehicle_tables.py` for `TURRET_WEAPONS` (76 rows keyed by weapon-at-TL name such as `"howitzer-tl12"`) and `WEAPON_AMMUNITION` (11 rows keyed by TL-agnostic weapon family), asserting that the fourteen recurring families each appear at every TL the book prints and that Missile Rack defers to the missile table
- [ ] T022 Add `TurretWeaponRow`, `AmmunitionRow`, `TURRET_WEAPONS` and `WEAPON_AMMUNITION` to `src/cetools/engine/vehicles/tables.py`
- [ ] T023 Write failing tests in `tests/test_vehicle_tables.py` for `ORDINANCE_BAY_WEAPONS` (12, six of them watercraft-only torpedo rows), `MISSILES` (10) and `ANTI_MISSILE_SYSTEMS` (9)
- [ ] T024 Add `OrdinanceRow`, `MissileRow`, `AntiMissileRow` and their constants to `src/cetools/engine/vehicles/tables.py`, transcribing the truncated Torpedo Nuclear Heavy row as the source gives it and recording that at the definition site (research R-003 defect 7)

### The six prose option families

**Note**: these are the entries the chapter prints as definition lists rather than as tables
(research R-001a). They are not optional extras: the Air/Raft is streamlined, three description
slots render from them, and FR-013 refuses three configuration options by name, so nothing downstream
works without them. One shared `OptionRow` carries all six, because they share a modifier shape.

- [ ] T026a Write failing tests in `tests/test_vehicle_tables.py` for `OptionRow`: every modifier field defaults to the identity (`spaces` and every percentage 0, `speed_mult` 1.0, `agility_mod` 0, `max_selections` 1), so a row states only what the chapter states, and a zero-price zero-space row is legal because several entries change only a derived figure
- [ ] T026b Write failing tests in `tests/test_vehicle_tables.py` for `CONFIGURATION_OPTIONS` (11) and `ARMOR_OPTIONS` (5), asserting Streamlined at +300% chassis price with `speed_mult` 5.0, Open Frame at −20%, the four Environmental Protection Systems priced per space of chassis, Wave-Piercing Hull at 5% of chassis spaces rounded up, Self-Sealing and Reflec priced per ton, and Reinforced Hull and Reinforced Structure carrying `max_selections=2` per their own prose
- [ ] T026c Add `OptionRow`, `CONFIGURATION_OPTIONS` and `ARMOR_OPTIONS` to `src/cetools/engine/vehicles/tables.py`, each constant followed by a bare docstring naming the SRD section it is transcribed from and recording that the section is prose rather than a table (FR-003a)
- [ ] T026d Write failing tests in `tests/test_vehicle_tables.py` for `DRIVE_OPTIONS` (11), `CONTROL_OPTIONS` (1), `COMPUTER_OPTIONS` (1) and `ARMAMENT_OPTIONS` (5), asserting Increased Agility at +50% chassis price with `agility_mod` +1 capped at three selections, Decreased Agility at −25% capped at two, that Extended Operational Environment Range is present in `DRIVE_OPTIONS`, and that Heavy and Light Turret Weapon are recorded as mutually exclusive
- [ ] T026e Add `DRIVE_OPTIONS`, `CONTROL_OPTIONS`, `COMPUTER_OPTIONS` and `ARMAMENT_OPTIONS` to `src/cetools/engine/vehicles/tables.py`, recording at the `DRIVE_OPTIONS` site that Extended Operational Environment Range is relocated here from the Atmospheres and Aircraft section, where the chapter prints it four sections away from the drive options it belongs with (FR-003a, FR-010)

### Special rules and the derived constants

- [ ] T025 Write failing tests in `tests/test_vehicle_tables.py` for `LIFT_ENVELOPES` (4), `ANIMAL_GAITS` (4), `DRAFT_ANIMALS` (5) and `SAILING_SPEEDS` (3)
- [ ] T026 Add `LiftEnvelopeRow`, `GaitRow`, `AnimalRow`, `SailingRow` and their constants to `src/cetools/engine/vehicles/tables.py`
- [ ] T027 Write failing tests in `tests/test_vehicle_tables.py` for `LOCOMOTION_ALIASES`, asserting the nine aliases are exactly `grav`, `wheeled`, `tracked`, `rotor`, `jet`, `legged`, `rail`, `mole`, `non-powered`, that every alias resolves to at least one `PROPULSION` key (SC-010), and that no alias points at Screw Propeller or Sails
- [ ] T028 Write failing tests in `tests/test_vehicle_tables.py` for `WATERCRAFT_ONLY`, asserting membership of the submersible, hydrofoil and wave-piercing hull entries of `CONFIGURATION_OPTIONS`, screw propeller and sails in `PROPULSION`, the underwater package in `SENSORS`, the six torpedo rows of `ORDINANCE_BAY_WEAPONS` and floats/pontoons in `ADDITIONAL_COMPONENTS`, and that every member resolves to a real key in its own constant. That last assertion only became satisfiable once T026b transcribed the configuration options, three of the members having had no table to resolve against
- [ ] T029 Add `LOCOMOTION_ALIASES: dict[str, tuple[str, ...]]` and `WATERCRAFT_ONLY: frozenset[str]` to `src/cetools/engine/vehicles/tables.py` (FR-013, FR-026a)
- [ ] T030 Write a failing test in `tests/test_vehicle_tables.py` asserting three counts and one prohibition, so FR-003's and FR-003a's completeness is checkable against numbers rather than at review: exactly **37** SRD table constants covering the **38** in-scope tables of the chapter's 40 (the two Drive Performance tables having merged, and Missile Time to Impact and Missile To-Hit being the only exclusions, as play rules under FR-010); exactly **6** option-family constants holding **34** entries; and no function or method definition anywhere in `tables.py`. Name the two excluded tables in the test as a comment so a future reader sees that 38 is a decision and not an oversight
- [ ] T031 Verify T030 green and run the mutation check from `quickstart.md` on three rows chosen from different groups: alter a value, confirm a test in `tests/test_vehicle_tables.py` fails, restore from a copy rather than with `git checkout`

### Prose, records and the design file

- [ ] T032 [P] Write failing tests in `tests/test_vehicle_prose.py` for the number, money, list and article primitives: fixed-precision rounding with trailing zeros stripped, no dangling decimal point, no scientific notation, thousands separators on money, and the spaces, kph, agility and performance-code spellings vehicles need (FR-034)
- [ ] T033 [P] Create `src/cetools/engine/vehicles/prose.py` with those primitives, importing nothing in-package and nothing from `cetools.engine.ships` (FR-001, research R-005)
- [ ] T034 Write failing tests in `tests/test_vehicle_models.py` for the enums `Configuration`, `PowerPlantType`, `PropulsionType`, `ControlInterface` and `MountKind`, asserting lowercase snake string values that mirror their table keys
- [ ] T035 Create `src/cetools/engine/vehicles/models.py` with those enums, importing from `tables` only
- [ ] T036 Write failing tests in `tests/test_vehicle_models.py` for the component fits `ArmorFit`, `DriveFit`, `ComputerFit`, `AccommodationFit`, `ComponentFit` and `AmmunitionFit`: frozen, tuple collections defaulting to `()`, and a `ValueError` naming the offending value and the legal set for each vocabulary error
- [ ] T037 Add those six component fits to `src/cetools/engine/vehicles/models.py`, each validated from `__post_init__` by a module-level `_validate_<name>` declared immediately above it
- [ ] T038 Write failing tests in `tests/test_vehicle_models.py` for `WeaponFit` and `MountFit`: a weapon name must appear in one of the four weapon tables, ammunition is rejected outright for a weapon family with no `WEAPON_AMMUNITION` row, a weapon illegal in its mount kind is rejected by table membership, a mount with no weapons is legal, and every entry of `WeaponFit.options` must key into `ARMAMENT_OPTIONS` with Heavy and Light Turret Weapon rejected together (FR-003a, FR-015, FR-016)
- [ ] T039 Add `WeaponFit` and `MountFit` to `src/cetools/engine/vehicles/models.py`, with a comment recording that FR-015 is satisfied structurally: a magazine is a field of a weapon and a weapon is a field of a mount, so neither is expressible alone. Armament options hang off `WeaponFit` rather than off the design, because the chapter's armament options modify a weapon's price, RoF and damage rather than the vehicle
- [ ] T040 Write failing tests in `tests/test_vehicle_models.py` for `VehicleDesign`: frozen, `tech_level` and `chassis` required with no default, every other field defaulted, no `cargo` field at any level, and each of the four option tuples (`configuration_options`, `armor_options`, `drive_options`, `control_options`) rejecting an entry that is not a key of its family's constant with a `ValueError` naming the option and the legal set (FR-003a, FR-006, FR-011)
- [ ] T041 Add `VehicleDesign` to `src/cetools/engine/vehicles/models.py` with the twenty-six fields listed in `data-model.md` Layer 2, and a comment at `standard_design` recording that it is deliberately one flag for three effects and that there is no second `mass_produced` field, because the chapter defines base construction time as being for mass production of a standard design (FR-007, FR-008)
- [ ] T042 Write failing tests in `tests/test_vehicle_models.py` for `LineItem` (`name`, `spaces`, `price`, `discountable=True`) and `Vehicle`, asserting `Vehicle` is frozen and carries every derived field in `data-model.md` Layer 3, including `design_fee` (FR-007)
- [ ] T043 Add `LineItem` and `Vehicle` to `src/cetools/engine/vehicles/models.py`
- [ ] T044 Write failing tests in `tests/test_vehicle_design.py` for `loads_design`: shape-only validation, `malformed TOML: {detail}` on a parse error, `unknown key(s) in [[mounts.weapons]]: ['ammo']` naming the TOML-literal path, wrong types and unknown enum strings as `ValueError`, a well-formed but rules-illegal design loading cleanly, and the four option families reading as bare top-level arrays of strings rather than as TOML tables, with armament options read from `[[mounts.weapons]].options` (contracts/design-file.md)
- [ ] T045 Create `src/cetools/engine/vehicles/design.py` with `loads_design`, `load_design` and the per-table `_reject_unknown(keys, allowed, path)` guard, propagating `OSError` unwrapped from `load_design`
- [ ] T046 Write failing tests in `tests/test_vehicle_design.py` for `dump_design`: a fixed canonical key order, anything equal to its model default omitted, every bare top-level scalar written before the first table header, and `loads_design(dump_design(d)) == d` over a design exercising nested mounts, weapons and ammunition
- [ ] T047 Add `dump_design` to `src/cetools/engine/vehicles/design.py`, turning T046 green and establishing User Story 4's round-trip guarantee before anything depends on it
- [ ] T047a Write a failing test in `tests/test_vehicle_models.py` (or a small `tests/test_vehicle_imports.py` if it reads better) walking every module under `src/cetools/engine/vehicles/` with `ast` and asserting none of them imports from `cetools.engine.ships` or from `cetools.cli`, and that the in-domain direction matches `contracts/library.md`, where `tables`, `prose` and `published` import nothing in-package. FR-001 is a MUST that until now was carried only as an instruction to whoever typed the import (FR-001, FR-002)

**Checkpoint**: thirty-seven table constants and six option constants transcribed and tested, records validated, design files round-trip, the domain boundary enforced by a test. User story work can begin.

---

## Phase 3: User Story 1 - Build a vehicle from a design file (Priority: P1) 🎯 MVP

**Goal**: A referee writes a TOML design and gets a table-ready Universal Vehicle Description Format
paragraph, with an opt-in component table showing where the price came from.

**Independent Test**: Author one design file by hand, run `uv run cetools vehicle build` against it,
and confirm the printed paragraph reports the values the construction tables produce for those
choices. No other story needs to exist.

### Tests for User Story 1

- [ ] T048 [P] [US1] Write failing tests in `tests/test_vehicle_builder.py` for the build order of FR-004: chassis and spaces at twelve to the displacement ton, configuration, armor, propulsion and power plant with their performance codes, fuel, controls, communications, sensors, computer and software, crew and accommodations, additional components, armaments, cargo as the remainder, then price and build time, asserting that a design breaking several rules reports the first in build order
- [ ] T049 [P] [US1] Write failing tests in `tests/test_vehicle_builder.py` for the validation rules: a missing `tech_level` fails saying tech level is required (FR-011); a component above the vehicle's tech level fails naming the component, its TL and the vehicle's (FR-012, SC-004); a design over 20 tons fails saying vehicles over 20 tons are not yet supported and says nothing about watercraft; a watercraft-only component fails naming watercraft as the missing capability and naming the offending component (FR-013, SC-005); and a spaces overage fails identifying the overage rather than reporting negative cargo (FR-014)
- [ ] T050 [P] [US1] Write failing tests in `tests/test_vehicle_builder.py` for the arithmetic edge cases: fractional space consumption never rounded per component (FR-005), cargo derived as the unconsumed remainder (FR-006), a negative-price component reducing the total rather than being floored at zero (FR-009), an unarmored vehicle taking its chassis base hours because the armor multiplier floors at one (FR-008), a design with no propulsion at all building with performance codes that reflect it, and an empty mount costing what an empty mount costs
- [ ] T051 [P] [US1] Write failing tests in `tests/test_vehicle_builder.py` for the discount: fuel and ammunition line items carry `discountable=False`, the 10% multiplier applies only to discountable lines, and the exempt lines are added at full price afterward (FR-007, research C-002)
- [ ] T051a [P] [US1] Write failing tests in `tests/test_vehicle_builder.py` for the standard-design election as **one flag with three effects** (FR-007, FR-008, research C-002a): two designs differing only in `standard_design` differ in final price, in `design_fee` and in `build_hours`, never in only one of the three; a standard design has `design_fee == 0.0` and base build hours; a new design pays 1% of the discounted total with a Cr100 floor, takes ten times the hours, and carries the fee as its own `discountable=False` line inside the printed price. Include the floor case, a design cheap enough that 1% is under Cr100
- [ ] T051b [P] [US1] Write failing tests in `tests/test_vehicle_builder.py` for option pricing (FR-003a): a percentage-of-chassis-price option, a per-ton option, a per-space option and a flat-price option each priced correctly against the same chassis; Wave-Piercing Hull consuming 5% of chassis spaces rounded up; Streamlined multiplying base speed by 5; Reinforced Hull selected twice and rejected at three; an option naming no entry in its family rejected with the offending name and the legal set; and an option whose tech level exceeds the vehicle's rejected exactly as a component is (FR-012)
- [ ] T052 [P] [US1] Write failing tests in `tests/test_vehicle_description.py` for `render_description`: every slot FR-025 lists is filled, including the three option slots (configuration options, drive options, and the options half of armor type, level and options) rendered from the FR-003a vocabularies, and the price slot printing the figure inclusive of the discount and the design fee as the template's own "(including discounts and fees)" requires; the paragraph contains no fire-control tonnage, no hardpoints sentence, no screens and no small craft hangars (FR-025b, SC-012); and every figure the paragraph prints is reachable without the component table
- [ ] T053 [P] [US1] Write failing tests in `tests/test_vehicle_description.py` for `render_component_table`: every line item with its spaces and price, discountable lines distinguished from exempt ones, then the summed price, the discount, the design fee where one is charged, the final price and the build time, with the lines summing to the printed price and the fee appearing below the discount because it is charged on the discounted total (FR-025a, FR-007)
- [ ] T054 [P] [US1] Write failing tests in the new `cetools vehicle` section of `tests/test_cli.py` for `build`: a valid design prints the paragraph on stdout and nothing else with exit 0; each failure path prints nothing to stdout, prints `str(exc)` verbatim to stderr and exits 1; an unreadable path reports `cannot read design file: {path}`; `--table` leaves the paragraph unchanged and appends the table

### Implementation for User Story 1

- [ ] T055 [US1] Create `src/cetools/engine/vehicles/builder.py` with `build_vehicle(design) -> Vehicle`, one positional argument, no `rolls`, pure and deterministic, implementing FR-004's build order through chassis, configuration, configuration options, armor, armor options and structure, with one `_price_option(row, chassis)` helper resolving the four modifier shapes so no option is priced by a branch on its name (FR-003a)
- [ ] T056 [US1] Extend `build_vehicle` in `src/cetools/engine/vehicles/builder.py` with propulsion, power plant, drive performance lookup, drive options and their agility and fuel-efficiency modifiers, agility, base speed with the option speed multipliers applied, cruise speed and range, and the lift-envelope sizing FR-010 keeps in scope
- [ ] T057 [US1] Extend `build_vehicle` in `src/cetools/engine/vehicles/builder.py` with fuel, controls, control options, robot brain, drone controller, communications, alternative communicator, sensors, computer and its hardened option, crew, accommodations and life support
- [ ] T058 [US1] Extend `build_vehicle` in `src/cetools/engine/vehicles/builder.py` with additional components, trailers, mounts, weapons, their armament options and ammunition, emitting one `LineItem` per component with `discountable=False` for fuel and ammunition
- [ ] T059 [US1] Complete `build_vehicle` in `src/cetools/engine/vehicles/builder.py` with cargo as the remainder, the split discount of FR-007, the design fee of 1% of the discounted total floored at Cr100 when `standard_design` is false as its own non-discountable line, and the build time of FR-008 taking total armor with a floor of one and multiplying by ten when that same flag is false, recording at the build-time calculation both the FR-017a decision (research R-003 defect 8) and that the ×10 and the discount read one flag because the chapter's base construction time is stated to be for mass production of a standard design (research C-002a)
- [ ] T060 [US1] Add the scope gates to `src/cetools/engine/vehicles/builder.py`: a missing chassis row for the displacement raises the over-20-ton message and says nothing about watercraft, and any component, propulsion type, sensor package or configuration option in `WATERCRAFT_ONLY` raises the watercraft message naming the offending entry and says nothing about the 20-ton limit. Each message names only the limit it actually hit; the spec's User Story 1 acceptance scenario 5 previously described a single combined message and was corrected in the analysis pass (FR-013, SC-005)
- [ ] T061 [US1] Create `src/cetools/engine/vehicles/description.py` with `render_description(vehicle) -> str`, filling every FR-025 slot and omitting the four starship slots of FR-025b
- [ ] T062 [US1] Add `render_component_table(vehicle) -> str` to `src/cetools/engine/vehicles/description.py` (FR-025a)
- [ ] T063 [US1] Populate `src/cetools/engine/vehicles/__init__.py` with the building, design-file I/O and description exports and an explicit sorted `__all__`, no logic (contracts/library.md)
- [ ] T064 [US1] Create `src/cetools/cli/vehicle.py` with the `build` command taking `FILE`, `--table`, `--toml` and `--out`, checking the argument rules at the top of the body before any engine call, mapping engine `ValueError` to `str(exc)` on stderr with exit 1, and keeping stdout to the artifact alone (FR-029a, contracts/cli.md)
- [ ] T065 [US1] Register the group in `src/cetools/cli/main.py`: one import, one `app.add_typer(vehicle.app, name="vehicle")`, and the root callback docstring updated to enumerate the four groups (FR-024)
- [ ] T066 [US1] Author `tests/data/vehicles/example.toml` and the four failure fixtures `over-tech-level.toml`, `no-tech-level.toml`, `submersible.toml` and `overfull.toml` under `tests/data/vehicles/`, matching the paths `quickstart.md` names

**Checkpoint**: `uv run cetools vehicle build tests/data/vehicles/example.toml` prints a description and exits 0; `--table` appends a table whose lines sum to the printed price. User Story 1 is deliverable end to end.

---

## Phase 4: User Story 2 - Re-derive the published catalog (Priority: P2)

**Goal**: Fifteen published vehicles ship as authored design files, are rebuilt by the same builder,
and every disagreement between the book and the rules is recorded where a referee will find it.

**Independent Test**: Build all fifteen shipped design files and compare every figure against the
published stat blocks. Each figure either matches or appears in the divergence list.

**Ordering note**: the comparison test (T068) is written before any catalog design is authored, so
authoring runs red to green against the published figures rather than being tuned until it passes
(research R-007, and the explicit open item at the end of `research.md`). Its pass condition is
"matches, or is on the page," so the page has to exist first: T067b creates the skeleton, and
T079/T080 fill it once the builds have surfaced what goes in it.

### Published figures and the comparison test

- [ ] T067 [US2] Create `src/cetools/engine/vehicles/published.py` with `PUBLISHED: dict[str, dict[str, object]]`, transcribing all fifteen stat blocks figure by figure from the SRD text with the labels `spaces`, `cargo`, `price`, `discounted_price`, `prose_price`, `agility`, `speed`, `armor`, `crew` and `build_time`, omitting any figure its stat block does not print (FR-021a)
- [ ] T067a [US2] Write failing tests in `tests/test_vehicle_published.py` for the transcription's own shape: exactly fifteen keys matching `catalog_names()`, every figure label drawn from the ten FR-021a allows and no other, every value a number, and no vehicle with an empty figure set. `published.py` is the one module that would otherwise have no mirrored test file (Principle III)
- [ ] T067b [US2] Create `DIVERGENCES.md` at the repository root as a skeleton: the vehicles section with its three headings (worked examples, rules defects, generation policy), and the first two carrying an empty machine-readable table with the header row Vehicle, Figure, Published, cetools, Why. Nothing is filled here; this exists so T068 has a page to read (FR-020, FR-020b)
- [ ] T068 [US2] Write the failing comparison test in `tests/test_vehicle_catalog.py`: build every catalog design, compare every `PUBLISHED` figure with `math.isclose` against a module-level `TOLERANCE = dict(rel_tol=0.0, abs_tol=0.01)`, one centicredit, sized to the Air/Raft's Cr104,614.51-against-Cr104,614.5 artifact and nothing larger (SC-002, research R-011); and fail on any mismatch not present on `DIVERGENCES.md` with the same published and produced values (FR-021a)
- [ ] T069 [US2] Write failing tests in `tests/test_vehicle_catalog.py` for `catalog_names()` returning exactly the fifteen kebab-case names of `data-model.md` Layer 4 in sorted order, `afv-tracked` first and `van` last, and `load_catalog(name)` raising `ValueError` naming the available names for an unknown name (FR-021b, FR-024a)
- [ ] T070 [US2] Create `src/cetools/engine/vehicles/catalog.py` with `catalog_names()` and `load_catalog(name)`, reading through `importlib.resources.files("cetools.engine.vehicles") / "catalog"` (research R-006)

### The fifteen authored designs

**Note on form**: T104 asserts that every installed design round-trips through
`dump_design(loads_design(text))` **unchanged**, so each file below must be written in `dump_design`
canonical form: its key order, nothing that equals a model default, every bare top-level scalar and
option array before the first table header. The practical way to satisfy that is to author freely,
then run the file through `dump_design` once and commit the output.

- [ ] T071 [US2] Author `src/cetools/engine/vehicles/catalog/air-raft.toml` and drive it green against its `PUBLISHED` figures, recording the four price divergences and the unbalanced spaces column as they surface (research C-003)
- [ ] T072 [P] [US2] Author `src/cetools/engine/vehicles/catalog/biplane.toml`, `helicopter.toml` and `twin-engine-jet.toml`, the three Chapter 2 aircraft
- [ ] T073 [P] [US2] Author `src/cetools/engine/vehicles/catalog/g-carrier.toml`, `grav-bike.toml`, `grav-floater.toml`, `grav-tank.toml` and `speeder.toml`, the remaining five Chapter 3 grav vehicles, which bring turrets and vehicular weapons
- [ ] T074 [P] [US2] Author `src/cetools/engine/vehicles/catalog/afv-tracked.toml`, `atv-tracked.toml`, `ground-car.toml` and `van.toml`, four of the five Chapter 4 ground vehicles
- [ ] T075 [P] [US2] Author `src/cetools/engine/vehicles/catalog/stagecoach.toml`, the TL3 design that requires animal power, non-powered propulsion and a negative-price component (FR-023)
- [ ] T076 [P] [US2] Author `src/cetools/engine/vehicles/catalog/tunnel-boring-machine.toml`, the Chapter 6 design whose Mole speeds are in meters per hour
- [ ] T077 [US2] Fix whatever the fifteen builds surfaced in `src/cetools/engine/vehicles/tables.py` and `src/cetools/engine/vehicles/builder.py`, adding a regression test in the matching `tests/test_vehicle_*.py` for each fix before the fix

### The divergence page and the widened gate

- [ ] T078 [US2] Fill in the prose of `DIVERGENCES.md` around the skeleton T067b created: what the page is for, why the three sections are three unlike things, why a divergence is errata rather than a house rule (FR-019), and a closing note that later domains open their own section below the vehicles one (FR-018, FR-020)
- [ ] T079 [US2] Fill the rules-defects table in `DIVERGENCES.md` with the nine defects of research R-003, each naming the table, the printed value, the value cetools uses and why
- [ ] T080 [US2] Fill the worked-examples table in `DIVERGENCES.md` with every divergence the fifteen builds surfaced, including the Air/Raft's four price figures and its 24.57-against-29.68 cargo (research C-003) and the discount-on-fuel divergence on every vehicle that carries fuel and elects the discount (research C-002)
- [ ] T081 [US2] Write a failing test in a **new** `tests/test_check_docs.py` asserting that `check_docs.py` fails when a `cetools` column value in `DIVERGENCES.md` no longer matches what the builder produces, naming the vehicle and the figure. There is no existing docs-check test module and `scripts/` is neither a package nor on `sys.path` (`pyproject.toml` sets `testpaths = ["tests"]` and no `pythonpath`), so load it explicitly with `importlib.util.spec_from_file_location("check_docs", ROOT / "scripts" / "check_docs.py")` rather than adding a package or widening the path for one test. Drive the failure by passing the parser a fixture string, not by editing the real page
- [ ] T082 [US2] Add `"DIVERGENCES.md"` to `DOCS` in `scripts/check_docs.py` and add a `check_divergences()` function that parses the two machine-readable tables, rebuilds each named catalog vehicle and confirms the `cetools` column still matches, wiring it into `main()` (FR-020a, FR-020b, research R-007)
- [ ] T083 [US2] Extend `NOT_CODE` in `scripts/check_docs.py` with any `DIVERGENCES.md` backtick that is an SRD table name rather than a package symbol, and confirm the punctuation and American-spelling checks now cover the new page

### CLI catalog access

- [ ] T084 [US2] Write failing tests in the `cetools vehicle` section of `tests/test_cli.py` for `--catalog NAME` on `build` and for the `catalog` listing: fifteen names one per line on stdout, an unknown name exiting 1 with a message listing the names that do exist, neither `FILE` nor `--catalog` exiting 1, both exiting 1, and a catalog vehicle by name printing the same description as building its installed file by path (FR-024a, SC-001)
- [ ] T085 [US2] Add `--catalog NAME` to `build` and the `catalog` listing command in `src/cetools/cli/vehicle.py`, and add the catalog exports to `src/cetools/engine/vehicles/__init__.py`

**Checkpoint**: `uv run pytest tests/test_vehicle_catalog.py --no-cov` green, all fifteen build, zero undocumented divergences, and `uv run python scripts/check_docs.py` reads the new page.

---

## Phase 5: User Story 3 - Generate a vehicle from a seed (Priority: P3)

**Goal**: A referee asks for a vehicle and gets a complete, legal, role-coherent one; the same seed
and constraints always produce the same vehicle.

**Independent Test**: Run generation twice with the same seed and constraints and compare byte for
byte; run with different seeds and confirm the vehicles differ. Testable without the catalog.

### Tests for User Story 3

- [ ] T086 [P] [US3] Write failing tests in `tests/test_vehicle_generator.py` for `Role` and its loadout profiles: exactly six roles (civil transport, military ground, military air, grav utility, aircraft, industrial), each profile deciding eligible chassis sizes, eligible locomotion families, whether armaments are drawn at all, eligible accommodations and eligible additional components, and each of the fifteen catalog vehicles falling in exactly one role (FR-026b, FR-026d)
- [ ] T087 [P] [US3] Write failing tests in `tests/test_vehicle_generator.py` using `RecordingRolls` asserting that `VEHICLE_ROLE` is the first `Draw` on the stream, because the role decides every later pool and changing the order silently invalidates every pinned baseline (FR-030a)
- [ ] T088 [P] [US3] Write failing tests in `tests/test_vehicle_generator.py` using `ScriptedRolls` for the constraint split: an unknown chassis code, a locomotion alias matching no propulsion row and a tech level below a chassis minimum each raise `ValueError` up front with nothing generated; a budget-dependent failure returns a vehicle with an `UnmetConstraint` naming the field exactly as a `GenerationConstraints` field, what was asked, what was given and why; and a drawn value that will not fit is dropped silently and produces no `UnmetConstraint` (FR-032)
- [ ] T089 [P] [US3] Write failing tests in `tests/test_vehicle_generator.py` asserting every generated vehicle carries only components its role's profile admits (SC-011), is identified by tech level and type rather than a rolled name (FR-029), and passes the ordinary `build_vehicle` validation a hand-authored design faces
- [ ] T090 [P] [US3] Write failing tests in `tests/test_vehicle_generator.py` for `SpacesLedger`: `spend`, `affords`, `decline` and `declined`, the one deliberately mutable class in the domain, and that it never escapes a single generation call

### Implementation for User Story 3

- [ ] T091 [US3] Create `src/cetools/engine/vehicles/generator.py` with the `Role` enum, one `LoadoutProfile` per role, the `SpacesLedger`, `GenerationConstraints` with `UNCONSTRAINED`, the `ABSENT` sentinel, `UnmetConstraint` and `GenerationResult`, with a comment recording that roles are cetools generation policy and are never imported by `builder.py` (FR-026c)
- [ ] T092 [US3] Implement `generate_vehicle(rolls=None, *, constraints=UNCONSTRAINED)` in `src/cetools/engine/vehicles/generator.py`, drawing the role first, then filling each category from that role's profile through the `Rolls` seam with up-front pool filtering rather than `bounded_retry` (research R-008, R-010). Include the two draws FR-026d's category list does not name but `VehicleDesign` still requires: endurance in weeks through `VEHICLE_FUEL` and crew count through `VEHICLE_CREW`. Draw no design options at all and leave the four option tuples empty, with a comment recording that this is FR-030's deliberate line rather than an omission
- [ ] T093 [US3] Add `locomotion_names()` and `locomotion_aliases()` to `src/cetools/engine/vehicles/generator.py` and export the generation surface from `src/cetools/engine/vehicles/__init__.py` (FR-026a, contracts/library.md)
- [ ] T094 [US3] Write a failing test in `tests/test_vehicle_generator.py` comparing unconstrained generation against `tests/data/baseline/vehicle_designs.json` keyed `"seed"` → `dump_design(...)` over 100 seeds, comparing serialized TOML rather than objects so a failure diffs readably (SC-003, research R-010)
- [ ] T095 [US3] Generate and commit `tests/data/baseline/vehicle_designs.json`, then verify the test from T094 fails when one baseline entry is altered
- [ ] T096 [US3] Write a failing test in `tests/test_vehicle_generator.py` for the constrained paths, running generation twice per constraint set and asserting equality, with a comment recording that a pinned constraint consumes no dice so only the unconstrained sequence is byte-stable across changes (FR-031, SC-003)
- [ ] T097 [US3] Write failing tests in the `cetools vehicle` section of `tests/test_cli.py` for `generate`: `--seed`, `--tech-level`, `--chassis` and `--locomotion`; an omitted seed echoed to stderr as `seed: {seed}`; the unmet-constraint report on stderr with exit **0**; a locomotion alias naming no row exiting 1; and `--table` behaving as it does on `build`
- [ ] T098 [US3] Add the `generate` command to `src/cetools/cli/vehicle.py`, keeping the exit code at 0 when constraints could not be honored because a vehicle really was produced and must still pipe (FR-029a, FR-032, contracts/cli.md)
- [ ] T099 [US3] Add the generation-policy section content to `DIVERGENCES.md`, naming all six roles and their loadout profiles as cetools choices rather than SRD rules, in prose the docs check does not parse (FR-026c, SC-011)

**Checkpoint**: `uv run cetools vehicle generate --seed 42` twice gives byte-identical stdout; the TL5-grav conflict reports on stderr and exits 0.

---

## Phase 6: User Story 4 - Round-trip a design as TOML (Priority: P4)

**Goal**: Either command can emit its result as a design file and write it to a path, and feeding
that file back in reproduces the same vehicle.

**Independent Test**: Generate a vehicle as a design file, build that file, and confirm the
description matches the one generation would have printed.

- [ ] T100 [P] [US4] Write failing tests in the `cetools vehicle` section of `tests/test_cli.py` for `--toml` on both commands: a design file is emitted instead of the description, and stdout stays empty when `--out` is given
- [ ] T101 [P] [US4] Write failing tests in the `cetools vehicle` section of `tests/test_cli.py` for the argument rules: `--out` without `--toml` exits 1 with the existing message `--out requires --toml` verbatim, and `--table` with `--toml` exits 1 explaining they are different representations of the same vehicle (FR-025a, FR-028)
- [ ] T102 [US4] Wire `--toml` and `--out` through both commands in `src/cetools/cli/vehicle.py`, with all argument rules checked before any rules work happens
- [ ] T103 [US4] Write a failing round-trip test in `tests/test_vehicle_design.py` asserting that a generated vehicle emitted as TOML and rebuilt renders the identical description (SC-008)
- [ ] T104 [US4] Write a failing test in `tests/test_vehicle_catalog.py` asserting every installed `catalog/*.toml` round-trips through `dump_design(loads_design(text))` unchanged, so the fifteen stay maintainable

**Checkpoint**: all four user stories independently functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T105 Identify the table rows no catalog vehicle and no generation path exercises, and commit the answer as `tests/data/vehicles/unexercised_rows.json` rather than leaving it in a scratch file: it is SC-006's evidence, and a list nobody can re-read is not evidence. The mechanism, since a plain `dict` of frozen dataclasses records nothing: in a test-only helper, wrap each table constant in a `Mapping` subclass whose `__getitem__` records the key, monkeypatch the wrapped mappings into `tables` for the duration of one run, build all fifteen catalog designs and generate across 100 seeds, then subtract the recorded keys from the full key set per constant. Sort the output so the file diffs readably (SC-006)
- [ ] T106 Add direct tests in `tests/test_vehicle_tables.py` for every row named in `tests/data/vehicles/unexercised_rows.json`, reading the fixture rather than restating the list, and assert the fixture is exhaustive so a row that stops being exercised is caught. Then verify by altering each such row's values and confirming the new test fails (SC-006, and the mutation-testing practice `quickstart.md` names)
- [ ] T107 [P] Add the vehicle section to `README.md` with runnable Python examples for `build_vehicle`, `render_description` and `load_catalog`, CLI examples for the three commands, and the two locomotion vocabularies `--locomotion` accepts: all sixteen propulsion names and all nine coarse aliases, generated into the prose from `locomotion_names()` and `locomotion_aliases()` at authoring time rather than hand-listed, so the page and the tables cannot drift (FR-026a, SC-010)
- [ ] T108 [P] Add `vehicles/` to the module map in `CONTRIBUTING.md`, listed by convention as `ships/` is
- [ ] T109 [P] Update the docs-check description in `AGENTS.md` so it names `DIVERGENCES.md` as a fourth maintained document (FR-020a)
- [ ] T110 Run every command in `quickstart.md` in order and confirm each expectation, including the deliberate `DIVERGENCES.md` figure change that must make `check_docs.py` fail by name
- [ ] T111 Run the five-command quality gate `uv run isort . && uv run black . && uv run flake8 src tests && uv run pytest && uv run python scripts/check_docs.py` and fix what it reports, treating the 85% coverage floor as a floor rather than as evidence (SC-009)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies
- **Foundational (Phase 2)**: depends on Setup; **blocks every user story**
- **US1 (Phase 3)**: depends on Phase 2
- **US2 (Phase 4)**: depends on US1, because the catalog is rebuilt by the builder US1 delivers
- **US3 (Phase 5)**: depends on US1; independent of US2
- **US4 (Phase 6)**: depends on US1 for `build --toml` and on US3 for `generate --toml`
- **Polish (Phase 7)**: depends on all four stories

### Story Dependencies

Unlike the template's usual shape, these stories are not mutually independent, and the spec says so:
US2 and US3 both consume the builder US1 delivers. Each is still *independently testable* against
its own acceptance criteria once US1 exists, which is what the checkpoints assert.

- **US1 (P1)**: the MVP. Nothing else can start.
- **US2 (P2)**: needs `build_vehicle` and `render_description`. Does not need generation.
- **US3 (P3)**: needs `build_vehicle`. Does not need the catalog.
- **US4 (P4)**: needs `dump_design` (Phase 2) plus whichever command it is being wired into.

### Within Each Phase

- Every test task precedes its implementation task and must be observed red first (Principle III)
- Row types and tables before the records that validate against them
- Records before the parser, the builder and the renderer
- Builder before the description, the catalog and the generator
- Engine before the CLI, always

### Parallel Opportunities

- **Phase 2**: T032 and T033 (`prose.py`) run parallel to the whole table sequence, being a different
  file with no dependency on it. The table tasks T004–T031, including T006a/T006b and T026a–T026e,
  are **not** parallel with each other: they all write `tables.py` and
  `tests/test_vehicle_tables.py`. T047a is parallel with everything in the phase, reading source
  rather than writing it.
- **Phase 3**: the nine test tasks T048–T054 plus T051a and T051b are all parallel, spanning three
  different test files. The implementation tasks T055–T060 are sequential: they are one function in
  one file.
- **Phase 4**: T072–T076 are parallel, being five disjoint sets of TOML files. T071 is deliberately
  first and alone, because the Air/Raft is where the divergence machinery gets shaken out.
- **Phase 5**: the five test tasks T086–T090 are parallel within one file only if written as separate
  additions; treat them as sequential if that file is being edited by one worker.
- **Phase 6**: T100 and T101 are parallel.
- **Phase 7**: T107, T108 and T109 are parallel, being three different documents.

---

## Parallel Example: User Story 1

```bash
# The nine US1 test tasks, all red before any implementation:
Task: "T048 Build-order tests in tests/test_vehicle_builder.py"
Task: "T049 Validation tests in tests/test_vehicle_builder.py"
Task: "T050 Arithmetic edge-case tests in tests/test_vehicle_builder.py"
Task: "T051 Discount tests in tests/test_vehicle_builder.py"
Task: "T051a Standard-design flag and design-fee tests in tests/test_vehicle_builder.py"
Task: "T051b Option-pricing tests in tests/test_vehicle_builder.py"
Task: "T052 Description-slot tests in tests/test_vehicle_description.py"
Task: "T053 Component-table tests in tests/test_vehicle_description.py"
Task: "T054 CLI build tests in tests/test_cli.py"
```

## Parallel Example: User Story 2

```bash
# The fourteen remaining catalog designs, after air-raft has shaken out the machinery:
Task: "T072 Three Chapter 2 aircraft in src/cetools/engine/vehicles/catalog/"
Task: "T073 Five Chapter 3 grav vehicles in src/cetools/engine/vehicles/catalog/"
Task: "T074 Four Chapter 4 ground vehicles in src/cetools/engine/vehicles/catalog/"
Task: "T075 The TL3 stagecoach in src/cetools/engine/vehicles/catalog/"
Task: "T076 The tunnel boring machine in src/cetools/engine/vehicles/catalog/"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1: Setup: the package and the nineteen roll names
2. Phase 2: Foundational: 37 table constants, 6 option constants, prose, records, design file **(blocks everything)**
3. Phase 3: User Story 1 — builder, description, `cetools vehicle build`
4. **STOP and VALIDATE**: run the User Story 1 section of `quickstart.md`

Plan.md step 8 records that steps 1–4 are the minimum that delivers value and could in principle
ship alone. The spec's Assumptions section records why they will not: the catalog is what verifies
the tables, and a builder without it is a half-change whose correctness cannot be demonstrated.

### Incremental Delivery

1. Setup + Foundational → tables transcribed and tested
2. US1 → a referee can design a vehicle and get a description
3. US2 → the tables become *verified* transcription; the gate widens
4. US3 → the referee-at-the-table use
5. US4 → generated vehicles become editable and the catalog maintainable

### Notes

- `[P]` means different files with no dependency on an incomplete task
- The whole change lands as one pull request by explicit, reaffirmed decision (spec Assumptions)
- Commit after each task or logical group, in Conventional Commits form
- Never restore a mutation-test edit with `git checkout`; restore from a copy
- The five-command gate must be green before the change is considered complete
