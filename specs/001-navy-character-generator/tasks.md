---
description: "Task list for Navy Character Generator implementation"
---

# Tasks: Navy Character Generator

**Input**: Design documents from `/specs/001-navy-character-generator/`

**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/cli.md ✓, quickstart.md ✓

**Tests**: Mandatory per Constitution Principle II (Test-First). Tests MUST be written and confirmed failing before any implementation begins.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- All file paths are relative to the repository root

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Create the `navy/` subpackage structure and ensure all dependencies are in place before any implementation begins.

- [ ] T001 Create `src/cetools/navy/` subpackage directory with `src/cetools/navy/__init__.py`
- [ ] T002 Add `typer` to the `[project.dependencies]` section of `pyproject.toml` and run `uv sync` to install it
- [ ] T003 [P] Create `tests/navy/` directory with `tests/navy/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: SRD constants (`tables.py`) and core dataclasses (`character.py`) that every user story depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

### SRD Constants (test-first)

- [ ] T004 [P] Write failing tests for `PSEUDO_HEX` string, `to_pseudo_hex()`, `characteristic_modifier()`, all Navy career check constants (`NAVY_QUALIFICATION`, `NAVY_SURVIVAL`, `NAVY_COMMISSION`, `NAVY_ADVANCEMENT`, `NAVY_REENLISTMENT`), `DRAFT_TABLE`, `NAVY_RANKS`, `NAVY_RANK_BONUS_SKILLS`, all four skill tables (`NAVY_PERSONAL_DEVELOPMENT`, `NAVY_SERVICE_SKILLS`, `NAVY_SPECIALIST_SKILLS`, `NAVY_ADVANCED_EDUCATION`), and all mustering-out constants in `tests/navy/test_tables.py`; confirm all tests FAIL before proceeding
- [ ] T005 Implement `PSEUDO_HEX`, `to_pseudo_hex()`, `characteristic_modifier()`, all Navy career check constants, `DRAFT_TABLE`, `NAVY_RANKS`, `NAVY_RANK_BONUS_SKILLS`, all four skill tables, `NAVY_CASH_BENEFITS`, `NAVY_MATERIAL_BENEFITS`, `NAVY_MUSTEROUT_RANK_BONUS`, `NAVY_MAX_CASH_ROLLS`, and `NAVY_MATERIAL_DM_MIN_RANK` in `src/cetools/navy/tables.py` until all `test_tables.py` tests pass

### Character Dataclasses (test-first)

- [ ] T006 [P] Write failing tests for `Benefit`, `CareerTerm`, and `Character` dataclasses (including `Character.upp` pseudo-hex property using `to_pseudo_hex`, `Character.rank_title` from `NAVY_RANKS`, skill-merge rule when a duplicate skill name is gained, and `Character.to_json_dict()` producing the FR-010 schema) in `tests/navy/test_character.py`; confirm all tests FAIL before proceeding
- [ ] T007 Implement `Benefit`, `CareerTerm`, and `Character` dataclasses with the `upp` derived property (calling `to_pseudo_hex` from `tables.py` for each of the six characteristics in STR/DEX/END/INT/EDU/SOC order), `rank_title` derived property, skill-merge logic (`add_skill` method or equivalent), and `to_json_dict()` in `src/cetools/navy/character.py` until all `test_character.py` tests pass

**Checkpoint**: SRD constants are importable and testable in isolation; `Character`, `CareerTerm`, and `Benefit` dataclasses pass all tests. User story implementation may now begin.

---

## Phase 3: User Story 1 — Generate a Complete Navy Character (Priority: P1) 🎯 MVP

**Goal**: Implement the full Navy career simulation — characteristic rolls, enlistment/draft loop (with 1,000-attempt hard stop), per-term resolution (survival, commission/advancement, skill acquisition, rank bonus grants), and mustering-out benefit calculation.

**Independent Test**: Calling `generate_character()` with a seeded `random.Random` produces a `Character` whose characteristics are each in range 2–15, rank is 0–6, terms is 1–7, `skills` includes at least `"Zero-G": 1` (granted on entry), and total benefit count equals `terms + NAVY_MUSTEROUT_RANK_BONUS.get(rank, 0)`.

### Tests for User Story 1 (MANDATORY — Write FIRST, Confirm FAILING)

- [ ] T008 [US1] Write failing tests covering: enlistment pass (INT modifier makes target), enlistment fail → draft roll 4 → Navy (draft success), enlistment fail → draft roll ≠ 4 → retry (non-Navy draft), retry loop hitting 1,000-attempt error, survival failure ending career on term 1 vs term N, re-enlistment failure after term 4, 7-term cap termination, skill acquisition and merge (duplicate skill increments level), commission advancing rank 0→1 with extra skill roll, advancement advancing rank 1→5 with extra skill roll, rank 3 granting Tactics-1 bonus, and muster-out producing correct roll count (terms + rank bonus) with cash capped at 3 rolls in `tests/navy/test_generator.py`; use `random.Random(seed)` for deterministic assertions; confirm all tests FAIL before proceeding

### Implementation for User Story 1

- [ ] T009 [US1] Implement `roll_characteristics(rng: random.Random) -> dict[str, int]` returning six 2d6 rolls keyed `STR`, `DEX`, `END`, `INT`, `EDU`, `SOC` in `src/cetools/navy/generator.py`
- [ ] T010 [US1] Implement `enlist_or_draft(characteristics: dict[str, int], rng: random.Random) -> None` (Navy qualification check via `NAVY_QUALIFICATION`, draft fallback via `DRAFT_TABLE`, non-Navy retry loop raising `RuntimeError` after 1,000 consecutive non-Navy outcomes per FR-002) in `src/cetools/navy/generator.py`
- [ ] T011 [US1] Implement `run_term(character: Character, term_number: int, rng: random.Random) -> CareerTerm` (base skill roll on chosen table, survival check via `NAVY_SURVIVAL`, commission check via `NAVY_COMMISSION` if rank=0, advancement check via `NAVY_ADVANCEMENT` if rank 1–5, one extra skill roll on commission/advancement success, rank bonus skill grant for ranks 0 and 3 per `NAVY_RANK_BONUS_SKILLS`, skill-merge via `character.add_skill`) in `src/cetools/navy/generator.py`
- [ ] T012 [US1] Implement `muster_out(character: Character, rng: random.Random) -> list[Benefit]` (total rolls = terms + `NAVY_MUSTEROUT_RANK_BONUS.get(rank, 0)`, cash rolls capped at `NAVY_MAX_CASH_ROLLS`, `+1` on material rolls if rank ≥ `NAVY_MATERIAL_DM_MIN_RANK`, `+1` cash roll if `"Gambling"` in character skills) in `src/cetools/navy/generator.py`
- [ ] T013 [US1] Implement `generate_character(rng: random.Random | None = None) -> Character` (top-level orchestration: call `enlist_or_draft`, run term loop calling `run_term`, re-enlistment check from term 5 via flat 2d6 ≥ `NAVY_REENLISTMENT`, stop at 7-term cap, call `muster_out`, set `character.age = 18 + 4 * character.terms`) in `src/cetools/navy/generator.py`

**Checkpoint**: `generate_character()` produces rules-legal Navy characters with correct characteristics, rank, skills, and benefits; all `test_generator.py` tests green.

---

## Phase 4: User Story 2 — Display Formatted Character Sheet (Priority: P2)

**Goal**: Implement human-readable output matching the format in `contracts/cli.md`, and wire the `cetools navy` CLI command to display it with `--count` flag and count validation.

**Independent Test**: `format_character_human(character)` returns a string whose first line is `UPP: <six pseudo-hex chars>`, with skills sorted alphabetically in `Name-Level` notation and cash benefits shown as `Cr<amount>`. `cetools navy` exits with code 0 and prints the block to stdout; `cetools navy --count 0` exits with code 1 and prints `Error: count must be a positive integer` to stderr.

### Tests for User Story 2 (MANDATORY — Write FIRST, Confirm FAILING)

- [ ] T014 [P] [US2] Write failing tests for `format_character_human()` covering: six-digit pseudo-hex UPP line, age computed as 18+4×terms, correct rank title string, skills sorted alphabetically in `Name-Level` format, `(none)` when no skills, cash benefits as `Cr<amount>`, material benefits by SRD name, and `---` separator between blocks when formatting multiple characters in `tests/navy/test_formatter.py`; confirm all tests FAIL before proceeding
- [ ] T016 [P] [US2] Write failing CLI integration tests covering: `cetools navy` single-character output block (stdout has `UPP:`, `Age:`, `Rank:`, `Terms:`, `Skills:`, `Benefits:` lines), `cetools navy --count 3` produces three blocks separated by `---`, exit code 0 on success, `cetools navy --count 0` exits with code 1 and stderr message `Error: count must be a positive integer`, `cetools navy --count -1` same error in `tests/test_cli.py`; confirm all tests FAIL before proceeding

### Implementation for User Story 2

- [ ] T015 [US2] Implement `format_character_human(character: Character) -> str` returning the human-readable block with fields `UPP`, `Age`, `Rank`, `Terms`, `Skills` (alphabetically sorted `Name-Level` entries, `(none)` if empty), and `Benefits` (`Cr<amount>` for cash, SRD name for material) per `contracts/cli.md` in `src/cetools/navy/formatter.py`
- [ ] T017 [US2] Implement `cetools navy` Typer command in `src/cetools/cli.py` with `--count INTEGER` option (default 1): validate count > 0 (print `Error: count must be a positive integer` to stderr and `raise typer.Exit(1)` on failure), call `generate_character()` count times, join human-readable blocks with `\n---\n`, print to stdout, exit 0 on success

**Checkpoint**: `cetools navy` and `cetools navy --count N` produce correctly formatted character sheets; count validation errors exit with code 1; all US2 tests green.

---

## Phase 5: User Story 3 — Export Character as Structured Data (Priority: P3)

**Goal**: Add `--json` flag to `cetools navy` producing the JSON schema defined in FR-010 and `contracts/cli.md`. Single character → JSON object; multiple → JSON array.

**Independent Test**: `format_character_json(character)` returns a dict with keys `upp`, `age`, `rank`, `terms`, `skills`, `benefits` (no `career_history`). `cetools navy --json | python -m json.tool` exits without error. `cetools navy --count 3 --json` produces a JSON array of length 3.

### Tests for User Story 3 (MANDATORY — Write FIRST, Confirm FAILING)

- [ ] T018 [P] [US3] Add failing tests for `format_character_json()` covering: all six required top-level fields present (`upp`, `age`, `rank`, `terms`, `skills`, `benefits`), `career_history` absent, `skills` is `{}` when character has no skills, `rank` is `"Starman"` for rank 0 character, each benefit dict has `"type"` (`"cash"` or `"material"`) and `"value"` (int for cash, string for material), `json.dumps(result)` is valid JSON to `tests/navy/test_formatter.py`; confirm all new tests FAIL before proceeding
- [ ] T020 [P] [US3] Add failing CLI integration tests for `--json` flag: `cetools navy --json` produces stdout parseable by `json.loads` as a dict with all required keys, `cetools navy --count 3 --json` produces a list of length 3, `cetools navy --count 1 --json` produces a dict (not a list) to `tests/test_cli.py`; confirm all new tests FAIL before proceeding

### Implementation for User Story 3

- [ ] T019 [US3] Implement `format_character_json(character: Character) -> dict` returning `{"upp": ..., "age": ..., "rank": ..., "terms": ..., "skills": {...}, "benefits": [...]}` per FR-010 schema (`career_history` excluded; `skills` is `{}` if empty; `rank` is always the title string, never null) in `src/cetools/navy/formatter.py`
- [ ] T021 [US3] Add `--json` boolean flag (default `False`) to the `cetools navy` Typer command in `src/cetools/cli.py`: when `True`, serialize single character with `json.dumps(format_character_json(char))` and multiple characters with `json.dumps([format_character_json(c) for c in chars])`; print to stdout; human-readable path unchanged

**Checkpoint**: `cetools navy --json` and `cetools navy --count N --json` emit valid JSON matching the FR-010 schema; all US3 tests green.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Code quality gate, final validation, and SRD compliance verification (SC-002, SC-003).

- [ ] T022 Run `uv run black . && uv run flake8 src tests`; fix all formatting and lint errors across `src/cetools/` and `tests/`
- [ ] T023 Run `uv run pytest`; confirm full test suite (`test_tables.py`, `test_character.py`, `test_generator.py`, `test_formatter.py`, `test_cli.py`) passes with zero failures
- [ ] T024 [P] Run quickstart.md manual validation: execute all 7 scenarios (single character, `--count 5`, `--json`, `--count 3 --json`, `--count 0` error, `--count 100` stress, `--count 100 --json` stress) and confirm each expected output and exit code
- [ ] T025 [P] Verify SC-002: run `cetools navy --count 10 --json > sample.json`; manually verify each of the 10 characters against CE SRD tables (characteristics range 2–15, skill names from Navy tables only, cash amounts from `NAVY_CASH_BENEFITS`, material names from `NAVY_MATERIAL_BENEFITS`, rank title from `NAVY_RANKS`); all 10 must pass with zero discrepancies
- [ ] T026 [P] Verify SC-003: run `cetools navy --count 100`; confirm exit code 0, 99 `---` separators in output, and no runtime errors

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — **BLOCKS all user stories**
- **Phase 3 (US1)**: Depends on Phase 2 — core generation logic; must complete before US2 or US3
- **Phase 4 (US2)**: Depends on Phase 3 — requires `generate_character()` to produce characters to format
- **Phase 5 (US3)**: Depends on Phase 3 — requires `generate_character()`; extends `formatter.py` and `cli.py` created in Phase 4
- **Phase 6 (Polish)**: Depends on Phases 3, 4, and 5 all complete

### User Story Dependencies

- **US1 (P1)**: Requires Foundational (Phase 2); no dependency on US2 or US3
- **US2 (P2)**: Requires US1 — formats the `Character` that `generate_character()` produces
- **US3 (P3)**: Requires US1 — also extends `formatter.py` and `cli.py` created for US2

### Within Each Phase

- Write tests → confirm all FAIL → implement → confirm tests pass (red-green-refactor per Principle II)
- `tables.py` before `character.py` (`character.py` imports `to_pseudo_hex` from `tables.py`)
- `generator.py` depends on both `tables.py` and `character.py`
- `formatter.py` depends on `character.py`
- `cli.py` depends on `generator.py` and `formatter.py`

### Parallel Opportunities

- **Phase 2**: T004 and T006 can be written in parallel (different files: `test_tables.py` vs `test_character.py`)
- **Phase 4**: T014 and T016 can be written in parallel (different files: `test_formatter.py` vs `test_cli.py`)
- **Phase 5**: T018 and T020 can be written in parallel (different files: `test_formatter.py` vs `test_cli.py`)
- **Phase 6**: T024, T025, T026 can run in parallel once T022 and T023 pass

---

## Parallel Examples

### Phase 2 (Foundational) — Parallel Test Writing

```
Parallel test writing (both FAIL immediately):
  T004 → tests/navy/test_tables.py  (SRD constants)
  T006 → tests/navy/test_character.py  (dataclasses)
```

### Phase 4 (US2) — Parallel Test Writing

```
Parallel test writing (both FAIL immediately):
  T014 → tests/navy/test_formatter.py  (human-readable format)
  T016 → tests/test_cli.py  (CLI integration)
```

### Phase 5 (US3) — Parallel Test Writing

```
Parallel test writing (both FAIL immediately):
  T018 → tests/navy/test_formatter.py  (JSON format, extending T014's file)
  T020 → tests/test_cli.py  (--json CLI tests, extending T016's file)
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks everything)
3. Complete Phase 3: User Story 1 (generation logic, library only)
4. Complete Phase 4: User Story 2 (human-readable display + CLI)
5. **STOP and VALIDATE**: run `cetools navy` and hand-verify output against SRD
6. Ship MVP; continue to US3 when ready

### Incremental Delivery

1. Phase 1 + 2 → Foundation ready (SRD constants + dataclasses tested)
2. Phase 3 (US1) → `generate_character()` works in isolation
3. Phase 4 (US2) → `cetools navy` produces readable character sheets **(MVP deliverable)**
4. Phase 5 (US3) → `cetools navy --json` adds structured export
5. Phase 6 → Polish, SRD compliance verified, quickstart scenarios all pass

### Notes

- `[P]` tasks target different files with no unresolved dependencies — safe to parallelize
- Every story phase: tests MUST be written and confirmed FAILING before the first line of implementation
- Pre-commit gate: `uv run black . && uv run flake8 src tests && uv run pytest` must pass before every commit
- The `formatter.py` file grows across Phases 4 and 5 — T015 creates it, T019 extends it
- The `cli.py` file grows across Phases 4 and 5 — T017 creates the command, T021 adds the `--json` flag
- The `test_cli.py` file grows across Phases 4 and 5 — T016 creates it, T020 extends it
- `generate_character()` accepts an optional `rng` argument for seeded testing; callers that omit it get a fresh `random.Random()`
