# Tasks: Scout Career & Career Selection Flag

**Input**: Design documents from `/specs/002-scout-career-character/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/cli.md ✅, quickstart.md ✅

**Tests**: Included — Constitution §IV (Test-First) is non-negotiable; tests MUST be written and confirmed failing before any implementation is committed. SC-004 explicitly names three functions requiring red-first treatment.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no cross-dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- File paths are exact; all paths are from repository root

---

## Phase 1: Setup

**Purpose**: Confirm the existing project structure matches plan.md before any new code is written.

- [ ] T001 Verify existing project structure: `src/cetools/engine/careers/`, `tests/test_careers.py`, `tests/test_generator.py`, `tests/test_cli.py`, `tests/test_formatter.py`, `tests/test_models.py` all exist and are importable

**Checkpoint**: Project structure confirmed — proceed to Phase 2

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Data structures and model changes that every user story depends on. No user story work can begin until this phase is complete.

**⚠️ CRITICAL**: Write tests first (red), then implement.

### Tests First (write and confirm failing)

- [ ] T002 [P] Write failing test: `Character.drafted` defaults to `False` and is a `bool` field in `tests/test_models.py`
- [ ] T003 [P] Write failing tests: `SCOUT_CAREER` field validation (all 16 fields from data-model.md — `name`, `qualification_stat`, `qualification_target`, `survival_stat`, `survival_target`, `commission_stat=None`, `commission_target=None`, `advancement_stat=None`, `advancement_target=None`, `reenlistment_target`, `service_skills`, `personal_development`, `specialist_skills`, `advanced_education`, `ranks`, `cash_benefits`, `material_benefits`) and `CAREER_REGISTRY`/`DRAFT_TABLE` structure (keys `"navy"` and `"scout"`, draft table length 6, index 4 is `"scout"`) in `tests/test_careers.py`

### Implementation (make tests green)

- [ ] T004 Add `drafted: bool = False` field to `Character` dataclass in `src/cetools/engine/models.py`
- [ ] T005 Create `SCOUT_CAREER` `Career` instance with all SRD-specified values (FR-002 through FR-005) in `src/cetools/engine/careers/scout.py`; single `ranks` entry: `RankEntry(rank=0, title="Scout", bonus_skills=("Piloting",))`, `cash_benefits=(1000, 5000, 10000, 10000, 20000, 50000, 50000)`, `material_benefits=("Low Passage", "+1 Edu", "Weapon", "Mid Passage", "Explorer's Society", "Courier Vessel")`
- [ ] T006 Create `CAREER_REGISTRY: dict[str, Career]` and `DRAFT_TABLE: tuple[str, ...]` in `src/cetools/engine/careers/registry.py`; registry keys `"navy"` and `"scout"`; draft table `("navy", "navy", "navy", "navy", "scout", "navy")`
- [ ] T007 Update `src/cetools/engine/careers/__init__.py` to re-export `CAREER_REGISTRY`, `DRAFT_TABLE`, and `SCOUT_CAREER`

**Checkpoint**: Foundation ready — `Character.drafted`, `SCOUT_CAREER`, `CAREER_REGISTRY`, and `DRAFT_TABLE` all exist and tests are green; user story phases can now begin

---

## Phase 3: User Story 1 — Generate a Scout Character (Priority: P1) 🎯 MVP

**Goal**: The engine processes Scout career data without modification, re-rolling characteristics until Intelligence 6+ is met, then generates a full character via `generate_career_character(scout_career)` callable directly without the CLI.

**Independent Test**: Call `generate_career_character(SCOUT_CAREER)` directly in a test; assert a `Character` is returned with `intelligence >= 6`, `Piloting` skill at level ≥ 1, and exactly two skill rolls recorded per term.

### Tests First — US1 (write and confirm failing)

- [ ] T008 [P] [US1] Write failing tests for `roll_until_qualified(career, roller)`: seeded roller that fails qualification N times then passes; assert returned dict has `qualification_stat` value ≥ `qualification_target`; assert loop runs multiple iterations when needed in `tests/test_generator.py`
- [ ] T009 [P] [US1] Write failing tests for `generate_character` with new params: `preset_characteristics` skips internal roll; `bypass_qualification=True` skips enlistment roll; `hard_max_terms=True` caps at 7 terms even on natural-12 re-enlistment; `drafted=True` sets `Character.drafted` in `tests/test_generator.py`
- [ ] T010 [P] [US1] Write failing tests for `generate_career_character(career, roller)` with Scout: asserts `Character` returned, `intelligence >= 6`, `Piloting` in skills at level ≥ 1 (rank-0 bonus applied), two skill rolls per term (no commission/advancement rolls), valid mustering-out benefits from Scout tables in `tests/test_generator.py`
- [ ] T011 [P] [US1] Write failing tests for two Scout skill rolls per term: mock roller to control re-enlistment; assert `len(character.skills)` grows by 2 per term (not 1) in `tests/test_generator.py`

### Implementation — US1 (make tests green)

- [ ] T012 [US1] Add optional params `preset_characteristics: dict[str, int] | None = None`, `bypass_qualification: bool = False`, `hard_max_terms: bool = False`, `drafted: bool = False` to `generate_character` in `src/cetools/engine/generator.py`; when `preset_characteristics` is set skip internal roll; when `bypass_qualification` is True skip enlistment check; when `hard_max_terms` is True suppress natural-12 extra term at the 7-term cap; set `character.drafted = drafted` on the returned object
- [ ] T013 [US1] Implement `roll_until_qualified(career: Career, roller: DiceRoller | None = None) -> dict[str, int]` in `src/cetools/engine/generator.py`; loop rolling all six characteristics until `characteristics[career.qualification_stat] >= career.qualification_target`; return the qualifying characteristic dict (no background skills or rank bonuses applied here)
- [ ] T014 [US1] Implement `generate_career_character(career: Career, roller: DiceRoller | None = None, drafted: bool = False) -> Character | GenerationFailure` in `src/cetools/engine/generator.py`; call `roll_until_qualified`, then call `generate_character` with `preset_characteristics`, `bypass_qualification=True`, `hard_max_terms=True`, `drafted=drafted`

**Checkpoint**: US1 is independently testable — `generate_career_character(SCOUT_CAREER)` returns a valid Scout `Character` without CLI involvement (SC-003 verified)

---

## Phase 4: User Story 2 — Default to Draft When No Career Specified (Priority: P2)

**Goal**: When invoked without `--career`, the CLI rolls the draft table to assign Navy or Scout, bypasses the qualification roll, and prints the career line with "(Drafted)".

**Independent Test**: Invoke `cetools character generate` (no flag) via subprocess; assert exit code 0, career line contains "(Drafted)", and career is either `Navy` or `Scout`.

### Tests First — US2 (write and confirm failing)

- [ ] T015 [P] [US2] Write failing tests for `draft_character(roller)`: seeded roller producing roll 5 → Scout outcome, rolls 1–4/6 → Navy outcome; assert `Character.drafted` is `True`; assert career name matches draft table result in `tests/test_generator.py`
- [ ] T016 [P] [US2] Write failing test for `draft_character` when draft resolves an unimplemented career: mock `DRAFT_TABLE` to contain `"marine"`; assert `GenerationFailure` is returned with a clear message containing `"marine"` in `tests/test_generator.py`
- [ ] T017 [P] [US2] Write failing test for formatter: `format_character(character_with_drafted_true)` includes `"(Drafted)"` in the career line between the career name and the rank parenthetical (e.g., `"Scout (Drafted) (Scout, Rank 0)"`) in `tests/test_formatter.py`
- [ ] T018 [P] [US2] Write failing tests for CLI draft default: invoke `cetools character generate` with no `--career`; assert exit code 0; assert stdout career line contains `"(Drafted)"` in `tests/test_cli.py`

### Implementation — US2 (make tests green)

- [ ] T019 [US2] Implement `draft_character(roller: DiceRoller | None = None) -> Character | GenerationFailure` in `src/cetools/engine/generator.py`; roll 1D6, index `DRAFT_TABLE[roll-1]`, look up career in `CAREER_REGISTRY`; if not found return `GenerationFailure` with message `"Draft assigned unimplemented career '{name}'"` (exit code 1); else call `generate_career_character(career, roller, drafted=True)`
- [ ] T020 [US2] Update career line in `src/cetools/formatter.py` to render `"{career} (Drafted) ({rank_title}, Rank {rank})"` when `character.drafted` is `True`; no change when `False`
- [ ] T021 [US2] Add `career: Optional[str] = typer.Option(None, "--career")` to `cetools character generate` in `src/cetools/cli/character.py`; when `career` is `None` call `draft_character()` and route result to formatter or stderr/exit-1

**Checkpoint**: US2 independently testable — draft path produces "(Drafted)" characters; US1 unaffected

---

## Phase 5: User Story 3 — Specify a Career at Invocation (Priority: P3)

**Goal**: `--career <name>` validates input (strip + lowercase), rejects unknown names with exit code 1 and `Unknown career '{original}'. Valid careers: navy, scout`, and routes recognized names to `generate_career_character`.

**Independent Test**: Invoke `cetools character generate --career navy` and assert exit code 0 with no "(Drafted)" in career line; invoke `cetools character generate --career marine` and assert exit code 1 and correct stderr message.

### Tests First — US3 (write and confirm failing)

- [ ] T022 [P] [US3] Write failing tests for named `--career` paths: `--career scout` exits 0, career line has no "(Drafted)", Intelligence ≥ 6; `--career navy` exits 0, career line has no "(Drafted)", Intelligence ≥ 6 in `tests/test_cli.py`
- [ ] T023 [P] [US3] Write failing tests for unrecognized career: `--career marine` exits 1, stderr equals `"Unknown career 'marine'. Valid careers: navy, scout"` exactly; original unmodified input appears in message in `tests/test_cli.py`
- [ ] T024 [P] [US3] Write failing tests for input normalization: `--career Scout`, `--career SCOUT`, `--career "  scout  "` all exit 0 and behave identically to `--career scout` in `tests/test_cli.py`

### Implementation — US3 (make tests green)

- [ ] T025 [US3] Implement `--career` normalization in `src/cetools/cli/character.py`: capture original value before normalization; strip whitespace, lowercase; validate against `CAREER_REGISTRY` keys
- [ ] T026 [US3] Implement recognized `--career` routing in `src/cetools/cli/character.py`: call `generate_career_character(CAREER_REGISTRY[normalized_name])` and route result to formatter or stderr/exit-1
- [ ] T027 [US3] Implement unrecognized career error in `src/cetools/cli/character.py`: print `Unknown career '{original_value}'. Valid careers: navy, scout` to stderr, `raise typer.Exit(1)`

**Checkpoint**: All three user stories independently functional; full feature complete

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Quality gate, formatting, and end-to-end validation.

- [ ] T028 [P] Run `uv run black .` and resolve any formatting issues across `src/cetools/` and `tests/`
- [ ] T029 [P] Run `uv run flake8 src tests` and resolve any lint warnings
- [ ] T030 Run `uv run pytest` and confirm all tests pass and `src/cetools` coverage is ≥ 85%
- [ ] T031 Run quickstart.md Scenarios 1–5 manually (`cetools character generate --career scout`, no-flag draft, `--career navy`, `--career marine`, case variants) and confirm all expected outputs and exit codes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user story phases
- **User Stories (Phases 3–5)**: All depend on Phase 2 completion
  - US1 (Phase 3) has no dependency on US2 or US3
  - US2 (Phase 4) depends on Phase 3 completion (needs `generate_career_character`)
  - US3 (Phase 5) depends on Phase 4 completion (needs the `--career` option wired up)
- **Polish (Phase 6)**: Depends on all user story phases

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — independently testable via direct engine call
- **US2 (P2)**: Requires US1 complete (`generate_career_character` must exist before `draft_character` calls it)
- **US3 (P3)**: Requires US2 complete (the `--career` CLI option is introduced in US2; US3 fills in the non-None branch)

### Within Each Phase

- ALL test tasks (red) MUST precede ALL implementation tasks (green) — Constitution §IV is non-negotiable
- Tasks marked [P] within a phase have no interdependencies and can be written/implemented together
- Implementation tasks within a user story follow: model params → loop function → entry point

### Parallel Opportunities

- T002 and T003 can be written simultaneously (different test files, independent content)
- T008, T009, T010, T011 can all be written simultaneously (all additive tests in `tests/test_generator.py`)
- T015, T016, T017, T018 can be written simultaneously (different test files and independent test functions)
- T022, T023, T024 can be written simultaneously (all additive tests in `tests/test_cli.py`)
- T028 and T029 can be run simultaneously (independent tools)

---

## Parallel Example: Phase 3 (US1) Test Writing

```bash
# Write all four test groups together before touching implementation:
Task T008: roll_until_qualified tests → tests/test_generator.py
Task T009: generate_character new-params tests → tests/test_generator.py
Task T010: generate_career_character scout tests → tests/test_generator.py
Task T011: two-skill-rolls-per-term tests → tests/test_generator.py

# Confirm all four are RED before starting T012
uv run pytest tests/test_generator.py --no-cov
```

---

## Implementation Strategy

### MVP First (US1 Only — Phases 1–3)

1. Complete Phase 1: Verify structure
2. Complete Phase 2: Foundational data and model
3. Complete Phase 3: US1 engine implementation
4. **STOP and VALIDATE**: Call `generate_career_character(SCOUT_CAREER)` directly; assert valid Scout `Character` (SC-003)
5. Scout career engine is done — demo engine-level Scout generation

### Incremental Delivery

1. Phases 1–2 → Foundation ready (Scout data, registry, drafted field)
2. Phase 3 → Scout engine works; testable without CLI
3. Phase 4 → Draft default behavior added; formatter updated; CLI routes no-flag path
4. Phase 5 → `--career` flag validated; full CLI contract met
5. Phase 6 → Quality gate passed; quickstart confirmed

---

## Notes

- [P] tasks = can run in parallel (no shared file conflicts or sequential dependencies)
- [Story] label maps each task to a specific user story for traceability
- Tests that are [P] within a story can be written in one LLM pass in the same file
- SC-004 three red-first functions: `roll_until_qualified` (T008→T013), draft table lookup in `draft_character` (T015→T019), Scout data structure processing (T003→T005+T010→T014)
- All tasks are self-contained: file paths are explicit, expected behavior is quoted from spec/contracts
- Run `uv run pytest tests/<file>.py --no-cov` after each test-writing batch to confirm red before implementing
