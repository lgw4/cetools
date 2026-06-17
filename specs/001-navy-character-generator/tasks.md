---
description: "Task list for Navy Character Generator implementation"
---

# Tasks: Navy Character Generator

**Input**: Design documents from `/specs/001-navy-character-generator/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [data-model.md](data-model.md), [research.md](research.md), [contracts/cli.md](contracts/cli.md), [quickstart.md](quickstart.md)

**Constitution**: [.specify/memory/constitution.md](../../.specify/memory/constitution.md) v1.0.0 — all five principles apply; see each phase for relevant gates.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Each task includes the exact file path where work is performed

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Scaffold the Python project with all required tooling and package structure.

- [X] T001 Initialize Python project — create `pyproject.toml` with Python 3.13, `[project.scripts]` entry `cetools = "cetools.cli.main:app"`, runtime dep `typer>=0.15`, dev deps `pytest>=8`, `black>=24`, `flake8>=7`, `src` layout, and `[tool.pytest.ini_options]` pointing to `tests/`
- [X] T002 [P] Create package skeleton — add empty `src/cetools/__init__.py`, `src/cetools/engine/__init__.py`, `src/cetools/engine/careers/__init__.py`, `tests/` directory (with `.keep` or initial `conftest.py`), and a minimal stub `src/cetools/cli/__init__.py` + `src/cetools/cli/main.py` containing `app = typer.Typer()` to satisfy the `cetools` entry point before T003
- [X] T003 Run `uv sync` and confirm `cetools --help` resolves without error

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core primitives shared by all user stories. MUST be complete before any US phase begins.

**Constitution — Principle IV (Test-First)**: Tests for these foundational modules appear alongside Phase 3 tests (T007–T009) and MUST be written and confirmed failing before any Phase 3 implementation begins. No implementation task in Phase 3 may start until T007–T009 are red.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 [P] Implement `DiceRoller` protocol and default `RandomDiceRoller` implementation in `src/cetools/engine/dice.py` — `roll(sides: int, count: int = 1) -> int` returns sum of `count` dice; default uses `random.randint`
- [X] T005 [P] Implement `RankEntry` and `Career` frozen dataclasses in `src/cetools/engine/careers/base.py` — include all fields from data-model.md (`qualification_stat`, `qualification_target`, `survival_stat`, `survival_target`, `commission_stat`, `commission_target`, `advancement_stat`, `advancement_target`, `reenlistment_target`, `service_skills`, `personal_development`, `specialist_skills`, `advanced_education`, `ranks`, `cash_benefits`, `material_benefits`)
- [X] T006 [P] Implement `Skill`, `Benefit`, `Term`, `Character`, and `GenerationFailure` dataclasses in `src/cetools/engine/models.py` — field types per data-model.md; `Benefit.kind` is `Literal["cash", "material"]`; `Character.upp` is a derived `str`

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 — Generate a Navy Character (Priority: P1) 🎯 MVP

**Goal**: Call `generate_character(NAVY_CAREER)` and receive a fully-formed `Character` with valid UPP, career history, skills, and mustering-out benefits — or a `GenerationFailure` on death/enlistment rejection.

**Independent Test**: Inject a controlled `DiceRoller` into `generate_character(NAVY_CAREER, roller=...)` and assert that:
- a `Character` is returned with a 6-character UPP containing only pseudo-hex chars (no `I` or `O`)
- `terms_served >= 1`, `skills` is non-empty, and `benefits` is non-empty
- A roller that always returns minimum values yields a `GenerationFailure` for enlistment

**Constitution — Principle IV (Test-First)**: ALL test tasks below (T007–T011) MUST be written and confirmed failing (red) before any implementation task (T012–T014) begins.

### Tests for User Story 1

> **Write these tests FIRST; ensure they FAIL before implementing T012–T014.**

- [X] T007 [P] [US1] Write dice tests (`DiceRoller` protocol compliance via structural subtyping, `RandomDiceRoller.roll(6)` returns value in `[1, 6]`, `RandomDiceRoller.roll(6, count=2)` returns value in `[2, 12]`, injected stub roller returns controlled value) in `tests/test_dice.py`
- [X] T008 [P] [US1] Write pseudo-hex encoding tests (all 34 mappings 0–33, boundary values 9→`9`/10→`A`/17→`H`/18→`J`/22→`N`/23→`P`/33→`Z`, out-of-range inputs raise `ValueError`: value 34, value -1, invalid char `"I"`, invalid char `"O"`) in `tests/test_pseudohex.py`
- [X] T009 [P] [US1] Write model tests (characteristic modifier table for all score bands 0–33+, `encode_upp` produces correct 6-char string for sample scores, `GenerationFailure.exit_code == 1`) in `tests/test_models.py`
- [X] T010 [P] [US1] Write Navy career data integrity tests (all tuple lengths are 6 for skill tables and 7 for benefit tables, rank titles match SRD, `qualification_stat="Intelligence"`, `qualification_target=6`, `survival_stat="Intelligence"`, `survival_target=5`, `commission_stat="Social Standing"`, `commission_target=7`, `advancement_stat="Education"`, `advancement_target=6`) in `tests/test_careers.py`
- [X] T011 [P] [US1] Write generator lifecycle tests (enlistment pass → `Character`; enlistment fail → `GenerationFailure`; survival fail mid-term → `GenerationFailure`; 7-term cap with voluntary muster-out; natural-12 on re-enlistment at term 7 forces term 8; first-term basic training grants all 6 service skills at Level 0; aging check triggers at term 4+; pension present at 5+ terms; cash roll cap enforced at 3; rank bonus rolls applied at O4/O5/O6; wall-clock duration of one full generation call is < 2 seconds — SC-001) in `tests/test_generator.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `NAVY_CAREER` instance in `src/cetools/engine/careers/navy.py` using SRD-corrected values from data-model.md (Qualification: Intelligence 6+; Survival: Intelligence 5+; Commission: Social Standing 7+; Advancement: Education 6+; ranks Starman–Commodore; Rank 0 grants Zero-G-1; Rank 3 grants Tactics-1)
- [X] T013 [P] [US1] Implement `to_pseudohex(value: int) -> str`, `from_pseudohex(char: str) -> int`, and `encode_upp(scores: dict[str, int]) -> str` in `src/cetools/engine/pseudohex.py` using the full 34-value SRD table (skip `I` and `O`); raise `ValueError` for out-of-range or invalid inputs
- [X] T014 [US1] Implement `generate_character(career: Career, roller: DiceRoller = RandomDiceRoller()) -> Character | GenerationFailure` in `src/cetools/engine/generator.py` following the state machine in data-model.md: roll characteristics → background skills (3 at Level 0 from primary education list) → qualification check → term loop (basic training on term 1, survival, commission/advancement, skill rolls, aging, re-enlistment) → mustering-out → pension → encode UPP

**Checkpoint**: `uv run pytest tests/test_dice.py tests/test_pseudohex.py tests/test_models.py tests/test_careers.py tests/test_generator.py` passes. `generate_character(NAVY_CAREER)` returns a `Character` or `GenerationFailure` via direct Python import.

**Constitution — Principle II gate**: `rg "from cetools.cli|import cetools.cli" src/cetools/engine/` returns no results (engine has zero CLI dependency). `rg "from cetools.engine|import cetools.engine" src/cetools/cli/` is the only direction of dependency allowed.

**Quality gate**: `uv run black . && uv run flake8 src tests && uv run pytest` — all must pass before opening any PR or proceeding to Phase 4.

---

## Phase 4: User Story 2 — View Character as Formatted Output (Priority: P2)

**Goal**: `cetools character generate` prints a human-readable plain-text record to stdout (exit 0) or prints a failure message to stderr (exit 1), with no output on the other stream.

**Independent Test**: Call the formatter directly with a constructed `Character`; assert stdout contains labeled sections for UPP, all six characteristics with names and values (pseudo-hex encoding for values > 9), skills with levels, mustering-out benefits (cash in Cr format, material names), and pension if present. Invoke CLI with a failing roller via `subprocess` and assert exit code 1, empty stdout, non-empty stderr.

**Constitution — Principle IV (Test-First)**: T015–T016 MUST be written and confirmed failing before T017–T019 are implemented.

### Tests for User Story 2

> **Write these tests FIRST; ensure they FAIL before implementing T017–T019.**

- [ ] T015 [P] [US2] Write formatter tests (output contains `UPP:`, career name, rank title, terms, age, all six characteristic names, skill list with levels, benefits section, pension line when `pension is not None`; characteristic value > 9 shows pseudo-hex letter; no `I` or `O` in UPP) in `tests/test_formatter.py`
- [ ] T016 [P] [US2] Write CLI integration tests (exit code 0 + non-empty stdout + empty stderr on success; exit code 1 + empty stdout + non-empty stderr on enlistment failure; exit code 1 + empty stdout + non-empty stderr on survival failure) in `tests/test_cli.py` — use `subprocess.run(["cetools", "character", "generate"])` or `typer.testing.CliRunner`

### Implementation for User Story 2

- [ ] T017 [US2] Implement `format_character(character: Character) -> str` in `src/cetools/formatter.py` — plain-text output matching the content contract in contracts/cli.md: UPP on first line or labeled, career name + rank title + terms + age, all six characteristics by name and value (with pseudo-hex letter if value > 9), all skills with levels, all benefits (cash amounts as `CrX,XXX`, material names), pension as `Cr10,000/year` if applicable
- [ ] T018 [US2] Implement root Typer app in `src/cetools/cli/main.py` — create `app = typer.Typer()`, add character sub-app via `app.add_typer(character.app, name="character")`
- [ ] T019 [US2] Implement `generate` command in `src/cetools/cli/character.py` — call `generate_character(NAVY_CAREER)`, on `Character` print `format_character(result)` to stdout and exit 0; on `GenerationFailure` print `result.reason` to stderr and `raise typer.Exit(code=1)` (no stdout output)

**Checkpoint**: `uv run cetools character generate` exits 0 with a formatted character on stdout, or exits 1 with only stderr output on failure. `uv run pytest tests/test_formatter.py tests/test_cli.py` passes.

**Constitution — Principle III gate**: Confirm `src/cetools/cli/character.py` contains no game logic — only: call `generate_character`, branch on result type, write to stdout/stderr, set exit code.

**Quality gate**: `uv run black . && uv run flake8 src tests && uv run pytest` — all must pass before opening any PR or proceeding to Phase 5.

---

## Phase 5: User Story 3 — Extend Generator to Additional Careers (Priority: P3)

**Goal**: Verify the generation engine is career-agnostic — no Navy-specific logic in `generator.py`; all career variation flows through the `Career` interface.

**Independent Test**: Define a minimal non-Navy `Career` instance using `dataclasses.replace(NAVY_CAREER, name="Scout", ...)` and pass it to `generate_character()`; confirm the engine processes it without modification and returns `Character | GenerationFailure`.

**Constitution — Principle IV (Test-First)**: T020 MUST be written and confirmed failing before T021 begins.

### Tests for User Story 3

> **Write this test FIRST; ensure it FAILS if any Navy-specific hardcoding exists.**

- [ ] T020 [P] [US3] Write extensibility test — define a minimal stub `Career` (use `dataclasses.replace` on `NAVY_CAREER` with `name="Scout"`) and assert `generate_character(stub_career, roller=controlled_roller)` returns `Character | GenerationFailure` without importing `navy.py` in the engine; assert no `"Navy"` string literal appears in `src/cetools/engine/generator.py` in `tests/test_careers.py` (extend existing file)

### Implementation for User Story 3

- [ ] T021 [US3] Audit `src/cetools/engine/generator.py` for any hardcoded Navy values (career name strings, fixed target numbers, rank title strings) and replace with `career.<field>` lookups if found — goal is zero Navy-specific references in the engine

**Checkpoint**: `uv run pytest tests/test_careers.py` passes including the extensibility test. `rg "Navy" src/cetools/engine/generator.py` returns no results.

**Constitution — Principle V gate**: Confirm adding a second career requires only a new `Career` instance file (e.g., `src/cetools/engine/careers/scout.py`) with zero changes to `generator.py`.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Formatting, linting, full suite validation, quickstart verification, and constitution compliance audit before opening the PR.

- [ ] T022 [P] Run Black and fix all formatting: `uv run black src tests`
- [ ] T023 [P] Run flake8 and fix all lint warnings: `uv run flake8 src tests`
- [ ] T024 Run full test suite and confirm all tests pass: `uv run pytest -v`
- [ ] T025 Run quickstart.md Scenario 1 manually (`uv run cetools character generate`) and verify output matches the content contract in contracts/cli.md
- [ ] T026 Run quickstart.md Scenario 3 pseudo-hex validation: `uv run pytest tests/test_pseudohex.py -v`
- [ ] T027 Constitution compliance audit — verify all five principles hold: (I) `rg "TODO|FIXME|HACK" src/` returns no SRD rule approximations; (II) `rg "from cetools.cli|import cetools.cli" src/cetools/engine/` returns no results; (III) `src/cetools/cli/character.py` contains only I/O routing with no game logic; (IV) every module under `src/cetools/` has a corresponding test file under `tests/`; (V) `rg "Navy" src/cetools/engine/generator.py` returns no results

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — blocks all user stories
- **US1 (Phase 3)**: Depends on Phase 2; T007–T011 (tests) can all run in parallel once T004–T006 complete; T012 and T013 can run in parallel once T007–T011 are red; T014 depends on T004, T005, T006, T012, T013
- **US2 (Phase 4)**: Depends on T014 (generator must exist); T017–T019 depend on T014; T015 and T016 can be written in parallel with T014
- **US3 (Phase 5)**: Depends on T014; T020 can be written immediately; T021 depends on T020 result
- **Polish (Phase 6)**: Depends on all prior phases

### User Story Dependencies

- **US1 (P1)**: Unblocks US2 and US3 (formatter and CLI wrap the engine)
- **US2 (P2)**: Depends on US1 engine; independently testable via formatter unit tests before CLI wiring
- **US3 (P3)**: Depends on US1 engine; is a validation of existing code, not additive functionality

### Within Each User Story

- Tests MUST be written and confirmed FAILING before implementing the targeted module (Constitution Principle IV — non-negotiable)
- Models/protocols before services (`dice.py`, `models.py` before `generator.py`)
- Engine before CLI (`generator.py` before `character.py`)
- Formatter before CLI command (`formatter.py` before `character.py`)
- Quality gate (`uv run black . && uv run flake8 src tests && uv run pytest`) before any PR

### Parallel Opportunities

- T004, T005, T006 (Phase 2) — different files, no internal dependencies
- T007, T008, T009, T010, T011, T012, T013 (Phase 3 tests + Navy data + pseudohex) — different files
- T015, T016 (Phase 4 tests) — different files
- T017, T018 can start in parallel (different files); T019 depends on both
- T022, T023 (Phase 6 format/lint) — different tools, same file set

---

## Parallel Example: User Story 1

```bash
# All can start as soon as Phase 2 is complete AND tests are red:
Task T007: tests/test_dice.py              (dice protocol and roller tests)
Task T008: tests/test_pseudohex.py         (pseudo-hex test coverage)
Task T009: tests/test_models.py            (model and modifier tests)
Task T010: tests/test_careers.py           (Navy data integrity tests)
Task T011: tests/test_generator.py         (full lifecycle tests)
Task T012: src/cetools/engine/careers/navy.py   (Navy career data)
Task T013: src/cetools/engine/pseudohex.py      (pseudo-hex encoding)

# T014 (generator.py) starts only after T004–T006 AND T012–T013 are complete
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Write ALL Phase 3 tests (T007–T011) and confirm they FAIL (Constitution Principle IV)
4. Complete Phase 3: User Story 1 (engine only)
5. **STOP and VALIDATE**: `generate_character(NAVY_CAREER)` returns structured output via direct Python import
6. Proceed to Phase 4 for CLI and formatted output

### Incremental Delivery

1. Phase 1 + 2 → Project scaffolded with core primitives
2. Phase 3 → Engine functional; library importable (SC-005 met)
3. Phase 4 → CLI functional; `cetools character generate` works end-to-end (SC-001, SC-002, SC-003 met)
4. Phase 5 → Extensibility verified (SC-004 met)
5. Phase 6 → Code quality gates pass and constitution compliance confirmed; ready for PR

---

## Notes

- `[P]` tasks operate on different files and have no shared dependencies within their phase
- `[USN]` label maps each task to a user story for traceability to spec.md acceptance criteria
- SRD-corrected values are in research.md; use data-model.md's `NAVY_CAREER` concrete instance as the authoritative source for all target numbers and rank data
- Aging stat reductions in MVP are applied in order: Strength → Dexterity → Endurance (no player input needed)
- Background skills: always 3 skills at Level 0 from the primary education list in research.md (simplified per spec Assumption)
- Pseudo-hex table has 34 entries (0–33); `I` and `O` are omitted; confirm with boundary tests at 17→`H`, 18→`J`, 22→`N`, 23→`P`
- Constitution v1.0.0 gates are enforced at each phase checkpoint — see plan.md Constitution Check for ratification details
