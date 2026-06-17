---
description: "Task list for Navy Character Generator implementation"
---

# Tasks: Navy Character Generator

**Input**: Design documents from `/specs/001-navy-character-generator/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [data-model.md](data-model.md), [research.md](research.md), [contracts/cli.md](contracts/cli.md), [quickstart.md](quickstart.md)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Each task includes the exact file path where work is performed

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Scaffold the Python project with all required tooling and package structure.

- [ ] T001 Initialize Python project — create `pyproject.toml` with Python 3.13, `[project.scripts]` entry `cetools = "cetools.cli.main:app"`, runtime dep `typer>=0.15`, dev deps `pytest>=8`, `black>=24`, `flake8>=7`, `src` layout, and `[tool.pytest.ini_options]` pointing to `tests/`
- [ ] T002 [P] Create package skeleton — add empty `src/cetools/__init__.py`, `src/cetools/cli/__init__.py`, `src/cetools/engine/__init__.py`, `src/cetools/engine/careers/__init__.py`, and `tests/` directory (with `.keep` or initial `conftest.py`)
- [ ] T003 Run `uv sync` and confirm `cetools --help` resolves without error after stub CLI exists

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core primitives shared by all user stories. MUST be complete before any US phase begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 [P] Implement `DiceRoller` protocol and default `RandomDiceRoller` implementation in `src/cetools/engine/dice.py` — `roll(sides: int, count: int = 1) -> int` returns sum of `count` dice; default uses `random.randint`
- [ ] T005 [P] Implement `RankEntry` and `Career` frozen dataclasses in `src/cetools/engine/careers/base.py` — include all fields from data-model.md (`qualification_stat`, `qualification_target`, `survival_stat`, `survival_target`, `commission_stat`, `commission_target`, `advancement_stat`, `advancement_target`, `reenlistment_target`, `service_skills`, `personal_development`, `specialist_skills`, `advanced_education`, `ranks`, `cash_benefits`, `material_benefits`)
- [ ] T006 [P] Implement `Skill`, `Benefit`, `Term`, `Character`, and `GenerationFailure` dataclasses in `src/cetools/engine/models.py` — field types per data-model.md; `Benefit.kind` is `Literal["cash", "material"]`; `Character.upp` is a derived `str`

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 — Generate a Navy Character (Priority: P1) 🎯 MVP

**Goal**: Call `generate_character(NAVY_CAREER)` and receive a fully-formed `Character` with valid UPP, career history, skills, and mustering-out benefits — or a `GenerationFailure` on death/enlistment rejection.

**Independent Test**: Inject a controlled `DiceRoller` into `generate_character(NAVY_CAREER, roller=...)` and assert that:
- a `Character` is returned with a 6-character UPP containing only pseudo-hex chars (no `I` or `O`)
- `terms_served >= 1`, `skills` is non-empty, and `benefits` is non-empty
- A roller that always returns minimum values yields a `GenerationFailure` for enlistment

### Tests for User Story 1

> **Write these tests FIRST; ensure they FAIL before implementing T011–T012.**

- [ ] T007 [P] [US1] Write pseudo-hex encoding tests (all 34 mappings 0–33, boundary values 9→`9`/10→`A`/17→`H`/18→`J`/22→`N`/23→`P`/33→`Z`, invalid inputs raise `ValueError`) in `tests/test_pseudohex.py`
- [ ] T008 [P] [US1] Write model tests (characteristic modifier table for all score bands 0–33+, `encode_upp` produces correct 6-char string for sample scores, `GenerationFailure.exit_code == 1`) in `tests/test_models.py`
- [ ] T009 [P] [US1] Write Navy career data integrity tests (all tuple lengths are 6 for skill tables and 7 for benefit tables, rank titles match SRD, `qualification_stat="Intelligence"`, `qualification_target=6`, `survival_stat="Intelligence"`, `survival_target=5`, `commission_stat="Social Standing"`, `commission_target=7`, `advancement_stat="Education"`, `advancement_target=6`) in `tests/test_careers.py`
- [ ] T010 [P] [US1] Write generator lifecycle tests (enlistment pass → `Character`; enlistment fail → `GenerationFailure`; survival fail mid-term → `GenerationFailure`; 7-term cap with voluntary muster-out; natural-12 on re-enlistment at term 7 forces term 8; first-term basic training grants all 6 service skills at Level 0; aging check triggers at term 4+; pension present at 5+ terms; cash roll cap enforced at 3; rank bonus rolls applied at O4/O5/O6) in `tests/test_generator.py`

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `NAVY_CAREER` instance in `src/cetools/engine/careers/navy.py` using SRD-corrected values from data-model.md (Qualification: Intelligence 6+; Survival: Intelligence 5+; Commission: Social Standing 7+; Advancement: Education 6+; ranks Starman–Commodore; Rank 0 grants Zero-G-1; Rank 3 grants Tactics-1)
- [ ] T012 [P] [US1] Implement `to_pseudohex(value: int) -> str`, `from_pseudohex(char: str) -> int`, and `encode_upp(scores: dict[str, int]) -> str` in `src/cetools/engine/pseudohex.py` using the full 34-value SRD table (skip `I` and `O`); raise `ValueError` for out-of-range or invalid inputs
- [ ] T013 [US1] Implement `generate_character(career: Career, roller: DiceRoller = RandomDiceRoller()) -> Character | GenerationFailure` in `src/cetools/engine/generator.py` following the state machine in data-model.md: roll characteristics → background skills (3 at Level 0 from primary education list) → qualification check → term loop (basic training on term 1, survival, commission/advancement, skill rolls, aging, re-enlistment) → mustering-out → pension → encode UPP

**Checkpoint**: `uv run pytest tests/test_pseudohex.py tests/test_models.py tests/test_careers.py tests/test_generator.py` passes. `generate_character(NAVY_CAREER)` returns a `Character` or `GenerationFailure` via direct Python import.

---

## Phase 4: User Story 2 — View Character as Formatted Output (Priority: P2)

**Goal**: `cetools character generate` prints a human-readable plain-text record to stdout (exit 0) or prints a failure message to stderr (exit 1), with no output on the other stream.

**Independent Test**: Call the formatter directly with a constructed `Character`; assert stdout contains labeled sections for UPP, all six characteristics with names and values (pseudo-hex encoding for values > 9), skills with levels, mustering-out benefits (cash in Cr format, material names), and pension if present. Invoke CLI with a failing roller via `subprocess` and assert exit code 1, empty stdout, non-empty stderr.

### Tests for User Story 2

> **Write these tests FIRST; ensure they FAIL before implementing T016–T018.**

- [ ] T014 [P] [US2] Write formatter tests (output contains `UPP:`, career name, rank title, terms, age, all six characteristic names, skill list with levels, benefits section, pension line when `pension is not None`; characteristic value > 9 shows pseudo-hex letter; no `I` or `O` in UPP) in `tests/test_formatter.py`
- [ ] T015 [P] [US2] Write CLI integration tests (exit code 0 + non-empty stdout + empty stderr on success; exit code 1 + empty stdout + non-empty stderr on enlistment failure; exit code 1 + empty stdout + non-empty stderr on survival failure) in `tests/test_cli.py` — use `subprocess.run(["cetools", "character", "generate"])` or `typer.testing.CliRunner`

### Implementation for User Story 2

- [ ] T016 [US2] Implement `format_character(character: Character) -> str` in `src/cetools/formatter.py` — plain-text output matching the content contract in contracts/cli.md: UPP on first line or labeled, career name + rank title + terms + age, all six characteristics by name and value (with pseudo-hex letter if value > 9), all skills with levels, all benefits (cash amounts as `CrX,XXX`, material names), pension as `Cr10,000/year` if applicable
- [ ] T017 [US2] Implement root Typer app in `src/cetools/cli/main.py` — create `app = typer.Typer()`, add character sub-app via `app.add_typer(character.app, name="character")`
- [ ] T018 [US2] Implement `generate` command in `src/cetools/cli/character.py` — call `generate_character(NAVY_CAREER)`, on `Character` print `format_character(result)` to stdout and exit 0; on `GenerationFailure` print `result.reason` to stderr and `raise typer.Exit(code=1)` (no stdout output)

**Checkpoint**: `uv run cetools character generate` exits 0 with a formatted character on stdout, or exits 1 with only stderr output on failure. `uv run pytest tests/test_formatter.py tests/test_cli.py` passes.

---

## Phase 5: User Story 3 — Extend Generator to Additional Careers (Priority: P3)

**Goal**: Verify the generation engine is career-agnostic — no Navy-specific logic in `generator.py`; all career variation flows through the `Career` interface.

**Independent Test**: Define a minimal non-Navy `Career` instance using `dataclasses.replace(NAVY_CAREER, name="Scout", ...)` and pass it to `generate_character()`; confirm the engine processes it without modification and returns `Character | GenerationFailure`.

### Tests for User Story 3

> **Write this test FIRST; ensure it FAILS if any Navy-specific hardcoding exists.**

- [ ] T019 [P] [US3] Write extensibility test — define a minimal stub `Career` (use `dataclasses.replace` on `NAVY_CAREER` with `name="Scout"`) and assert `generate_character(stub_career, roller=controlled_roller)` returns `Character | GenerationFailure` without importing `navy.py` in the engine; assert no `"Navy"` string literal appears in `src/cetools/engine/generator.py` in `tests/test_careers.py` (extend existing file)

### Implementation for User Story 3

- [ ] T020 [US3] Audit `src/cetools/engine/generator.py` for any hardcoded Navy values (career name strings, fixed target numbers, rank title strings) and replace with `career.<field>` lookups if found — goal is zero Navy-specific references in the engine

**Checkpoint**: `uv run pytest tests/test_careers.py` passes including the extensibility test. `rg "Navy" src/cetools/engine/generator.py` returns no results.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Formatting, linting, full suite validation, and quickstart verification.

- [ ] T021 [P] Run Black and fix all formatting: `uv run black src tests`
- [ ] T022 [P] Run flake8 and fix all lint warnings: `uv run flake8 src tests`
- [ ] T023 Run full test suite and confirm all tests pass: `uv run pytest -v`
- [ ] T024 Run quickstart.md Scenario 1 manually (`uv run cetools character generate`) and verify output matches the content contract in contracts/cli.md
- [ ] T025 Run quickstart.md Scenario 3 pseudo-hex validation: `uv run pytest tests/test_pseudohex.py -v`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — blocks all user stories
- **US1 (Phase 3)**: Depends on Phase 2; T011 and T012 can run in parallel once T004–T006 complete; T013 depends on T004, T005, T006, T011, T012
- **US2 (Phase 4)**: Depends on T013 (generator must exist); T016–T018 depend on T013; T014 and T015 can be written in parallel with T013
- **US3 (Phase 5)**: Depends on T013; T019 can be written immediately; T020 depends on T019 result
- **Polish (Phase 6)**: Depends on all prior phases

### User Story Dependencies

- **US1 (P1)**: Unblocks US2 and US3 (formatter and CLI wrap the engine)
- **US2 (P2)**: Depends on US1 engine; independently testable via formatter unit tests before CLI wiring
- **US3 (P3)**: Depends on US1 engine; is a validation of existing code, not additive functionality

### Within Each User Story

- Tests MUST be written and confirmed FAILING before implementing the targeted module
- Models/protocols before services (`dice.py`, `models.py` before `generator.py`)
- Engine before CLI (`generator.py` before `character.py`)
- Formatter before CLI command (`formatter.py` before `character.py`)

### Parallel Opportunities

- T004, T005, T006 (Phase 2) — different files, no internal dependencies
- T007, T008, T009, T010, T011, T012 (Phase 3 tests + Navy data + pseudohex) — different files
- T014, T015 (Phase 4 tests) — different files
- T017, T016 can start in parallel (different files); T018 depends on both
- T021, T022 (Phase 6 format/lint) — different tools, same file set

---

## Parallel Example: User Story 1

```bash
# All can start as soon as Phase 2 is complete:
Task T007: tests/test_pseudohex.py         (pseudo-hex test coverage)
Task T008: tests/test_models.py            (model and modifier tests)
Task T009: tests/test_careers.py           (Navy data integrity tests)
Task T010: tests/test_generator.py         (full lifecycle tests)
Task T011: src/cetools/engine/careers/navy.py   (Navy career data)
Task T012: src/cetools/engine/pseudohex.py      (pseudo-hex encoding)

# T013 (generator.py) starts only after T004–T006 AND T011–T012 are complete
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (engine only)
4. **STOP and VALIDATE**: `generate_character(NAVY_CAREER)` returns structured output via direct Python import
5. Proceed to Phase 4 for CLI and formatted output

### Incremental Delivery

1. Phase 1 + 2 → Project scaffolded with core primitives
2. Phase 3 → Engine functional; library importable (SC-005 met)
3. Phase 4 → CLI functional; `cetools character generate` works end-to-end (SC-001, SC-002, SC-003 met)
4. Phase 5 → Extensibility verified (SC-004 met)
5. Phase 6 → Code quality gates pass; ready for PR

---

## Notes

- `[P]` tasks operate on different files and have no shared dependencies within their phase
- `[USN]` label maps each task to a user story for traceability to spec.md acceptance criteria
- SRD-corrected values are in research.md; use data-model.md's `NAVY_CAREER` concrete instance as the authoritative source (not spec FRs, which contain errors)
- Aging stat reductions in MVP are applied in order: Strength → Dexterity → Endurance (no player input needed)
- Background skills: always 3 skills at Level 0 from the primary education list in research.md (simplified per spec Assumption)
- Pseudo-hex table has 34 entries (0–33); `I` and `O` are omitted; confirm with boundary tests at 17→`H`, 18→`J`, 22→`N`, 23→`P`
