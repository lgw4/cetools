---

description: "Task list for Marine Career feature"
---

# Tasks: Marine Career

**Input**: Design documents from `/specs/005-marine-career/`

**Prerequisites**: plan.md, spec.md, data-model.md, contracts/career-registry.md, research.md, quickstart.md

**Tests**: TDD is MANDATORY per Constitution §IV. Test tasks appear before their corresponding implementation tasks in each phase. All tests MUST be written and confirmed failing (red) before implementation begins.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- All file paths are relative to the repository root

---

## Phase 1: Setup (Baseline Verification)

**Purpose**: Confirm the project baseline is clean before making any changes.

- [X] T001 Verify the existing test suite passes with `uv run pytest` to establish a clean baseline

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No new infrastructure is required — the `Career` dataclass, registry pattern, and CLI framework are already in place (added in features 001–003). Phase 2 is satisfied by the existing codebase.

**⚠️ CRITICAL**: Phase 3 may begin immediately after Phase 1 completes.

---

## Phase 3: User Story 1 — Generate a Marine Character (Priority: P1) 🎯 MVP

**Goal**: A user can invoke `cetools character generate --career "Marine"` (and case variants) and receive a correctly generated Marine character.

**Independent Test**: `cetools character generate --career "Marine"` exits 0 and stdout contains `Career: Marine` and a rank title from the Marine rank table.

### Tests for User Story 1 (TDD — write FIRST, confirm FAILING before T011)

- [X] T002 [US1] Write failing tests for MARINE_CAREER qualification, survival, commission, advancement, reenlistment field values (FR-002) and `name == "Marine"` in tests/test_marine_career.py (new file)
- [X] T003 [P] [US1] Write failing tests for all four MARINE_CAREER skill tables (personal_development, service_skills, specialist_skills, advanced_education), asserting the exact skill name at each of the 6 positions per table (24 positions total, per FR-004) in tests/test_marine_career.py
- [X] T004 [P] [US1] Write failing tests for all seven MARINE_CAREER rank entries (rank 0 Trooper through rank 6 Brigadier, with the Zero-G bonus skill at rank 0 and Tactics bonus skill at rank 3, and no bonus skills at ranks 1, 2, 4, 5, 6) per FR-003 in tests/test_marine_career.py
- [X] T005 [P] [US1] Write failing tests for MARINE_CAREER mustering-out tables — 7 cash entries and 7 material entries matching FR-005, including `material_benefits[6] == "Explorers' Society"` (exact spelling) — in tests/test_marine_career.py
- [X] T006 [P] [US1] Write failing CLI test asserting `--career "Marine"` exits 0, stdout contains `Career: Marine` and a rank title that is one of the seven valid Marine rank strings (Trooper, Lieutenant, Captain, Major, Lt Colonel, Colonel, Brigadier), and no `(Drafted)` marker appears, in tests/test_cli.py
- [X] T007 [P] [US1] Write failing CLI tests for case-insensitive input (`"marine"`, `"MARINE"`) resolving to the Marine career in tests/test_cli.py
- [X] T007A [P] [US1] Write test asserting `generate_career_character(MARINE_CAREER)` run 100 times with `RandomDiceRoller` raises no unhandled exception, and that every `Character` result (excluding a `GenerationFailure` from a died-during-survival-check outcome, which is a handled non-error per Acceptance Scenario 1.3) has `career == "Marine"` and a `rank_title` in the seven valid Marine rank titles (SC-001) in tests/test_marine_career.py
- [X] T008 [US1] Update the three pre-existing FR-012 tests in tests/test_cli.py — `test_career_unknown_exits_1`, `test_career_unknown_stderr_message_exact`, `test_career_unknown_original_value_in_message` — to use `"merchant"` in place of the `"marine"` placeholder (all-lowercase for the first two; `test_career_unknown_original_value_in_message` uses the capitalized `"Merchant"` instead, to keep verifying that the CLI echoes the original, unnormalized input casing), and update `test_career_unknown_stderr_message_exact`'s expected message to `"Unknown career 'merchant'. Valid careers: Aerospace System Defense, Marine, Navy, Scout"` (this assertion goes RED until T012 registers Marine)
- [X] T009 [P] [US1] Update `test_career_no_match_valid_careers_format` in tests/test_cli.py to expect `"Unknown career 'xyzzy'. Valid careers: Aerospace System Defense, Marine, Navy, Scout"` (RED until T012)
- [X] T009A [P] [US1] Write failing test asserting `--career "Marines"` exits 1 with stderr exactly `"Unknown career 'Marines'. Did you mean: Marine?"` — this near-miss path is deterministic (`difflib.get_close_matches("marines", CAREER_REGISTRY.keys(), cutoff=0.6)` returns `["marine"]`, ratio ≈0.92) — in tests/test_cli.py (FR-010; RED until T012)
- [X] T010 [P] [US1] Update `test_draft_character_unimplemented_career_returns_failure` in tests/test_generator.py to patch `DRAFT_TABLE` with `"merchant"` in place of `"marine"` and assert `"merchant" in result.reason` (FR-012)

### Implementation for User Story 1

- [X] T011 [US1] Create MARINE_CAREER instance per data-model.md (all qualification/survival/commission/advancement/reenlistment fields, 4 skill tables, 7 rank entries, cash and material benefit tables) in src/cetools/engine/careers/marine.py
- [X] T012 [US1] Register `"marine": MARINE_CAREER` in `CAREER_REGISTRY` in src/cetools/engine/careers/registry.py (depends on T011)

**Checkpoint**: T002–T010 (plus T007A, T009A) tests all green; `cetools character generate --career "Marine"` and its case variants work end-to-end.

---

## Phase 4: User Story 2 — Commission and Advancement in the Marines (Priority: P2)

**Goal**: Marine characters can be commissioned as officers and advance through ranks (using Social Standing as the advancement stat — the first commissioned career to do so), with the rank 0 Zero-G-1 and rank 3 Tactics-1 bonus skills applied and retained correctly.

**Independent Test**: Generate multiple Marine characters and observe officer ranks, the rank 0 Zero-G-1 bonus (always present, even after commissioning), and Tactics-1 at rank 3.

**Note**: The implementation for US2 is already complete after Phase 3 — MARINE_CAREER contains all commission/advancement fields and rank bonus skills, and the engine's commission/advancement/rank-bonus mechanisms are career-agnostic. This phase adds targeted tests to validate that behavior independently.

### Tests for User Story 2 (TDD — confirm failing before verifying they pass)

- [X] T013 [P] [US2] Write failing tests asserting: (a) when a mocked commission roll succeeds (Education 6+) the character advances from rank 0 (Trooper) to rank 1 (Lieutenant) and receives one extra skill roll that term; (b) when the commission roll fails the character stays at rank 0 (the "low-Education, never commissions" edge case from spec.md §Edge Cases) — in tests/test_marine_career.py
- [X] T014 [P] [US2] Write failing test asserting that a commissioned Marine officer who passes a mocked advancement roll (Social Standing 7+) has their rank incremented by 1 — in tests/test_marine_career.py
- [X] T015 [P] [US2] Write failing test asserting that a character already at rank 6 (Brigadier) who succeeds on a mocked advancement roll remains at rank 6 — the rank cap edge case from spec.md §Edge Cases — in tests/test_marine_career.py
- [X] T016 [P] [US2] Write failing tests asserting: a freshly generated Marine character has Zero-G in their skill list (rank 0 bonus applied at enlistment); a character who reaches rank 3 (Major) has Tactics in their skill list; and a character commissioned to rank 1 or higher retains the Zero-G bonus skill gained at rank 0 (FR-013 retention behavior) — in tests/test_marine_career.py
- [X] T017 [P] [US2] Write failing test asserting that a character reaching rank 4 (Lt Colonel) or higher receives the existing rank-based bonus mustering-out rolls (1 extra at rank 4, 2 at rank 5, 3 at rank 6) in addition to one roll per term served (FR-011) — in tests/test_marine_career.py

**Checkpoint**: T013–T017 tests pass (no additional implementation needed — data is already in MARINE_CAREER from T011).

---

## Phase 5: User Story 3 — Marine Character Enters the Draft (Priority: P3)

**Goal**: A draft roll of 2 assigns Marine, consistent with the SRD draft table (FR-008), replacing the prior "navy" placeholder.

**Independent Test**: `DRAFT_TABLE[1] == "marine"` and drafted characters with roll 2 use the Marine career data.

### Tests for User Story 3 (TDD — write FIRST, confirm FAILING before T021)

- [X] T018 [US3] Write failing test asserting `DRAFT_TABLE[1] == "marine"` in tests/test_careers.py
- [X] T019 [US3] Update `test_draft_table_other_entries_are_navy` in tests/test_careers.py to exclude index 1 (now `"marine"`) from the "must be navy" loop, alongside the existing exclusions of indices 0 and 4
- [X] T020 [P] [US3] Write failing test `test_draft_character_roll_2_gives_marine` asserting a `SequenceRoller([2])` passed to `draft_character()` returns a `Character` with `career == "Marine"` and `drafted is True` in tests/test_generator.py

### Implementation for User Story 3

- [X] T021 [US3] Change `DRAFT_TABLE` index 1 from `"navy"` to `"marine"` in src/cetools/engine/careers/registry.py (depends on T012)

**Checkpoint**: T018–T020 tests pass; draft roll 2 assigns Marine.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Confirm the zero-CLI-change guarantee (FR-009) holistically and close out the quality gate.

- [X] T022 [P] Add an assertion for `"Marine"` to `test_career_help_lists_canonical_names` in tests/test_cli.py, confirming `--career --help` enumerates Marine alongside the other three canonical names with no code change (FR-009)
- [X] T023 Run quality gate: `uv run black . && uv run flake8 src tests && uv run pytest` and resolve any failures
- [X] T024 Run quickstart.md validation scenarios 1–7 manually

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Satisfied by existing codebase — no tasks needed.
- **User Story 1 (Phase 3)**: Depends on Phase 1 baseline confirmation.
- **User Story 2 (Phase 4)**: Depends on Phase 3 completion (MARINE_CAREER must exist).
- **User Story 3 (Phase 5)**: Depends on Phase 3 completion (registry must have the `marine` key before the draft table fix is testable end-to-end). Can be worked in parallel with Phase 4.
- **Polish (Phase 6)**: Depends on Phases 3–5 completion; must run after all user stories are working.

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 1 — no dependencies on other stories.
- **US2 (P2)**: Depends on US1 (MARINE_CAREER must exist); tests only, no new implementation.
- **US3 (P3)**: Depends on US1 (registry key must exist for the draft to resolve correctly end-to-end); small registry edit.

### Within Each User Story

1. Write all tests for the story → confirm they FAIL.
2. Implement until tests pass.
3. Confirm story independently before moving to next.

### Parallel Opportunities

- T003, T004, T005, T006, T007, T007A can all run in parallel (new test content in the same or different files — no conflicts with T002 if T002 is written first).
- T009, T009A, and T010 can run in parallel with each other and with T008 (different test functions/files).
- T013, T014, T015, T016, T017 can all run in parallel.
- T020 can run in parallel with T018/T019 (different file).

---

## Parallel Example: User Story 1

```bash
# Write all failing tests in parallel (after T002 creates the file):
Task T003: Write skill table tests in tests/test_marine_career.py
Task T004: Write rank entry tests in tests/test_marine_career.py
Task T005: Write mustering-out table tests in tests/test_marine_career.py
Task T006: Write CLI generation test in tests/test_cli.py
Task T007: Write case-insensitive CLI tests in tests/test_cli.py

# Then implement in sequence:
Task T011: Create src/cetools/engine/careers/marine.py
Task T012: Edit src/cetools/engine/careers/registry.py
```

---

## Implementation Strategy

### MVP (User Story 1 Only)

1. Complete Phase 1: Baseline verification (T001).
2. Complete Phase 3: Write tests T002–T010 (plus T007A, T009A), confirm failing where applicable; implement T011–T012.
3. **STOP and VALIDATE**: Run quickstart.md Scenarios 1, 2, 4, and 6.

### Incremental Delivery

1. Phase 1 → baseline confirmed.
2. Phase 3 (US1) → Marine character generation works. MVP ready.
3. Phase 4 (US2) → Commission/advancement/rank-retention tests added.
4. Phase 5 (US3) → Draft table corrected.
5. Phase 6 (Polish) → help-text confirmation + quality gate. PR ready.

### Quickstart Validation Mapping

| Quickstart Scenario | Tasks Covered |
|--------------------|---------------|
| Scenario 1: Generate by name | T006, T007A, T011–T012 |
| Scenario 2: Case-insensitive input | T007 |
| Scenario 3: Commission/advancement (statistical) | T013–T017 |
| Scenario 4: Mustering-out benefits | T005, T011 |
| Scenario 5: Draft produces Marine characters | T018–T021 |
| Scenario 6: Unrecognized career, four careers registered | T008–T009, T009A, T022 |
| Scenario 7: Full test suite | T023 |

---

## Notes

- **TDD is non-negotiable** (Constitution §IV): confirm each test file's new tests are RED before writing implementation code.
- **[P]** tasks target different files (or non-conflicting sections/functions) and can run in parallel.
- **[Story]** label maps each task to a specific user story for traceability and independent testing.
- US2 requires no new implementation files — all rank/commission/advancement data is in `MARINE_CAREER` (T011); the engine's rank-bonus and mustering-out-bonus mechanisms are already generic (FR-011, FR-013).
- T008, T009, and T009A intentionally go RED the moment they're written (the four-name list / Marine registry key doesn't exist until T012 registers Marine) — this is expected TDD behavior, not a regression.
- After T021, re-run `test_careers.py` to confirm the draft table correction does not break any existing Navy/Scout/Aerospace draft assertions.
- Commit after each phase or logical group using Conventional Commits (e.g., `feat: add marine career`).
