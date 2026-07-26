# Tasks: Fuel-Limited Jump Drive Rating

**Input**: Design documents from `/specs/013-fuel-limited-jump-drive/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/jump-drive-fit.md,
quickstart.md

**Tests**: Test tasks are included. Constitution IV (Test-First) is a project gate, and plan.md
states "Every task in the Phase 2 breakdown is written test-first".

Every test of *new behaviour* is written before its implementation task and MUST be confirmed red
first: T006, T007, T010–T013, T017, T018, T020–T023 and T025. Three tests are deliberately **not**
red-first, because they pin properties that already hold rather than behaviour being added:

- **T004, T005** — table-ordering invariants. They pass on the current tables by design; their job
  is to fail loudly on a *future* SRD row that breaks the ordering the search documents.
- **T027** — the re-pinned stability baseline. Its data is generated from the post-change generator
  in the same task, so it can never be red here. It is a regression net for the next feature, not a
  gate on this one.

**Organization**: Tasks are grouped by user story so each story can be implemented, tested and
checkpointed independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths appear in every description

## Path Conventions

Single project: `src/cetools/` and `tests/` at the repository root, per plan.md's Project Structure.
Feature-scoped artifacts live under `specs/013-fuel-limited-jump-drive/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the red state and capture the pre-change measurements the success criteria
compare against. Nothing here modifies `src/cetools`.

- [X] T001 Run `uv run python specs/013-fuel-limited-jump-drive/scripts/survey_drive_fit.py` and confirm it exits 1 with the counts quickstart.md Scenario 0 predicts (111 short-fuelled, 111 zero-jump prose, 1087 not-lightest, 0 starved); record the output in the implementation notes as the measured red state
  - Measured red state (exit 1): `jump_tons strictly increasing: True`; `rating non-decreasing: True`; `starved combos: 0`; over 2000 seeds — `short-fuelled: 111`, `FR-014 starved hulls: 0`, `negative cargo: 0`, `'zero Jump-n' in prose: 111`, `drive not lightest at rating: 1087`, `non-reproducible seeds: 0`; small craft reproducible: `True`. Matches quickstart.md Scenario 0 exactly.
- [X] T002 Capture the pre-change sweep that SC-007 and SC-005 compare against: write `specs/013-fuel-limited-jump-drive/baseline/pre_change_sweep.json` with two top-level keys, using a throwaway script run before any edit to `src/cetools/engine/ships/generator.py` — (a) `"standard"`, mapping each of 2000 seeds to that seed's `hull_tons`, `jump_rating`, `jump_code`, `maneuver_code`, `power_code` and `assumed_jump_distance` from today's `generate_ship(RandomRolls.seeded(n))`; (b) `"small_craft"`, mapping each of the same 2000 seeds to `dump_design(generate_ship(RandomRolls.seeded(n), small_craft=True).design)`, the reference SC-005 needs and which cannot be recovered once the generator is edited
  - Captured via a throwaway script (not committed): 2000 `"standard"` entries and 2000 `"small_craft"` entries, written to `specs/013-fuel-limited-jump-drive/baseline/pre_change_sweep.json` (908K, seed keys as strings).
- [X] T003 [P] Capture the authored-design anchor SC-010 and FR-012 compare against: write `specs/013-fuel-limited-jump-drive/baseline/authored_designs.json` mapping each of the repository's six authored example TOMLs — `specs/010-starship-generator/examples/{fighter,free-trader,heavy-cruiser,scout-courier,warship}.toml` and `specs/011-universal-ship-format/examples/subsidized-merchant.toml` — to today's `build_ship(load_design(path))` as a full field dump, and additionally record the free-trader's headline figures (`total_cost`, `cargo_tons`, `crew.total` = 29.772, 135, 5) in the implementation notes as the human-checkable spot value of quickstart.md Scenario 3
  - Captured via a throwaway script (not committed) using a recursive dataclass/Enum/tuple-to-JSON dump, written to `specs/013-fuel-limited-jump-drive/baseline/authored_designs.json` (20K, keyed by TOML path). Free-trader spot check confirmed: `total_cost=29.772`, `cargo_tons=135.0`, `crew.total=5` — matches quickstart.md Scenario 3 exactly.

**Checkpoint**: The defect is measured, and both "before" references exist —
`baseline/pre_change_sweep.json` (standard-hull and small-craft) and `baseline/authored_designs.json`
(all six authored examples). **T002 MUST complete before any task in Phase 2 or later**: once
`generator.py` is edited, the pre-change sweep is unrecoverable. T003 should be captured now for the
same reason, though `builder.py` is untouched by this feature, so its data would survive a later
capture.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The pure fit search and the table invariants it rests on. Every user story depends on
this function existing and being correct.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 [P] Add a table-ordering invariant test to `tests/test_ship_tables.py` asserting that `DRIVE_COSTS[letter].jump_tons` is strictly increasing across all letters in table order (research.md Part C, invariant 1) — expected to pass on the current tables and to fail loudly on a future SRD row that breaks it
- [X] T005 [P] Add a second table-ordering invariant test to `tests/test_ship_tables.py` asserting that, for every hull in `HULLS`, `DRIVE_PERFORMANCE[letter][hull]` is non-decreasing across that hull's legal letters in table order (research.md Part C, invariant 2)
- [X] T006 Write the failing contract tests for the fit helper in `tests/test_ship_generator.py`, one test per postcondition C1–C4 and C8 from `contracts/jump-drive-fit.md`, driven by the contract's four non-fallback worked examples (400/`C`/200 → `B`; 700/`Z`/600 → `U`; 700/`Z`/400 → `N`; 100/`C`/72 → `B`) plus a legality-and-ceiling sweep over every hull and every legal drawn code — these must fail with `AttributeError`/`ImportError` because `_fit_jump_drive` does not yet exist
- [X] T007 Write the failing FR-014 starved-hull tests in `tests/test_ship_generator.py` covering postconditions C5 and C6: `_fit_jump_drive(100, "A", 5.0)` returns `"A"`, a budget of `0.0` on every hull returns that hull's lightest lowest-rated legal drive, and no input satisfying the preconditions raises (quickstart.md Scenario 5)
- [X] T008 Implement `_fit_jump_drive(hull_tons: int, drawn_code: str, budget: float) -> str` in `src/cetools/engine/ships/generator.py` per data-model.md's four-step selection rule: reuse `_codes_valid_for_hull` for legality, filter to ratings `<= DRIVE_PERFORMANCE[drawn_code][hull_tons]`, reduce to the lightest letter per distinct rating by explicit `min(..., key=jump_tons)` (never by letter order), return the highest-rated candidate satisfying `jump_tons + 0.1 * hull_tons * rating <= budget`, else the lowest-rated candidate; take no `Rolls` parameter, so C7 holds by construction
- [X] T009 Run `uv run pytest tests/test_ship_generator.py tests/test_ship_tables.py -v --no-cov` and confirm the red tests T006 and T007 now pass, that T004 and T005 still pass (they were green from the start — see the Tests note above), and that no other test in those files changed result

**Checkpoint**: `_fit_jump_drive` is correct and total in isolation, and the table invariants it
documents are pinned. User story work can begin.

---

## Phase 3: User Story 1 - Every generated starship can make at least one jump (Priority: P1) 🎯 MVP

**Goal**: Wire the fit search into `generate_ship` so every generated starship's jump fuel covers at
least one complete jump at its installed rating, with freed tonnage flowing on to fuel and fittings.

**Independent Test**: Over a 2000-seed sweep, every generated starship satisfies
`ship.jump_fuel >= 0.1 * ship.hull_tons * ship.jump_rating`, with any FR-014 starved-hull ship
counted on its own line rather than as a pass.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST and confirm they FAIL before T014.**

- [X] T010 [P] [US1] Add the SC-001/SC-002 sweep test to `tests/test_ship_generator.py`: over a 2000-seed sweep of `generate_ship(RandomRolls.seeded(n))`, assert `ship.jump_fuel >= 0.1 * ship.hull_tons * ship.jump_rating` and `ship.assumed_jump_distance == ship.jump_rating` for every seed, classifying an FR-014 ship by the spec's two-part recomputable test (short fuel **and** no legal drive fuellable within its own budget) and asserting that count is zero
  - Confirmed red before T014: failed with the pre-change generator (111 seeds short-fuelled); passes after T014.
- [X] T011 [P] [US1] Add the US1 Acceptance Scenario 1 **end-to-end** test to `tests/test_ship_generator.py`: drive `generate_ship` with a `ScriptedRolls` that forces a 100-ton hull, maneuver code `A` and jump code `C`, and power code `C`, and assert the *finished ship* mounts jump drive `B` at Jump-4 with `assumed_jump_distance == 4` and `jump_fuel == 40.0`. This is the whole-generator counterpart to T006's `100`/`C`/`72` helper case, which asserts the same selection at the unit level; keep both — T006 proves the search, T011 proves the wiring, and the budget arithmetic (72 tons once the 10-ton bridge, 2-ton maneuver drive, 10-ton power plant and 6 tons of power-plant fuel are deducted) is only observable end to end
  - Confirmed red before T014: pre-change ship mounted `C` (Jump-6, underfuelled); mounts `B` (Jump-4) after T014.
- [X] T012 [P] [US1] Add the US1 Acceptance Scenario 3 / SC-007 test to `tests/test_ship_generator.py`: for every seed under the `"standard"` key of `specs/013-fuel-limited-jump-drive/baseline/pre_change_sweep.json` (T002) that is recorded as already fully fuelled (`assumed_jump_distance == jump_rating`), assert the post-change ship keeps its pre-change `hull_tons`, `jump_rating`, `maneuver_code` and `power_code`, and that any change of `jump_code` is to a drive of strictly lower `jump_tons` at the same rating
  - Passed even before T014 (the generator was still byte-identical to the code that produced the baseline, so the comparison was vacuously true); it becomes a meaningful regression net once T014 lands, and still passes.
- [X] T013 [P] [US1] Add the SC-003 tonnage test to `tests/test_ship_generator.py`: over the same sweep, assert `ship.cargo_tons >= 0` and that total allocated tonnage never exceeds `ship.hull_tons`, so the freed tonnage of FR-005 never overruns the hull (FR-013, contract G5). Add a comment recording why FR-013's *other* half — "passes exactly the same validation a caller-supplied design must pass" — needs no separate assertion: `generate_ship` returns `build_ship(design)`, so a sweep that completes without raising has already run every generated design through the sole validation authority
  - Held both before and after T014 (SC-003 was never the defect); asserted here as a regression net.

### Implementation for User Story 1

- [X] T014 [US1] Reorder the allocation in `generate_ship` in `src/cetools/engine/ships/generator.py` per data-model.md's "After" block: compute `budget = hull_tons - (maneuver_tons + power_tons + bridge_tons + power_fuel_tons)` with the jump drive excluded, call `jump_code = _fit_jump_drive(hull_tons, drawn_jump_code, budget)`, then set `remaining = max(0.0, budget - DRIVE_COSTS[jump_code].jump_tons)`; leave the `max_jump_distance` / `jump_distance` arithmetic and the `max(0.0, ...)` clamp verbatim, and leave `_select_drive_codes` and every later `_select_*` call untouched
- [X] T015 [US1] Confirm `_select_drive_codes` in `src/cetools/engine/ships/generator.py` is unmodified and the power plant is not re-derived (research.md Part F: the power-plant legality constraint is a floor that a downgrade only relaxes), so FR-008 holds by construction
  - Confirmed by inspection: `_select_drive_codes` is untouched; only the block after it in `generate_ship` was reordered.
- [X] T016 [US1] Run `uv run pytest tests/test_ship_generator.py -k "jump" -v --no-cov` plus the quickstart.md Scenario 1 one-liner (50 seeds at `hull_size=100`, asserting `assumed_jump_distance == jump_rating`) and confirm all pass
  - 31 passed, 26 deselected. One-liner: "100-ton hulls: every drive is fully fuelled". Survey script now exits 0 with every line reading 0 and `PASS`.

**Checkpoint**: The defect is fixed. Every generated starship carries a full jump of fuel, and the
survey script's short-fuelled and starved-hull lines both read 0.

---

## Phase 4: User Story 2 - The description reports an honest, non-zero jump range (Priority: P2)

**Goal**: Assert that the referee-facing prose reports one or more jumps, and that the drive letter,
performance rating and jump count agree.

**Independent Test**: Render descriptions across the seed sweep and confirm no generated starship
description contains a zero jump count, counting any FR-014 ship separately.

**Note**: `description.py` is **not** modified. Its arithmetic is already correct (research.md Part
A); this story asserts the behaviour US1 delivers.

### Tests for User Story 2 ⚠️

- [ ] T017 [P] [US2] Add the SC-004 prose sweep test to `tests/test_ship_description.py`: render `render_description(generate_ship(RandomRolls.seeded(n)))` over the 2000-seed sweep and assert no description reports a zero jump count, classifying any FR-014 ship separately and asserting that count is zero
- [ ] T018 [P] [US2] Add the US2 Acceptance Scenario 2 consistency test to `tests/test_ship_description.py`: for a sample of seeds including at least one whose drive was downgraded, assert the drive letter in the drives sentence, the `Jump-N` in the performance clause and the jump count in the fuel sentence are mutually consistent and agree with `ship.design.jump_code`

### Implementation for User Story 2

- [ ] T019 [US2] Confirm `src/cetools/engine/ships/description.py` needs no change by running `uv run pytest tests/test_ship_description.py -v --no-cov` and `uv run cetools ship generate --seed 42`, checking the fuel sentence reads "one Jump-N jump" and never "zero" (quickstart.md Scenario 2)

**Checkpoint**: The prose is honest. US1 and US2 both hold independently.

---

## Phase 5: User Story 3 - Existing seeds, small craft and authored designs stay predictable (Priority: P3)

**Goal**: Prove the change disturbs neither determinism, nor the small-craft path, nor
hand-authored designs, and replace the feature-012 baseline guard this feature legitimately
invalidates.

**Independent Test**: Re-run seeded generation twice and compare; sweep small-craft seeds against
pre-change output; build a design file specifying a jump distance below its drive's rating and
confirm it builds unaltered.

### Tests for User Story 3 ⚠️

- [ ] T020 [P] [US3] Add the SC-006 determinism test to `tests/test_ship_generator.py`: over the sweep, assert `generate_ship(RandomRolls.seeded(n)) == generate_ship(RandomRolls.seeded(n))` on the standard-hull path, the small-craft path and the hull-constrained path alike
- [ ] T021 [P] [US3] Add the SC-005 small-craft test to `tests/test_ship_generator.py`: for every seed in the sweep, assert `dump_design(generate_ship(RandomRolls.seeded(n), small_craft=True).design)` equals that seed's entry under the `"small_craft"` key of `specs/013-fuel-limited-jump-drive/baseline/pre_change_sweep.json` (T002), proving FR-010
- [ ] T022 [P] [US3] Add the SC-009 hull-size test to `tests/test_ship_generator.py`: over the sweep, assert every ship generated with `hull_size=n` has `ship.hull_tons == n` (FR-011)
- [ ] T023 [P] [US3] Add the FR-012 / SC-010 authored-design test to `tests/test_ship_builder.py`: build a `ShipDesign` whose `jump_distance` is explicitly below one full jump at its drive's rating and assert `build_ship` produces exactly that ship, never a silently corrected one; then assert that all six authored example TOMLs build to `Ship` values field-equal to the ones recorded in `specs/013-fuel-limited-jump-drive/baseline/authored_designs.json` (T003), covering SC-010's "every design in the repository's authored example designs" rather than the free-trader alone
- [ ] T024 [US3] Add a `RecordingRolls` wrapper to `tests/test_ship_generator.py` — a `Rolls` decorator that records each `RollName` drawn, defined in `tests/` and **not** in `src/cetools/engine/rolls.py` (research.md Part G, Constitution's no-abstraction-until-a-second-caller posture)
- [ ] T025 [US3] Add the SC-008 draw-order test to `tests/test_ship_generator.py` using `RecordingRolls`: over a seed sweep on both the standard-hull and small-craft paths, assert `RollName.SHIP_NAME` is the final recorded draw and is drawn exactly once, and that `SHIP_JUMP_CODE`, `SHIP_MANEUVER_CODE` and `SHIP_POWER_CODE` appear in that order; do **not** assert a stable total draw count, which FR-008 explicitly does not promise

### Implementation for User Story 3

- [ ] T026 [US3] Delete `test_naming_is_purely_additive_against_the_pre_feature_baseline` and the `_BASELINE_PATH` constant from `tests/test_ship_generator.py` (lines 13 and 139–157), which this feature legitimately invalidates for 54% of seeds; leave `specs/012-ship-names/baseline/designs.json` in the repository as history
- [ ] T027 [US3] Generate the re-pinned stability anchor `specs/013-fuel-limited-jump-drive/baseline/designs.json` from the post-change generator over the same seed set the 012 baseline used, and add a test to `tests/test_ship_generator.py` comparing seeded designs against it — a blunt regression net for *future* features, not for this one
- [ ] T028 [US3] Run `uv run pytest tests/test_ship_generator.py tests/test_ship_builder.py tests/test_ship_design.py -v --no-cov` and the quickstart.md Scenario 3 free-trader one-liner, confirming all pass and the Beowulf's figures have not moved

**Checkpoint**: All three user stories hold independently. Determinism, small craft and authored
designs are provably undisturbed.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, docstrings and the full quality gate.

- [ ] T029 [P] Update the generator section of `README.md` to state the one-jump guarantee: a randomly generated starship always carries fuel for at least one complete jump at its installed rating, and the lightest drive at a rating is always the one installed
- [ ] T030 [P] Update the ship-generator vocabulary in `CONTEXT.md` to name fuel-limited drive selection, and record that the correction is generation policy which `builder.py` deliberately does not apply to authored designs
- [ ] T031 [P] Update the baseline-guard docstring references in `src/cetools/engine/ships/names.py` (lines 11 and 18) and `src/cetools/engine/ships/generator.py` (line 355) to point at the SC-008 draw-order test and `specs/013-fuel-limited-jump-drive/baseline/designs.json` instead of the retired 012 pinned-design test
- [ ] T032 Run `uv run python specs/013-fuel-limited-jump-drive/scripts/survey_drive_fit.py` and confirm it exits 0 with `PASS` and every counted line reading 0 (quickstart.md Scenario 0, green)
- [ ] T033 Confirm the performance budget still holds by running `uv run pytest tests/test_ship_generator.py -k "tenth_of_a_second" -v --no-cov`; the fit search scans at most 24 letters and must remain immeasurable against the existing cost
- [ ] T034 Run the full quality gate from AGENTS.md: `uv run black . && uv run flake8 src tests && uv run pytest && uv run python scripts/check_docs.py`, confirming pytest is green with `src/cetools` coverage at or above 85% and `check_docs.py` clean across the T029–T031 edits
- [ ] T035 Walk quickstart.md Scenarios 0 through 5 end to end and confirm each produces its documented expected output

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies. T002 is a hard prerequisite for everything after it — the
  pre-change sweep cannot be captured once `generator.py` is edited. T003 is a prerequisite for T023
  and should be captured alongside T002.
- **Foundational (Phase 2)**: Depends on Phase 1. BLOCKS all user stories.
- **User Story 1 (Phase 3)**: Depends on Phase 2 (needs `_fit_jump_drive`).
- **User Story 2 (Phase 4)**: Depends on Phase 3 — the honest prose is a consequence of US1's fix,
  not an independent code change. Its tests can be *written* after Phase 2.
- **User Story 3 (Phase 5)**: Depends on Phase 3 for T021/T027 (which compare post-change output);
  T023 additionally needs T003's capture; T020, T022, T024 and T026 depend only on Phase 2.
- **Polish (Phase 6)**: Depends on Phases 3–5.

### User Story Dependencies

- **US1 (P1)**: Independent once Phase 2 lands. Delivers the fix on its own.
- **US2 (P2)**: Observational — it asserts US1's outcome in prose and changes no source. Genuinely
  independent to test, but will fail until US1 lands.
- **US3 (P3)**: Regression safety. Independent of US1 and US2 in intent; T021 and T027 need the
  post-change generator to compare against.

### Within Each User Story

- Tests are written first and MUST fail before the implementation task in the same phase.
- The fit helper (T008) precedes the allocation reorder (T014).
- T026 (retire the old guard) must not land before T025 (the replacement guard) passes, so the
  invariant is never unguarded.

### Parallel Opportunities

- T004 and T005 are independent tests in the same file — write together, one commit.
- T010, T011, T012 and T013 are independent US1 test tasks; all four can be written before T014.
- T017 and T018 touch only `tests/test_ship_description.py` and are independent of each other.
- T020, T021, T022 and T023 are independent US3 test tasks.
- T029, T030 and T031 touch three different files and can proceed together.

---

## Parallel Example: User Story 1

```bash
# Write all four US1 tests together, before touching generator.py:
Task: "SC-001/SC-002 sweep test in tests/test_ship_generator.py"          # T010
Task: "Overview 100-ton-hull scenario test in tests/test_ship_generator.py"  # T011
Task: "SC-007 pre-change comparison test in tests/test_ship_generator.py"    # T012
Task: "SC-003 tonnage test in tests/test_ship_generator.py"               # T013

# Confirm all four fail, then implement:
Task: "Allocation reorder in src/cetools/engine/ships/generator.py"       # T014
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: capture the red state and the pre-change sweep (T001–T003).
2. Phase 2: the fit helper and its table invariants (T004–T009) — **blocks everything**.
3. Phase 3: the allocation reorder (T010–T016).
4. **STOP and VALIDATE**: run the survey script; the short-fuelled line must read 0.

At this point the reported defect is fixed and the tool emits no unusable starships.

### Incremental Delivery

1. Setup + Foundational → `_fit_jump_drive` proven correct in isolation.
2. Add US1 → survey short-fuelled count drops 111 → 0 → **MVP**.
3. Add US2 → prose sweep proves no zero jump counts reach the referee.
4. Add US3 → determinism, small craft and authored designs proven undisturbed; the draw-order guard
   is replaced by a stronger direct assertion.
5. Polish → docs, docstrings, full quality gate.

### Notes

- The single source change is `src/cetools/engine/ships/generator.py`: one ~15-line private
  function plus a ~6-line reorder. `builder.py`, `tables.py`, `description.py`, `models.py`,
  `prose.py` and `cli/ship.py` are all untouched by design.
- FR-014 is unreachable through `generate_ship` with the current tables (research.md Part E), so it
  is tested against the helper directly (T007). This keeps the branch covered without a seed that
  cannot exist.
- Seed-to-ship output moves for ~54% of seeds. That is intended (FR-004, research.md Part D), which
  is why SC-007 is asserted per seed against T002's capture rather than by whole-ship comparison.
- Commit after each task or logical group; stop at any checkpoint to validate a story on its own.
