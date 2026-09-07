# Tasks: Validation Vocabulary

**Input**: Design documents from `/specs/006-validation-vocabulary/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/schema-vocabulary.md](contracts/schema-vocabulary.md),
[quickstart.md](quickstart.md)

**Tests**: Included, and non-negotiable. Constitution Principle III makes this
project test-first: write the test, watch it fail, then implement. FR-018
requires the vocabulary's own tests to exist and fail before `schema.py` does.

**Organization**: Grouped by the spec's three user stories, in priority order.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on incomplete work)
- **[Story]**: `[US1]`, `[US2]`, `[US3]`
- Every task names the file it touches

## Path Conventions

Single project: `src/cetools/` and `tests/` at the repository root.

## A note on parallelism

Almost nothing here is `[P]`, and that is a property of the work rather than an
oversight. Principle III requires one test at a time with the whole suite run
after each step, which serializes every test task. Each module migration ends
in its own commit, which serializes those too. Only the two baseline checks in
Phase 1 are genuinely independent.

## A note on the capture harness

FR-013a forbids inferring message-neutrality from a passing suite. The suite
names nine of the sixty-three distinct `expected` phrasings the source emits,
nineteen counting whole-problem comparisons; the fifty-four it never names
include every table phrasing the `require_dict` conversions carry. So every
structural step is checked by diffing the validator's own output.

The harness lives **outside the repository**, so that it survives the
`git stash` / checkout the comparison needs and never becomes a committed
artifact the project has no use for after this feature. Two locations are used
below:

- `$CORPUS`: a broken copy of the packaged data set (`/tmp/cetools-006/corpus`)
- `$CAPTURES`: the captured JSON reports (`/tmp/cetools-006/captures`)

---

## Phase 1: Setup

**Purpose**: establish that the tree is green before anything moves, so a later
failure is attributable.

- [ ] T001 [P] Run `uv run pytest` from the repository root and record the pass count as the pre-feature baseline in `/tmp/cetools-006/baseline-suite.txt`
- [ ] T002 [P] Run `uv run black --check src tests`, `uv run isort --check src tests`, and `uv run flake8 src tests` and confirm all three are clean, so a later warning is known to be this feature's

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: build the evidence FR-013a requires. Nothing in Phase 3 or beyond
can be shown message-neutral without it.

**⚠️ CRITICAL**: no user story work begins until T006 confirms the corpus
actually reaches the messages this feature disturbs.

- [ ] T003 Write a corpus builder at `/tmp/cetools-006/build-corpus.sh` (pure Bourne shell) that copies `src/cetools/data/` to `$CORPUS` and applies one breakage per outcome in `contracts/schema-vocabulary.md`: an absent key, a wrong type, a `bool` in an integer field, an empty string, a below-minimum value at `minimum=1` and at `minimum=0`, a non-table where each of the five named tables is required, a malformed dice notation, `d66` where a throw is required, a non-boolean optional flag, and an unrecognized key
- [ ] T004 Write a capture script at `/tmp/cetools-006/capture.sh` (pure Bourne shell) that runs `uv run cetools validate $CORPUS --json`, sorts the problems by `(file, location, found, expected)`, and writes the result to a named file under `$CAPTURES`
- [ ] T005 Run T003 and T004 against the current tree to produce `$CAPTURES/00-pre-feature.json`, the reference every later capture is diffed against
- [ ] T006 Confirm the corpus is not vacuous: `$CAPTURES/00-pre-feature.json` must contain `"an integer >= 1"`, `"a string"` from an absent required text field, and all five table phrasings (`"a table"`, `"a table with label and class"`, `"a [task] table"`, `"a [pseudo-hex] table"`, `"a mustering-out table"`). If any is absent, extend `/tmp/cetools-006/build-corpus.sh` until it is present—a corpus that misses the messages this feature moves proves nothing

**Checkpoint**: the before-and-after comparison is available and demonstrably
reaches the messages at risk.

---

## Phase 3: User Story 1 - One wording for one rule (Priority: P1) 🎯 MVP

**Goal**: two rules that each have two phrasings today get one phrasing each,
in every data-file kind. This is the only user-visible part of the feature, and
it must land first: the duplicate checks cannot be merged until they agree on
what to say (FR-019).

**Independent Test**: put a below-minimum value in each field requiring at least
one, and leave each required text field absent, then validate and confirm each
rule is described in the same words wherever it is broken—with `schema.py`
still not existing.

### Tests and implementation for User Story 1

Strictly alternating red/green, one test at a time, whole suite after each.

- [ ] T007 [US1] Add a failing test in `tests/unit/test_chargen.py` asserting that `terms.term-years = 0` reports `expected == "a positive integer"`; watch it fail against the current `"an integer >= 1"`
- [ ] T008 [US1] Change the `minimum` branch of `_require_int` in `src/cetools/chargen.py` (lines 102-111) to match `src/cetools/careers.py:192`, special-casing `minimum == 1` as `"a positive integer"`; run `uv run pytest`
- [ ] T009 [US1] Add a pinning test in `tests/unit/test_chargen.py` asserting a `minimum=0` field still reports `expected == "an integer >= 0"` (FR-010, Acceptance Scenario 3). This one passes on first run by design: it pins behavior that must not move, and is not a red step
- [ ] T010 [US1] Add a failing test in `tests/unit/test_careers.py` asserting that a career file with no `name` reports `expected == "a non-empty string"`; watch it fail against `"a string"`
- [ ] T011 [US1] Change the absent-key branch of `_require_string` in `src/cetools/careers.py` (line 145) to report `"a non-empty string"`; run `uv run pytest`
- [ ] T012 [US1] Add a failing test in `tests/unit/test_names.py` asserting an absent required text field reports `expected == "a non-empty string"`; watch it fail
- [ ] T013 [US1] Change the absent-key branch of `_require_string` in `src/cetools/names.py` (line 32); run `uv run pytest`
- [ ] T014 [US1] Add a failing test in `tests/unit/test_chargen.py` asserting an absent required text field reports `expected == "a non-empty string"`; watch it fail
- [ ] T015 [US1] Change the absent-key branch of `_require_string` in `src/cetools/chargen.py` (line 115); run `uv run pytest`
- [ ] T016 [US1] Confirm `tests/unit/test_rules.py:459` still passes untouched: an absent `task.roll` keeps `expected == "a string"`, because a dice-notation field is not a required text field (FR-010a)

### Verification and delivery for User Story 1

- [ ] T017 [US1] Capture the post-change report to `$CAPTURES/01-behavioral.json` with `/tmp/cetools-006/capture.sh` and diff it against `$CAPTURES/00-pre-feature.json`
- [ ] T018 [US1] Confirm the diff contains only the six `minimum=1` fields moving to `"a positive integer"` and the thirteen required-text-field sites moving to `"a non-empty string"`, per `data-model.md`'s *Inventory: behavioral blast radius*. Any other moved message is a finding for the maintainer under FR-013b, not a message to rewrite, and halts the work until settled
- [ ] T019 [US1] Add one `CHANGELOG.md` entry covering both wording changes and nothing else (FR-019)
- [ ] T020 [US1] Run `uv run pytest` and the three lint commands, then commit as a **behavioral** change with a Conventional Commits scope (`fix(schema): …` or `feat(schema): …`), the message stating that it is behavioral

**Checkpoint**: User Story 1 is complete and independently verifiable. No
duplicate has yet been removed. `$CAPTURES/01-behavioral.json` is now the
reference every structural step below is diffed against.

---

## Phase 4: User Story 2 - One place to state a rule (Priority: P2)

**Goal**: `src/cetools/schema.py` exists, owns the seven checks, and is
exercised directly by its own tests—with no parser module changed yet.

**Independent Test**: `uv run pytest tests/unit/test_schema.py -v` passes while
the whole existing suite also passes unchanged, which is only possible if the
vocabulary is correct and nothing yet depends on it.

### Tests and implementation for User Story 2

Each pair below is one red step and one green step. The `expected` and `found`
strings come from the tables in `contracts/schema-vocabulary.md`, which is the
contract; these tests are its transcription.

- [ ] T021 [US2] Create `tests/unit/test_schema.py` covering all seven outcomes of `require_int` (absent key, `bool` value, non-`int` value, no minimum, below a `minimum` of 1, below another `minimum`, at or above `minimum`); it fails on import because `src/cetools/schema.py` does not exist
- [ ] T022 [US2] Create `src/cetools/schema.py` importing `ValidationProblem` and `type_name` from `src/cetools/errors.py` and `_check_dice` from `src/cetools/tasks.py`, and implement `require_int` by moving `careers.py:169`'s body; run `uv run pytest`
- [ ] T023 [US2] Add the four `require_string` outcomes to `tests/unit/test_schema.py` (absent key, empty string, non-`str`, accepted); watch them fail
- [ ] T024 [US2] Implement `require_string` in `src/cetools/schema.py` with `registries._require_nonempty_string`'s behavior; run `uv run pytest`
- [ ] T025 [US2] Add the three `require_bool` outcomes to `tests/unit/test_schema.py`; watch them fail
- [ ] T026 [US2] Implement `require_bool` in `src/cetools/schema.py` by moving `chargen.py:139`'s body; run `uv run pytest`
- [ ] T027 [US2] Add the four `require_roll` outcomes to `tests/unit/test_schema.py`, including a rejected `d66` and an absent key still expecting `"a string"`; watch them fail
- [ ] T028 [US2] Implement `require_roll` in `src/cetools/schema.py` by moving `careers.py:200`'s body; run `uv run pytest`
- [ ] T029 [US2] Add the three `require_dict` outcomes to `tests/unit/test_schema.py`, the `value is None` row asserting `found == "missing"` and the caller's own `expected`; watch them fail
- [ ] T030 [US2] Implement `require_dict` in `src/cetools/schema.py`, value-taking, with the `None`-means-missing row `careers._require_dict` lacks; run `uv run pytest`
- [ ] T031 [US2] Add the three `optional_bool` outcomes to `tests/unit/test_schema.py`, the non-`bool` row asserting that a problem is reported **and** the declared default is returned (FR-005); watch them fail
- [ ] T032 [US2] Implement `optional_bool` in `src/cetools/schema.py` from the shape `careers.py:944-972` repeats twice; run `uv run pytest`
- [ ] T033 [US2] Add `unrecognized_key_problems` cases to `tests/unit/test_schema.py`: one problem per unadmitted key, sorted by key name, each `expected` naming the sorted admitted keys, and the empty list when every key is admitted; watch them fail
- [ ] T034 [US2] Implement `unrecognized_key_problems` in `src/cetools/schema.py` as a pure move of the byte-identical body; run `uv run pytest`

### Verification and delivery for User Story 2

- [ ] T035 [US2] Confirm `src/cetools/schema.py` is absent from `src/cetools/__init__.py`'s `__all__` and that every function is bare-named rather than underscore-prefixed (FR-016)
- [ ] T036 [US2] Confirm `tests/unit/test_schema.py` covers every row of every table in `contracts/schema-vocabulary.md`—twenty-four rows across six checks—plus the three behaviors stated in prose for `unrecognized_key_problems`, since FR-018 binds the contract's own enumeration rather than a fixed four-path list
- [ ] T037 [US2] Run `uv run pytest` and the three lint commands, then commit as a **structural** change (`refactor(schema): …`), with no `CHANGELOG.md` entry (FR-019)

**Checkpoint**: the vocabulary exists and is proven. No parser has changed, so
the whole existing suite still passes untouched.

---

## Phase 5: User Story 3 - The parsers stop restating the rules (Priority: P3)

**Goal**: sixteen definitions across five modules become zero, the eleven inline
sites are converted, and a guard holds the rule.

**Independent Test**: the existing suite passes with no change beyond Story 1's
wording assertions, the before-and-after capture diff is empty for every step,
and each of the seven checks is defined exactly once.

Module order is smallest first, so a mistake in the pattern shows up where it is
cheapest to find. Each module is its own commit.

### names.py (2 definitions, 7 call sites, 0 inline)

- [ ] T038 [US3] In `src/cetools/names.py`: import the vocabulary, delete `_unrecognized_key_problems` (line 17) and `_require_string` (line 32), and rewire all 7 call sites (lines 102, 104, 143, 145, 184, 187, 188)
- [ ] T039 [US3] Leave `names._require_name_array` (lines 56-85) exactly as it is: its per-element non-empty-string test decides an element identified by position rather than a field named by key, so it is array handling FR-020 excludes, not an inline site FR-015 converts
- [ ] T040 [US3] Run `uv run pytest`, capture to `$CAPTURES/02-names.json`, diff against `$CAPTURES/01-behavioral.json`, confirm the diff is empty, then commit as **structural**

### rules.py (2 definitions, 4 call sites, 3 inline)

- [ ] T041 [US3] In `src/cetools/rules.py`: import the vocabulary, delete `_unrecognized_key_problems` (line 142) and `_require_int` (line 269), and rewire all 4 call sites (lines 166, 182, 212, 213)
- [ ] T042 [US3] Convert the three inline sites in `src/cetools/rules.py`: the dict check at 169-179 to `require_dict`, keeping `"a [task] table"`; the fully inlined roll check at 185-210 to `require_roll`; and the integer check at 231-240 to `require_int(dd, name, …)`, replacing its `ok = False; continue` bookkeeping with `is None`
- [ ] T043 [US3] Leave `rules.py:217-227` alone: it rejects a table that is absent, wrong-typed, **or** empty in one compound message, a different rule from `require_dict`'s (`data-model.md`, *Not converted*)
- [ ] T044 [US3] Run `uv run pytest`, capture to `$CAPTURES/03-rules.json`, diff against `$CAPTURES/02-names.json`, confirm the diff is empty, then commit as **structural**

### registries.py (2 definitions, 7 call sites, 4 inline)

- [ ] T045 [US3] In `src/cetools/registries.py`: import the vocabulary, delete `_unrecognized_key_problems` (line 131) and `_require_nonempty_string` (line 253), and rewire all 7 call sites (lines 243, 246, 247, 290, 348, 445, 532), the two `_require_nonempty_string` calls becoming `require_string`
- [ ] T046 [US3] Convert the four inline sites in `src/cetools/registries.py`: the integer check at 176-186 to `require_int(data, key, …)`; the dict check at 231-240 to `require_dict`, keeping `"a table with label and class"`; the dict check at 279-288 to `require_dict`, keeping `"a [pseudo-hex] table"` **and** its `"missing"` report for an absent value; and the integer check at 292-300 to `require_int(data, "minimum", …)`
- [ ] T047 [US3] Leave `registries.py:160-170` alone, for the same reason as T043
- [ ] T048 [US3] Run `uv run pytest`, capture to `$CAPTURES/04-registries.json`, diff against `$CAPTURES/03-rules.json`, confirm the diff is empty, then commit as **structural**

### careers.py (5 definitions, 19 call sites, 2 inline)

- [ ] T049 [US3] In `src/cetools/careers.py`: import the vocabulary and delete `_unrecognized_key_problems` (117), `_require_dict` (132), `_require_string` (145), `_require_int` (169), and `_require_roll` (200)
- [ ] T050 [US3] Rewire all 19 named call sites in `src/cetools/careers.py` (lines 329, 334, 360, 361, 381, 416, 421, 506, 536, 541, 544, 655, 660, 663, 806, 810, 924, 941, 942)
- [ ] T051 [US3] Convert the two inline optional-bool sites in `src/cetools/careers.py`—`always-available` at 944-957 and `re-enterable` at 959-972—to `optional_bool(…, default=False)`
- [ ] T052 [US3] Leave `careers._notation_field` and `careers._skill_problem` alone: they resolve names against a registry rather than check TOML types, and FR-020 excludes them
- [ ] T053 [US3] Run `uv run pytest`, capture to `$CAPTURES/05-careers.json`, diff against `$CAPTURES/04-registries.json`, confirm the diff is empty, then commit as **structural**

### chargen.py (5 definitions, 36 call sites, 2 inline)

- [ ] T054 [US3] In `src/cetools/chargen.py`: import the vocabulary and delete `_unrecognized_key_problems` (30), `_require_roll` (45), `_require_int` (80), `_require_string` (115), and `_require_bool` (139)
- [ ] T055 [US3] Rewire all 36 named call sites in `src/cetools/chargen.py` (lines 179, 181, 283, 286, 287, 363, 366, 401, 404, 570, 581, 586, 587, 671, 674, 729, 734, 735, 862, 929, 932, 933, 965, 968, 1028, 1031, 1032, 1215, 1216, 1217, 1270, 1277, 1279, 1281, 1283, 1312)
- [ ] T056 [US3] Convert the two inline dict sites in `src/cetools/chargen.py`: 1207-1213 and 1259-1268, both keeping `"a table"`, the second keeping its `"missing"` report for an absent group (its `group not in data` membership test becomes `require_dict`'s `value is None` row)
- [ ] T057 [US3] Confirm `_CHARGEN_GROUPS` (`src/cetools/chargen.py:1087-1137`) stays in the module unchanged and that `_parse_chargen_group` (1249-1305) now dispatches each declared kind to the vocabulary rather than to chargen's deleted copies (FR-017)
- [ ] T058 [US3] Leave `chargen._parse_rank_bonus_list` alone: it is array handling, excluded by FR-020
- [ ] T059 [US3] Run `uv run pytest`, capture to `$CAPTURES/06-chargen.json`, diff against `$CAPTURES/05-careers.json`, confirm the diff is empty, then commit as **structural**

### The guard (FR-014a, FR-014b, FR-014c)

- [ ] T060 [US3] Create `tests/guards/test_no_duplicate_checks.py` with its can-it-fail self-test first: plant a module source that defines one of the seven checks at top level, and assert the detector rejects it. It fails because the detector does not exist yet
- [ ] T061 [US3] Implement the detector in `tests/guards/test_no_duplicate_checks.py`, walking `src/**/*.py` with `ast` and following the pattern of `tests/guards/test_no_locale.py` (its `repo_root` fixture comes from `tests/conftest.py`); run `uv run pytest`
- [ ] T062 [US3] Add the real assertion to `tests/guards/test_no_duplicate_checks.py`: each of the seven checks, with or without a leading underscore, is defined at top level in `src/cetools/schema.py` and nowhere else in `src/`
- [ ] T063 [US3] State the guard's limit in the module docstring of `tests/guards/test_no_duplicate_checks.py`: it recognizes a check by its name at a module's top level, so it does not catch a check written fresh and inline without a name (FR-014b)
- [ ] T064 [US3] Run the quickstart Scenario 4 loop by hand and confirm each of the seven checks reports exactly one definition, all in `src/cetools/schema.py`, down from sixteen across five files (SC-002)
- [ ] T065 [US3] Run `uv run pytest` and the three lint commands, then commit the guard as **structural**, with no `CHANGELOG.md` entry

**Checkpoint**: all three stories complete. The duplication is gone and cannot
grow back unnoticed in the shape it grew in.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T066 Run the whole suite including the slow marker: `uv run pytest` with no `-m` filter, from the repository root
- [ ] T067 Run `uv run black src tests`, `uv run isort src tests`, and `uv run flake8 src tests` and resolve every warning
- [ ] T068 Walk all four scenarios in [quickstart.md](quickstart.md) end to end and confirm each expected outcome, including the FR-010a check that an absent `task.roll` still expects `"a string"`
- [ ] T069 Confirm `CHANGELOG.md` carries exactly one entry from this feature, the wording change from T019, and that no structural commit claimed one (FR-019, SC-004)
- [ ] T070 Confirm the final capture `$CAPTURES/06-chargen.json` differs from `$CAPTURES/00-pre-feature.json` only in the two rules named in FR-013 (SC-003)
- [ ] T071 Mark this file complete and confirm every checklist item in [checklists/refactor.md](checklists/refactor.md) still holds against the delivered work

---

## Dependencies & Execution Order

### Phase dependencies

- **Phase 1 (Setup)**: no dependencies
- **Phase 2 (Foundational)**: depends on Phase 1. **Blocks every user story**—FR-013a's evidence cannot be produced retroactively, because the "before" state stops existing once the first change lands
- **Phase 3 (US1)**: depends on Phase 2. Blocks Phase 4 and Phase 5 by FR-019: the wording change ships before any duplicate is removed, and there is no single definition to extract until the copies agree on what to say
- **Phase 4 (US2)**: depends on Phase 3. Blocks Phase 5—the parsers cannot call a vocabulary that does not exist
- **Phase 5 (US3)**: depends on Phase 4
- **Phase 6 (Polish)**: depends on Phase 5

The stories are **not** independent of one another here, unlike the usual case.
The ordering is forced by Tidy First and by FR-019, not chosen, and the plan
says so. Each story is still independently *verifiable* at its checkpoint, which
is what the checkpoints are for.

### Within Phase 5

Module order is `names.py` → `rules.py` → `registries.py` → `careers.py` →
`chargen.py`, smallest first. `chargen.py` carries half the named call sites and
goes last, after the pattern has been established four times.

The guard (T060-T065) comes after all five migrations, because it must pass
against the finished tree.

### Halting condition

FR-013b: if any diff step (T018, T040, T044, T048, T053, T059) shows a message
this feature did not intend to move, stop. Surface it to the maintainer as a
decision about the wording. No further structural task ships until it is
settled, and the divergence and its resolution go in the record either way.

---

## Parallel Opportunities

- T001 and T002 (setup) are independent
- Nothing else. Principle III serializes the test tasks; the per-module commit
  boundaries serialize Phase 5

---

## Implementation Strategy

### MVP (User Story 1 only)

1. Phase 1: Setup
2. Phase 2: Foundational—the capture harness
3. Phase 3: User Story 1
4. **Stop and validate**: the two rules now read the same way everywhere, and
   the capture diff proves nothing else moved

This is a shippable increment on its own: it is the whole of what a reader of
the validation reports can see, and it carries the feature's only changelog
entry. If the structural work were abandoned here, nothing would be left
half-done.

### Incremental delivery

1. MVP as above → the wording is unified
2. Add User Story 2 → the vocabulary exists and is proven, with nothing yet
   depending on it. Also shippable: it adds a module and its tests and changes
   no behavior
3. Add User Story 3 → the duplication is gone, module by module, each migration
   its own commit and its own empty diff

---

## Notes

- Every commit states whether it is **structural** or **behavioral**, per the
  project's Tidy First rule, and follows Conventional Commits with a scope
- Only T020 touches `CHANGELOG.md`. A structural commit claiming an entry would
  put noise in a document that exists to tell readers what changed for them
- No `.toml` file under `src/cetools/data/` is added, edited, or moved by any
  task here, so no licensing or Open Game Content question arises
- `tests/golden/` and `tests/contract/` are untouched: this feature changes no
  command, option, exit code, or output stream, and the four validation-problem
  strings the contract corpus pins are a malformed file and two
  registry-resolution messages, none of them either rule being changed
