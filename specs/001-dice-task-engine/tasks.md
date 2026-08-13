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

**Expected values**: every literal a test asserts must come from the published table
in contracts/cli.md, not from running the implementation. Two seeds are published:
`session-alpha` (2d6 → `1, 5`) and `1` (2d6 → `2, 5`). If a case needs a seed that is
not in that table, add it to the table first by running the specified algorithm, then
write the test.

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
harness (FR-033) that satisfies the licensing constraints attaching to any distribution
carrying Open Game Content (FR-035).

- [X] T001 Create the directory tree per plan.md: `src/cetools/`, `src/cetools/data/`, `tests/unit/`, `tests/contract/`, `tests/integration/`, `tests/guards/`, `tests/property/`, `tests/golden/`
- [X] T002 Create `pyproject.toml` at repository root: `hatchling` build backend, `requires-python = ">=3.13"`, CalVer `version = "2026.08.1"`, `dependencies = ["typer"]`, dev dependency group (`pytest`, `hypothesis`, `black`, `isort`, `flake8`), `[project.scripts] cetools = "cetools.cli:main"`, `license-files = ["LICENSE", "LICENSE-OGL.txt"]` so **both** licenses land in the wheel and the sdist (FR-035), hatch wheel target packaging `src/cetools` including `data/tasks.toml`, `[tool.black]`, `[tool.isort] profile = "black"`, `[tool.pytest.ini_options] testpaths = ["tests"]`
- [X] T003 [P] Create `.flake8` at repository root with `max-line-length` matching Black's `line-length` and `extend-ignore = E203` so flake8 agrees with Black (flake8 cannot read `pyproject.toml`, per research.md R13). The figure was settled at `99` during implementation, and plan.md and research.md were amended to match by T075
- [X] T004 [P] Add the licensing artifacts at repository root (FR-035, constitution Licensing & Distribution Constraints): `LICENSE` with the full GPL-3.0 text covering the code; `LICENSE-OGL.txt` with the full OGL 1.0a text plus the SRD's complete Section 15 copyright-notice chain **verbatim**, extended with this project's own game-data copyright line; and a minimal `README.md` stating the project purpose, the `uv sync` / `uv run pytest` workflow, and a short licensing section naming `src/cetools/data/tasks.toml` as the sole Open Game Content file with everything else under GPL-3.0. The README makes **no compatibility claim**, so it owes no trademark attribution; if a later edit adds such a claim, the attribution and non-affiliation statement come with it in the same change. Only the published-package work (PyPI description, published compatibility statement, release process) is out of scope here
- [X] T005 [P] Create `.github/workflows/ci.yml` running `uv sync` then `uv run pytest` on a matrix of every Python version in `requires-python` (3.13, 3.14) across `ubuntu-latest`, `macos-latest`, and `windows-latest`. This is what discharges FR-007 and SC-001's cross-platform clause: without it, the cross-version reproducibility claim rests on a one-off manual check that nothing re-runs (research.md R15)
- [X] T006 Run `uv sync` then `uv run pytest`, confirming the environment builds and the suite is invocable. **`pytest` exits 5 here, not 0**, because no tests have been collected yet; exit 5 is the expected result at this point and the first real pass comes at T012

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The error taxonomy and package skeleton every story raises through and
imports from, plus the licensing guard that keeps the constitution's constraints from
being quietly undone by a later edit.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T007 [P] Write `tests/unit/test_errors.py` asserting the hierarchy in data-model.md: `DiceError`, `RulesDataError`, and `TaskError` each subclass `CetoolsError`, `CetoolsError` subclasses `Exception`, and all four are importable from `cetools`
- [X] T008 [P] Write `tests/unit/test_licensing.py` covering the distribution half of SC-012: `LICENSE` and `LICENSE-OGL.txt` both exist at the repository root and are non-empty; `LICENSE-OGL.txt` contains the OGL 1.0a title and a Section 15 heading; `pyproject.toml` lists both in `license-files` so neither can be dropped from a build; and `README.md` contains the OGC/GPL designation. The data-file half is added in T031 once `tasks.toml` exists
- [X] T009 [P] Create `tests/conftest.py` with shared fixtures: a `Roller` seeded to a fixed literal, the repository-root path, and a helper that reads a file from `tests/golden/`. The rules-data cache fixture is added in T029, once there is a cache to clear
- [X] T010 [P] Create `src/cetools/data/__init__.py` (empty) so the data directory is an importable package readable through `importlib.resources.files("cetools.data")`
- [X] T011 Create `src/cetools/errors.py` defining `CetoolsError`, `DiceError`, `RulesDataError`, `TaskError` with docstrings naming the conditions each covers; the library raises these and never prints or exits (FR-029)
- [X] T012 Create `src/cetools/__init__.py` re-exporting the four error types with an explicit `__all__`, which grows in each story phase and is the public contract (contracts/library-api.md)

**Checkpoint**: `uv run pytest tests/unit/` passes; `python -c "import cetools"` resolves against the installed package.

---

## Phase 3: User Story 1 - Throw dice reproducibly (Priority: P1) 🎯 MVP

**Goal**: Seeded, cross-version-reproducible dice throws, described by notation, exposed
as library API and as `cetools roll` with human-readable output and a seed in every
result.

**Independent Test**: `cetools roll 2d6` with no seed, note the reported seed, run again
with `--seed <that seed>`, confirm faces and total are byte-identical. Repeat in a
separate process and under a different `PYTHONHASHSEED` with a text seed.

### Tests for User Story 1 ⚠️ Write first, confirm failing

- [X] T013 [P] [US1] Write `tests/unit/test_seeds.py` covering seed resolution (research.md R1, R4, R5): `None` draws 64 bits from `secrets`; an `int` passes through unchanged including a negative and a value above 2^64; a string matching `^[+-]?[0-9]+$` becomes that integer including a signed one; any other string folds via blake2b-64 over UTF-8 big-endian with the literal expected value `resolve_seed("session-alpha") == 14333185781139156525`; case, surrounding whitespace, and NFC vs NFD forms of the same accented text each resolve to *different* seeds (FR-003)
- [X] T014 [P] [US1] Write `tests/unit/test_dice.py` covering `parse_notation` (`2d6`, `d6`, `2D6+1`, `3d6 - 2`, `1d100`, `1d66`; rejects `7dQ`, `0d6`, `2d0`, `""`), `Roller.die`/`Roller.dice` including `sides=1` returning face `1` via `getrandbits(0)`, and `throw`/`throw_dice` with literal expected values from the published table in contracts/cli.md: `throw(Roller("session-alpha"), "2d6+1")` gives `faces == (1, 5)`, `modifier == 1`, `total == 7`, `notation == "2d6+1"`, `seed == 14333185781139156525`; plus FR-012 exhaustive coverage, that a fixed seeded sample of at least 1000 `d6` faces contains all six values; plus `DiceError` for every rejected input (FR-011); plus **FR-008 roller independence**: two `Roller`s built in the same process, drawn from alternately, each yield exactly the sequence they yield when drawn from alone, so neither consumes the other's stream
- [X] T015 [P] [US1] Write `tests/unit/test_render.py` covering `as_text` for `ThrowResult` per the rendering rules in contracts/cli.md: header `{notation} = {total}`, `(sum N)` and the `Modifier:` line present only when `modifier != 0`, `Seed:` always present, labels padded to the longest label actually present, trailing newline
- [X] T016 [P] [US1] Write `tests/integration/test_cli.py` using Typer's `CliRunner` for `cetools roll`: successful throw exits 0 with output on stdout, bad notation exits 1 with the message on stderr and stdout empty, an unknown option exits 2, `--version` prints the package version and exits 0, and `roll --help` lists exactly `NOTATION`, `--seed`, `--json` and no check-only options (FR-025); plus the **SC-004 round trip**, which is the feature's load-bearing promise and must be automated rather than left to the quickstart: run with no `--seed`, parse the reported seed out of the output, run again supplying it, and assert the two outputs are byte-identical
- [X] T017 [P] [US1] Hand-write the golden files `tests/golden/roll_2d6_plus1.txt` and `tests/golden/roll_1d6.txt` for `--seed session-alpha`, spelling out the expected rendered text from the published values (`2d6+1` → faces `1, 5`, total `7`; `1d6` → face `1`, total `1`); no regeneration flag is provided, deliberately (quickstart.md)
- [X] T018 [US1] Write `tests/integration/test_golden.py` comparing `cetools roll` stdout byte-for-byte against the files created in T017
- [X] T019 [P] [US1] Write `tests/guards/test_seed_contract.py` with both guards from research.md R12: guard A captures `random.getstate()`, runs a full CLI invocation, and asserts the state is bit-for-bit unchanged (SC-005); guard B runs `python -m cetools roll 2d6 --seed session-alpha` in two subprocesses with `PYTHONHASHSEED=1` and `PYTHONHASHSEED=2` and asserts byte-identical output (SC-002)
- [X] T020 [P] [US1] Write `tests/property/test_invariants.py` with hypothesis invariants for throws: every face lies in `1..sides`, `len(faces) == count`, `total == sum(faces) + modifier`, and the same seed with the same arguments always yields an equal result (FR-006)
- [X] T021 [US1] Run `uv run pytest` and confirm every test added in T013–T020 fails, recording the red state required by Principle III and SC-008

### Implementation for User Story 1

- [X] T022 [US1] Implement `src/cetools/seeds.py`: `resolve_seed(seed: int | str | None) -> int` applying the four-case table in data-model.md, with the digit-string regex and the blake2b-64 UTF-8 big-endian fold each in exactly one place
- [X] T023 [US1] Implement `src/cetools/dice.py`: `Roller` (constructed via `resolve_seed`, holding a private `random.Random` seeded only with an `int`, `die` using rejection sampling on `getrandbits` per research.md R3, `dice` returning a tuple in draw order, raising `DiceError` on a count or side count below 1), the frozen slotted `ThrowResult` dataclass, `parse_notation`, `throw`, and `throw_dice`
- [X] T024 [US1] Implement `src/cetools/render.py`: `as_text` as a `functools.singledispatch` generic with a `ThrowResult` registration, following the rendering rules pinned by T017's golden files
- [X] T025 [US1] Implement `src/cetools/cli.py`: the Typer app, `main()`, the `roll` command taking `NOTATION` and `--seed`, the top-level `--version` eager option (FR-025), results printed to stdout, and the single `except CetoolsError` site writing the message to stderr and exiting 1 (FR-030); usage errors are left to Typer, which already exits 2
- [X] T026 [US1] Implement `src/cetools/__main__.py` so `python -m cetools` invokes `cli.main()`, which guard test B in T019 requires
- [X] T027 [US1] Extend `src/cetools/__init__.py` `__all__` with `Roller`, `ThrowResult`, `parse_notation`, `throw`, `throw_dice`, `as_text`
- [X] T028 [US1] Run `uv run pytest` to green, then walk quickstart.md Scenarios 1, 2, and 10 by hand and confirm each expected result

**Checkpoint**: US1 is complete and independently useful. A referee has a reproducible dice roller; the reproducibility contract that cannot be retrofitted is now established, guarded, and re-checked on every supported platform by T005's matrix.

---

## Phase 4: User Story 2 - Resolve a task check (Priority: P2)

**Goal**: `cetools check` resolves a 2D6 task against SRD parameters held in
`tasks.toml`, itemizing every modifier with its label.

**Independent Test**: Resolve a check at each named difficulty with a fixed seed;
confirm `target` never moves, faces are identical across all seven, and totals step by
2 from `Simple` to `Formidable`. Confirm the itemized modifiers sum to the difference
between the dice total and the final total.

### Tests for User Story 2 ⚠️ Write first, confirm failing

- [X] T029 [P] [US2] Write `tests/unit/test_rules.py` against the loader seam in contracts/library-api.md, and add to `tests/conftest.py` an autouse fixture calling `load_task_parameters.cache_clear()` so no test leaks cached data into the next. Cover: `load_task_parameters()` reads the shipped file through `importlib.resources.files("cetools.data")` and yields the expected target, unskilled DM, roll notation, seven-rung ladder in file order, and twelve bands; every `RulesDataError` path from contracts/tasks-toml.md driven through `_task_parameters_from_toml` with fixture text (missing table, non-integer value, unparseable `task.roll`, malformed band key, zero or several unbounded bands, zero or several zero-modifier rungs, invalid TOML), each asserting no silent fallback to built-in values (FR-024); the missing-and-unreadable-file cases through the public function by pointing `importlib.resources` at an absent resource; **SC-010 through the real loader** by feeding `_task_parameters_from_toml` a *valid* edited file whose target, a difficulty value, the unskilled DM, and a band bound all differ, and asserting the parsed values follow, including the structural edits FR-022 names (a renamed rung, an added rung, an altered band bound); and **FR-023** by placing a decoy `tasks.toml` in the working directory and asserting the loaded values are still the packaged ones
- [X] T030 [P] [US2] Write `tests/unit/test_tasks.py` covering check arithmetic case by case against the data in force (SC-003): all seven difficulty rungs, all twelve characteristic bands including scores 33, 99, and 4000 in the unbounded top band, `default_difficulty()` returning the sole zero-modifier rung by value not by name (FR-014), the three skill states with `skill=None` untrained and `skill=0` trained at zero (FR-016), modifier order fixed as difficulty, characteristic, skill, situational, `TaskError` for an unknown difficulty whose message lists the valid names (FR-019), `TaskError` for a negative characteristic or negative skill, no automatic success or failure on natural 12 or natural 2 (FR-020), and SC-010 also demonstrated at the API level by passing an edited `TaskParameters`
- [X] T031 [P] [US2] Extend `tests/unit/test_licensing.py` with the data-file half of SC-012: the packaged `tasks.toml`, read through `importlib.resources` rather than off disk, opens with its Open Game Content designation and contains neither `"Cepheus Engine"` nor `"Samardan Press"` (FR-021, constitution Licensing & Distribution Constraints). A later data edit that reintroduces either string now fails the suite instead of shipping
- [X] T032 [P] [US2] Hand-write the golden file `tests/golden/check_difficult.txt` for `--difficulty Difficult --characteristic 9 --skill 2 --dm "cover=-2" --seed session-alpha`, matching the worked example in contracts/cli.md, plus `tests/golden/check_unskilled.txt` for a bare `--seed 1` check, whose expected content is derived from the published table: dice `2, 5` (sum `7`), `Difficulty (Average) +0`, `Unskilled -3`, `Total: 4 vs target 8`, FAILURE
- [X] T033 [US2] Extend `tests/unit/test_render.py` with `as_text` for `CheckResult`: `Check: SUCCESS`/`Check: FAILURE` header, the dice line always carrying `(sum N)`, one four-space-indented line per modifier with labels padded to the longest and values signed including `+0`, `Total: {total} vs target {target}`, and the `Seed:` line
- [X] T034 [US2] Extend `tests/integration/test_cli.py` for `cetools check`: a failed check exits 0 (FR-032), an unknown difficulty exits 1 with stdout empty, a malformed `--dm` (`cover`, `=-2`, `label=x`) exits 2 as a usage error (FR-017, FR-031), `--dm "a=b=-2"` splits on the last `=` giving label `a=b`, repeated `--dm` preserves supplied order, `check --help` lists exactly its own options, and the SC-004 round trip holds for `check` as it does for `roll`
- [X] T035 [US2] Extend `tests/integration/test_golden.py` to compare `cetools check` stdout against the files created in T032
- [X] T036 [US2] Extend `tests/property/test_invariants.py` with check invariants: `total == dice_total + sum(m.value for m in modifiers)` and `success == (total >= target)` hold for every generated combination of difficulty, characteristic, skill, and situational modifiers
- [X] T037 [US2] Run `uv run pytest` and confirm every test added in T029–T036 fails

### Implementation for User Story 2

- [X] T038 [US2] Create `src/cetools/data/tasks.toml` exactly as specified in contracts/tasks-toml.md, opening with its Open Game Content designation comment pointing at `LICENSE-OGL.txt` (which T004 created, so the reference resolves) and containing neither "Cepheus Engine" nor "Samardan Press" (FR-021, FR-035)
- [X] T039 [US2] Implement the frozen slotted `Band` and `TaskParameters` dataclasses in `src/cetools/tasks.py` with `difficulty_dm`, `default_difficulty`, and `characteristic_dm` per data-model.md; the types live here rather than in `rules.py` so that feature 2 replacing the loader does not also replace the types
- [X] T040 [US2] Implement `src/cetools/rules.py` as the two-function seam from contracts/library-api.md: `_task_parameters_from_toml(text)` holds the `tomllib` parse and the entire validation table from contracts/tasks-toml.md, raising `RulesDataError` with no fallback; `load_task_parameters()` reads the single packaged `tasks.toml` via `importlib.resources`, hands the text to it, and is wrapped in `functools.cache`. No filesystem search path (FR-023). Keep this module minimal; feature 2 replaces it wholesale
- [X] T041 [US2] Implement `Modifier`, `CheckResult`, and `check` in `src/cetools/tasks.py`. `check(roller, *, difficulty=None, characteristic=None, skill=None, modifiers=(), parameters=None)` is keyword-only after `roller`; `difficulty=None` resolves through `parameters.default_difficulty()` so no rung name appears in code (FR-014, checklist CHK012); the check's dice come from `parameters.roll` parsed by `parse_notation` (FR-013); labels follow the fixed table in data-model.md
- [X] T042 [US2] Register `as_text` for `CheckResult` in `src/cetools/render.py`
- [X] T043 [US2] Add the `check` command to `src/cetools/cli.py` with `--difficulty`, `--characteristic`, `--skill`, repeatable `--dm`, and `--seed`; parse `--dm` by splitting on the last `=`, validating the value against `^[+-]?[0-9]+$` and a non-empty trimmed label, raising `typer.BadParameter` so the failure exits 2 before the library is called (FR-031)
- [X] T044 [US2] Extend `src/cetools/__init__.py` `__all__` with `Modifier`, `CheckResult`, `TaskParameters`, `Band`, `check`, `load_task_parameters`. `_task_parameters_from_toml` is **not** exported; it is internal by contract
- [X] T045 [US2] Run `uv run pytest` to green, then walk quickstart.md Scenarios 3, 4, 5, 6, 7, and 8 by hand, reverting the `tasks.toml` edit from Scenario 8 afterwards

**Checkpoint**: US1 and US2 both work. The dice roller is now a rules engine, every SRD value it uses is a data edit away from being house-ruled, and that claim is verified through the real loader rather than only at the API boundary.

---

## Phase 5: User Story 3 - Consume results from another program (Priority: P3)

**Goal**: Every command renders the same library result as machine-readable JSON with a
committed, stable shape.

**Independent Test**: Run each command in both modes with the same seed and confirm the
JSON parses cleanly and every shared value is identical to the text output.

### Tests for User Story 3 ⚠️ Write first, confirm failing

- [X] T046 [P] [US3] Write `tests/contract/test_json_contract.py` pinning both payloads from contracts/json-output.md: the exact key set and insertion order, the type of every value, `kind` being `"roll"` and `"check"`, the two arithmetic invariants, and specifically `isinstance(payload["seed"], str)` with a dedicated assertion whose stated purpose is to fail loudly if the type is later "tidied" to `int`
- [X] T047 [US3] Extend `tests/unit/test_render.py` with `as_dict` and `as_json` for both result types, asserting `json.dumps(..., indent=2, ensure_ascii=False)` formatting and that `as_json` returns a string already carrying its trailing newline
- [X] T048 [US3] Extend `tests/integration/test_cli.py` with `--json` on both commands: output parses, every value shared with the text mode is identical for the same seed (FR-026), and on an error nothing is written to stdout while the plain-text (not JSON) message goes to stderr (FR-027)
- [X] T049 [US3] Run `uv run pytest` and confirm every test added in T046–T048 fails

### Implementation for User Story 3

- [X] T050 [US3] Implement `as_dict` and `as_json` in `src/cetools/render.py` as `singledispatch` generics registered for `ThrowResult` and `CheckResult`, emitting `seed` as a decimal string and every other numeric field as a JSON number
- [X] T051 [US3] Add the `--json` flag to both commands in `src/cetools/cli.py`, printing `as_json(result)` with `end=""`; errors stay plain text on stderr in both modes, with no JSON error envelope (deliberate, per FR-027)
- [X] T052 [US3] Extend `src/cetools/__init__.py` `__all__` with `as_dict` and `as_json`
- [X] T053 [US3] Run `uv run pytest` to green and confirm `cetools roll 2d6 --seed session-alpha --json | python -m json.tool` round-trips

**Checkpoint**: All three stories work. The JSON shape is now a committed public interface (FR-028), and any later change to it is a breaking change.

---

## Phase 6: User Story 4 - Throw a two-digit table die (Priority: P4)

**Goal**: `d66` as a first-class throw that cannot be confused with a 66-sided die.

**Independent Test**: Throw `d66` with a fixed seed and confirm the value is composed of
the two faces as tens and units, that no digit is `0` or above `6`, and that across a
fixed seeded sample of at least 1000 throws all 36 values occur.

### Tests for User Story 4 ⚠️ Write first, confirm failing

- [X] T054 [P] [US4] Write `tests/unit/test_d66.py` as dedicated coverage per SC-009: `d66(Roller("session-alpha"))` gives `faces == (1, 5)`, `total == 15`, `modifier == 0`, `notation == "d66"`; `parse_notation("d66")` returns `None` (the literal, matched before the general grammar) while `parse_notation("1d66")` returns `(1, 66, 0)`; `D66` is accepted case-insensitively; and a fixed seeded sample of at least 1000 throws covers all 36 values with no digit `0` and none above `6` (FR-012)
- [X] T055 [P] [US4] Hand-write the golden file `tests/golden/roll_d66.txt` for `cetools roll d66 --seed session-alpha`, matching the worked example in contracts/cli.md
- [X] T056 [US4] Extend `tests/integration/test_cli.py` and `tests/integration/test_golden.py` for `cetools roll d66`, and `tests/contract/test_json_contract.py` for the `d66` JSON payload where `total` is the composed value rather than a sum and `notation` is what discriminates it (FR-010)
- [X] T057 [US4] Extend `tests/property/test_invariants.py` with the `d66` invariant that both digits always lie in `1..6` and `total == faces[0] * 10 + faces[1]`
- [X] T058 [US4] Run `uv run pytest` and confirm every test added in T054–T057 fails

### Implementation for User Story 4

- [X] T059 [US4] Implement `d66(roller)` in `src/cetools/dice.py` and make `parse_notation` match the `d66` literal case-insensitively *before* the general grammar; route `throw` to `d66` on that literal, and export `d66` from `src/cetools/__init__.py`
- [X] T060 [US4] Run `uv run pytest` to green and walk quickstart.md Scenario 9, confirming `d66` and `1d66` are different throws

**Checkpoint**: All four user stories are independently functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T061 [P] Audit SC-011 across `tests/`: confirm every capability (seed resolution, throw, `throw_dice`, `d66`, `check`, `load_task_parameters`, all three renderers) is exercised by at least one test that imports the library without invoking the CLI, and add the missing cases to the relevant `tests/unit/` module
- [X] T062 [P] Add docstrings to every symbol in `src/cetools/__init__.py`'s `__all__`, since Principle I requires library modules to be documented
- [X] T063 [P] Expand `README.md` with installation, the `roll` and `check` examples from contracts/cli.md, and a note that results are reproducible from a seed plus a package version. Keep the licensing section T004 added, and keep the file free of compatibility claims unless the trademark attribution and non-affiliation statement are added in the same change (FR-035)
- [X] T064 Run `uv run black --check src tests`, `uv run isort --check-only src tests`, and `uv run flake8 src tests`, fixing findings; these are quality tooling and explicitly not a gate on done (Principle III)
- [X] T065 Build the distribution with `uv build` and confirm the sdist and wheel both carry `LICENSE` and `LICENSE-OGL.txt` and that the wheel contains `cetools/data/tasks.toml` (FR-035, SC-012). This is the one check that exercises the built artifact rather than the source tree
- [X] T066 Walk quickstart.md end to end, all eleven scenarios, and confirm each stated expectation, then confirm the full suite is green with `uv run pytest` and that T005's CI matrix is green on every supported version and platform

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies; start immediately
- **Foundational (Phase 2)**: needs Phase 1; blocks every story
- **US1 (Phase 3)**: needs Phase 2. Blocks US2, US3, and US4, because all three consume `Roller`, `ThrowResult`, and `render`
- **US2 (Phase 4)**: needs US1
- **US3 (Phase 5)**: needs US1 for the throw payload and US2 for the check payload
- **US4 (Phase 6)**: needs US1 only. Could be built in parallel with US2 by a second person; T056's JSON extension is the sole point where it touches US3's file
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
- Golden files (T017, T032, T055) are written by hand before the code that produces the
  text, from the published values in contracts/cli.md; there is no regeneration flag,
  deliberately
- Types before the functions that use them: T039 before T040 and T041
- Library before CLI: T022–T024 before T025; T039–T042 before T043
- `__init__.py` export tasks come last in each phase, once the symbols exist

### Parallel Opportunities

- Phase 1: T003, T004, and T005 in parallel after T002
- Phase 2: T007, T008, T009, and T010 in parallel; T011 then T012
- Phase 3: T013–T017, T019, and T020 all in parallel (seven distinct files); T018 waits on T017
- Phase 4: T029, T030, T031, and T032 in parallel; T033–T036 each extend a file US1 created, so they are sequential against those files but independent of one another's content
- Phase 6: T054 and T055 in parallel
- Phase 7: T061–T063 all in parallel; T064, T065, T066 last and in that order
- Across stories: US4 can proceed alongside US2 once US1 is green

---

## Parallel Example: User Story 1

```bash
# Launch the seven independent US1 test files together:
Task: "Write tests/unit/test_seeds.py"                 # T013
Task: "Write tests/unit/test_dice.py"                  # T014
Task: "Write tests/unit/test_render.py"                # T015
Task: "Write tests/integration/test_cli.py"            # T016
Task: "Hand-write tests/golden/roll_2d6_plus1.txt and roll_1d6.txt"  # T017
Task: "Write tests/guards/test_seed_contract.py"       # T019
Task: "Write tests/property/test_invariants.py"        # T020

# Then, after T021 confirms red, implement in dependency order:
# T022 seeds -> T023 dice -> T024 render -> T025 cli -> T026 __main__ -> T027 exports
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

1. Setup + Foundational → installable, correctly licensed package with a running suite
2. + US1 → reproducible dice roller (MVP)
3. + US2 → rules engine reading SRD parameters from data
4. + US3 → machine-readable output; the JSON shape becomes a committed interface
5. + US4 → `d66` groundwork for post-MVP world and trade generation
6. + Polish

### Parallel Team Strategy

Once US1 is green, one person can take US2 (rules data, check arithmetic, `check`
command) while another takes US4 (`d66`), since they touch different files apart from
T056. US3 needs both to be complete, so it is best done by whoever finishes second.

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
  intended behavior change described in the same commit
- Every literal expected value comes from the published table in contracts/cli.md. If a
  test needs a seed that is not in that table, extend the table first by running the
  specified algorithm; never read an expected value off a run of the implementation

---

## Phase 8: Convergence

**Purpose**: Close the gaps found by `/speckit-converge` on 2026-08-12 between the
artifacts and the code as it now stands. The suite is green at 158 passing tests and
all four stories function; what follows is what the artifacts still call for and the
code does not yet do. Test-first (Principle III) applies to these tasks as it does to
every other, so each behavior change gets its failing test first.

- [X] T067 **CRITICAL** Resolve the compatibility claim in `README.md` per FR-035 and the constitution's Licensing & Distribution Constraints (contradicts). The opening line, "A dice and task-check engine for Cepheus Engine SRD-based games", claims compatibility with the source rules while the file carries neither the Compatibility-Statement License attribution ("Cepheus Engine and Samardan Press are the trademarks of Jason 'Flynn' Kemp") nor a statement of non-affiliation. plan.md's Constitution Check records that this feature "takes the second route and says only what the tool does", and T063 required the file to stay free of such claims unless the attribution arrived in the same change. Take one route explicitly: either drop the claim (e.g. describe it as a 2D6 SRD-derived task-check engine without naming the trademark) or add both the attribution and the non-affiliation statement. Then add the guard to `tests/unit/test_licensing.py` that was missing — assert that if `README.md` mentions "Cepheus Engine" it also carries the attribution and the non-affiliation statement — so the same regression cannot ship silently a second time. **Done**: the first route was taken, matching plan.md's recorded decision. `README.md` now opens "A dice and task-check engine for SRD-derived 2D6 roleplaying rules", and the `pyproject.toml` `description` was corrected the same way, since it is text this feature writes and it carried the identical unattributed claim (the *published* compatibility statement remains `packaging-release`'s). The guard in `tests/unit/test_licensing.py` covers both surfaces: naming the trademark without the attribution *and* a statement of non-affiliation now fails the suite
- [X] T068 Reject a `task.roll` value that is not a count-and-sides throw, per FR-029 (partial; also FR-024 and FR-030). `_task_parameters_from_toml` in `src/cetools/rules.py` calls `parse_notation(roll)` only to see whether it raises and discards the return value, so the `d66` literal (which returns `None`) validates cleanly; `check` in `src/cetools/tasks.py` then executes `count, sides, roll_modifier = parse_notation(parameters.roll)` and dies with `TypeError: cannot unpack non-iterable NoneType object`. FR-029 requires every condition the library detects to be raised as a `CetoolsError` descendant, and the CLI's single `except CetoolsError` site does not catch `TypeError`, so the user gets a traceback instead of a message on stderr and exit 1. Add the failing test to `tests/unit/test_rules.py` first, then have the loader raise `RulesDataError` when `parse_notation` returns `None`, naming `task.roll` and why `d66` cannot describe a check's dice. **Done**: `_task_parameters_from_toml` now keeps `parse_notation`'s return value and raises `RulesDataError` when it is `None`
- [X] T069 Make the packaging guarantee real, per SC-012 and plan.md's Structure Decision (partial). plan.md justifies the `src/` layout on the grounds that "if packaging fails to include `tasks.toml`, the test suite fails rather than silently reading it off disk", and SC-012 requires the data file to be checked "as read from the installed package". `uv sync` installs editable, so `importlib.resources.files("cetools.data")` resolves to `src/cetools/data/tasks.toml` in the working tree and both guarantees are nominal: a wheel target that stopped including `data/tasks.toml` would leave all 158 tests green. T065 catches it, but T065 is a manual step and SC-012 asks for an automated check rather than inspection. Add a test that builds or inspects the distribution — assert the wheel contains `cetools/data/tasks.toml` and that both `LICENSE` and `LICENSE-OGL.txt` (with its Section 15 chain) are in it — marked slow if the build cost warrants it. **Done**: `tests/guards/test_packaging.py` builds the wheel with `uv build --wheel` into a module-scoped temporary directory and inspects it with `zipfile`, asserting `cetools/data/tasks.toml` is present and still carries its Open Game Content designation, and that both licenses are under `.dist-info/licenses/` with the OGL's Section 15 chain intact. No slow marker: the build takes about 0.3s, so gating it behind a marker would only make the guarantee nominal again. The test skips, rather than failing, when `uv` is not on `PATH`
- [X] T070 Normalize spelling to American English across the repository, per the user directive of 2026-08-12 (contradicts). **Done in this pass**: 66 corrections over 15 files — `CHANGELOG.md`, `CONTRIBUTING.md`, `src/cetools/cli.py` (the user-visible `--dm` help text), `src/cetools/tasks.py`, and every `specs/001-dice-task-engine/` artifact including this file. The word families corrected were the `-our`/`-or`, `-ise`/`-ize`, `-ce`/`-se`, doubled-`l`, and `artefact`/`artifact` pairs. Two exclusions are deliberate and must survive any future sweep: `LICENSE` and `LICENSE-OGL.txt` are verbatim third-party license text the GPL and the OGL require be reproduced unaltered, and `wayfinder/` contains only the proper noun *Traveller*, which is a trademark and not a spelling. The convention now governs everything written here — prose, docstrings, identifiers, and Spec Kit artifacts alike
- [X] T071 Review or justify `CHANGELOG.md` and `CONTRIBUTING.md`, per FR-028 (unrequested). FR-028 states plainly that "the changelog itself is created by the packaging and release feature rather than this one", and no task in Phases 1-7 called for either file; `README.md` now links to both. Neither is harmful and both are referenced by T067's and T070's targets, so this is a scope decision rather than a defect: either record them as a deliberate early delivery (and note in the packaging-release spec that they already exist) or move them to that feature. Do not delete either without confirming the call, since `README.md` and `CONTRIBUTING.md` cross-reference the licensing rules T067 touches. **Resolved (user decision, 2026-08-12)**: both files are kept as a deliberate early delivery, recorded in plan.md's post-convergence re-check. `CONTRIBUTING.md` carries the licensing constraints on new files that T067's repair depends on contributors knowing, so deferring it would remove guidance the repository is currently relying on. `packaging-release` inherits both files and extends them; its spec must not restate them as new deliverables

---

## Phase 9: Convergence

**Purpose**: Close the gaps found by the second `/speckit-converge` run on 2026-08-12.
The suite is green at 164 passing tests, all four stories function, no constitution
MUST principle is violated, and the Phase 8 repairs all hold. What follows is
verification the artifacts call for and the suite does not yet perform, plus one
toolchain value that diverged from the plan. Test-first (Principle III) applies here
as everywhere else: each of these *is* a test, so write it, watch it fail against the
gap it names, and only then close it.

- [X] T072 Cover the five untested characteristic bands per SC-003 (partial). `test_characteristic_bands_including_unbounded_top` in `tests/unit/test_tasks.py` parametrizes thirteen scores, but they land in only seven of the twelve bands the shipped `tasks.toml` holds: `0-2`, `3-5`, `6-8`, `9-11`, `12-14`, `30-32`, and `33+`. The five bands in the middle of the curve — `15-17` (+3), `18-20` (+4), `21-23` (+5), `24-26` (+6), and `27-29` (+7) — have no case at all, so a transcription error in any of them, or an off-by-one in `characteristic_dm`'s boundary comparison across that stretch, would ship green. SC-003 requires the arithmetic to be verified "for every difficulty entry and every characteristic band that data contains", and names twelve as the case count for the shipped suite; T030 said "all twelve" and the suite delivers seven. Add a case for each missing band, testing both bounds where a boundary is the thing at risk, so the parametrized list walks the whole table rather than its ends. The seven-rung ladder is already fully covered by `test_difficulty_ladder_steps_by_two_with_fixed_dice_and_target`, so this is the only half of SC-003 outstanding. **Done**: `test_characteristic_bands_including_unbounded_top` now parametrizes both bounds of all twelve bands, 25 cases, so the list walks the whole table rather than its ends. That closes the off-by-one half. The transcription half needed a second test, because the parametrized one builds its bands as a local constant and so cannot see the shipped file at all: `test_packaged_bands_match_the_published_table_in_full` in `tests/unit/test_rules.py` reads through `load_task_parameters()` and compares all twelve `(minimum, maximum, dm)` triples, where the existing coverage checked only `len() == 12` and the first and last band. Verified to bite by changing `"18-20"` in the shipped `tasks.toml` from `4` to `5`, which fails that test and nothing else
- [X] T073 Make the seed round trip actually assert the round trip, per SC-004 and FR-006 (partial). `test_roll_seed_round_trip_is_byte_identical` and `test_check_seed_round_trip_is_byte_identical` in `tests/integration/test_cli.py` each run the command with no `--seed`, parse the reported seed out of the output, run twice more supplying it, and then assert the *second and third* runs match. `first.stdout` is never compared to anything. What that asserts is only that a given explicit seed is deterministic — which the property tests already cover — and not the promise SC-004 actually makes, that "every rendered result ... includes a seed that reproduces that result when supplied back". An implementation that reported a seed unrelated to the dice it had just thrown would pass both tests unchanged. T016 and T034 spelled the assertion out: "run again supplying it, and assert the two outputs are byte-identical". Assert `first.stdout == second.stdout` in both tests, keeping the third run if a separate determinism assertion is wanted. This is the feature's load-bearing promise and it is currently the one thing in the suite not tested. **Done**: both tests now assert `first.stdout == second.stdout`, with the second-against-third comparison kept as the separate determinism assertion it always was. Verified to bite by making `roll` report a seed unrelated to its throw (`dataclasses.replace(..., seed=12345)`), which fails the new assertion while leaving the old one green, exactly the implementation the gap described
- [X] T074 Extend the packaging guard to the sdist, per SC-012 and the constitution's Licensing & Distribution Constraints (partial). `tests/guards/test_packaging.py` builds a wheel with `uv build --wheel` and inspects it, which is what T069 delivered, but the constitution's bundling clause is written against "**every distribution (sdist and wheel)**" and T065 checked both by hand. The sdist is therefore promised and unguarded: a later edit dropping `LICENSE-OGL.txt` from `[tool.hatch.build.targets.sdist].include` would leave the whole suite green. Confirmed by inspection during this convergence run that the sdist as built today does carry `LICENSE`, `LICENSE-OGL.txt`, and `src/cetools/data/tasks.toml`, so this is an unguarded guarantee rather than a live violation — which is exactly the state T069 existed to end for the wheel. Add an sdist fixture alongside the wheel one (`uv build --sdist`, read with `tarfile`) and assert the same three things: the rules data is present and still carries its Open Game Content designation, and both licenses are present with the OGL's Section 15 chain intact. Keep the existing skip-when-`uv`-is-absent behavior. **Done**: `tests/guards/test_packaging.py` now builds both artifacts through a shared `_build` helper that keeps the skip-when-`uv`-is-absent behavior, with a module-scoped `sdist` fixture reading the tarball via `tarfile` alongside the existing `wheel` one, and three matching assertions per artifact. Members are matched with the leading `{name}-{version}/` prefix stripped, so the test does not hard-code the version. One finding while verifying: dropping `LICENSE-OGL.txt` from `[tool.hatch.build.targets.sdist].include` does **not** remove it from the sdist, because hatchling ships `[project] license-files` into both artifacts regardless, so that `include` entry is redundant rather than load-bearing. The real single point of failure is the `license-files` key, and both the wheel and sdist guards fail when the OGL is dropped from it, which is the regression worth guarding
- [X] T075 Reconcile the line-length setting with plan.md's Toolchain decision (contradicts). plan.md states that flake8 "needs a separate `.flake8` set to `max-line-length = 88` with `extend-ignore = E203` to agree with Black", and T003 repeated the figure. The repository ships `.flake8` with `max-line-length = 99` and `pyproject.toml` with `[tool.black] line-length = 99`. The plan's stated *purpose* is met — the two tools do agree with each other, and nothing is inconsistent from the formatter's point of view — but the value itself contradicts the recorded decision, and several lines in `src/cetools/` (for example `rules.py`'s `resources.files(...).read_text(...)` line) sit in the 88-to-99 window. Take one route explicitly: set both to `88` and reformat, or, if `99` was a deliberate later choice, amend plan.md through `/speckit-plan` so the artifact records the decision the repository is actually following. Converge cannot make that amendment itself, which is why the choice is stated here rather than made. This is quality tooling and explicitly not a gate on done (Principle III), so it is the lowest-priority item in this phase. **Resolved (user decision, 2026-08-12)**: the second route was taken. `99` was a deliberate implementation-time choice, so the repository is unchanged and no source was reformatted; instead plan.md's Toolchain section and research.md's R13 now record `99`, state why (the codebase's signal-carrying lines are long single expressions that 88 splits without clarifying), and note that the constraint the decision rests on is that the two tools agree rather than any particular figure. T003's description above was amended the same way so a future convergence run does not rediscover the same contradiction from a completed task. The amendment was made as a targeted edit rather than by re-running `/speckit-plan`, since the decision itself was already made here and regenerating the design artifacts wholesale would churn far beyond the one value at issue

---

## Phase 10: Convergence

**Purpose**: Close the gaps found by the third `/speckit-converge` run on 2026-08-12. The
suite is green at 180 passing tests, `black`, `isort`, and `flake8` are all clean, all
four stories function, no constitution MUST principle is violated, and every Phase 8 and
Phase 9 repair holds. What follows is two behavior defects that reach a caller through the
public API, one contract that the code contradicts under an edit the spec explicitly
permits, and a set of verification gaps where an artifact promises a check the suite does
not perform. Test-first (Principle III) applies here as everywhere: write the failing test
first, watch it bite the gap it names, and only then close it.

- [ ] T076 Raise a `CetoolsError` when `check` is handed a `task.roll` that is not a count-and-sides throw, per FR-029 (contradicts). T068 closed this for the *loader* path, but the guard sits in `_task_parameters_from_toml` and is bypassed entirely by the public `parameters=` argument: `check(Roller(1), parameters=TaskParameters(roll="d66", ...))` reaches `count, sides, roll_modifier = parse_notation(parameters.roll)` at `src/cetools/tasks.py:95` and dies with `TypeError: cannot unpack non-iterable NoneType object`. Both `check` and `TaskParameters` are in `__all__`, and contracts/library-api.md calls passing an explicit `TaskParameters` "an API, not a filesystem search" — it is the documented way SC-010 is tested and the documented way a future house-rule consumer supplies its own table. FR-029 requires every condition the library detects to be raised as a `CetoolsError` descendant, so a `TypeError` out of a public entry point is the same defect T068 named, one layer up. Add the failing test to `tests/unit/test_tasks.py` first, then have `check` reject a `None` return from `parse_notation` with a `RulesDataError` naming `task.roll`. Do not fix it by re-validating inside `_task_parameters_from_toml`; that path is already correct and is not the one at fault
- [ ] T077 Stop negative integer seeds from aliasing onto their positive counterparts, per FR-002 (contradicts). `Roller.__init__` hands the resolved integer straight to `random.Random` (`src/cetools/dice.py:24`), and CPython's `random.Random` seeds from the **absolute value** of an exact integer. Verified: `Roller(-5)` and `Roller(5)` both throw `2d6` as `(5, 3)`, and `-(2**200 + 7)` collides with `2**200 + 7` the same way. FR-002 says an integer seed "MAY carry a negative sign" and "MUST be used exactly as given, without truncation, rounding, or reduction into a narrower range"; folding the sign halves the effective seed space, which is a reduction. The round trip is *not* broken — the sign survives in `Roller.seed` and in both renderings, so FR-006 and SC-004 still hold — which is exactly why nothing in the suite catches it. **Binding constraint on the fix**: results for non-negative integer seeds and for text seeds MUST stay byte-identical, because the published table in contracts/cli.md, all five golden files, and the `session-alpha`/`1` literals throughout the suite depend on them. That rules out a symmetric remap such as zigzag encoding, which would move every positive seed. Folding only the negative branch (for instance through the same blake2b path text seeds already take, keyed on the signed decimal form) satisfies FR-002 while leaving every published value untouched. Rejecting negative seeds is **not** an option: FR-002 permits them explicitly. Add tests driving a negative seed and a seed above 2^64 through `Roller`, `throw`, and the CLI in both output modes — FR-002's coverage today stops at `resolve_seed` and never reaches `Roller` (`tests/unit/test_seeds.py:17,21`), and the hypothesis strategy is bounded to `0..2**64-1` (`tests/property/test_invariants.py:8`)
- [ ] T078 Cover the characteristic band-gap error path, per FR-015 (partial). `TaskParameters.characteristic_dm` raises `RulesDataError(f"no characteristic band covers score {score}")` at `src/cetools/tasks.py:49`, and no test in the suite reaches it. FR-015 states the clause outright: because the table is editable under FR-022, "a score falling outside every band in the data then in force MUST be reported as a rules-data error rather than silently contributing zero", and contracts/tasks-toml.md makes it explicit that gap detection is deliberately deferred to lookup time rather than performed on load, with feature 2 owning full coverage checking. That makes the lookup-time raise the only thing standing between a house-ruled table with a hole in it and a silent wrong answer, and it is unguarded. Verified reachable: editing the shipped band `"3-5"` to `"4-5"` and resolving a check with `--characteristic 3` raises correctly today. Add the test through `check` as well as through `characteristic_dm` directly, so the error survives the call path a referee actually uses
- [ ] T079 Reconcile `dice_total` with the two artifacts that define it, per FR-018 (contradicts; also data-model.md and contracts/json-output.md). Both `specs/001-dice-task-engine/data-model.md:103` and `specs/001-dice-task-engine/contracts/json-output.md:88` define `dice_total` as "`sum(faces)`, before modifiers". `check` computes `dice_total = sum(faces) + roll_modifier` (`src/cetools/tasks.py:97`), where `roll_modifier` comes from parsing `task.roll`. With the shipped `roll = "2d6"` the two agree, so nothing fails today. Under `roll = "2d6+1"` they diverge, and FR-013 explicitly enables that edit — "the check's own dice are rules content and are held in data ... so a referee can house-rule the core throw". Verified: with `roll = "2d6+1"` and faces `1, 5`, `dice_total` is `7`, the text rendering prints the literally false `Dice: 1, 5 (sum 7)`, and the `+1` is applied without appearing in the itemized list, which FR-018 requires of "every applied modifier". The committed JSON invariant `total == dice_total + sum(modifiers)` still holds, so a consumer is not broken, but `dice_total`'s documented meaning is. Take one route explicitly: either itemize the roll's flat modifier as a `Modifier` (keeping `dice_total` a true `sum(faces)`, which matches both artifacts and FR-018 but adds a row to the shipped-data rendering only when a referee house-rules one in), or amend both artifacts to define `dice_total` as the throw's total including any notation modifier. The first route needs no artifact edit and is the one FR-018 points at. Add a test with a modifier-bearing `task.roll` either way; no test today exercises one, and the only `roll` edits covered are invalid ones (`tests/unit/test_rules.py:120,130`)
- [ ] T080 Check the Product Identity strings and the Section 15 chain against the built artifacts, per SC-012 and the constitution's Licensing & Distribution Constraints (partial). SC-012 requires that "the data file **as read from the installed package** carries its Open Game Content designation and contains neither Product Identity string". Only half of that is verified against a distribution: `tests/guards/test_packaging.py:54,84` assert `"Open Game Content" in text` for the wheel and the sdist, and stop there. The PI-absence assertions live only in `test_packaged_tasks_toml_opens_with_ogc_designation_and_omits_pi_strings` (`tests/unit/test_licensing.py:76-82`), which reads through `importlib.resources` — and as `tests/guards/test_packaging.py`'s own docstring records, `uv sync` installs editable, so that resolves into the working tree rather than into anything built. This is precisely the nominal-guarantee problem T069 and T074 existed to end, surviving in the one clause they did not carry over. Add `"Cepheus Engine" not in text` and `"Samardan Press" not in text` to both artifact fixtures. While there, close the second half: `LICENSE-OGL.txt`'s chain is checked only by the presence of a `Section 15`/`COPYRIGHT NOTICE` heading (`tests/unit/test_licensing.py:43-47`, `tests/guards/test_packaging.py:69-70,93-94`), so the Cepheus Engine SRD copyright line could be deleted and the suite would stay green. The constitution requires the chain "verbatim" and "complete"; assert each notice line in it, including this project's own game-data line
- [ ] T081 Extend the ambient-random-state guard beyond `roll`, per SC-005 and FR-001 (partial). SC-005 says "**running any operation** leaves any ambient process-wide random state bit-for-bit unchanged, verified as an automated check", and FR-001 forbids reading from or writing to any process-global random state. `test_guard_a_cli_invocation_does_not_touch_module_random_state` (`tests/guards/test_seed_contract.py:13-17`) captures `random.getstate()` around exactly one operation, `roll 2d6`. `check` — which loads rules data, parses notation, and runs a different code path — is not covered, nor is `--json`, nor any direct library call. A regression that reached for module-level `random` inside `tasks.py` or `rules.py` would ship green. Parametrize the guard over both commands in both output modes, and add a library-only case covering `throw`, `throw_dice`, `d66`, and `check` so FR-001 is verified where the library is used without the CLI (SC-011's standard)
- [ ] T082 Make the seed round trip cover the machine-readable mode and the signed case, per SC-004 and FR-006 (partial). SC-004 binds "**every** rendered result, in **both** output modes and for **every** command". T073 fixed the assertion in the two text-mode round trips, but the JSON mode is still only presence-checked: `tests/integration/test_cli.py:152,167,223` assert `payload["seed"] in text_result.stdout`, which shows the seed is printed, not that feeding it back reproduces the result. Add a JSON round trip for both commands: run unseeded with `--json`, read `payload["seed"]`, run again supplying it, assert byte-identical stdout. Second gap: both text round trips capture the seed with `re.search(r"Seed:\s+(\d+)", ...)` (`test_cli.py:58,128`), which cannot match a leading `-`. Unseeded runs never produce one, so the regex is adequate today and silently would not be once T077 lands; widen it to `[+-]?\d+` and add an explicit `--seed -5` round trip in both modes. Third gap: FR-006 binds programmatic invocation as well as command invocation, and `test_same_seed_and_arguments_yield_equal_result` (`tests/property/test_invariants.py:37-41`) covers throws only — add the equivalent for `check`
- [ ] T083 Assert the exact option set in both `--help` outputs, per FR-025 (partial). FR-025 requires each subcommand's help to "list exactly the options that subcommand accepts and no others", and says so specifically to state the requirement "as something checkable rather than as a matter of taste". The two tests are weaker than that: `test_roll_help_lists_exactly_its_own_options` (`tests/integration/test_cli.py:45-52`) checks that `NOTATION`, `--seed`, and `--json` are present and that the four check-only options are absent, and `test_check_help_lists_exactly_its_own_options` (`:117-122`) checks six options are present and `NOTATION` is absent. Both are an allowlist plus a denylist, so adding a spurious option to either subcommand — a `--target` on `roll`, say, which the spec puts out of scope by name — passes unchanged. Parse the option tokens out of the help text and compare the resulting set for equality against the expected set (including `--help`), so the assertion is the exact one FR-025 asks for. The current help output is correct, so this is a test-strength repair rather than a behavior fix
- [ ] T084 Reconcile `requires-python` with what FR-007 can actually discharge (partial). FR-007 binds identical results "across every version of the underlying language runtime that the package declares itself to support", and is careful to add that "the supported set is the one the package declares in its own metadata; this requirement binds every version in that set, **which is what makes it dischargeable rather than open-ended**". `pyproject.toml:10` declares `requires-python = ">=3.13"`, which is unbounded, while `.github/workflows/ci.yml:13` verifies `3.13` and `3.14`. The declared set is therefore infinite and the requirement is, as written, not dischargeable: when 3.15 ships, this package already claims to support it and nothing has verified it. Take one route explicitly, as T075 did for the line length: either give `requires-python` an upper bound (`">=3.13,<3.15"`) so the declared set matches the matrix and widening it becomes a deliberate act that updates both, or record in plan.md that the declaration is intentionally open and that the matrix tracks released versions, in which case add a guard test that fails when a Python version inside `requires-python` is missing from the CI matrix. Converge cannot choose between an artifact amendment and a metadata change, which is why the choice is stated here rather than made
- [ ] T085 Assert empty stdout on usage errors and cover exit 2 under `--json`, per FR-027 and SC-006 (partial). FR-027 says that on **any** error "nothing at all is written to the output stream, so a consumer never sees a partial result", and SC-006 says requesting machine-readable output "changes none of" the exit statuses. The library-error class is covered on both counts for both commands and both modes (`tests/integration/test_cli.py:27-31,78-82,170-176,226-232`). The usage-error class is not: `test_cli.py:34-37,85-88,90-93,95-98` assert only `exit_code == 2` and never inspect stdout, and no exit-2 case is run with `--json` at all. Confirmed by hand that stdout is in fact empty for `check --dm cover` with and without `--json`, so this is unguarded behavior rather than a live defect. Add `assert result.stdout == ""` to each exit-2 test and run at least one malformed `--dm` case under `--json`. While there, cover the "missing required argument" form FR-031 names: no test invokes `roll` with no `NOTATION`
- [ ] T086 Give `as_text` a typed failure for a `CheckResult` with no modifiers, per FR-029 (partial). `src/cetools/render.py:44` computes `mod_width = max(len(modifier.label) for modifier in result.modifiers)`, which raises `ValueError: max() iterable argument is empty` when `modifiers` is empty. Both `CheckResult` and `as_text` are in `__all__`, so a library caller can construct one and hit it; `check` itself always appends at least a difficulty and a skill-or-unskilled modifier, so the CLI cannot reach it. FR-029 requires the library to signal every condition it detects through a `CetoolsError` descendant, and an unguarded `max()` signals nothing. This is the lowest-severity item in the phase precisely because no supported call path reaches it — resolve it either by rendering an empty modifier list cleanly (a defensible reading, since `Modifiers:` with no rows is not malformed) or by documenting the non-empty precondition in the docstring and raising a typed error. Do not add validation to `CheckResult.__post_init__` without checking the frozen-slotted-dataclass cost first
- [ ] T087 Widen the compatibility-claim guard past README and the package description, per FR-035 (partial). FR-035 binds "**any text this feature writes**" that claims compatibility with the source rules. `_assert_claim_carries_attribution` (`tests/unit/test_licensing.py:16-28`) is applied to exactly two surfaces, `README.md` and the `pyproject.toml` description (`:64-73`). The CLI help strings in `src/cetools/cli.py:52-86` and `CHANGELOG.md` are text this feature writes and are unguarded; CONTRIBUTING.md itself names both trademarks (`CONTRIBUTING.md:138-152`) while telling contributors that a claim added "anywhere (README, PyPI description, CLI help)" must carry the attribution, so the rule is documented and unenforced for two of the three surfaces it names. **Design constraint**: the current heuristic treats any occurrence of "Cepheus Engine" as a claim, and pointing it at CONTRIBUTING.md as-is fails — verified — because that file names the trademark while *explaining the licensing rules* rather than claiming compatibility, and its non-affiliation wording ("a statement of non-affiliation") matches neither phrase in `NON_AFFILIATION_PHRASES`. Naming a trademark is not claiming compatibility, so the widened guard must distinguish the two rather than demand attribution from every mention; decide the rule deliberately and record it in the helper's docstring
- [ ] T088 Cover an added and a removed difficulty rung, per FR-022 (partial). FR-022 names three structural edits that MUST be honored: "adding, removing, or renaming a difficulty ladder entry". T029 asked for "a renamed rung, an added rung, an altered band bound"; `test_sc010_edited_target_difficulty_unskilled_dm_and_band_bound_are_reflected` (`tests/unit/test_rules.py:212-225`) delivers the rename (`"Average"` to `"Balanced"`) and the band-bound change, and neither an added nor a removed rung is exercised anywhere. A loader that silently dropped unknown rungs, or that mishandled a shorter ladder, would ship green. Add both cases through `_task_parameters_from_toml`, asserting the new rung resolves through `difficulty_dm` and that a removed one raises `TaskError` listing the remaining valid names (FR-019)
- [ ] T089 Finish the American English sweep in the two files it missed, per the user directive of 2026-08-12 (contradicts). T070 recorded the sweep as complete across "every `specs/001-dice-task-engine/` artifact", but "neighbouring" survives in two places: `specs/001-dice-task-engine/spec.md:275` (in FR-014's own prose, "silently resolved to a neighbouring rung") and `specs/001-dice-task-engine/checklists/pre-tasks.md:59` (quoting the same clause back). A full scan of the repository for the `-our`, `-ise`, `-ce`/`-se`, doubled-`l`, and `artefact` families found no other survivors outside the two deliberate exclusions T070 named. Note that this edits `spec.md`, which converge itself may not touch; T070 set the precedent that the spelling convention governs Spec Kit artifacts, so the edit belongs to `/speckit-implement` and changes no requirement's meaning
- [ ] T090 Stop the editor dictionary from whitelisting the spellings the convention bans, per the user directive of 2026-08-12 (contradicts). The same change that removed British spellings from the prose added `"artefacts"` (`.vscode/settings.json:7`), `"behaviour"` (`:9`), and `"organised"` (`:48`) to `cSpell.words`, so the spell checker now accepts exactly the three forms T070 spent 66 corrections removing. That is the opposite of a guard: the next contributor to type "behaviour" gets no squiggle. Remove the three entries. Leave the rest of the list alone — the other additions (`docstrings`, `pyproject`, `Samardan`, `speckit`, `underspecified`) are genuine vocabulary, and `Samardan` in particular must stay, since it is a Product Identity string that appears legitimately in `LICENSE-OGL.txt` and `CONTRIBUTING.md`
