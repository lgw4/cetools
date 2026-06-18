---

description: "Task list for Aerospace System Defense Career feature"
---

# Tasks: Aerospace System Defense Career

**Input**: Design documents from `/specs/003-aerospace-system-defense-career/`

**Prerequisites**: plan.md, spec.md, data-model.md, contracts/cli-career-flag.md, research.md, quickstart.md

**Tests**: TDD is MANDATORY per Constitution §IV. Test tasks appear before their corresponding implementation tasks in each phase. All tests MUST be written and confirmed failing (red) before implementation begins.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- All file paths are relative to the repository root

---

## Phase 1: Setup (Baseline Verification)

**Purpose**: Confirm the project baseline is clean before making any changes.

- [ ] T001 Verify the existing test suite passes with `uv run pytest` to establish a clean baseline

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No new infrastructure is required — the `Career` dataclass, registry pattern, and CLI framework are already in place. Phase 2 is satisfied by the existing codebase.

**⚠️ CRITICAL**: Phase 3 may begin immediately after Phase 1 completes.

---

## Phase 3: User Story 1 — Generate Aerospace System Defense Character (Priority: P1) 🎯 MVP

**Goal**: A user can invoke `cetools character generate --career "Aerospace System Defense"` (and case/hyphen variants) and receive a correctly generated character.

**Independent Test**: `cetools character generate --career "Aerospace System Defense"` exits 0 and stdout contains `Career: Aerospace System Defense` and a rank title from the Aerospace rank table.

### Tests for User Story 1 (TDD — write FIRST, confirm FAILING before T008)

- [ ] T002 [US1] Write failing tests for AEROSPACE_CAREER qualification, survival, commission, advancement, and reenlistment field values in tests/test_aerospace_career.py
- [ ] T003 [P] [US1] Write failing tests for all four AEROSPACE_CAREER skill tables (personal_development, service_skills, specialist_skills, advanced_education), asserting the exact skill name at each of the 6 positions per table (24 positions total — no count-only or "etc." assertions) in tests/test_aerospace_career.py
- [ ] T004 [P] [US1] Write failing tests for all seven AEROSPACE_CAREER rank entries (rank 0 Airman through rank 6 Air Commodore, with correct bonus skills at ranks 0 and 3) in tests/test_aerospace_career.py
- [ ] T005 [P] [US1] Write failing tests for AEROSPACE_CAREER mustering-out tables (7 cash entries and 7 material entries matching FR-005) in tests/test_aerospace_career.py
- [ ] T006 [P] [US1] Write failing CLI test asserting `--career "Aerospace System Defense"` exits 0, output contains "Aerospace System Defense", and the rank title is one of the seven valid Aerospace rank strings (Airman, Flight Officer, Flight Lieutenant, Squadron Leader, Wing Commander, Group Captain, Air Commodore) in tests/test_cli.py
- [ ] T007 [P] [US1] Write failing CLI tests for case-insensitive input (`"aerospace system defense"`, `"AEROSPACE SYSTEM DEFENSE"`) and hyphenated input (`"aerospace-system-defense"`) resolving to the Aerospace career in tests/test_cli.py

### Implementation for User Story 1

- [ ] T008 [US1] Create AEROSPACE_CAREER instance per data-model.md (all fields, rank entries, skill tables, mustering-out tables) in src/cetools/engine/careers/aerospace.py
- [ ] T009 [US1] Register `"aerospace system defense": AEROSPACE_CAREER` in CAREER_REGISTRY in src/cetools/engine/careers/registry.py
- [ ] T010 [US1] Add hyphen normalization (`input.strip().lower().replace("-", " ")`) to career name lookup in src/cetools/cli/character.py

**Checkpoint**: T002–T007 tests all green; `cetools character generate --career "Aerospace System Defense"` and its case/hyphen variants work end-to-end.

---

## Phase 4: User Story 2 — Commission and Advancement in Aerospace (Priority: P2)

**Goal**: Aerospace characters can be commissioned as officers and advance through ranks, with the rank 3 Squadron Leader bonus skill (Leadership-1) applied correctly.

**Independent Test**: Generate multiple Aerospace characters and observe officer ranks and Leadership skill at rank 3.

**Note**: The implementation for US2 is already complete after Phase 3 — AEROSPACE_CAREER contains all commission/advancement fields and rank bonus skills. This phase adds targeted tests to validate that behavior independently.

### Tests for User Story 2 (TDD — confirm failing before verifying they pass)

- [ ] T011 [P] [US2] Write failing behavior tests asserting: (a) when a mocked commission roll succeeds (≥ commission_target) the character advances from rank 0 to rank 1 AND receives one extra skill roll that term; (b) when the commission roll fails the character stays at rank 0 (covering the "low-Education, never commissions" edge case from spec.md §Edge Cases); (c) when a mocked advancement roll succeeds (≥ advancement_target) an already-commissioned character's rank increments by 1 — in tests/test_aerospace_career.py (distinct from T002's data-field assertions)
- [ ] T012 [P] [US2] Write failing behavior tests asserting that a freshly generated Aerospace character (before any terms) has Aircraft in their skill list (rank 0 bonus applied), and that a character who reaches rank 3 has Leadership in their skill list (rank 3 bonus applied) — in tests/test_aerospace_career.py (distinct from T004's RankEntry data assertions)
- [ ] T011b [P] [US2] Write failing test asserting that a character already at rank 6 (Air Commodore) who succeeds on a mocked advancement roll remains at rank 6 — the rank cap edge case from spec.md §Edge Cases — in tests/test_aerospace_career.py

**Checkpoint**: T011, T011b, T012 tests pass (no additional implementation needed — data is already in AEROSPACE_CAREER from T008).

---

## Phase 5: User Story 3 — Aerospace Character Enters Draft (Priority: P3)

**Goal**: A draft roll of 1 assigns Aerospace System Defense, consistent with the SRD draft table (FR-008).

**Independent Test**: `DRAFT_TABLE[0] == "aerospace system defense"` and drafted characters use the Aerospace career data.

### Tests for User Story 3 (TDD — write FIRST, confirm FAILING before T015)

- [ ] T013 [US3] Write failing test asserting `DRAFT_TABLE[0] == "aerospace system defense"` in tests/test_careers.py
- [ ] T014 [US3] Update `test_draft_table_other_entries_are_navy` in tests/test_careers.py to allow index 0 as the Aerospace slot while asserting indices 1, 2, 3, and 5 remain "navy" and index 4 remains "scout"

### Implementation for User Story 3

- [ ] T015 [US3] Change `DRAFT_TABLE` index 0 from `"navy"` to `"aerospace system defense"` in src/cetools/engine/careers/registry.py

**Checkpoint**: T013–T014 tests pass; draft roll 1 assigns Aerospace System Defense.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: CLI error messages (FR-009) and help text (FR-010) — improvements that affect all user stories.

### Tests for Polish (TDD — write FIRST, confirm FAILING before T019–T020)

- [ ] T016 [P] Write failing tests for "did you mean" error message format on near-miss input (e.g., `--career "Areospace"` → `Unknown career 'Areospace'. Did you mean: Aerospace System Defense?`) in tests/test_cli.py
- [ ] T017 [P] Write failing tests for "no close match" error format listing all canonical career names (e.g., `--career "marine"` → `Unknown career 'marine'. Valid careers: Aerospace System Defense, Navy, Scout`) in tests/test_cli.py
- [ ] T017b [P] Write failing test for `--career --help` output showing all canonical career names in sorted alphabetical order (e.g., output contains `"Aerospace System Defense, Navy, Scout"`) in tests/test_cli.py
- [ ] T018 Update `test_career_unknown_stderr_message_exact` in tests/test_cli.py to match the new error message format introduced by the "did you mean" logic — this test is currently PASSING (old format); updating it makes it RED immediately; T019's implementation makes it GREEN (T018 MUST precede T019 to keep the TDD red-green cycle unambiguous)

### Implementation for Polish

- [ ] T019 Implement "did you mean" suggestion using `difflib.get_close_matches(normalized, CAREER_REGISTRY.keys(), n=1, cutoff=0.6)` in the CLI error path in src/cetools/cli/character.py; if no match, list all canonical names from `CAREER_REGISTRY.values()` sorted by `career.name`
- [ ] T020 Update `--career` flag help text to enumerate canonical career names derived from `CAREER_REGISTRY` at import time in src/cetools/cli/character.py
- [ ] T021 Run quality gate: `uv run black . && uv run flake8 src tests && uv run pytest` and resolve any failures

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Satisfied by existing codebase — no tasks needed.
- **User Story 1 (Phase 3)**: Depends on Phase 1 baseline confirmation.
- **User Story 2 (Phase 4)**: Depends on Phase 3 completion (AEROSPACE_CAREER must exist).
- **User Story 3 (Phase 5)**: Depends on Phase 3 completion (registry must have aerospace key before DRAFT_TABLE fix is testable end-to-end). Can be worked in parallel with Phase 4.
- **Polish (Phase 6)**: Depends on Phases 3–5 completion; must run after all user stories are working.

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 1 — no dependencies on other stories.
- **US2 (P2)**: Depends on US1 (AEROSPACE_CAREER must exist); tests only, no new implementation.
- **US3 (P3)**: Depends on US1 (registry key must exist to make draft resolve correctly end-to-end); small registry edit.

### Within Each User Story

1. Write all tests for the story → confirm they FAIL.
2. Implement until tests pass.
3. Confirm story independently before moving to next.

### Parallel Opportunities

- T003, T004, T005, T006, T007 can all run in parallel (all are new test content in the same file or different files — no conflicts with T002 if T002 is written first).
- T011, T011b, and T012 can run in parallel.
- T013 and T014 can run in parallel.
- T016, T017, T017b can run in parallel.
- T019 and T020 can run in parallel (both edit `cli/character.py` — coordinate if pairing).

---

## Parallel Example: User Story 1

```bash
# Write all failing tests in parallel (after T002 creates the file):
Task T003: Write skill table tests in tests/test_aerospace_career.py
Task T004: Write rank entry tests in tests/test_aerospace_career.py
Task T005: Write mustering-out table tests in tests/test_aerospace_career.py
Task T006: Write CLI generation test in tests/test_cli.py
Task T007: Write case/hyphen variant CLI tests in tests/test_cli.py

# Then implement in sequence:
Task T008: Create src/cetools/engine/careers/aerospace.py
Task T009: Edit src/cetools/engine/careers/registry.py
Task T010: Edit src/cetools/cli/character.py
```

---

## Implementation Strategy

### MVP (User Story 1 Only)

1. Complete Phase 1: Baseline verification (T001).
2. Complete Phase 3: Write tests T002–T007, confirm failing; implement T008–T010.
3. **STOP and VALIDATE**: Run quickstart.md Scenarios 1–4.

### Incremental Delivery

1. Phase 1 → baseline confirmed.
2. Phase 3 (US1) → Aerospace character generation works. MVP ready.
3. Phase 4 (US2) → Commission/advancement tests added.
4. Phase 5 (US3) → Draft table corrected.
5. Phase 6 (Polish) → "Did you mean" + help text + quality gate. PR ready.

### Quickstart Validation Mapping

| Quickstart Scenario | Tasks Covered |
|--------------------|---------------|
| Scenario 1: Exact name | T006, T008–T010 |
| Scenario 2: Case/hyphen variants | T007, T010 |
| Scenario 3: Commission/advancement (statistical) | T011–T012 |
| Scenario 4: Mustering-out benefits | T005, T008 |
| Scenario 5: Typo "did you mean" | T016, T019 |
| Scenario 6: No close match | T017, T019 |
| Scenario 9: Help text enumerates careers | T017b, T020 |
| Scenario 7: Draft | T013–T015 |
| Scenario 8: Full test suite | T021 |

---

## Notes

- **TDD is non-negotiable** (Constitution §IV): confirm each test file's new tests are RED before writing implementation code.
- **[P]** tasks target different files (or non-conflicting sections) and can run in parallel.
- **[Story]** label maps each task to a specific user story for traceability and independent testing.
- US2 requires no new implementation files — all rank/commission/advancement data is in `AEROSPACE_CAREER` (T008). T011b (rank cap) and the CHK023 edge case are covered by existing engine logic; tests validate it rather than requiring new implementation.
- `cli/character.py` is edited three times across phases (T010, T019, T020); sequence these to avoid conflicts.
- T017b must be written and confirmed FAILING before T020 is started (TDD).
- After T015, re-run `test_careers.py` to confirm the draft table correction does not break any Scout/Navy draft assertions.
- Commit after each phase or logical group using Conventional Commits (e.g., `feat: add aerospace system defense career`).
