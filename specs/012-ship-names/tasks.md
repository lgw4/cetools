# Tasks: Ship Names

**Input**: Design documents from `/specs/012-ship-names/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/name-catalogue.md](./contracts/name-catalogue.md),
[quickstart.md](./quickstart.md)

**Tests**: Test tasks are included and are mandatory. The constitution's Principle IV (Test-First,
NON-NEGOTIABLE) requires red-green-refactor on all new code, and plan.md's Constitution Check
commits to writing each catalogue invariant, the selection test and the SC-008 additivity test
before the code they constrain.

**Organization**: Tasks are grouped by user story so each story can be implemented, tested and
delivered independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- File paths are exact and relative to the repository root

## Path Conventions

Single project: engine library in `src/cetools/engine/`, CLI in `src/cetools/cli/`, tests in
`tests/` mirroring the package. No new directories are created by this feature.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the environment and the one pre-captured artifact the feature depends on

- [ ] T001 Run `uv sync` and confirm `uv run pytest` is green on `012-ship-names` before any edit, so every later failure is attributable to this feature
- [ ] T002 Verify the pre-feature baseline artifact `specs/012-ship-names/baseline/designs.json` is present and holds 100 entries keyed `standard:<seed>` and `small_craft:<seed>` for seeds 0–49; it was captured at commit `d387b70` and MUST NOT be regenerated after `src/cetools/engine/ships/generator.py` is touched (research.md Part A)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The roll name, the catalogue types and a non-empty starter catalogue — everything the
three stories build on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Add `SHIP_NAME = "ship_name"` to `RollName` in `src/cetools/engine/rolls.py`, in the "Uniform picks from a list" block after `SHIP_SCREEN` (data-model.md §RollName.SHIP_NAME)
- [ ] T004 Write failing per-entry shape tests V1–V6 in `tests/test_ship_names.py`, parametrised over `SHIP_NAMES`: fiction entries carry a `BasisKind` member (V1) and a non-empty stripped `basis_reference` (V2); `MYTHOLOGY_FOLKLORE` entries carry `basis_kind is None` and `basis_reference == ""` (V3); every `name` is non-empty and `isascii()` (V4); no leading, trailing, doubled or non-space whitespace (V4a); no name begins with a ship-type designation from the deny-list in research.md Part E (V5); every name survives `ShipDesign(hull_tons=100, name=…)` construction (V6). The file must fail on import — `names.py` does not exist yet
- [ ] T005 Create `src/cetools/engine/ships/names.py` with a module docstring recording **two** invariants. First, the draw-last placement (research.md Part A). Second, FR-010b's stability rule: the seed→*name* mapping is not a compatibility surface, so adding, removing or reordering entries is a permitted data-only edit, while the seed→*ship* mapping is one and is pinned by the baseline test. A contributor withdrawing a mis-sourced entry must be able to read that warrant in the module itself. Then add `Tradition` (StrEnum: `MYTHOLOGY_FOLKLORE`, `WRITTEN_SF`, `SCREEN_SF`) and `BasisKind` (StrEnum: `ORDINARY_WORD`, `REAL_VESSEL`, `PUBLIC_DOMAIN_WORK`) per data-model.md (FR-010b)
- [ ] T006 Add the frozen `ShipName` dataclass (`name: str`, `tradition: Tradition`, `basis_kind: BasisKind | None = None`, `basis_reference: str = ""`) and a starter `SHIP_NAMES: tuple[ShipName, ...]` of at least three entries covering all three traditions, in `src/cetools/engine/ships/names.py`, turning T004's tests green. The module MUST import only from `cetools.engine.rolls` — never `models`, `tables` or `cli`
- [ ] T007 Export `BasisKind`, `SHIP_NAMES`, `ShipName` and `Tradition` from `src/cetools/engine/ships/__init__.py`, adding them to both the imports and the alphabetised `__all__`

**Checkpoint**: The catalogue types exist, a non-empty catalogue is importable from
`cetools.engine.ships`, and per-entry shape is enforced by test. User story work can begin.

---

## Phase 3: User Story 1 - A generated ship arrives already named (Priority: P1) 🎯 MVP

**Goal**: Every randomly generated ship — starship or small craft — comes back carrying a
catalogue name, which reaches the rendered description and the exported design and survives a
rebuild from that export.

**Independent Test**: Run `uv run cetools ship generate --seed 42` and
`uv run cetools ship generate --seed 7 --small-craft`; both print a named heading and no
"Unnamed Ship". Export with `--toml`, rebuild with `ship build`, and the same name renders
(quickstart.md Scenarios 1 and 2).

### Tests for User Story 1 ⚠️

> Write these FIRST and confirm they FAIL before the matching implementation task

- [ ] T008 [US1] Write a failing selection test for `generate_ship_name` in `tests/test_ship_names.py`: `ScriptedRolls(choices={RollName.SHIP_NAME: 0})` returns `SHIP_NAMES[0].name`, a negative index picks from the end, and the return value is always an existing catalogue `name` rather than a constructed string (FR-003, FR-011; contracts §`generate_ship_name`)
- [ ] T009 [US1] Write failing naming tests for both generation paths in `tests/test_ship_generator.py`: `generate_ship(RandomRolls.seeded(42)).design.name` is a catalogue name, and the same holds for `small_craft=True` (FR-001, FR-002)
- [ ] T010 [P] [US1] Write a failing test in `tests/test_ship_description.py` that a generated ship's `render_description` output contains its `design.name` and does not contain "Unnamed Ship", on both paths (FR-012, SC-001)
- [ ] T011 [P] [US1] Write a failing round-trip test in `tests/test_ship_design.py`: `dump_design` of a generated design emits the `name`, and `build_ship(loads_design(dump_design(design)))` renders under the same name (FR-013, SC-002)
- [ ] T012 [P] [US1] Write failing CLI tests in `tests/test_cli.py` using `CliRunner`: `ship generate --seed 42` prints a named `TL<n> <name>` heading with no "Unnamed Ship", `--small-craft` does the same, and `--toml` output carries a `name = "…"` key. One command, no manual naming step, no file editing (contracts §2, SC-004)
- [ ] T019 [US2] Write the SC-008 additivity regression test in `tests/test_ship_generator.py`: load `specs/012-ship-names/baseline/designs.json`, regenerate each of the 100 pinned seeds on its recorded path, assert `design.name` is set, then assert `dump_design(dataclasses.replace(design, name=None))` equals the recorded string; the assertion message MUST name the failing key (FR-010a, SC-008)

> **T019 is deliberately out of numeric order and out of its story.** It belongs to User Story 2,
> but it is the test that *gates* T015 and T016: the draw-last placement is the feature's
> load-bearing invariant, and plan.md's Constitution Check commits to writing this test against
> the pre-captured baseline before `generator.py` is touched. Principle IV is not satisfied by
> T009 alone: T009 proves a name appears, not that nothing else moved. Write T019, confirm it
> fails red, then implement.

### Implementation for User Story 1

- [ ] T013 [US1] Implement `generate_ship_name(rolls: Rolls | None = None) -> str` in `src/cetools/engine/ships/names.py` as exactly one `rolls.choose(SHIP_NAMES, RollName.SHIP_NAME)` returning `.name`, defaulting `rolls` to `RandomRolls()`; no other entropy, no I/O, no seed access (FR-011)
- [ ] T014 [US1] Add `generate_ship_name` to the imports and `__all__` of `src/cetools/engine/ships/__init__.py`
- [ ] T015 [US1] Wire naming into the standard starship path in `src/cetools/engine/ships/generator.py`: call `generate_ship_name(rolls)` after `_select_screen` and pass it as `name=` to the `ShipDesign(...)` at line 383. The call MUST be the last `Rolls` draw on the path (FR-010a)
- [ ] T016 [US1] Wire naming into the small-craft path in `src/cetools/engine/ships/generator.py`: call `generate_ship_name(rolls)` after `_select_small_craft_turret` and pass it as `name=` to the `ShipDesign(...)` at line 316, again as the last `Rolls` draw (FR-002, FR-010a)
- [ ] T017 [US1] Extend the `generate_ship` docstring in `src/cetools/engine/ships/generator.py` to record that the name draw MUST stay last on every path, and why, pointing at the baseline regression test (plan.md Risks)

**Checkpoint**: Random generation is named end to end (description, TOML export and rebuild), and
the baseline sweep proves nothing else about any pinned seed moved. US1 is independently
demonstrable via quickstart.md Scenarios 1, 2 and 4.

---

## Phase 4: User Story 2 - The same seed yields the same ship, name included (Priority: P2)

**Goal**: Naming is reproducible by seed and purely additive — a seed pinned before this feature
still produces the identical ship, differing only by now carrying a name — and a name an author
supplied is never overwritten.

**Independent Test**: Generate twice from one seed and compare names; run the pinned-baseline
sweep over all 100 recorded seeds with the name cleared; build a design that names its own ship
and confirm the name is unchanged (quickstart.md Scenarios 3, 4 and 5).

### Tests for User Story 2 ⚠️

- [ ] T018 [US2] Write reproducibility tests in `tests/test_ship_generator.py`: `generate_ship(RandomRolls.seeded(42))` twice yields equal ships including `design.name`, and names across distinct seeds are not forced to match (FR-010, SC-002)

> **T019** (the SC-008 additivity regression test) belongs to this story but is listed in Phase 3,
> because it must be red before T015 and T016 are written. It is not a second task; do not count
> it twice.

- [ ] T020 [P] [US2] Write tests in `tests/test_ship_builder.py` that `build_ship` assigns no name: a design with `name=None` builds and still renders "Unnamed Ship", and building consumes no randomness (FR-015)
- [ ] T021 [P] [US2] Write tests in `tests/test_ship_description.py` that an author-supplied name always wins and that `name=""` or a whitespace-only name renders "Unnamed Ship" (FR-014, FR-015a, SC-006)
- [ ] T022 [P] [US2] Write a CLI test in `tests/test_cli.py` that `ship build specs/010-starship-generator/examples/free-trader.toml` still renders `TL8 Beowulf`, unchanged from before this feature (contracts §2)

### Implementation for User Story 2

- [ ] T023 [US2] No production code is expected: US1's draw-last placement is what makes T018 and T020–T022 pass (T019 having already been proven green in Phase 3). If any of them fail, correct the draw position in `src/cetools/engine/ships/generator.py` — do NOT regenerate `specs/012-ship-names/baseline/designs.json`, which is the pre-feature record and the only evidence FR-010a holds

**Checkpoint**: Determinism and additivity are proven against a pre-captured baseline, and
hand-authored designs are demonstrably untouched by naming.

---

## Phase 5: User Story 3 - Names span the source traditions, without repeating themselves (Priority: P3)

**Goal**: Grow the starter catalogue into a balanced body of ~160 curated names — 76 mythology and
folklore, 42 written science fiction, 42 science fiction film and television — each fiction entry
carrying a reviewed sourcing basis, with no duplicates.

**Independent Test**: Inspect the catalogue for the size floor, per-tradition floors, the 50% cap,
uniqueness and basis well-formedness, all of which hold against the catalogue alone
(quickstart.md Scenario 6). The variety check (generate 20 ships from seeds 0–19 and count
distinct names, quickstart.md Scenario 3) is *not* independent: it exercises `generate_ship` and
therefore requires US1's wiring.

### Tests for User Story 3 ⚠️

- [ ] T024 [US3] Write failing composition tests in `tests/test_ship_names.py`: `len(SHIP_NAMES) >= 150` (C1), every `Tradition` member has `>= 20` entries (C2), no member exceeds `len(SHIP_NAMES) // 2` (C3), and `len({e.name.strip().casefold() for e in SHIP_NAMES}) == len(SHIP_NAMES)` (V7). Assert floors and caps only — never exact counts, so adding a name is never a test edit (FR-008, FR-009, SC-005)
- [ ] T025 [US3] Write a failing variety test in `tests/test_ship_generator.py` over the fixed seed set 0–19: at least 17 of the 20 generated ships carry distinct names. Pin the seeds so the check cannot flake (SC-003). This test calls `generate_ship`, so it stays red until T015 and T016 have landed and the catalogue has grown; it is the one US3 task that is not independent of US1

### Implementation for User Story 3

- [ ] T026 [US3] Mythology and folklore pass in `src/cetools/engine/ships/names.py`: grow `SHIP_NAMES` to 76 `MYTHOLOGY_FOLKLORE` entries drawn across Greek, Norse, Arthurian, Celtic, Mesopotamian, Japanese, Chinese, West African and Mesoamerican sources (research.md C3), each with `basis_kind=None` and `basis_reference=""`, romanised and ASCII-only (FR-004, FR-007a, FR-018)
- [ ] T027 [US3] Written science fiction pass in `src/cetools/engine/ships/names.py`: add 42 `WRITTEN_SF` entries, each recording exactly one `BasisKind` and a reference specific enough to confirm without repeating the research — e.g. `"HMS Endeavour, 1764"`, `"Rocinante, Cervantes, Don Quixote (1605)"`. Exclude any distinctive coined name; skip any name already catalogued under mythology (FR-005, FR-007a, FR-016, FR-016a)
- [ ] T028 [US3] Screen science fiction pass in `src/cetools/engine/ships/names.py`: add 42 `SCREEN_SF` entries on the same terms — real-vessel and ordinary-word names predominate, coined franchise names (`Millennium Falcon`, `Tantive IV`, `Executor`) are excluded. Skip any name already catalogued under mythology or written SF: FR-007a assigns a name to the *earliest* tradition it belongs to, so `Pegasus`, `Prometheus`, `Bellerophon` and `Agamemnon` stay under `MYTHOLOGY_FOLKLORE` however famous the ship that later bore them. V7 catches an exact duplicate but cannot catch a misassigned tradition, so this is a review obligation rather than a test (FR-006, FR-007a, FR-016, FR-016a)
- [ ] T029 [US3] FR-016c review pass over `src/cetools/engine/ships/names.py`: read every `WRITTEN_SF` and `SCREEN_SF` entry against its recorded basis and confirm the claim is *true*, not merely well-formed — the real vessel existed, the ordinary word has an independent sense, the borrowed work is public domain under US copyright law. Withdraw any entry that cannot be confirmed in one line and replace it, keeping the per-tradition counts at their targets

**Checkpoint**: The catalogue meets every composition floor and cap, every fiction entry's basis is
present, well-formed and reviewed, and generated batches read as varied.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T030 [P] Add `ships/names.py` to the engine module map in `CONTRIBUTING.md` so `scripts/check_docs.py` passes
- [ ] T031 [P] Note in the starship section of `README.md` that randomly generated ships arrive named from a curated catalogue, with any new backticked symbol resolving against the package
- [ ] T032 Run every quickstart.md scenario (1–6) from the repository root and confirm each prints its expected result
- [ ] T033 Run the four-command quality gate: `uv run black . && uv run flake8 src tests && uv run pytest && uv run python scripts/check_docs.py`, confirming coverage stays above the 85% floor
- [ ] T034 Confirm `src/cetools/cli/ship.py` is untouched by `git diff --stat` and that no engine module imports from `cli/` (Constitution Principles II and III)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational only. Includes T019, a US2 test that gates
  US1's implementation
- **User Story 2 (Phase 4)**: Depends on Foundational; its remaining tests exercise US1's generator
  wiring, so run after Phase 3
- **User Story 3 (Phase 5)**: Its catalogue content (T024, T026–T029) depends on Foundational only
  and can be grown against the starter selection mechanism independently. **T025 is the exception**:
  the SC-003 variety check calls `generate_ship`, so it cannot pass until T015 and T016 have landed
- **Polish (Phase 6)**: Depends on all desired stories

### Within Phase 2

- T003 is independent of T004–T007
- T004 (tests) MUST precede T005/T006 (types and starter catalogue) and MUST fail first
- T007 depends on T005 and T006

### Within Each User Story

- Every test task precedes its implementation task and MUST fail first
- US1: T008 → T013 → T014; T009 and T019 → T015 → T016; T010–T012 pass once T015/T016 land
- **T019 MUST be written and failing before T015.** It is the only test that would catch a draw
  landing anywhere but the end of a path, and it is worthless written after the fact
- US2: T018, T020–T022 → T023 (which is expected to be a no-op)
- US3: T024 → T026 → T027 → T028 → T029; T025 is written with T024 but stays red until T015/T016

### Parallel Opportunities

- **Phase 2**: T003 runs alongside T004
- **US1 tests**: T010, T011 and T012 touch three different test files and run together; T008 and T009 also touch distinct files from each other
- **US2 tests**: T020, T021 and T022 touch three different test files and run together
- **US3**: T026, T027 and T028 all edit `names.py` and MUST be sequential; T024 and T025 touch different test files and run together
- **Polish**: T030 and T031 edit different documents and run together
- **Across stories**: once Phase 2 completes, US3's catalogue content (T026–T029) can be researched in parallel with US1's wiring. But T013 adds `generate_ship_name` to `names.py`, so the overlap is the whole file, not just the `SHIP_NAMES` literal, so land T013 first or expect to merge `names.py` by hand

## Parallel Example: User Story 1

```bash
# Launch the three independent test-writing tasks together:
Task: "Description test — no 'Unnamed Ship' in tests/test_ship_description.py"      # T010
Task: "Round-trip test — name survives dump/load/build in tests/test_ship_design.py" # T011
Task: "CLI tests — generate names the ship in tests/test_cli.py"                     # T012
```

## Parallel Example: User Story 2

```bash
Task: "build_ship assigns no name in tests/test_ship_builder.py"        # T020
Task: "Author's name wins; blank is no name in tests/test_ship_description.py"  # T021
Task: "ship build renders TL8 Beowulf unchanged in tests/test_cli.py"   # T022
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 Setup — confirm the baseline artifact is intact
2. Phase 2 Foundational — roll name, types, starter catalogue (BLOCKS everything)
3. Phase 3 User Story 1 — naming reaches description, export and rebuild. T019 (the baseline
   additivity test) is written and red *before* the generator is touched
4. **STOP and VALIDATE**: quickstart.md Scenarios 1, 2 and 4

At this point every generated ship is named. The catalogue is small, but the feature delivers its
table value.

### Incremental Delivery

1. Setup + Foundational → catalogue types importable
2. US1 → generated ships are named, with additivity already proven against the pinned baseline by
   T019 → validate → demo (MVP)
3. US2 → reproducibility by seed, and hand-authored designs shown untouched → validate
4. US3 → catalogue grown to ~160 balanced, sourced entries → validate
5. Polish → docs, quickstart sweep, quality gate

### Notes

- `[P]` tasks touch different files and carry no ordering dependency
- The draw-last placement (T015, T016) is the feature's load-bearing invariant; T019 is what proves it, which is why T019 is written first and gates them
- `specs/012-ship-names/baseline/designs.json` is a pre-feature artifact — never regenerate it
- Tests assert floors and caps, never exact catalogue counts, so future name additions need no test edit
- Commit after each task or logical group, using Conventional Commits
