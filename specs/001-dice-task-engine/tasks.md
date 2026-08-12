---

description: "Task list for 001-dice-task-engine"
---

# Tasks: Dice and Task Check Engine

**Input**: Design documents from `/specs/001-dice-task-engine/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Test tasks are **mandatory** here, not optional. Constitution Principle III
(Test-First, NON-NEGOTIABLE) and SC-008 require expected values to be committed
before the implementing change and each test observed failing before it passes.
Every phase below therefore ends its test group with an explicit "confirm red" task.

**Organization**: Tasks are grouped by user story. The stories are layered rather than
fully independent, which the spec itself states: US2 depends on the seeded throw from
US1, US3 renders US1 and US2 results, US4 reuses US1's roller and rendering. Each story
is still an independently *testable* increment and its checkpoint says how to test it.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Exact file paths are given in every task

## Path Conventions

Single library with a thin CLI, `src/` layout, per plan.md: source in
`src/cetools/`, tests in `tests/`, both at repository root. `src/` is deliberate: it
makes tests run against the installed package, so a packaging failure that omits
`tasks.toml` fails the suite instead of silently reading the file off disk.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Bootstrap the repository into an installable package with a runnable test
harness (FR-033).

- [ ] T001 Create the directory tree per plan.md: `src/cetools/`, `src/cetools/data/`, `tests/unit/`, `tests/contract/`, `tests/integration/`, `tests/guards/`, `tests/property/`, `tests/golden/`
- [ ] T002 Create `pyproject.toml` at repository root: `hatchling` build backend, `requires-python = ">=3.13"`, CalVer `version = "2026.08.1"`, `dependencies = ["typer"]`, dev dependency group (`pytest`, `hypothesis`, `black`, `isort`, `flake8`), `[project.scripts] cetools = "cetools.cli:main"`, hatch wheel target packaging `src/cetools` including `data/tasks.toml`, `[tool.black]`, `[tool.isort] profile = "black"`, `[tool.pytest.ini_options] testpaths = ["tests"]`
- [ ] T003 [P] Create `.flake8` at repository root with `max-line-length = 88` and `extend-ignore = E203` so flake8 agrees with Black (flake8 cannot read `pyproject.toml`, per research.md R13)
- [ ] T004 [P] Add `LICENSE` (full GPL-3.0 text) and a minimal `README.md` stating the project purpose and the `uv sync` / `uv run pytest` workflow; the OGL bundling, Section 15 chain, and compatibility statement are explicitly out of scope for this feature
- [ ] T005 Run `uv sync` then `uv run pytest`, confirming the environment builds and the suite runs (zero collected tests is a pass at this point)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The error taxonomy and package skeleton every story raises through and
imports from.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T006 [P] Write `tests/unit/test_errors.py` asserting the hierarchy in data-model.md: `DiceError`, `RulesDataError`, and `TaskError` each subclass `CetoolsError`, `CetoolsError` subclasses `Exception`, and all four are importable from `cetools`
- [ ] T007 [P] Create `tests/conftest.py` with shared fixtures: a `Roller` seeded to a fixed literal, the repository-root path, and a helper that reads a file from `tests/golden/`
- [ ] T008 [P] Create `src/cetools/data/__init__.py` (empty) so the data directory is an importable package readable through `importlib.resources.files("cetools.data")`
- [ ] T009 Create `src/cetools/errors.py` defining `CetoolsError`, `DiceError`, `RulesDataError`, `TaskError` with docstrings naming the conditions each covers; the library raises these and never prints or exits (FR-029)
- [ ] T010 Create `src/cetools/__init__.py` re-exporting the four error types with an explicit `__all__`, which grows in each story phase and is the public contract (contracts/library-api.md)

**Checkpoint**: `uv run pytest tests/unit/test_errors.py` passes; `python -c "import cetools"` resolves against the installed package.

---

## Phase 3: User Story 1 - Throw dice reproducibly (Priority: P1) 🎯 MVP

**Goal**: Seeded, cross-version-reproducible dice throws, described by notation, exposed
as library API and as `cetools roll` with human-readable output and a seed in every
result.

**Independent Test**: `cetools roll 2d6` with no seed, note the reported seed, run again
with `--seed <that seed>`, confirm faces and total are byte-identical. Repeat in a
separate process and under a different `PYTHONHASHSEED` with a text seed.

### Tests for User Story 1 ⚠️ Write first, confirm failing

- [ ] T011 [P] [US1] Write `tests/unit/test_seeds.py` covering seed resolution (research.md R1, R4, R5): `None` draws 64 bits from `secrets`; an `int` passes through unchanged including a negative and a value above 2^64; a string matching `^[+-]?[0-9]+$` becomes that integer including a signed one; any other string folds via blake2b-64 over UTF-8 big-endian with the literal expected value `resolve_seed("session-alpha") == 14333185781139156525`; case, surrounding whitespace, and NFC vs NFD forms of the same accented text each resolve to *different* seeds (FR-003)
- [ ] T012 [P] [US1] Write `tests/unit/test_dice.py` covering `parse_notation` (`2d6`, `d6`, `2D6+1`, `3d6 - 2`, `1d100`, `1d66`; rejects `7dQ`, `0d6`, `2d0`, `""`), `Roller.die`/`Roller.dice` including `sides=1` returning face `1` via `getrandbits(0)`, and `throw`/`throw_dice` with literal expected values written before implementation: `throw(Roller("session-alpha"), "2d6+1")` gives `faces == (1, 5)`, `modifier == 1`, `total == 7`, `notation == "2d6+1"`, `seed == 14333185781139156525`; plus FR-012 exhaustive coverage, that a fixed seeded sample of at least 1000 `d6` faces contains all six values; plus `DiceError` for every rejected input (FR-011)
- [ ] T013 [P] [US1] Write `tests/unit/test_render.py` covering `as_text` for `ThrowResult` per the rendering rules in contracts/cli.md: header `{notation} = {total}`, `(sum N)` and the `Modifier:` line present only when `modifier != 0`, `Seed:` always present, labels padded to the longest label actually present, trailing newline
- [ ] T014 [P] [US1] Write `tests/integration/test_cli.py` using Typer's `CliRunner` for `cetools roll`: successful throw exits 0 with output on stdout, bad notation exits 1 with the message on stderr and stdout empty, an unknown option exits 2, `--version` prints the package version and exits 0, and `roll --help` lists exactly `NOTATION`, `--seed`, `--json` and no check-only options (FR-025)
- [ ] T015 [P] [US1] Hand-write the golden files `tests/golden/roll_2d6_plus1.txt` and `tests/golden/roll_1d6.txt` for `--seed session-alpha`, spelling out the expected rendered text; no regeneration flag is provided, deliberately (quickstart.md)
- [ ] T016 [US1] Write `tests/integration/test_golden.py` comparing `cetools roll` stdout byte-for-byte against the files created in T015
- [ ] T017 [P] [US1] Write `tests/guards/test_seed_contract.py` with both guards from research.md R12: guard A captures `random.getstate()`, runs a full CLI invocation, and asserts the state is bit-for-bit unchanged (SC-005); guard B runs `python -m cetools roll 2d6 --seed session-alpha` in two subprocesses with `PYTHONHASHSEED=1` and `PYTHONHASHSEED=2` and asserts byte-identical output (SC-002)
- [ ] T018 [P] [US1] Write `tests/property/test_invariants.py` with hypothesis invariants for throws: every face lies in `1..sides`, `len(faces) == count`, `total == sum(faces) + modifier`, and the same seed with the same arguments always yields an equal result (FR-006)
- [ ] T019 [US1] Run `uv run pytest` and confirm every test added in T011–T018 fails, recording the red state required by Principle III and SC-008

### Implementation for User Story 1

- [ ] T020 [US1] Implement `src/cetools/seeds.py`: `resolve_seed(seed: int | str | None) -> int` applying the four-case table in data-model.md, with the digit-string regex and the blake2b-64 UTF-8 big-endian fold each in exactly one place
- [ ] T021 [US1] Implement `src/cetools/dice.py`: `Roller` (constructed via `resolve_seed`, holding a private `random.Random` seeded only with an `int`, `die` using rejection sampling on `getrandbits` per research.md R3, `dice` returning a tuple in draw order, raising `DiceError` on a count or side count below 1), the frozen slotted `ThrowResult` dataclass, `parse_notation`, `throw`, and `throw_dice`
- [ ] T022 [US1] Implement `src/cetools/render.py`: `as_text` as a `functools.singledispatch` generic with a `ThrowResult` registration, following the rendering rules pinned by T015's golden files
- [ ] T023 [US1] Implement `src/cetools/cli.py`: the Typer app, `main()`, the `roll` command taking `NOTATION` and `--seed`, the top-level `--version` eager option (FR-025), results printed to stdout, and the single `except CetoolsError` site writing the message to stderr and exiting 1 (FR-030); usage errors are left to Typer, which already exits 2
- [ ] T024 [US1] Implement `src/cetools/__main__.py` so `python -m cetools` invokes `cli.main()`, which guard test B in T017 requires
- [ ] T025 [US1] Extend `src/cetools/__init__.py` `__all__` with `Roller`, `ThrowResult`, `parse_notation`, `throw`, `throw_dice`, `as_text`
- [ ] T026 [US1] Run `uv run pytest` to green, then walk quickstart.md Scenarios 1, 2, and 10 by hand and confirm each expected result

**Checkpoint**: US1 is complete and independently useful. A referee has a reproducible dice roller; the reproducibility contract that cannot be retrofitted is now established and guarded.

---

## Phase 4: User Story 2 - Resolve a task check (Priority: P2)

**Goal**: `cetools check` resolves a 2D6 task against SRD parameters held in
`tasks.toml`, itemizing every modifier with its label.

**Independent Test**: Resolve a check at each named difficulty with a fixed seed;
confirm `target` never moves, faces are identical across all seven, and totals step by
2 from `Simple` to `Formidable`. Confirm the itemized modifiers sum to the difference
between the dice total and the final total.

### Tests for User Story 2 ⚠️ Write first, confirm failing

- [ ] T027 [P] [US2] Write `tests/unit/test_rules.py` covering `load_task_parameters()`: the shipped file loads through `importlib.resources.files("cetools.data")` and yields the expected target, unskilled DM, roll notation, seven-rung ladder in file order, and twelve bands; and every `RulesDataError` path from contracts/tasks-toml.md, exercised against temporary TOML fixtures (missing table, non-integer value, unparseable `task.roll`, malformed band key, zero or several unbounded bands, zero or several zero-modifier rungs, invalid TOML), each asserting no silent fallback to built-in values (FR-024)
- [ ] T028 [P] [US2] Write `tests/unit/test_tasks.py` covering check arithmetic case by case against the data in force (SC-003): all seven difficulty rungs, all twelve characteristic bands including scores 33, 99, and 4000 in the unbounded top band, `default_difficulty()` returning the sole zero-modifier rung by value not by name (FR-014), the three skill states with `skill=None` untrained and `skill=0` trained at zero (FR-016), modifier order fixed as difficulty, characteristic, skill, situational, `TaskError` for an unknown difficulty whose message lists the valid names (FR-019), `TaskError` for a negative characteristic or negative skill, no automatic success or failure on natural 12 or natural 2 (FR-020), and SC-010 demonstrated by passing an edited `TaskParameters` for the target, a difficulty value, the unskilled DM, and a characteristic band
- [ ] T029 [P] [US2] Hand-write the golden file `tests/golden/check_difficult.txt` for `--difficulty Difficult --characteristic 9 --skill 2 --dm "cover=-2" --seed session-alpha`, matching the worked example in contracts/cli.md, plus `tests/golden/check_unskilled.txt` for a bare `--seed 1` check
- [ ] T030 [US2] Extend `tests/unit/test_render.py` with `as_text` for `CheckResult`: `Check: SUCCESS`/`Check: FAILURE` header, the dice line always carrying `(sum N)`, one four-space-indented line per modifier with labels padded to the longest and values signed including `+0`, `Total: {total} vs target {target}`, and the `Seed:` line
- [ ] T031 [US2] Extend `tests/integration/test_cli.py` for `cetools check`: a failed check exits 0 (FR-032), an unknown difficulty exits 1 with stdout empty, a malformed `--dm` (`cover`, `=-2`, `label=x`) exits 2 as a usage error (FR-017, FR-031), `--dm "a=b=-2"` splits on the last `=` giving label `a=b`, repeated `--dm` preserves supplied order, and `check --help` lists exactly its own options
- [ ] T032 [US2] Extend `tests/integration/test_golden.py` to compare `cetools check` stdout against the files created in T029
- [ ] T033 [US2] Extend `tests/property/test_invariants.py` with check invariants: `total == dice_total + sum(m.value for m in modifiers)` and `success == (total >= target)` hold for every generated combination of difficulty, characteristic, skill, and situational modifiers
- [ ] T034 [US2] Run `uv run pytest` and confirm every test added in T027–T033 fails

### Implementation for User Story 2

- [ ] T035 [US2] Create `src/cetools/data/tasks.toml` exactly as specified in contracts/tasks-toml.md, opening with its Open Game Content designation comment and containing neither "Cepheus Engine" nor "Samardan Press" (FR-021, constitution Licensing constraints)
- [ ] T036 [US2] Implement the frozen slotted `Band` and `TaskParameters` dataclasses in `src/cetools/tasks.py` with `difficulty_dm`, `default_difficulty`, and `characteristic_dm` per data-model.md; the types live here rather than in `rules.py` so that feature 2 replacing the loader does not also replace the types
- [ ] T037 [US2] Implement `src/cetools/rules.py`: `load_task_parameters()` reading the single packaged `tasks.toml` via `importlib.resources` and `tomllib`, wrapped in `functools.cache`, performing exactly the validation table in contracts/tasks-toml.md and raising `RulesDataError` with no fallback; no filesystem search path (FR-023). Keep this module minimal; feature 2 replaces it wholesale
- [ ] T038 [US2] Implement `Modifier`, `CheckResult`, and `check` in `src/cetools/tasks.py`. `check(roller, *, difficulty=None, characteristic=None, skill=None, modifiers=(), parameters=None)` is keyword-only after `roller`; `difficulty=None` resolves through `parameters.default_difficulty()` so no rung name appears in code (FR-014, checklist CHK012); the check's dice come from `parameters.roll` parsed by `parse_notation` (FR-013); labels follow the fixed table in data-model.md
- [ ] T039 [US2] Register `as_text` for `CheckResult` in `src/cetools/render.py`
- [ ] T040 [US2] Add the `check` command to `src/cetools/cli.py` with `--difficulty`, `--characteristic`, `--skill`, repeatable `--dm`, and `--seed`; parse `--dm` by splitting on the last `=`, validating the value against `^[+-]?[0-9]+$` and a non-empty trimmed label, raising `typer.BadParameter` so the failure exits 2 before the library is called (FR-031)
- [ ] T041 [US2] Extend `src/cetools/__init__.py` `__all__` with `Modifier`, `CheckResult`, `TaskParameters`, `Band`, `check`, `load_task_parameters`
- [ ] T042 [US2] Run `uv run pytest` to green, then walk quickstart.md Scenarios 3, 4, 5, 6, 7, and 8 by hand, reverting the `tasks.toml` edit from Scenario 8 afterwards

**Checkpoint**: US1 and US2 both work. The dice roller is now a rules engine, and every SRD value it uses is a data edit away from being house-ruled.

---

## Phase 5: User Story 3 - Consume results from another program (Priority: P3)

**Goal**: Every command renders the same library result as machine-readable JSON with a
committed, stable shape.

**Independent Test**: Run each command in both modes with the same seed and confirm the
JSON parses cleanly and every shared value is identical to the text output.

### Tests for User Story 3 ⚠️ Write first, confirm failing

- [ ] T043 [P] [US3] Write `tests/contract/test_json_contract.py` pinning both payloads from contracts/json-output.md: the exact key set and insertion order, the type of every value, `kind` being `"roll"` and `"check"`, the two arithmetic invariants, and specifically `isinstance(payload["seed"], str)` with a dedicated assertion whose stated purpose is to fail loudly if the type is later "tidied" to `int`
- [ ] T044 [US3] Extend `tests/unit/test_render.py` with `as_dict` and `as_json` for both result types, asserting `json.dumps(..., indent=2, ensure_ascii=False)` formatting and that `as_json` returns a string already carrying its trailing newline
- [ ] T045 [US3] Extend `tests/integration/test_cli.py` with `--json` on both commands: output parses, every value shared with the text mode is identical for the same seed (FR-026), and on an error nothing is written to stdout while the plain-text (not JSON) message goes to stderr (FR-027)
- [ ] T046 [US3] Run `uv run pytest` and confirm every test added in T043–T045 fails

### Implementation for User Story 3

- [ ] T047 [US3] Implement `as_dict` and `as_json` in `src/cetools/render.py` as `singledispatch` generics registered for `ThrowResult` and `CheckResult`, emitting `seed` as a decimal string and every other numeric field as a JSON number
- [ ] T048 [US3] Add the `--json` flag to both commands in `src/cetools/cli.py`, printing `as_json(result)` with `end=""`; errors stay plain text on stderr in both modes, with no JSON error envelope (deliberate, per FR-027)
- [ ] T049 [US3] Extend `src/cetools/__init__.py` `__all__` with `as_dict` and `as_json`
- [ ] T050 [US3] Run `uv run pytest` to green and confirm `cetools roll 2d6 --seed session-alpha --json | python -m json.tool` round-trips

**Checkpoint**: All three stories work. The JSON shape is now a committed public interface (FR-028), and any later change to it is a breaking change.

---

## Phase 6: User Story 4 - Throw a two-digit table die (Priority: P4)

**Goal**: `d66` as a first-class throw that cannot be confused with a 66-sided die.

**Independent Test**: Throw `d66` with a fixed seed and confirm the value is composed of
the two faces as tens and units, that no digit is `0` or above `6`, and that across a
fixed seeded sample of at least 1000 throws all 36 values occur.

### Tests for User Story 4 ⚠️ Write first, confirm failing

- [ ] T051 [P] [US4] Write `tests/unit/test_d66.py` as dedicated coverage per SC-009: `d66(Roller("session-alpha"))` gives `faces == (1, 5)`, `total == 15`, `modifier == 0`, `notation == "d66"`; `parse_notation("d66")` returns `None` (the literal, matched before the general grammar) while `parse_notation("1d66")` returns `(1, 66, 0)`; `D66` is accepted case-insensitively; and a fixed seeded sample of at least 1000 throws covers all 36 values with no digit `0` and none above `6` (FR-012)
- [ ] T052 [P] [US4] Hand-write the golden file `tests/golden/roll_d66.txt` for `cetools roll d66 --seed session-alpha`, matching the worked example in contracts/cli.md
- [ ] T053 [US4] Extend `tests/integration/test_cli.py` and `tests/integration/test_golden.py` for `cetools roll d66`, and `tests/contract/test_json_contract.py` for the `d66` JSON payload where `total` is the composed value rather than a sum and `notation` is what discriminates it (FR-010)
- [ ] T054 [US4] Extend `tests/property/test_invariants.py` with the `d66` invariant that both digits always lie in `1..6` and `total == faces[0] * 10 + faces[1]`
- [ ] T055 [US4] Run `uv run pytest` and confirm every test added in T051–T054 fails

### Implementation for User Story 4

- [ ] T056 [US4] Implement `d66(roller)` in `src/cetools/dice.py` and make `parse_notation` match the `d66` literal case-insensitively *before* the general grammar; route `throw` to `d66` on that literal, and export `d66` from `src/cetools/__init__.py`
- [ ] T057 [US4] Run `uv run pytest` to green and walk quickstart.md Scenario 9, confirming `d66` and `1d66` are different throws

**Checkpoint**: All four user stories are independently functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T058 [P] Audit SC-011 across `tests/`: confirm every capability (seed resolution, throw, `throw_dice`, `d66`, `check`, `load_task_parameters`, all three renderers) is exercised by at least one test that imports the library without invoking the CLI, and add the missing cases to the relevant `tests/unit/` module
- [ ] T059 [P] Add docstrings to every symbol in `src/cetools/__init__.py`'s `__all__`, since Principle I requires library modules to be documented
- [ ] T060 [P] Update `specs/001-dice-task-engine/contracts/library-api.md` so the `check` signature reads `difficulty: str | None = None` resolved via `default_difficulty()`; the file still shows the superseded `= "Average"` default that FR-014 and checklist CHK012 replaced in cli.md and data-model.md
- [ ] T061 [P] Expand `README.md` with installation, the `roll` and `check` examples from contracts/cli.md, and a note that results are reproducible from a seed plus a package version
- [ ] T062 Run `uv run black --check src tests`, `uv run isort --check-only src tests`, and `uv run flake8 src tests`, fixing findings; these are quality tooling and explicitly not a gate on done (Principle III)
- [ ] T063 Walk quickstart.md end to end, all ten scenarios, and confirm each stated expectation, then confirm the full suite is green with `uv run pytest`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies; start immediately
- **Foundational (Phase 2)**: needs Phase 1; blocks every story
- **US1 (Phase 3)**: needs Phase 2. Blocks US2, US3, and US4, because all three consume `Roller`, `ThrowResult`, and `render`
- **US2 (Phase 4)**: needs US1
- **US3 (Phase 5)**: needs US1 for the throw payload and US2 for the check payload
- **US4 (Phase 6)**: needs US1 only. Could be built in parallel with US2 by a second person; T053's JSON extension is the sole point where it touches US3's file
- **Polish (Phase 7)**: needs every story that is being shipped

### User Story Dependencies

The stories are layered, not independent, and the spec says so: US2's "Why this
priority" states it depends on the seeded throw from US1, US3 renders results the other
stories produce, and US4 reuses US1's roller. What each story keeps is independent
*testability*: each has its own test files, its own golden files, and its own
checkpoint that can be validated without the later stories existing.

### Within Each User Story

- Every test task precedes every implementation task in that phase, and the phase's
  "confirm red" task is the gate between them (Principle III, SC-008)
- Golden files (T015, T029, T052) are written by hand before the code that produces the
  text; there is no regeneration flag, deliberately
- Types before the functions that use them: T036 before T037 and T038
- Library before CLI: T020–T022 before T023; T036–T039 before T040
- `__init__.py` export tasks come last in each phase, once the symbols exist

### Parallel Opportunities

- Phase 1: T003 and T004 in parallel after T002
- Phase 2: T006, T007, and T008 in parallel; T009 then T010
- Phase 3: T011–T015, T017, and T018 all in parallel (seven distinct files); T016 waits on T015
- Phase 4: T027, T028, and T029 in parallel; T030–T033 each extend a file US1 created, so they are sequential against those files but independent of one another's content
- Phase 6: T051 and T052 in parallel
- Phase 7: T058–T061 all in parallel; T062 and T063 last
- Across stories: US4 can proceed alongside US2 once US1 is green

---

## Parallel Example: User Story 1

```bash
# Launch the seven independent US1 test files together:
Task: "Write tests/unit/test_seeds.py"                 # T011
Task: "Write tests/unit/test_dice.py"                  # T012
Task: "Write tests/unit/test_render.py"                # T013
Task: "Write tests/integration/test_cli.py"            # T014
Task: "Hand-write tests/golden/roll_2d6_plus1.txt and roll_1d6.txt"  # T015
Task: "Write tests/guards/test_seed_contract.py"       # T017
Task: "Write tests/property/test_invariants.py"        # T018

# Then, after T019 confirms red, implement in dependency order:
# T020 seeds -> T021 dice -> T022 render -> T023 cli -> T024 __main__ -> T025 exports
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1: Setup
2. Phase 2: Foundational
3. Phase 3: User Story 1
4. **STOP and VALIDATE**: quickstart Scenarios 1, 2, and 10. A reproducible seeded dice
   roller is already useful on its own, and the reproducibility guarantee it establishes
   is the one thing in this feature that cannot be retrofitted later.

### Incremental Delivery

1. Setup + Foundational → installable package with a running suite
2. + US1 → reproducible dice roller (MVP)
3. + US2 → rules engine reading SRD parameters from data
4. + US3 → machine-readable output; the JSON shape becomes a committed interface
5. + US4 → `d66` groundwork for post-MVP world and trade generation
6. + Polish

### Parallel Team Strategy

Once US1 is green, one person can take US2 (rules data, check arithmetic, `check`
command) while another takes US4 (`d66`), since they touch different files apart from
T053. US3 needs both to be complete, so it is best done by whoever finishes second.

---

## Notes

- Traps already resolved in the contracts, worth re-reading before implementing:
  `d66` must be matched before the general grammar; `--dm` splits on the **last** `=`;
  a malformed `--dm` is exit 2, not exit 1; `getrandbits(0)` returning `0` is what makes
  a 1-sided die work, so do not special-case it; never pass a `str` to `random.Random`
- Consult the `fluent-python:*` skills named in plan.md's Implementation Notes:
  `choosing-a-data-class-builder`, `designing-function-signatures`,
  `using-functools-and-operator`, `designing-value-objects`
- Commit test tasks and implementation tasks separately, so SC-008's evidence (expected
  values committed before the implementing change) exists in the history
- Golden files are reviewed as diffs; changing one is acceptable only alongside an
  intended behaviour change described in the same commit
