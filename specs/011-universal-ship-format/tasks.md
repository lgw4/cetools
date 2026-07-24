---

description: "Task list for Universal Ship Description Format"
---

# Tasks: Universal Ship Description Format

**Input**: Design documents from `/specs/011-universal-ship-format/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Tests**: Included and mandatory. Constitution Principle IV (Test-First) requires
red-green-refactor, and plan.md commits to it explicitly: `prose.py` gets table-driven tests
before implementation, each sentence builder gets its assertion before `description.py` exists,
and the tech-level derivation is tested through `build_ship` before the table columns land.

**Organization**: Tasks are grouped by user story so each can be implemented and tested
independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Every task names the exact file it touches

## Path Conventions

Single project (existing layout): `src/cetools/`, `tests/` at repository root.

## Authoritative references

- Per-sentence output text: [contracts/description-format.md](./contracts/description-format.md)
- Public-surface delta: [contracts/engine-api.md](./contracts/engine-api.md)
- TOML schema delta: [contracts/design-schema.md](./contracts/design-schema.md)
- Table columns and derivations: [data-model.md](./data-model.md)

---

## Phase 1: Setup

**Purpose**: Establish the baseline SC-005 will be checked against.

- [ ] T001 Record the pre-change quality-gate baseline by running `uv run black --check . && uv run flake8 src tests && uv run pytest && uv run python scripts/check_docs.py` from the repository root, and note the passing test count in the working notes so SC-005 ("every pre-existing test passes unmodified") can be verified at the end.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The data layer every sentence reads from — text primitives, SRD display names and
tech levels, the two new design fields, and the derived `Ship.tech_level`. No sentence can be
rendered until these exist.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

### Tests (write first, confirm they fail)

- [ ] T002 Add table-column invariants to `tests/test_ship_tables.py`: every nameable row in `ARMOR`, `ARMOR_OPTIONS`, `ELECTRONICS`, `TURRET_MOUNTS`, `TURRET_WEAPONS`, `AMMO`, `BAYS`, `SCREENS` and `FITTINGS` has a non-empty `name`; every row the paragraph can count also has a non-empty `plural`; every `AmmoRow.weapon` is a `TURRET_WEAPONS` key; every `ELECTRONICS` row carries a `tl` and a `dm`; `MountRow.tl` is `None` only for `fixed`; `ArmorRow.tl` exists and `min_tl` does not.
- [ ] T003 Add the two-new-table invariants to `tests/test_ship_tables.py`: `CONFIGURATIONS` is keyed by every `Configuration.value` and carries the ×0.9/×1.0/×1.1 cost modifiers with lower-case names; `CONFIG_MODIFIERS` is gone; every `CREW_POSITIONS.field` names a `Crew` count attribute, every such attribute appears exactly once, and the tuple order is the FR-018 order (pilot, navigator, engineers, gunners, screen operators, medic, stewards).
- [ ] T004 [P] Add shape-validation tests to `tests/test_ship_models.py`: `ShipDesign.purpose` and `ShipDesign.tech_level` default to `None`; a present `purpose` must be a non-empty, non-whitespace `str`; a present `tech_level` must be an `int >= 0` (and a `bool` is rejected); `Ship.tech_level` is included in the `>= 0` validation sweep.
- [ ] T005 [P] Add tech-level derivation tests to `tests/test_ship_builder.py` per [data-model.md §3](./data-model.md): the derived value is the max `tl` over fitted rows only; an explicit `design.tech_level` is used as given whether higher or lower than the derived value (FR-028b) and is never clamped or warned about; hulls, drives, configurations, cockpits, quarters, fittings and software contribute nothing; a `fixed` mount contributes nothing; a design with no purchased electronics still derives at least 8 from `ELECTRONICS["standard"]` (FR-028c).
- [ ] T006 [P] Create `tests/test_ship_prose.py` with table-driven cases for every function in [data-model.md §5](./data-model.md): `count` (words zero–ten, digits above ten — FR-022), `tons` (count rule when whole, digits when fractional — FR-022b), `number` (digits always, no scientific notation, no trailing zeros, no dangling decimal point — FR-022a, FR-025), `money` (thousands separators, `MCr29.772` never `MCr29.771999999999998`, `MCr2,768.145` never `2768.14` — FR-025, FR-025a), `signed` (explicit sign at every magnitude including `+0` — FR-009), `plural` (FR-023), `join` (one item alone, two joined with "and", three with commas and no serial comma — FR-024), `article` (FR-023a), and `tonnage_article` (`"an"` for a leading 8, else `"a"`).

### Implementation

- [ ] T007 [P] Create `src/cetools/engine/ships/prose.py` implementing `count`, `tons`, `number`, `money`, `signed`, `plural`, `join`, `article` and `tonnage_article` per [data-model.md §5](./data-model.md). Import nothing from `models.py`, `tables.py` or any other ships module. Format floats at a fixed six decimal places and *then* strip trailing zeros — never `:g`.
- [ ] T008 Add the SRD display-name, plural, tech-level and dice-modifier columns to the row dataclasses and tables in `src/cetools/engine/ships/tables.py` per [data-model.md §4](./data-model.md): `ArmorRow.name` and `min_tl` renamed to `tl`; `ArmorOptionRow.name`/`tl`; `ElectronicsRow.name`/`tl`/`dm`; `MountRow`, `WeaponRow`, `BayRow`, `ScreenRow` gaining `name`/`plural`/`tl`; `AmmoRow` gaining `name`/`plural`/`tl`/`weapon`; `FittingRow` gaining `name` (article included), `plural` (no article), `counted_in_tons` and `unrefined_fuel_per_ton`. Transcribe every value from the SRD tables recorded in [research.md Parts D and E](./research.md); invent none. Retire the "deliberately unenforced" docstrings on `ArmorRow` and `ComputerRow`.
- [ ] T009 Replace `CONFIG_MODIFIERS` with `ConfigurationRow(name, cost_modifier)` and `CONFIGURATIONS: dict[str, ConfigurationRow]` in `src/cetools/engine/ships/tables.py`, keyed identically by `Configuration.value`, with the lower-case names "distributed", "standard" and "streamlined".
- [ ] T010 Add `CrewPositionRow(field, name, plural)` and `CREW_POSITIONS: tuple[CrewPositionRow, ...]` to `src/cetools/engine/ships/tables.py` in the FR-018 print order, per the table in [data-model.md §4](./data-model.md).
- [ ] T011 Add `ShipDesign.purpose: str | None = None`, `ShipDesign.tech_level: int | None = None` and `Ship.tech_level: int` to `src/cetools/engine/ships/models.py`, extend `_validate_ship_design` and `_validate_ship` with shape-only checks, and re-route `Configuration.cost_modifier` through `CONFIGURATIONS[self.value].cost_modifier` (same three values, so no arithmetic changes). Do not compare `tech_level` against any derived value.
- [ ] T012 Derive `Ship.tech_level` in `build_ship` in `src/cetools/engine/ships/builder.py`: use `design.tech_level` when supplied, otherwise the maximum `tl` over the rows of the components actually fitted, walking the rows generically so a new row with a `tl` widens the derivation with no per-category list. Add no line item, and change no tonnage, cost, crew, hull/structure, hardpoint or build-time value.
- [ ] T013 Confirm FR-032 by running `uv run pytest tests/test_ship_builder.py tests/test_ship_generator.py tests/test_ship_design.py tests/test_ship_models.py tests/test_ship_tables.py` and verifying every pre-existing assertion still passes with no test edited except to add the new coverage from T002–T005.

**Checkpoint**: `prose.py` is green in isolation, every table carries its SRD wording, and every built ship has a tech level. Sentence rendering can now begin.

---

## Phase 3: User Story 1 - Read a generated ship in the format the rules use (Priority: P1) 🎯 MVP

**Goal**: `render_description(ship)` produces a `TL<n> <name>` heading, a blank line, and one
prose paragraph whose sentences run in the FR-004 order with the SRD's wording, and
`cetools ship generate` prints it instead of the label-per-line sheet.

**Independent Test**: Run `uv run cetools ship generate --seed 42` and confirm the output is a
tech-level-and-name heading followed by one paragraph whose sentences appear in the SRD's
prescribed order and use the SRD's prescribed wording; run it twice and diff for byte-identity.

### Tests for User Story 1 (write first, confirm they fail)

- [ ] T014 [US1] Create `tests/test_ship_description.py` with a fully-equipped starship fixture — turrets (including three identical triple turrets), a bay, ammunition, screens, a hangar, two armour layers with an option, fittings including a fuel processor, low berths and emergency low berths — and assert the output shape from [contracts/description-format.md](./contracts/description-format.md) "Overall shape": heading line `TL<n> <name>`, one blank line, exactly one paragraph, no newline inside the paragraph, no trailing newline, single spaces between sentences (FR-001, FR-001a).
- [ ] T015 [US1] Add a sentence-order assertion to `tests/test_ship_description.py`: for the fully-equipped fixture, the sixteen sentences appear in the FR-004 order and in no other (FR-004, SC-004).
- [ ] T016 [US1] Add sentence 1–3 assertions to `tests/test_ship_description.py` per contract sections 1–3: hull ("Using a 200-ton hull (4 Hull, 4 Structure), the …"), drives ("It mounts jump drive A, maneuver drive A and power plant A, giving a performance of Jump-1 and 1-G acceleration."), fuel ("Fuel tankage of 22 tons supports the power plant for two weeks and one Jump-1 jump.") — FR-005, FR-006, FR-007, FR-007a.
- [ ] T017 [US1] Add sentence 4–6 assertions to `tests/test_ship_description.py` per contract sections 4–6: computer with `/bis`, `/fib` and `/bis/fib` suffixes (FR-008); sensors naming the `ElectronicsRow.name` with an explicitly signed DM, including `DM+0`, and falling back to the Standard package when the design purchases none (FR-009, FR-009a, FR-030a); quarters distinguishing low berths from emergency low berths with `is`/`are` agreement (FR-010, FR-023).
- [ ] T018 [US1] Add sentence 7–10 assertions to `tests/test_ship_description.py` per contract sections 7–10: hardpoints with fire-control tons equal to the hardpoint count (FR-011); installed weapons with bays before turrets, three identical triple turrets grouped as one phrase, and ammunition aggregated per `(kind, type)` naming the weapon it feeds (FR-012, FR-012a); screens with total count then grouped types (FR-013); hangars stating count and capacity in tons and never naming the craft carried (FR-014).
- [ ] T019 [US1] Add sentence 11–13 assertions to `tests/test_ship_description.py` per contract sections 11–13: cargo (FR-015); hull configuration with two armour layers rendering **one** armour clause and **one** total protection rating followed by the options clause (FR-016, FR-016a, FR-016b); special features including the fuel-processor throughput clause at 20 tons per ton per day, "two tons of luxuries" for a `counted_in_tons` row, and "fuel scoops" with no count at quantity one (FR-017).
- [ ] T020 [US1] Add sentence 14–16 assertions to `tests/test_ship_description.py` per contract sections 14–16: crew total plus a breakdown in `CREW_POSITIONS` order omitting zero-count positions (FR-018); passengers at double occupancy in non-crew staterooms plus low passengers, with emergency low berths excluded (FR-019, FR-019a); cost with thousands separators and stripped trailing zeros plus build time in weeks (FR-020, FR-025).
- [ ] T021 [US1] Add a determinism test to `tests/test_ship_description.py`: build two equal `Ship` values from the same design and assert `render_description` returns byte-identical strings; assert no seed, timestamp or locale-dependent text appears (FR-003, SC-003).
- [ ] T022 [US1] Update `tests/test_cli.py` so the `cetools ship generate` cases assert a heading line plus one paragraph instead of the sheet's labelled lines, that the reported seed appears on stderr and nowhere in the paragraph, and that two runs with the same seed produce identical stdout.

### Implementation for User Story 1

- [ ] T023 [US1] Create `src/cetools/engine/ships/description.py` with `render_description(ship: Ship) -> str`, the heading assembly, and the fixed sixteen-entry tuple of private sentence builders, each returning `str | None` and each dropped from the paragraph when `None` (per [data-model.md §6](./data-model.md)). Import only `models`, `tables` and `prose`.
- [ ] T024 [US1] Implement `_hull`, `_drives` and `_fuel` in `src/cetools/engine/ships/description.py` per contract sections 1–3.
- [ ] T025 [US1] Implement `_computer`, `_sensors` and `_quarters` in `src/cetools/engine/ships/description.py` per contract sections 4–6.
- [ ] T026 [US1] Implement `_hardpoints`, `_weapons` and `_screens` in `src/cetools/engine/ships/description.py` per contract sections 7–9, including turret grouping by `(mount, weapons)`, bay and screen grouping by `kind`, ammunition aggregation by `(kind, type)`, and bays-before-turrets ordering — every group in first-appearance order over the design's ordered tuples, never over a set or a dict keyed on unordered input.
- [ ] T027 [US1] Implement `_hangars`, `_cargo` and `_configuration` in `src/cetools/engine/ships/description.py` per contract sections 10–12, identifying a hangar by `FittingRow.tons_per_vehicle_ton is not None` and never by key comparison (FR-031).
- [ ] T028 [US1] Implement `_special_features`, `_crew`, `_passengers` and `_cost` in `src/cetools/engine/ships/description.py` per contract sections 13–16, driving the fitting clauses off `counted_in_tons` and `unrefined_fuel_per_ton` and the crew breakdown off `CREW_POSITIONS` — no branch keyed on a component's spelling.
- [ ] T029 [US1] Export `render_description` from `src/cetools/engine/ships/__init__.py` and remove `render_sheet` from the imports and `__all__`.
- [ ] T030 [US1] Change `src/cetools/cli/ship.py` to call `render_description` instead of `render_sheet`, leaving argument parsing, `--toml`, `--out`, seed-on-stderr and exit codes untouched.
- [ ] T031 [US1] Delete `src/cetools/engine/ships/sheet.py` and `tests/test_ship_sheet.py`, and update the two `render_sheet` references in the `LineItem` and `Ship` docstrings in `src/cetools/engine/ships/models.py` to name `description.py`'s `render_description(ship)`.

**Checkpoint**: `cetools ship generate` prints a USDF heading and paragraph; the sheet is gone. This is the MVP.

---

## Phase 4: User Story 2 - Describe a hand-authored design file (Priority: P1)

**Goal**: A TOML design file can carry an author-supplied `purpose` and `tech_level`, both
round-trip losslessly, and `cetools ship build` renders the design's own components in a USDF
paragraph.

**Independent Test**: Build every checked-in example design and confirm each produces a
well-formed USDF paragraph naming that design's own components, with the authored purpose
completing the first sentence where one is supplied.

### Tests for User Story 2 (write first, confirm they fail)

- [ ] T032 [US2] Add round-trip tests to `tests/test_ship_design.py` per [contracts/design-schema.md](./contracts/design-schema.md): `loads_design(dump_design(d)) == d` for designs setting neither key, `purpose` only, `tech_level` only and both; `dump_design` omits an unset key; a `purpose` containing a quote or backslash survives `_toml_str`; a non-string `purpose` and a non-integer `tech_level` raise `ValueError`; a misspelled key still fails with the existing "unknown key(s) in design" message (FR-033).
- [ ] T033 [US2] Add first-sentence tests to `tests/test_ship_description.py`: an authored `purpose` completes sentence 1 verbatim with the renderer supplying the period (FR-029); a design with no `purpose` falls back to its hull class, "a starship" or "a small craft" (FR-029a); a design with no `name` uses `Unnamed Ship` in both the heading line and sentence 1 (FR-029b); an explicit `tech_level` above the derived value appears in the heading unchanged (FR-028b).
- [ ] T034 [US2] Update `tests/test_cli.py` so `cetools ship build` cases assert a heading plus one paragraph, and add a case asserting that building `specs/010-starship-generator/examples/free-trader.toml` produces the paragraph worked out in full at the end of [contracts/description-format.md](./contracts/description-format.md), heading `TL8 Beowulf` included.

### Implementation for User Story 2

- [ ] T035 [US2] Parse and dump `purpose` and `tech_level` in `src/cetools/engine/ships/design.py`: add both to `_TOP_LEVEL_KEYS`, validate `purpose` as a string and `tech_level` through the existing `_require_int`, and emit each from `dump_design` only when set, in the canonical order given in [contracts/design-schema.md](./contracts/design-schema.md).
- [ ] T036 [US2] Implement the purpose clause and the name fallback in `_hull` and the heading in `src/cetools/engine/ships/description.py`: `design.purpose` verbatim when supplied, otherwise the hull class; `Unnamed Ship` in both places when the design has no name.
- [ ] T037 [US2] Finalise `specs/011-universal-ship-format/examples/subsidized-merchant.toml` as the checked-in fixture carrying both new keys, and add a test to `tests/test_ship_description.py` that builds it and asserts the authored purpose completes sentence 1 and the authored tech level appears in the heading.

**Checkpoint**: Both P1 stories are complete. Every example design renders, and the TOML round trip is still lossless.

---

## Phase 5: User Story 3 - Omit sentences for equipment the ship does not carry (Priority: P2)

**Goal**: Sentences and clauses for equipment the ship does not carry are dropped whole, and the
paragraph stays grammatical after every omission.

**Independent Test**: Describe a ship with no turrets, no screens and no hangars and confirm the
corresponding sentences are absent while the rest of the paragraph is unchanged and grammatical.

### Tests for User Story 3 (write first, confirm they fail)

- [ ] T038 [US3] Add omission tests to `tests/test_ship_description.py` covering the omitted-when column of [data-model.md §6](./data-model.md): no computer fitted drops sentence 4; no staterooms, low berths or emergency low berths drops sentence 6 (FR-010a); no turrets and no bays drops sentence 8 while sentence 7 remains and gains ", but has no weapons installed" (FR-011a); no screens drops sentence 9; no vehicle-sized fitting drops sentence 10; no non-hangar fittings drops sentence 13 (FR-021).
- [ ] T039 [US3] Add clause-level omission tests to `tests/test_ship_description.py`: a starship with no maneuver drive drops both the maneuver-drive clause and the G-acceleration clause and stays grammatical (FR-006a); a design with no jump fuel still states "zero Jump-N jumps" (FR-007a); no armour renders "and no additional armor has been installed", never "armored with nothing (0 points)" (FR-016); a ship with neither non-crew staterooms nor low berths renders "The ship cannot carry any additional passengers." (FR-019b).
- [ ] T040 [US3] Add the remaining spec edge cases to `tests/test_ship_description.py`: zero cargo renders "Cargo capacity is zero tons."; a crew of one renders "a crew of one: one pilot", never "a crew of 1: 1 pilots"; a fractional cost such as MCr33.219 renders at full precision with no scientific notation and no dangling decimal point; a fractional cargo renders in digits.
- [ ] T041 [US3] Add a grammar sweep to `tests/test_ship_description.py` that renders every checked-in example design under `specs/010-starship-generator/examples/` and `specs/011-universal-ship-format/examples/`, plus a spread of generated ships from fixed seeds, and asserts of each paragraph: no doubled space, no space before a comma or period, no trailing " and", no "()", no "None", no newline inside the paragraph, and exactly one heading line (SC-001, FR-021a).

### Implementation for User Story 3

- [ ] T042 [US3] Implement the per-sentence omission conditions in `src/cetools/engine/ships/description.py` so each builder returns `None` exactly when [data-model.md §6](./data-model.md) says it should, with omission the only control flow between sentences — no builder reads another's output.
- [ ] T043 [US3] Implement the clause-level degenerate cases in `src/cetools/engine/ships/description.py`: the drives sentence's dropped maneuver and performance clauses, the fuel sentence's retained zero-jump clause, the hardpoints sentence's "but has no weapons installed" clause, the configuration sentence's no-armour form, and the passengers sentence's "cannot carry any additional passengers" form.

**Checkpoint**: Unarmed civilian ships read as prose rather than as a list of negations.

---

## Phase 6: User Story 4 - Describe a small craft (Priority: P3)

**Goal**: A small craft is described as a non-jump-capable vessel with a cockpit rather than a
bridge.

**Independent Test**: Describe a generated small craft and confirm no jump-related wording
appears and the computer sentence refers to its cockpit.

### Tests for User Story 4 (write first, confirm they fail)

- [ ] T044 [US4] Add small-craft tests to `tests/test_ship_description.py`: the drives sentence names only maneuver drive and power plant and states G-acceleration with no Jump rating (FR-026); the fuel sentence states power-plant weeks only and makes no claim about jumps (FR-026); the computer sentence reads "Adjacent to the cockpit" (FR-027); the words "jump" and "Jump" appear nowhere in the paragraph.
- [ ] T045 [US4] Update `tests/test_cli.py` to assert that `cetools ship generate --small-craft --hull 40 --seed 7` and `cetools ship build specs/010-starship-generator/examples/fighter.toml` each print a jump-free heading and paragraph, with the fighter's cargo rendering in digits.

### Implementation for User Story 4

- [ ] T046 [US4] Add the small-craft forms to `_drives`, `_fuel` and `_computer` in `src/cetools/engine/ships/description.py`, branching on the ship's hull class per contract sections 2, 3 and 4.

**Checkpoint**: All four user stories are independently functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T047 [P] Replace the label-per-line sample output in the ship section of `README.md` (the `console` block at lines 295–320) with the USDF heading and paragraph from [contracts/description-format.md](./contracts/description-format.md)'s worked example, keeping the surrounding commands unchanged.
- [ ] T048 [P] Update the module map in `CONTRIBUTING.md` (line 46): `sheet.py # render_sheet(ship)` becomes `description.py # render_description(ship)`, and add `prose.py`.
- [ ] T049 [P] Update `CONTEXT.md`: retire the "ship sheet" vocabulary in favour of "ship description", and retire the now-false claim that armor and computer tech levels are "checked nowhere, since v1 has no tech-level model" — this feature builds that model, and `scripts/check_docs.py` cannot catch a prose claim that has merely gone stale.
- [ ] T050 Run `uv run python scripts/check_docs.py` and fix any remaining backticked symbol, module-map entry or README example that the `render_sheet` → `render_description` rename left dangling.
- [ ] T051 Verify SC-007 by hand per [quickstart.md §10](./quickstart.md): add one screen row to `src/cetools/engine/ships/tables.py` with its `name`, `plural` and `tl`, fit it in a scratch design, confirm its wording appears in the screens sentence and its tech level in the derived heading with no edit to `description.py` or `builder.py`, then revert the row.
- [ ] T052 Walk every check in [quickstart.md](./quickstart.md) sections 1–9 and confirm each produces the stated output, including the byte-identity diffs (§2) and the round-trip diff (§8).
- [ ] T053 Run the full gate `uv run black . && uv run flake8 src tests && uv run pytest && uv run python scripts/check_docs.py` and confirm all four are green with coverage at or above 85%, and that the pre-existing test count from T001 is unchanged except for the replaced rendering tests (SC-005).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup. **Blocks every user story** — no sentence can be rendered before `prose.py`, the display-name columns and `Ship.tech_level` exist.
- **User Story 1 (Phase 3)**: Depends on Foundational. No dependency on any other story.
- **User Story 2 (Phase 4)**: Depends on Foundational. T036 edits `_hull`, created in T024, so US2 follows US1 in practice; T032 and T035 (`design.py`) are independent of US1 entirely.
- **User Story 3 (Phase 5)**: Depends on Foundational and on the sentence builders from US1 (T024–T028), whose omission conditions it completes.
- **User Story 4 (Phase 6)**: Depends on Foundational and on T024–T025, whose builders it branches.
- **Polish (Phase 7)**: T047–T050 depend on T029–T031 (the rename). T051–T053 depend on every story being complete.

### Within Each Phase

- Tests are written and confirmed failing before the implementation task that satisfies them.
- Tables and models before the builder; the builder before the renderer; the renderer before the CLI.
- Tasks touching the same file are sequential even when logically independent.

### Parallel Opportunities

- **Phase 2 tests**: T004, T005 and T006 touch three different files and can run together. T002 and T003 share `tests/test_ship_tables.py` and must be sequential.
- **Phase 2 implementation**: T007 (`prose.py`) is independent of everything else in the phase and can run alongside T008–T010. T008, T009 and T010 all edit `tables.py` and must be sequential.
- **Phase 3**: T014–T021 all append to `tests/test_ship_description.py` and T023–T028 all edit `description.py`, so neither group parallelises. T022 (`test_cli.py`) can be written alongside them.
- **Phase 4**: T032/T035 (`design.py` and its tests) run independently of T033/T036 (`description.py` and its tests).
- **Phase 7**: T047, T048 and T049 touch three different documents and can run together.

---

## Parallel Example: Phase 2

```bash
# Three foundational test files, three different targets — write together:
Task: "Add shape-validation tests to tests/test_ship_models.py"          # T004
Task: "Add tech-level derivation tests to tests/test_ship_builder.py"    # T005
Task: "Create tests/test_ship_prose.py with table-driven cases"          # T006

# Then, prose.py has no package dependency and can land alongside the table work:
Task: "Create src/cetools/engine/ships/prose.py"                         # T007
Task: "Add display-name/plural/tl/dm columns to tables.py"               # T008
```

## Parallel Example: Phase 7

```bash
Task: "Replace the sample output in README.md"          # T047
Task: "Update the module map in CONTRIBUTING.md"        # T048
Task: "Update the ship vocabulary in CONTEXT.md"        # T049
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1: Setup — record the baseline.
2. Phase 2: Foundational — `prose.py`, the table columns, the two design fields, the derived tech level. **Blocks everything.**
3. Phase 3: User Story 1 — the renderer and the `generate` path.
4. **STOP and VALIDATE**: `uv run cetools ship generate --seed 42` twice, diff for byte-identity, read the paragraph beside an SRD Chapter 9 vessel.

At this point the feature is complete and useful: generated ships render in the format the rules
use.

### Incremental Delivery

1. Setup + Foundational → the data layer is in place.
2. + User Story 1 → generated ships render as SRD vessels (**MVP**).
3. + User Story 2 → hand-authored designs render, with `purpose` and `tech_level` round-tripping.
4. + User Story 3 → unarmed and lightly-equipped ships read as prose, not negations.
5. + User Story 4 → small craft read correctly as non-jump-capable vessels.
6. + Polish → docs, gates and the quickstart walkthrough.

### Notes

- [P] tasks touch different files and have no incomplete dependencies.
- Both P1 stories are served by one renderer, so US2 is a thin increment over US1 rather than a parallel track.
- Commit after each task or logical group; the pre-push hooks run isort, Black, flake8 and pytest.
- FR-032 is the standing constraint: no task in this list may change a computed ship value. If a task appears to require one, stop — the presentation-only reading is the correct one.
