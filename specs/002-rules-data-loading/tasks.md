---

description: "Task list for 002-rules-data-loading"
---

# Tasks: Validated Rules Data Loading

**Input**: Design documents from `/specs/002-rules-data-loading/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: REQUIRED. Constitution Principle III (Test-First) and SC-012 both bind this
feature: expected values must be committed in a change that precedes the implementing
change, and each test must be observed to fail before it passes. Every implementation
task below is preceded by the test task that must fail first.

**Organization**: Tasks are grouped by user story to enable independent implementation
and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

Single project: `src/cetools/` and `tests/` at repository root, per plan.md.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Preserve the evidence SC-009 depends on, and add the test helper the
version placeholder needs, before any behavior changes.

- [X] T001 Copy `tests/golden/check_difficult.txt`, `tests/golden/check_unskilled.txt`, `tests/golden/roll_1d6.txt`, `tests/golden/roll_2d6_plus1.txt`, and `tests/golden/roll_d66.txt` verbatim into `tests/golden/pre-loader/` and commit them before any other change; this directory is never regenerated (plan.md Implementation Notes, research R12, SC-009)
- [X] T002 Add a package-version placeholder constant and a normalization helper fixture to `tests/conftest.py` so golden files and JSON fixtures can hold the version as a placeholder substituted at comparison time (SC-009)

**Checkpoint**: The pre-loader evidence is committed and cannot be destroyed by a later regeneration.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The problem type, the notation, the registries, the career types, and the
provenance types. Every user story builds on these.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

**Build order** follows plan.md: `errors` → `notation` → `registries` → `careers` → `provenance`.

- [X] T003 [P] Write failing tests for `ValidationProblem` fields, its `(file, location)` sort order, the empty-string location a problem about a file as a whole carries, and `RulesDataError.problems` including the message-only construction, in `tests/unit/test_errors.py` (FR-022, data-model.md)
- [X] T004 Add `ValidationProblem` as a frozen slotted dataclass, its `location` a `str` that is empty for a problem about a file as a whole rather than an optional field, and extend `RulesDataError` with a `problems` field in `src/cetools/errors.py` (FR-022, data-model.md) (depends on T003)
- [X] T005 [P] Write failing tests for `parse_entry` covering the four forms, tail-anchored precedence, names with spaces/apostrophes/slashes/hyphens, parenthesized specialties, the three `EntryContext` subsets, and every malformed case in `contracts/notation.md`, in `tests/unit/test_notation.py` (FR-004, FR-006, FR-009, FR-009a)
- [X] T006 Implement `parse_entry`, `EntryContext`, `SkillReference`, `CharacteristicCheck`, `CharacteristicAdjustment`, `SkillGrant`, and `BenefitItem` in `src/cetools/notation.py`; parsing does no registry lookup (depends on T005)
- [X] T007 [P] Write failing tests for the three registry types and their file schemas, including exact case-sensitive matching and the four `SkillRegistry` resolution outcomes, one of which is a bare name for a skill that has specialties remaining distinguishable from a fully-specified reference, in `tests/unit/test_registries.py` (FR-007, FR-008, FR-010, FR-011, FR-012, FR-013)
- [X] T008 Implement `CharacteristicRegistry`, `SkillRegistry`, `BenefitRegistry` and the `characteristics`, `skills`, and `benefits` file schemas in `src/cetools/registries.py`, returning collected problems and never raising (depends on T004, T007)
- [X] T009 [P] Write failing tests for `Disposition`, `FileProvenance`, `Provenance`, `is_packaged`, and the SHA-256-over-raw-bytes fingerprint in `tests/unit/test_provenance.py` (FR-033, FR-033a, FR-034, FR-035, FR-036, research R4)
- [X] T010 Implement `Disposition`, `FileProvenance`, `Provenance`, and the fingerprint function in `src/cetools/provenance.py`, reading the package version from `importlib.metadata` and hashing bytes without decoding (FR-033, FR-033a, FR-036) (depends on T009)
- [X] T011 [P] Write failing tests for the career file schema covering every required and optional element, closed throw and table name sets, positive targets, non-negative distinct rank positions, distinct ladder names, non-empty tables, and each notation-bearing field validated against the registry its position implies, including a characteristic adjustment in a mustering-out benefits entry checked against the characteristics registry rather than the benefit items registry; assert too that the plain numeric fields, the throw targets and the mustering-out cash amounts, are typed by position and never routed through the notation, so a target written as a string reports a bad type rather than an unrecognized entry form, in `tests/unit/test_careers.py` (FR-004a, FR-005, FR-014 through FR-019a)
- [X] T012 Implement `CareerDefinition`, `Throw`, `SkillTable`, `RankLadder`, `Rank`, `MusteringOut` and the `career` file schema in `src/cetools/careers.py`, resolving each notation-bearing field against the registry its position or its form implies, typing the throw targets and cash amounts as plain values outside the notation, and returning collected problems (FR-004a, FR-005) (depends on T004, T006, T008, T011)
- [X] T013 [P] Add a guard asserting that basenames are unique across every `.toml` under `src/cetools/data/` in `tests/guards/test_data_layout.py`; this is the premise basename positioning rests on, and it fails the moment a second `navy.toml` is added under another directory (FR-029, plan.md trap list)

**Checkpoint**: The notation parses, the registries resolve names, and a career file has a schema. User story work can begin.

---

## Phase 3: User Story 1 - Resolve against trustworthy rules content (Priority: P1) 🎯 MVP

**Goal**: A data set loads only when all of it validated, or refuses; the existing task
check resolves through the new loader with an identical outcome.

**Independent Test**: Load the shipped data set and confirm every part resolves; then
corrupt a copy in each distinct way a hand-authored file can be wrong and confirm the
load refuses, naming the file and location.

**Scope note**: this story owns the whole library-side loader, composition and cross-file
rules included, because `load_rules(override)` is one function and FR-024 validates the
whole set on every load. US3 owns the command-line surface and the end-to-end evidence
that a house rule takes effect. Splitting them the other way would have left T022
implementing composition behavior whose tests lived two phases later, which Principle III
forbids, and left SC-002's closed list half-satisfied at this story's checkpoint.

### Tests for User Story 1 ⚠️ Write first, observe failing

- [X] T014 [P] [US1] Rewrite `tests/unit/test_rules.py` for discovery of every `.toml` under `cetools/data/`, composition keyed by basename, the task-parameters schema restated as collected problems, `RulesData`, `ValidationReport`, `load_rules`, and `validate_rules`; assert the supported schema version for each kind is a literal constant that is neither read from nor derived from the package release version (FR-003, FR-020a, FR-021, FR-024, FR-025, FR-026, FR-044)
- [X] T015 [P] [US1] Write `tests/unit/test_composition.py` for how an override location composes, at library level and before any command exists: a basename matching a packaged file replaces it, a basename matching nothing is admitted as an addition, a non-`.toml` file is recorded as ignored without failing the load, a dot-prefixed file is passed over silently and appears nowhere including when its extension is also wrong, an override holding only ignored files still composes as packaged while listing them, an existing but empty location composes as packaged, and a location that does not exist is a usage error naming it (FR-028, FR-029, FR-032, FR-032a, FR-032b)
- [X] T016 [P] [US1] Write `tests/integration/test_validation_categories.py` with one case per category in SC-002's closed list: unrecognized name, unrecognized key, malformed entry, well-formed entry in a context that does not admit it, missing required element, wrong value type, unsupported schema version (asserting no other problem from that file), missing or unrecognized kind declaration, replacement kind mismatch, unreadable or malformed TOML, two careers declaring one name, duplicate or absent single-instance kind, and two override files sharing a basename; assert that each whole-file category reports its file with an empty location rather than a fabricated one (SC-002, FR-022)
- [X] T017 [P] [US1] Write `tests/integration/test_reference_career.py` removing each required element of the shipped career in turn and asserting a specific rejection naming what is missing (SC-004, FR-018, FR-019)
- [X] T018 [P] [US1] Write `tests/unit/test_rules_agreement.py` asserting `validate_rules` and `load_rules` agree on the same inputs, valid and invalid alike (FR-023, SC-015)
- [X] T019 [P] [US1] Write `tests/guards/test_no_outside_reads.py` installing a `sys.addaudithook` hook at module import, arming it around a packaged load, and asserting every opened path lies inside the installed package; import everything before arming and filter `__pycache__` (SC-007, research R6)
- [X] T020 [P] [US1] Widen `tests/guards/test_packaging.py` to iterate over every `.toml` under `cetools/data/` in the built wheel and sdist instead of naming `tasks.toml`, asserting each carries its Open Game Content designation and neither Product Identity string, and additionally asserting that the data set read from the built artifact validates without a single problem, since SC-001 asks about the installed package rather than the source tree and a file present in the tree but missing from the wheel would otherwise pass (SC-001, SC-014, FR-046)
- [X] T021 [P] [US1] Rewrite the notice-chain check in `tests/unit/test_licensing.py` to derive what the Section 15 game-data line must cover from the data files actually present rather than comparing against a fixed expected text, so adding a data file without widening the notice fails (FR-047, SC-016)

### Implementation for User Story 1

- [X] T022 [US1] Implement discovery and composition in `src/cetools/rules.py`: walk `importlib.resources.files("cetools.data")` recursively for `*.toml` sorted, collect an override directory or single file, refuse a nonexistent location as a usage error naming it, discard dot-prefixed names before the extension filter, record non-`.toml` names as ignored, and key everything by basename (FR-027, FR-028, FR-029, FR-032, FR-032a, FR-032b, research R5, plan.md trap list) (depends on T015)
- [X] T023 [US1] Implement the task-parameters schema, the kind and schema-version header check with version mismatch suppressing every other problem from that file, the validation driver over the composed set, `RulesData`, `ValidationReport`, `load_rules` and `validate_rules` in `src/cetools/rules.py`; remove `load_task_parameters` (FR-001, FR-001a, FR-002, FR-002a, FR-003, FR-020, FR-020b, FR-021, FR-023, FR-025, FR-044) (depends on T022)
- [X] T024 [US1] Implement the cross-file rules in `src/cetools/rules.py`, checked after every file has been read: duplicate career names, duplicate and absent single-instance kinds, and duplicate override basenames, each naming both files where two are implicated (FR-010a, FR-019b, FR-029a) (depends on T023)
- [X] T025 [P] [US1] Author `src/cetools/data/registries/characteristics.toml` with its OGC designation comment, `schema`, and `schema-version`
- [X] T026 [P] [US1] Author `src/cetools/data/registries/skills.toml` with its OGC designation comment, `schema`, `schema-version`, and an explicit specialty list for every skill
- [X] T027 [P] [US1] Author `src/cetools/data/registries/benefits.toml` with its OGC designation comment, `schema`, and `schema-version`
- [X] T028 [US1] Author `src/cetools/data/careers/navy.toml` from the source material, not from the illustrative values in `contracts/data-files.md`, exercising a commission, a second rank ladder, at least one rank bonus, and a characteristic-gated table (FR-018) (depends on T025, T026, T027)
- [X] T029 [P] [US1] Add the `schema = "task-parameters"` and `schema-version = 1` header lines to `src/cetools/data/tasks.toml`
- [X] T030 [US1] Widen this project's game-data copyright line in `LICENSE-OGL.txt` to cover the whole `src/cetools/data/` directory, and update the matching entry in `SECTION_15_NOTICES` in `tests/conftest.py` in the same change (FR-047)
- [X] T031 [US1] Repoint the autouse cache-clearing fixture in `tests/conftest.py` from `load_task_parameters` to `load_rules.cache_clear()` (plan.md trap list)
- [X] T032 [US1] Add the `provenance` field to `CheckResult` after `seed`, and change `check` to take keyword-only `rules: RulesData | None` in place of `parameters:`, in `src/cetools/tasks.py` (FR-037, FR-045, research R8)
- [X] T033 [US1] Add the packaged provenance block to the `CheckResult` registrations of `as_text`, `as_dict`, and `as_json` in `src/cetools/render.py`, keeping the label column seven characters wide and appending `provenance` last in the JSON key order (contracts/cli.md, contracts/json-output.md)
- [X] T034 [US1] Update the `check` command in `src/cetools/cli.py` to load rules and pass `rules=`, with no new option yet (FR-044)
- [X] T035 [US1] Update `src/cetools/__init__.py` to export the added public surface and drop `load_task_parameters` (contracts/library-api.md, FR-043)
- [X] T036 [US1] Regenerate `tests/golden/check_difficult.txt` and `tests/golden/check_unskilled.txt` with the version held as a placeholder, leaving the three `roll` goldens and all of `tests/golden/pre-loader/` untouched (SC-009)
- [X] T037 [US1] Update the `check` payload expectations in `tests/contract/test_json_contract.py` for the appended `provenance` key, holding the version as a placeholder (contracts/json-output.md)
- [X] T038 [US1] Add the SC-009 comparison to `tests/integration/test_golden.py`: each check golden equals its `tests/golden/pre-loader/` counterpart with exactly the provenance block added, each roll golden is byte-identical, and the dice, modifiers and labels, total, target, outcome, and seed compare field by field

**Checkpoint**: The shipped data set validates, a corrupted copy is rejected with every problem located, every SC-002 category including the cross-file ones is covered, and existing seeds resolve identically. This is the MVP.

---

## Phase 4: User Story 2 - Author rules data with fast, complete feedback (Priority: P2)

**Goal**: One command reports everything wrong with a data set, in either output mode,
with meaningful exit codes.

**Independent Test**: Run the command against the shipped data set and see it pass; run
it against a file seeded with four distinct mistakes and see all four reported in one run.

### Tests for User Story 2 ⚠️ Write first, observe failing

- [X] T039 [P] [US2] Write `tests/integration/test_validate_cli.py` for `cetools validate` with no argument: exit 0 on the packaged set, exit 1 when any problem is found, exit 2 for a usage error, the same outcome in both output modes, and four distinct problems reported from a single run (SC-003, SC-010, FR-038, FR-039, FR-041)
- [X] T040 [P] [US2] Add `ValidationReport` rendering expectations to `tests/unit/test_render.py` for the valid summary, the one-problem-per-line form, the file-as-a-whole form that drops `:LOCATION`, and the `(file, location)` sort order (contracts/cli.md, FR-022)
- [X] T041 [P] [US2] Add the `validation` payload expectations to `tests/contract/test_json_contract.py` with key order `kind`, `valid`, `file_count`, `provenance`, `problems`, and `problems[].location` present but empty for a problem about a file as a whole rather than absent or null (contracts/json-output.md, FR-022)

### Implementation for User Story 2

- [X] T042 [US2] Register `ValidationReport` with `as_text`, `as_dict`, and `as_json` in `src/cetools/render.py` (FR-041, FR-043)
- [X] T043 [US2] Add the `cetools validate` command to `src/cetools/cli.py` with `--json`, problems on stdout, usage errors on stderr, and exit codes 0/1/2 (FR-038, FR-039, FR-041)
- [X] T044 [US2] Print the problems of a failed load to stderr in the same one-line form and exit 1 at the existing single catch site in `src/cetools/cli.py` (contracts/cli.md, FR-025)

**Checkpoint**: Authoring feedback is complete and one run per file is always enough.

---

## Phase 5: User Story 3 - Apply house rules without forking code (Priority: P3)

**Goal**: An explicitly named override location puts one file's content in force while
everything else comes from the packaged data, held to exactly the same standard.

**Independent Test**: Supply an override with a single modified file; confirm the
modified content is in force, every absent file still comes from the shipped data, and a
mistake in the supplied file fails the load exactly as a shipped file would.

**Scope note**: composition and the cross-file rules landed in US1 (T022, T024) and their
mechanics are covered by T015 and T016. What remains here is the story itself: that an
overridden value actually reaches a result, that the override is held to the same standard
as a shipped file and to no more than that, and that both commands accept a location.

### Tests for User Story 3 ⚠️ Write first, observe failing

- [X] T045 [P] [US3] Write `tests/integration/test_overrides.py` for a house rule reaching a result: an overridden survival throw changes what a resolved check produces, a value present in the packaged file and omitted from the override that replaces it is absent rather than inherited, every file the override does not contain still comes from the packaged data, an unrecognized name in an override file fails the load with the same diagnostics a shipped file would produce, and an override file carrying no Open Game Content designation loads without complaint because FR-046 binds shipped files only (SC-005, SC-006, FR-030, FR-031, FR-046)
- [X] T046 [P] [US3] Write `tests/integration/test_data_driven.py` demonstrating a behavior change with no code edit for a career throw, a skill table entry, a rank bonus, and a registry entry, the last by removing a skill name and observing every career reference to it fail (SC-011, FR-013)

### Implementation for User Story 3

- [X] T047 [US3] Add `--rules-data PATH` to the `check` command in `src/cetools/cli.py` (FR-042)
- [X] T048 [US3] Add the optional `PATH` argument to the `validate` command in `src/cetools/cli.py`, accepting a directory or a single file and positioning it by basename alone (FR-040, FR-040a)

**Checkpoint**: House rules take effect through data alone, and a misspelled filename is visible rather than silent.

---

## Phase 6: User Story 4 - Tell whether a result is reproducible (Priority: P4)

**Goal**: Anyone handed a seed and a result can tell what data produced it, and what was
modified if anything was.

**Independent Test**: Load with and without an override and compare the reported
provenance; alter the content of an override file at the same location and confirm the
reported fingerprint changes.

### Tests for User Story 4 ⚠️ Write first, observe failing

- [X] T049 [P] [US4] Write `tests/unit/test_provenance_reporting.py` asserting identical content at two different locations fingerprints identically, differing content fingerprints differently, the reported value is reproducible with `shasum -a 256`, and the reported version equals the installed package version asserted directly rather than through a placeholder (SC-008, FR-036)
- [X] T050 [P] [US4] Write `tests/integration/test_provenance_cli.py` for the overridden text block in both `check` and `validate`: file column padded to the longest basename, disposition column to the longest disposition, effective files first sorted by name then ignored files sorted by name, an ignored line ending at the disposition, and an override holding only ignored files still reading `packaged` while listing them (contracts/cli.md, FR-032a, FR-035)

### Implementation for User Story 4

- [X] T051 [US4] Render the overridden provenance text block with its per-file disposition, fingerprint, and ignored lines in `src/cetools/render.py` (FR-035, FR-037)
- [X] T052 [US4] Emit the provenance JSON object with key order `source`, `version`, `files`, `ignored` and `files[]` sorted by `file` in `src/cetools/render.py` (contracts/json-output.md) (depends on T051)

**Checkpoint**: All four stories are independently functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T053 [P] Add notation round-trip invariants to `tests/property/test_invariants.py`: a rendered entry parses back to an equal value for each of the four forms (plan.md Testing)
- [X] T054 [P] Add `tests/unit/test_library_api.py` exercising every capability in this feature through `import cetools` without invoking the command line (SC-013, FR-043)
- [X] T055 [P] Record the removal of `load_task_parameters` and the `parameters=` keyword under **Breaking changes**, and the added surface under additions, in `CHANGELOG.md` (contracts/library-api.md)
- [X] T056 [P] Document `cetools validate` and `--rules-data` in `README.md`, with no help or prose text naming the trademark as something this tool works with (contracts/cli.md)
- [X] T057 Walk every scenario in `specs/002-rules-data-loading/quickstart.md` by hand and confirm each expected outcome
- [X] T058 Run the full suite plus the project's lint and type checks and resolve anything outstanding

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: T001 must precede every other task in this feature; the evidence it preserves is destroyed the moment the renderer changes.
- **Foundational (Phase 2)**: depends on Setup. **Blocks all user stories.**
- **User Story 1 (Phase 3)**: depends on Foundational. No dependency on US2, US3, or US4. Owns the library-side loader entire: discovery, composition, the schemas, the driver, and the cross-file rules.
- **User Story 2 (Phase 4)**: depends on Foundational and on US1's `validate_rules`.
- **User Story 3 (Phase 5)**: depends on Foundational, on US1's composition and cross-file rules (T022, T024), and on US2's `validate` command for T048. Its own tasks are the story-level evidence and the two command-line surfaces.
- **User Story 4 (Phase 6)**: depends on US1 for an overridden data set to report on and on US3 for the command-line surfaces T050 exercises.
- **Polish (Phase 7)**: depends on all stories being complete.

### Within Foundational

`errors` (T003→T004) → `notation` (T005→T006) → `careers` (T012); `registries`
(T007→T008) → `careers` (T012). `provenance` (T009→T010) is independent of all three.
T013 is independent of everything.

### Within User Story 1

T015 must precede T022, and T016 must precede T023 and T024: each of those
implementation tasks has behavior no earlier test covers, and Principle III admits no
implementation whose failing test has not been observed. Then, within implementation,
composition (T022) before the driver (T023) before the cross-file rules (T024) before
the data files those rules police (T025 through T029), data files before rendering,
rendering before the CLI, CLI before goldens.

### Within Each User Story

Tests are written and observed failing before the implementation they cover, per
Principle III and SC-012.

### Parallel Opportunities

- Foundational: T003, T005, T007, T009, T011, T013 are all different files and can be written together; their four implementation tasks then follow their own test task.
- US1 tests: T014 through T021 are eight different files, all parallel.
- US1 data files: T025, T026, T027, T029 are four different files, all parallel; T028 follows the three registries.
- US2 tests: T039, T040, T041 are parallel.
- US3 tests: T045, T046 are parallel.
- US4 tests: T049, T050 are parallel.
- Polish: T053, T054, T055, T056 are parallel.
- Once Foundational completes, US1 must land before US2/US3/US4 can be finished, so the four stories are not fully parallel across developers here; US2's and US3's test tasks can be written in parallel with US1's implementation.

---

## Parallel Example: User Story 1

```bash
# Launch all eight US1 test tasks together:
Task: "Rewrite tests/unit/test_rules.py for discovery, composition, and the loader"
Task: "Write tests/unit/test_composition.py for override positioning and dispositions"
Task: "Write tests/integration/test_validation_categories.py for SC-002's closed list"
Task: "Write tests/integration/test_reference_career.py for SC-004's removal matrix"
Task: "Write tests/unit/test_rules_agreement.py for SC-015"
Task: "Write tests/guards/test_no_outside_reads.py for SC-007"
Task: "Widen tests/guards/test_packaging.py for SC-001 and SC-014"
Task: "Rewrite the notice-chain check in tests/unit/test_licensing.py for SC-016"

# Then launch the three registry data files together:
Task: "Author src/cetools/data/registries/characteristics.toml"
Task: "Author src/cetools/data/registries/skills.toml"
Task: "Author src/cetools/data/registries/benefits.toml"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Complete Phase 1: Setup. T001 first, always.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. **STOP and VALIDATE**: the shipped data set validates, each SC-002 category is
   rejected with its problem located, and every pre-loader golden's resolution outcome
   is unchanged.

That gate is reachable at this point only because the cross-file rules land in US1. Three
of SC-002's categories are cross-file, so leaving them to a later story would have made
the gate unreachable at the moment it is stated.

That is a shippable increment on its own: the existing task check keeps working, now
through a loader that catches a bad edit to the data instead of absorbing it.

### Incremental Delivery

1. Setup + Foundational → the schema and the notation exist.
2. + US1 → the loader is trustworthy. **MVP.**
3. + US2 → authoring the remaining careers is one run per file.
4. + US3 → house rules take effect without a code edit.
5. + US4 → a result carries a complete reproduction key.

---

## Notes

- **T001 is not optional and not reorderable.** SC-009 compares against the outputs
  committed with the previous feature; regenerating first destroys the evidence.
- **Test-first is evidenced, not asserted** (SC-012): commit each test task's expected
  values in a change that precedes the implementing change, and observe the failure.
- **Composition and cross-file rules belong to US1**, not to US3. Every behavior T022 and
  T024 implement has its failing test in the same phase, and the three cross-file entries
  in SC-002's closed list are satisfied at the MVP gate rather than two phases after it.
  US3 keeps the story-level evidence and the command-line surface.
- Traps already resolved in the contracts, repeated here because they are easy to lose:
  the fingerprint hashes raw bytes and must not decode first; a version mismatch
  suppresses every other problem from that file; the dot filter runs before the extension
  filter; an ignored file is a separate tuple on `Provenance`, not a third `Disposition`
  member; `load_rules` is cached only for the no-override call; `Rules:` is no longer
  than `Total:` so the label column width does not change; never delete
  `tests/golden/pre-loader/` when regenerating goldens; every committed golden and JSON
  fixture holds the package version as a placeholder; a problem about a file as a whole
  carries an empty location, never a fabricated one, and the rendered line drops
  `:LOCATION` while the JSON keeps the key with an empty value.
- Consult the `fluent-python:*` skills plan.md names when writing each module.
- [P] tasks touch different files and have no dependency on incomplete tasks.

---

## Phase 8: Convergence

Appended by `/speckit-converge` after assessing the codebase against spec.md, plan.md,
and this file. Everything else converged: the suite passes, the shipped data set
validates, all thirteen SC-002 categories are rejected, provenance renders in both
modes, and `tests/golden/pre-loader/` is intact.

- [ ] T059 **CRITICAL, not done, deliberately**: restore the test-first evidence Constitution Principle III and SC-012 require, which the branch history does not carry: `22bcbb2` lands `notation.py`, `registries.py`, `careers.py`, and `provenance.py` together with `test_notation.py`, `test_registries.py`, `test_careers.py`, and `test_provenance.py`, and `8ffc9a0`, `a7ed647`, and `11cb32b` do the same for `rules.py`, `tasks.py`, `render.py`, `cli.py`, and the data files, so no test commit precedes any implementing commit; the branch history is left as it stands and the gap is recorded instead, under **Recorded Deviation** in plan.md, so a reviewer sees that SC-012 is open on this branch rather than assuming it satisfied; rewriting the history was declined because a reconstructed red state asserts test-first exactly as much as the present history does (Constitution III, SC-012)
- [X] T060 Author `src/cetools/data/careers/navy.toml` from the source material rather than from the illustrative values in `contracts/data-files.md`, which is what currently ships: the enlisted ladder holds only ranks 1 and 5 and titles rank 1 `Recruit`, the officer ladder only ranks 1, 2, and 4, and the mustering-out cash and benefits rows do not match the source; a career with gaps in both rank ladders is not the complete, SRD-faithful reference FR-018 requires, and every element the schema exercises must survive the rewrite so `tests/integration/test_reference_career.py` still proves SC-004 per FR-018 and plan.md Implementation Notes (partial)
- [X] T061 Add a case for an *unrecognized* kind declaration to `tests/integration/test_validation_categories.py` beside `test_missing_kind_declaration`: SC-002's closed list names "a missing or unrecognized kind declaration", and only the missing half has a case, so the unrecognized half can regress into silent acceptance untested per SC-002 and FR-001a (partial)
- [X] T062 Assert `problem.location == ""` on every whole-file category in `tests/integration/test_validation_categories.py`, not only on `test_file_not_well_formed_toml_at_all`: the unsupported schema version, the missing and unrecognized kind, the replacement kind mismatch, two careers declaring one name, a duplicate or absent single-instance kind, and two override files sharing a basename all report about the file as a whole and none of them currently pins the empty location, which is what T016 asked for per FR-022 and SC-002 (partial)
- [X] T063 Reconcile the package version the tool reports with the one the project declares and documents: `pyproject.toml` declares `2026.08.1`, PEP 440 normalization makes `importlib.metadata.version("cetools")` return `2026.8.1`, and every rendered result therefore reads `Rules: packaged (cetools 2026.8.1)` while `README.md`, `specs/002-rules-data-loading/quickstart.md`, and `contracts/cli.md` all document `2026.08.1`; either render the declared form or correct the documented outputs, and add the assertion that keeps the two from drifting again, per FR-033a and the constitution's CalVer `YYYY.0M.INC1` scheme (contradicts)

---

## Phase 9: Convergence

Appended by a second `/speckit-converge` run. Phase 8's T060 through T063 are done and
verified; T059 is still open by the deliberate choice recorded under **Recorded
Deviation** in plan.md and is not restated here. Everything else converged: 535 tests
pass, `black`, `isort`, and `flake8` are clean over `src` and `tests`, the packaging
guard runs unskipped and proves the built wheel and sdist validate, every SC-002
category is rejected with its location pinned, and SC-009's one-added-line comparison
against `tests/golden/pre-loader/` holds.

- [X] T064 Export `NotationProblem` and `SkillResolution` from `src/cetools/__init__.py` and add them to `__all__`, then extend `tests/unit/test_library_api.py` to reach the malformed-entry result of `cetools.parse_entry` and the four outcomes of `cetools.SkillRegistry.resolve` through `import cetools` alone: `parse_entry` is exported and returns `NotationProblem` for a malformed entry or a form its context does not admit, and `SkillRegistry.resolve` returns `SkillResolution`, so today a library-only caller can obtain both values but cannot name either type without reaching past the package into `cetools.notation` and `cetools.registries`, and the SC-013 test exercises only the four well-formed forms, leaving the failure path proved nowhere through the surface FR-043 binds (FR-043, SC-013, contracts/library-api.md) (partial)
- [X] T065 Reconcile the notation section of `specs/002-rules-data-loading/contracts/library-api.md` with `src/cetools/notation.py`, which contradicts it in two ways: the contract says `parse_entry` "Raises `RulesDataError` for a malformed entry or a form the context does not admit" while the implementation returns a `NotationProblem`, and the contract says `EntryContext` is a `StrEnum` while the implementation makes it a plain `Enum` of `auto()` members; the return-a-problem model is the one plan.md's "validation is a function, not a control flow" requires and the contract text is what should move, but `EntryContext`'s enum base is a live difference in an exported type and must be settled rather than left to whichever artifact a reader consults first — settling it is also what makes T064's export list correct (plan: contracts/library-api.md notation section, plan.md Summary) (contradicts)
- [X] T066 Qualify the requirement references in the files this feature edited that now resolve to a different requirement under this feature's spec: `src/cetools/tasks.py` cites this feature's FR-037 at line 122 and then `001-dice-task-engine`'s FR-022 and FR-018 at lines 124 and 127 of the same docstring, where FR-022 is problem location and FR-018 the reference career here; `src/cetools/render.py` lines 85 and 88 and `tests/unit/test_licensing.py` lines 71 and 141 do the same with FR-029 and FR-035, which mean basename positioning and overridden-file provenance here; name the feature alongside each such reference so a bare `FR-NNN` never spans two numberings, and while in `tasks.py` refresh line 120, which still describes `parameters.default_difficulty()` after T032 replaced the `parameters=` keyword with `rules=` (FR-018, FR-022, FR-029, FR-035, contracts/library-api.md) (contradicts)

---

## Phase 10: Convergence

Appended by a third `/speckit-converge` run. Phase 9's T064 through T066 are done and
verified; T059 is still open by the deliberate choice recorded under **Recorded
Deviation** in plan.md and is not restated here. Everything else converged: 537 tests
pass, `black`, `isort`, and `flake8` are clean over `src` and `tests`, the guards run
unskipped, override composition behaves as `contracts/data-files.md` specifies for
replacement, addition, ignored, dot-prefixed, duplicate-basename, and nonexistent
locations, and SC-009's one-added-line comparison against `tests/golden/pre-loader/`
holds.

- [X] T067 Implement the "cannot be read" half of FR-020a, which is absent: `src/cetools/rules.py` reads every data file with a bare `read_bytes()` at lines 320 and 346 and handles no `OSError`, so a data file present but unreadable does not become a collected problem — `cetools validate` over an override holding a mode-000 `navy.toml` dies with an uncaught `PermissionError` traceback, which breaks FR-021's collect-everything, leaves the remaining files unchecked contrary to FR-020a's own second sentence, and escapes the single `except CetoolsError` site that `contracts/library-api.md` promises catches everything the library raises; two neighbouring cases fail silently instead, a broken symlink named `navy.toml` in an override (`Path.is_file()` is false, so it is passed over with no report and the house rule quietly does not take effect) and a `PATH` that exists but is neither a regular file nor a directory such as `/dev/null` (composed as `packaged` with no report, which is the mistyped-path-that-appears-to-succeed failure FR-028 exists to remove). Wrap the reads so an unreadable file is a `ValidationProblem` naming the file with an empty location per FR-022, refuse a location that is neither file nor directory as a usage error naming it per FR-028, and add the missing SC-002 case to `tests/integration/test_validation_categories.py` beside `test_file_not_well_formed_toml_at_all`, since SC-002's closed list names "a file that is not well-formed at all, **or cannot be read**" and only the first half has a case (FR-020a, FR-021, FR-022, FR-028, SC-002, contracts/library-api.md) (missing)
- [X] T068 Name the governing registry in the `expected` text of an unrecognized-name problem: `src/cetools/careers.py` reports `a known skill name`, `a known characteristic code`, and `a known benefit item` at lines 209, 222, 235, 242 and 248, while FR-013 requires the report to carry "which registry it was checked against" and `contracts/cli.md` line 133 illustrates the intended form, `expected a name in the skills registry` — a form the shipped output never emits although the synthetic fixtures in `tests/contract/test_json_contract.py` and `tests/integration/test_validate_cli.py` already assert rendering against it. Say which of the three registries was consulted, and update the one test that pins the current wording, `tests/integration/test_overrides.py` line 97 (FR-013, FR-005, contracts/cli.md) (partial)

---

## Phase 11: Convergence

Appended by a fourth `/speckit-converge` run. Phase 10's T067 and T068 are done and
verified; T059 is still open by the deliberate choice recorded under **Recorded
Deviation** in plan.md and is not restated here. Everything else converged: 542 tests
pass with no skips, `black`, `isort`, and `flake8` are clean over `src` and `tests`, the
built wheel and sdist validate, quickstart Scenarios 1, 4, 4b, and 5 behave as written
when run by hand, and SC-009's one-added-line comparison against
`tests/golden/pre-loader/` holds.

- [X] T069 Stop the single-instance-kind presence check in `src/cetools/rules.py` from reporting a file that is present as absent: a file of one of the four single-instance kinds that is rejected at the header stage never reaches `parsed`, so the loop over `_SINGLETON_KINDS` at lines 525 through 545 finds no declarer and appends a second problem reading `tasks.toml: found no file; expected exactly one file declaring kind 'task-parameters'` for a file that is sitting in the composed data set — an override `tasks.toml` carrying `schema-version = 99` reports both `found version 99` and `found no file`, an override `skills.toml` declaring `schema = "skils"` reports both `unrecognized kind 'skils'` and `no file`, and a `benefits.toml` that is malformed TOML, unreadable, or a replacement whose declared kind mismatches does the same; this contradicts contracts/data-files.md rule 2, which says a file rejected on its version has its contents left uninterpreted "so no further problem is reported from that file", contradicts quickstart Scenario 2, which asks a reviewer to expect "a version-mismatch problem and *no other* problem from that file", and contradicts FR-002's reason for existing, that such a file "must fail as a version mismatch and not as a cascade of confusing validation errors"; it also states something false, since the report names a file and then says there is none, which is the opposite of the sharp diagnostic the strictness in this feature is for. Distinguish a kind that no composed file declares from a kind whose file was rejected earlier, reporting the absent-kind problem only in the first case, and add a case to `tests/integration/test_validation_categories.py` beside `test_unsupported_schema_version_reports_nothing_else_from_that_file` that makes the same assertion for a single-instance kind rather than for a career, since that test uses `navy.toml` and a career is the one kind this defect cannot reach (FR-002, FR-010a, FR-021, contracts/data-files.md, quickstart Scenario 2) (contradicts)
- [X] T070 Reject a parenthesized specialty on a characteristic check or adjustment in `src/cetools/notation.py`: `_parse_name` splits a specialty off the name of every form, but the check and adjustment branches at lines 172 through 175 build `CharacteristicCheck` and `CharacteristicAdjustment` from `base` alone and drop the specialty on the floor, so `INT (Foo) 4+` validates as a gate on `INT` and `STR (Foo) +1` as an adjustment to `STR`, with the discarded text reported nowhere — content an author wrote has no effect and no diagnostic, which is the silent-typo failure this feature exists to remove, and it evades FR-013's requirement that a name be matched exactly against its governing registry, since the name as written is `INT (Foo)` and the characteristics registry holds only `INT`. Report such an entry as malformed per FR-009, naming the entry as written and the forms acceptable in that position; add the two cases to the malformed-entry table in `specs/002-rules-data-loading/contracts/notation.md`, whose grammar currently admits a specialty on every form and so is the artifact that has to move, and to `tests/unit/test_notation.py` beside the other malformed cases (FR-009, FR-013, contracts/notation.md) (partial)

---

## Phase 12: Convergence

Appended by a fifth `/speckit-converge` run. Phase 11's T069 and T070 are done and
verified; T059 is still open by the deliberate choice recorded under **Recorded Deviation**
in plan.md and is not restated here. Everything else converged: 547 tests pass with no
skips, `black`, `isort`, and `flake8` are clean over `src` and `tests`, the guards run
unskipped and the packaging guard really builds a wheel and an sdist, every clause of
FR-014 through FR-019b is correctly implemented, all thirteen SC-002 categories have at
least one case, exit status stays within `{0, 1, 2}` on every reachable path in both output
modes, quickstart Scenarios 1 through 9 behave as written when run by hand, fingerprints
match `shasum -a 256` across two locations, and SC-009's one-added-line comparison against
`tests/golden/pre-loader/` holds.

This round's yield is larger than the last two because the method changed rather than
because the code regressed: findings were sought by mutating a scratch copy of the tree and
re-running the suite, which surfaces required behavior that no test would notice losing.
Most of what follows is therefore unproven behavior rather than wrong behavior, and each
such task says so.

- [X] T071 Traverse an override location explicitly instead of through `Path.rglob`, which
      drops whole subtrees in silence: `src/cetools/rules.py:407` iterates
      `override_path.rglob("*")`, and `rglob` defaults to `recurse_symlinks=False` and
      swallows `OSError`, so an override holding `linked/navy.toml` behind a symlinked
      directory, or a subdirectory the process cannot list, or an override root that is
      itself unreadable, composes nothing, reports `Rules: packaged (cetools 2026.8.1)` over
      five files, and exits 0 — the author's house rules are entirely out of force while the
      run appears to succeed, which is verbatim the failure FR-028 names as the one this
      feature exists to remove, and it contradicts contracts/data-files.md's composition
      rule that every file under the location, at any depth, is collected. The inconsistency
      is stark three lines below at `rules.py:408-410`, where T067's comment explains that a
      broken symlink must be read rather than passed over "because passing it over would
      leave a misnamed house rule silently out of force": a directory-level traversal
      failure currently gets exactly the treatment that comment rejects for a file. Walk the
      tree with `iterdir` so a directory that cannot be listed becomes a `ValidationProblem`
      naming it with an empty location per FR-022, the way `_collect_entry` already answers
      an unreadable file at `rules.py:372-376`, and add cases beside
      `tests/unit/test_composition.py:95`, which today covers only a broken symlink to a
      file (FR-028, FR-029, FR-020a, FR-022, contracts/data-files.md) (partial)
- [X] T072 Make the SC-016 notice-coverage check capable of failing, which it is not:
      `tests/unit/test_licensing.py:210-219` builds `data_files` by globbing
      `src/cetools/data/**/*.toml` and then asserts that each resulting path starts with
      `src/cetools/data/`, which is true by construction for every path that glob can
      produce, so the loop is a tautology and the only live assertions are that the notice
      names that prefix and appears in `LICENSE-OGL.txt`. Adding a sixth data file to a
      scratch copy of the tree and leaving `LICENSE-OGL.txt` untouched leaves this test and
      the whole of `tests/unit/test_licensing.py` passing, which is precisely the outcome
      SC-016 requires to fail and precisely the weakness FR-047 was written to remove, and
      the test's own comment at lines 199-203 states the job it is not doing. The check is
      also blind in the other direction: it never looks outside `src/cetools/data/`, so an
      Open Game Content file shipped anywhere else is covered by neither this test nor the
      designation guard at `tests/guards/test_packaging.py:65-70`, which filters on the same
      directory. Derive the coverage obligation from the data files the built distribution
      actually contains, as SC-014 already does, and assert that every one of them falls
      under a path the game-data notice names. The substantive obligation is met today —
      the directory-wide line at `LICENSE-OGL.txt:137-138` does cover all five shipped files
      — so this is the mechanism failing, not the licence (FR-047, SC-016, Constitution
      Licensing & Distribution) (partial)
- [X] T073 Type-check the declared schema version before comparing it: `src/cetools/rules.py:529`
      tests `declared_version != supported` against a bare `toml_data.get("schema-version")`,
      and Python equality makes `True == 1` and `1.0 == 1`, so a career file declaring
      `schema-version = true` or `schema-version = 1.0` passes the version gate and validates
      clean, while `schema-version = "1"` is correctly refused. Every other integer-valued
      field in the same module guards itself at `rules.py:298` with
      `not isinstance(value, int) or isinstance(value, bool)`, so the omission is asymmetric
      rather than a considered line, and it defeats FR-002's requirement that a file be refused
      unless its declared version is the one supported for its kind as well as FR-020b's
      requirement that a value of the wrong type report the type found and the type expected.
      Apply the same guard, report a non-integer version as a wrong-typed value rather than as
      a version mismatch, and add the case beside
      `tests/integration/test_validation_categories.py:88` (FR-002, FR-020b, FR-022) (partial)
- [X] T074 Stop rejecting a bare entry whose specialty ends in a digit:
      `src/cetools/notation.py:157-158` applies the "the trailing token contains a digit but
      matches no suffix form" heuristic to the last whitespace-separated token before the
      name is split into base and specialty, so the closing `)` of `Blade (Mark 2)` is caught
      and the entry is reported malformed, while the same specialty in the grant form
      `Blade (Mark 2) 1` parses correctly into `SkillReference(name='Blade',
      specialty='Mark 2')`. contracts/notation.md's grammar admits any run of
      non-parenthesis characters as the text of a specialty and its parsing table sends
      anything matching no suffix form to the bare case, so the contract requires acceptance;
      the contract's own Trap section documents only the opposite over-match, a name ending
      in a bare integer, which is evidence this over-rejection was never decided on. Split
      the name before applying the heuristic, and add the case to
      `tests/unit/test_notation.py`; note that the property strategy at
      `tests/property/test_invariants.py:142` excludes digits from generated specialties and
      so cannot find this (FR-006, FR-009, contracts/notation.md) (contradicts)
- [X] T075 Name the forms acceptable in the position when reporting a malformed entry, which
      FR-009 requires in terms and which only the wrong-form path currently does: every
      malformed-entry site in `src/cetools/notation.py` (lines 113, 121, 125, 141, 156, 158
      and 170) reports the context-free string `one of the four notation forms`, while the
      inadmissible-form path at `notation.py:163` consults `_ADMISSIBLE_FORMS[context]`. Since
      a table's characteristic gate admits exactly one form and a mustering-out benefits entry
      exactly two, the message is not merely incomplete but false — `parse_entry('INT +4+',
      GATE)` tells an author that four forms were available where one was. FR-009a restates
      the same clause as its own reason for existing, that without a defined subset per field
      FR-009's promise "has nothing to report". While at these sites, report the entry as
      written per FR-009 rather than the stripped text: `'  Pilot -  '` currently reports
      `found='Pilot -'` everywhere except the empty-entry case at `notation.py:141`
      (FR-009, FR-009a, contracts/notation.md) (partial)
- [X] T076 Report every non-string element of a skill's specialty array rather than only the
      first: `src/cetools/registries.py:171` finds one offending index with
      `next((i for i, s in enumerate(specialties) if not isinstance(s, str)), None)` and then
      `continue`s to the next skill, so `Blade = ["Cutlass", 5, 7, 9]` yields one problem while
      the equivalent malformation in `parse_benefits` (`registries.py:218-228`) and
      `parse_characteristics` (`registries.py:116-127`) yields three, both of those looping and
      reporting each element. This is the one field in the feature where fixing the reported
      mistake reveals the next one on the following run, which is exactly what FR-021's
      collect-everything and SC-003's "the number of runs needed to find every problem in a
      file is always one" forbid, and the asymmetry with its two sibling parsers shows it was
      not a deliberate line. Loop as they do, and extend `tests/unit/test_registries.py` with a
      multiple-bad-element case (FR-021, SC-003) (partial)
- [X] T077 Settle how a problem that names two files reports them, because the code and the
      contracts disagree: `src/cetools/rules.py:575` and `rules.py:629` build
      `file=", ".join(...)` for the two multi-file categories, emitting
      `"file": "navvy.toml, navy.toml"` in `--json` output, while
      contracts/json-output.md:134 and data-model.md type `problems[].file` as the composition
      key of *the* file, singular, and contracts/cli.md:152-153 justifies the text line's shape
      on the grounds that leading with the file "makes the report greppable and sortable" — a
      consumer grouping by composition key gets a phantom key matching no file, and one
      filtering for `navy.toml` misses this problem entirely. FR-019b and FR-010a do require
      both files named, and FR-029a already achieves that at `rules.py:418-424` by naming both
      paths in `found` while leaving `file` a single key, so the shape that satisfies every
      artifact already exists in the module. Either follow FR-029a's precedent at both sites or
      amend the two contracts to admit a multi-file form, and update
      `tests/integration/test_validation_categories.py:204-214`, which today asserts only
      substring containment and so passes under either choice (FR-019b, FR-010a, FR-022,
      contracts/json-output.md, contracts/cli.md) (contradicts)
- [X] T078 Apply the dot-prefixed carve-out to directories, not only to files:
      `src/cetools/rules.py:367-368` returns early on a basename beginning with a dot, but the
      traversal above it descends dot-prefixed directories, so every file inside one is treated
      as authored content. Pointing `cetools validate` at an override directory that is a git
      checkout — the obvious way to share a rule set — produces eighteen `ignored` lines drawn
      from `.git/`, naming `HEAD` and `applypatch-msg.sample` among others, and a `.toml` under
      such a directory composes silently into the data set: `.hidden/navy.toml` replaces the
      packaged Navy career and is reported as `replaced`. The literal text of FR-032b and of
      contracts/data-files.md's third composition rule draws the line at the file's own leading
      dot, so the code follows the letter while defeating both stated purposes — "a report full
      of such files is a report that stops being read", and the line drawn "at authorship
      rather than at a list of known filenames", `.git/config` having been written by no
      author. Decide this against FR-032b's rationale rather than its wording, amend the
      requirement and the contract rule if the line moves to the directory, and add both cases
      to `tests/unit/test_composition.py` (FR-032b, FR-032a, contracts/data-files.md) (partial)
- [X] T079 Assert the file and the location on the SC-002 categories whose problems are not
      about the file as a whole, which T062 supplied for the whole-file categories and never
      for their complement: `tests/integration/test_validation_categories.py:29-36` checks an
      unrecognized name by asserting only `found` and `expected`, `:47-52` checks a malformed
      entry by asserting only that `"Comms 2x"` appears in `found`, and `:55-62` checks a
      well-formed entry of an inadmissible form by asserting only that `"INT 4+"` appears in
      `found`. SC-002 requires the report to name the file and, where the problem is not about
      the file as a whole, the location within it, so all three of these could regress into
      whole-file problems carrying `location == ""` against any file and still pass. The
      behavior is correct today — each emits `file` `navy.toml` and a location such as
      `tables.service.entries[0]` — so this is the assertion missing, not the behavior
      (SC-002, FR-022) (partial)
- [X] T080 Widen the Open Game Content designation in the two prose artifacts that still name
      only the file which shipped before this feature: `CHANGELOG.md:108-111` states that
      `LICENSE-OGL.txt` "covers `src/cetools/data/tasks.toml` as Open Game Content" when four
      more OGC files now ship, and `CHANGELOG.md` travels in the sdist per `pyproject.toml:37`,
      so the under-inclusive designation is distributed; `CONTRIBUTING.md:136-140` heads its
      licensing bullet with "`src/cetools/data/tasks.toml` is Open Game Content under OGL
      1.0a" and then instructs a contributor that a new OGC file "must be named as OGC in the
      README's licensing section", which `README.md:92-96` no longer does per file, having
      moved to designating the whole directory. Both contradict the widened Section 15 line at
      `LICENSE-OGL.txt:137-138` and the constitution's requirement that the repository and
      package clearly designate which files are OGC, and the changelog omission is also a
      user-visible change this feature made without the entry the project requires in the same
      commit. While in CONTRIBUTING.md, refresh `:155-158`, which enumerates what
      `tests/unit/test_licensing.py` checks and omits both checks this feature added
      (Constitution Licensing & Distribution, FR-046, FR-047) (contradicts)
- [X] T081 Pin the characteristic gate that FR-018 requires the reference career to exercise,
      and prove FR-015's clause that a gate is permitted on every table rather than fixed to
      one: deleting `requires = "EDU 8+"` from `src/cetools/data/careers/navy.toml:43` leaves
      all 547 tests passing, and no test anywhere asserts anything about a packaged career's
      gate, so the one element of FR-018's list that SC-004 does not reach by removing a
      required element is proved by nothing — the other three fail something when removed, the
      commission at `tests/integration/test_overrides.py:81` and the second ladder and the rank
      bonus at `tests/integration/test_data_driven.py:46` and `:61`. Separately, restricting
      `src/cetools/careers.py:352-354` so that `requires` is an unrecognized key on every table
      except `advanced-education` also leaves 547 tests passing, because the only gate anywhere
      in the suite or the shipped data sits on that one table; FR-015 says in terms that "the
      gate is optional on every table rather than fixed to one of them", which is the clause
      nothing holds. Add a reference-career assertion for the gate and a unit case placing a
      gate on a different table (FR-018, FR-015, SC-004) (missing)
- [X] T082 Cover the required sub-keys and the two non-emptiness rules that no test would
      notice losing, each confirmed by mutating a scratch copy of the tree and observing all
      547 tests still pass: making `throws.*.target` optional at `src/cetools/careers.py:300`
      against FR-014's "The target is required", making `ranks[].rank` optional at
      `careers.py:478` against FR-016's requirement that each rank carry its position, making
      `ranks[].title` optional at `careers.py:479` against the same requirement's "its title",
      making `ladders[].name` optional at `careers.py:564`, removing the empty-array rejection
      for a ladder's `ranks` at `careers.py:511-518` against FR-016's "A ladder MUST carry at
      least one rank", and removing it for `mustering-out.benefits` at `careers.py:709-722`
      against FR-017's "both MUST declare at least one entry". The two non-emptiness gaps are
      asymmetric rather than a drawn line, since `tests/unit/test_careers.py:380-397` already
      covers the sibling cases of empty `entries`, empty `ladders`, and empty `cash`. These
      fall in the seam between FR-019's top-level enumeration, which SC-004 tests exhaustively
      and correctly, and the per-object tables in contracts/data-files.md, which nothing tests
      (FR-014, FR-016, FR-017, contracts/data-files.md) (missing)
- [X] T083 Test FR-005's "and no other" clause in both directions, which nothing currently
      does: `tests/unit/test_careers.py:401-408` rejects `"Not A Real Skill"` in a skill table
      and `:428-433` rejects `"Not A Real Benefit"` in a benefits table, but both names are
      absent from *both* registries, so an implementation that consulted both registries and
      accepted a name found in either would pass every test in the suite. FR-005 states the
      requirement together with its reason — "so that a skill name is never accepted because it
      happens to appear in the benefit items registry" — and the spec's Edge Case about one
      name in two registries rests on the same guarantee. Put a benefits-only name such as
      `Low Passage` in a skill table and a skills-only name such as `Vacc Suit` in a benefits
      table, and assert each is rejected against the registry its position selects. The
      implementation is correct today, so this is the proof missing (FR-005, SC-002) (missing)
- [X] T084 Add regression cases for the five career key-closure sites that survive neutering:
      the career top level at `src/cetools/careers.py:757-761`, inside a throw at `:272-274`,
      inside a skill table at `:352-354`, inside a rank at `:474-476`, and inside a ladder at
      `:562` each leave all 547 tests passing when the unrecognized-key check is removed. FR-020
      is formally covered by one case, `mustering-out.chash` at
      `tests/integration/test_validation_categories.py:39-44`, so SC-002's closed list is
      satisfied and this is coverage rather than a category gap — but FR-020 exists because a
      misspelled key "would otherwise leave the throw or table that key configures silently
      inoperative", and a misspelled `charactristic` inside a throw is today caught by nothing a
      regression would trip. The closed sets of throw names and table names are properly pinned
      at `tests/unit/test_careers.py:293-310`; it is the key closure within each object that is
      not (FR-020, SC-002) (partial)
- [X] T085 Assert the three distinguishable messages FR-007 requires, which exist in the code
      and are pinned nowhere: `src/cetools/careers.py:246-258` builds distinct text for
      `SPECIALTY_NOT_ALLOWED`, `UNRECOGNIZED_SPECIALTY`, and `UNRECOGNIZED_SKILL`, and a
      repository-wide search for those strings returns only that source line.
      `tests/unit/test_registries.py:125-133` and `tests/unit/test_library_api.py:102-103`
      assert the `SkillResolution` members rather than the rendered problems, and
      `tests/integration/test_validation_categories.py:270` reaches the
      `UNRECOGNIZED_SPECIALTY` branch through `"Gunnery (Turret)"` but asserts only
      `len(navy_problems) >= 4`, so the `SPECIALTY_NOT_ALLOWED` branch has no end-to-end test at
      all. FR-007 requires a specialty given for a skill that has none and a specialty the
      registry does not list for that skill to be "reported distinguishably from an
      unrecognized skill name", which is a claim about the reported problem and not about the
      enum (FR-007, SC-002) (missing)
- [X] T086 Report every ignored file rather than every distinct ignored basename:
      `src/cetools/rules.py:402` accumulates `ignored` as a `set[str]` and `rules.py:370` adds
      the basename alone, so an override containing `a/notes.md` and `b/notes.md` yields
      `provenance.ignored == ("notes.md",)` and one of the two author-written files that failed
      to take effect is named nowhere. FR-035 requires that any file FR-032a marks ignored be
      named, unconditionally, and FR-032a's whole bargain is that admitting an unrecognized
      filename is paid for by reporting it — a file reported under another file's name is not
      reported. Declining to raise FR-029a's duplicate-basename problem for ignored files is
      defensible, since an ignored file claims no composition position, but the naming
      obligation is separate from it (FR-035, FR-032a) (partial)
- [X] T087 Match a benefit item against the registry as written rather than after
      renormalization: `src/cetools/notation.py:190` reassembles the name as
      `f"{base} ({specialty})"` from the split made at `notation.py:104`, so `Weapon(Blade)` and
      `Weapon  (Blade)` both resolve to `BenefitItem(name='Weapon (Blade)')`. Two things follow.
      contracts/notation.md's grammar makes whitespace before the parenthesis mandatory, so
      accepting `Weapon(Blade)` is more permissive than the contract; and FR-013 requires every
      name to be "matched exactly", giving case folding as the example of the quiet widening it
      forbids, while inserting or collapsing a space widens the notation the same way — a
      registry item spelled `Weapon(Blade)` could never be matched at all, and one spelled
      `Weapon (Blade)` answers to three written forms. Unreachable through the shipped
      `benefits.toml`, which holds no parenthesized item, and so reachable only through an
      override registry; the property strategy excludes parentheses and no unit test covers a
      parenthesized benefit item (FR-013, contracts/notation.md) (contradicts)
- [X] T088 Prove that schema versions are counted per kind, which is FR-002a's whole claim and
      which no test could currently falsify: `src/cetools/rules.py:45-51` keys
      `_SUPPORTED_VERSION` by kind and is structurally correct, but every file in every test
      declares version 1 for every kind, the only version cases being
      `tests/integration/test_validation_categories.py:88` and `:99`, which supply 2 and 99
      against a single expectation of 1, and `tests/unit/test_rules.py:248`, which asserts only
      that the constant is not the package version. Nothing raises one kind's supported version
      and then asserts that a user-supplied file of an untouched kind still validates, which is
      the behavior FR-002a states — "a change to one kind's shape MUST NOT invalidate a
      user-supplied file of a kind whose shape did not change" — and the sole justification the
      spec's Assumptions give for the version field's existence at all (FR-002a, SC-012)
      (missing)
- [X] T089 Reconcile three stale artifact passages against the output and types the code
      actually produces: contracts/cli.md:90-92 shows an ignored-only provenance block padding
      `notes.md` to eleven columns, while `src/cetools/render.py:35,47` pads to the longest
      basename present and the contract's own prose rule at line 80 agrees with the code, so
      only the worked example is wrong; contracts/cli.md:134 shows
      `found a string; expected an integer` where `src/cetools/rules.py:301` and
      `src/cetools/careers.py:165-166` emit the Python type name, `found str`, with the suite
      itself split between the two spellings at `tests/contract/test_json_contract.py:41` and
      `tests/unit/test_render.py:390`, both hand-built fixtures that pin neither, so this one
      needs deciding rather than merely correcting — a Python type name reaching a user-facing
      report is a legitimate thing to settle either way; and data-model.md:99 says "Three
      distinguishable outcomes when resolving a `SkillReference`" directly above its own
      four-row table at `:101-107`, where `src/cetools/registries.py:32-40` defines four
      `SkillResolution` members and contracts/notation.md:92 says four (FR-020b, FR-007,
      contracts/cli.md, data-model.md) (contradicts)
- [X] T090 Make the identical-content override assertion capable of failing:
      `tests/unit/test_composition.py:129-134` is the only test using byte-identical override
      content and it asserts `directory_result.provenance.files == file_result.provenance.files`,
      which holds vacuously if both are empty, so an implementation that compared content and
      composed an identical override as packaged would satisfy it. The spec's Edge Case at
      lines 252-254 requires such a file to be "still recorded as overridden, because provenance
      describes where content came from, not whether it differs". The behavior is correct today,
      `src/cetools/rules.py:432` never comparing content, so this is an assertion that the
      files tuple is non-empty and carries the expected disposition (spec Edge Case, FR-035)
      (partial)
- [X] T091 Declare the package's licence in machine-readable metadata: `pyproject.toml:5-11`
      sets `license-files` but carries no `[project] license` expression and no licence
      classifier, so the built wheel's METADATA holds only two `License-File` lines and PyPI
      and `pip show` report the package as unlicensed, while the constitution states outright
      that source code is licensed under GPL-3.0 and that the repository and package must
      clearly designate what is GPL-licensed code. `tests/unit/test_licensing.py:110-115`
      checks the `license-files` list and nothing beyond it. This predates the feature and is
      inherited from `001-dice-task-engine` rather than introduced here, so it may reasonably
      be deferred; it is recorded because the licensing obligations this feature discharges are
      the occasion on which it was found (Constitution Licensing & Distribution) (missing)

---

## Phase 13: Convergence

Appended by a sixth `/speckit-converge` run. Phase 12's T071 through T091 are done and
verified; T059 is still open by the deliberate choice recorded under **Recorded Deviation**
in plan.md and is not restated here. Everything else converged: 628 tests pass with no
skips, `black`, `isort`, and `flake8` are clean over `src` and `tests`, the built wheel and
sdist carry all five Open Game Content files with their designations and neither Product
Identity string, quickstart Scenarios 1 through 9 behave literally as written when run by
hand, every error path tried exits within `{0, 1, 2}` with usage errors on stderr and
reports on stdout in both output modes, the library surface matches
`contracts/library-api.md` in both directions, and SC-009's one-added-line comparison
against `tests/golden/pre-loader/` holds.

This round continued Phase 12's method — mutating a scratch copy of the tree and re-running
the suite — and extended it to the built artifacts and to the real CLI, run against
hand-built override trees. Of 208 mutations applied, 185 were killed. Rendering proved the
best-covered area in the feature, with more than sixty mutations killed and three left
open. As in Phase 12, most of what follows is unproven behavior rather than wrong behavior,
and each such task says so.

- [X] T092 Prove FR-002's "MUST NOT attempt to interpret that file's contents", which
      nothing currently could falsify: deleting the `continue` at `src/cetools/rules.py:618`,
      so a version-mismatched file falls through into `parsed` and is fully validated, leaves
      all 628 tests passing. The two cases that claim to cover this,
      `tests/integration/test_validation_categories.py:143` and `:154`, both bump
      `schema-version` on an *otherwise clean* file, so their `len(from_navy) == 1` assertion
      holds whether or not the contents were interpreted. The behavior is right today — a
      `navy.toml` carrying `schema-version = 2` together with an unrecognized skill name and a
      misspelled key yields exactly one problem, `found version 2; expected version 1` — but
      the cascade FR-002 exists to prevent could return unnoticed, and this is the same
      guarantee T069 was written to protect from the other side. Seed the version-mismatched
      fixture with two further deliberate mistakes and assert the file still reports exactly
      one problem (FR-002, FR-021, contracts/data-files.md rule 2, quickstart Scenario 2)
      (partial)
- [X] T093 Cover the two required career sub-keys whose absence is checked but proved by
      nothing, which is not a lost-diagnostic gap but a lost rejection: replacing the
      `"entries" not in table` check at `src/cetools/careers.py:373-381` and the
      `"ranks" not in table` check at `careers.py:564-572` with `pass` each leaves all 628
      tests passing, and under either mutation `parse_career` returns no problems at all and
      builds a `CareerDefinition` whose `tables` silently omits `service`, or whose `ladders`
      is `None` — a data set with a missing service table loads successfully. T082 closed the
      sibling seam for `throws.*.target`, `ranks[].rank`, `ranks[].title` and `ladders[].name`,
      and `tests/unit/test_careers.py` `TestNonEmptyTables` covers an *empty* `entries` or
      `ranks` array, but nothing deletes either key, and
      `tests/integration/test_reference_career.py` removes only whole tables and whole ladders
      (FR-015, FR-016, FR-019, SC-004, contracts/data-files.md) (missing)
- [X] T094 Cover the failed-load reporting path of `check`, which is the whole of T044 and is
      proved by nothing: no test anywhere invokes `check --rules-data` against an invalid data
      set — the four exit-1 cases in `tests/integration/test_cli.py` all reach `TaskError`
      through `--difficulty Trivial`, and `tests/integration/test_overrides.py:61,69` cover
      only the usage-error path. Two independent mutations survive the suite: printing the
      problems to stdout instead of stderr at `src/cetools/cli.py:123`, which breaks
      Constitution II's requirement that diagnostics go to stderr, and replacing the whole
      branch at `cli.py:121-125` with `typer.echo(str(exc), err=True)`, which replaces the
      one-line-per-problem form `contracts/cli.md` fixes with a bare summary and so silently
      discards every problem FR-021 collected. The behavior is correct today — five
      `FILE:LOCATION: found …; expected …` lines on stderr, empty stdout, exit 1, identical in
      both output modes (Constitution II, FR-021, FR-025, contracts/cli.md) (missing)
- [X] T095 Add the `Rules:` line FR-037 requires to the worked `check` example in
      `README.md:35-46`, which is byte-for-byte identical to
      `tests/golden/pre-loader/check_difficult.txt` — the *pre-feature* output — while
      `tests/golden/check_difficult.txt` and the real command both carry one line more. T056
      added the `validate` and `--rules-data` sections and left the pre-existing `check` block
      untouched, so the one command whose output this feature changed is documented as it was
      before the change. This ships: `README.md` is the `Description` in both the wheel's
      METADATA and the sdist's PKG-INFO, so it is what PyPI renders, and the project's own
      rule that changing human-readable CLI output means updating the committed reference
      output in the same commit is exactly the rule that was missed. Hold the version as the
      documented form the `tests/guards/test_documented_version.py` drift guard already
      checks, so a release does not stale it (FR-037, contracts/cli.md) (contradicts)
- [X] T096 Assert the `(file, location)` ordering of `ValidationReport.problems` at the place
      that establishes it, which is asserted nowhere: deleting `problems.sort()` at
      `src/cetools/rules.py:726` leaves 628 tests passing, and so does replacing it with
      `problems.sort(reverse=True)`. The one test that mentions the order,
      `tests/unit/test_render.py:444`, asserts that *rendering* must not re-sort and says so in
      its own comment — "The loader guarantees (file, location) order" — so the renderer defers
      to a guarantee that nothing holds, and `tests/unit/test_errors.py` pins the dataclass's
      `order=True` rather than the loader's use of it. data-model.md:235 and
      contracts/cli.md:158 both state the guarantee as the reason a report is stable run to
      run, which SC-002 and SC-003 depend on to assert content. Assert it over a data set
      broken in several files at once (FR-022, SC-002, SC-003, data-model.md, contracts/cli.md)
      (missing)
- [X] T097 Pin the boolean guard on every integer-valued field, which T073 added for
      `schema-version` and which is untested at five further sites: weakening
      `not isinstance(value, int) or isinstance(value, bool)` to a bare `isinstance` check at
      `src/cetools/rules.py:294` (`_require_int`, governing `task.target` and
      `task.unskilled-dm`), `rules.py:185` (`difficulty-dms.*`), `rules.py:226`
      (`characteristic-dms.*`), `src/cetools/careers.py:163` (`throws.*.target` and
      `ranks[].rank`) and `careers.py:670` (`mustering-out.cash[i]`) each leaves 628 tests
      passing. The consequence is a rules value changed with no report, not merely a worse
      message: under the mutation `"Difficult" = true` composes silently as difficulty
      modifier `1`, and `target = true` yields `Throw(target=True)`. Every site is correct
      today, reporting `found a boolean; expected an integer` (FR-020b, FR-014, FR-016, FR-017)
      (partial)
- [X] T098 Add regression cases for the five collected-problem branches in
      `src/cetools/rules.py` that survive being neutered, each verified against the real
      package before the mutation: the UTF-8 decode failure at `rules.py:548-557`, whose
      `problems.append` can be dropped while keeping the `continue`, so an override career file
      with one bad byte vanishes from the data set with no report and exit 0 — the sibling
      `tomllib.TOMLDecodeError` branch three lines below *is* covered, so this is an asymmetry
      rather than a drawn line, and SC-002's closed list names "a file that is not well-formed
      at all, or cannot be read"; the `task.roll` string-type check at `rules.py:145`, whose
      loss sends a non-string into `_check_dice` and leaves `validate_rules` raising rather
      than collecting, which is an FR-021 and FR-023 break and not only a worse message; the
      key closure inside `[task]` at `rules.py:134-136`, the `tasks.toml` analogue of the five
      career sites T084 closed, where `unskiled-dm` today correctly reports both the
      unrecognized key and the missing one and only the second is proved; the unreadable
      *packaged* file at `rules.py:334-335`, whose override-side twin is covered; and the three
      sources of `_singleton_slots` at `rules.py:521-526`, each individually removable with the
      suite green, so T069's union is proved only in aggregate and its canonical-basename
      source is exercised by nothing (FR-020, FR-020a, FR-020b, FR-021, FR-023, SC-002)
      (partial)
- [X] T099 Pin the rule that non-string content in a notation-bearing field is a *type*
      problem reported against the field rather than text routed to the parser: replacing the
      guard at `src/cetools/careers.py:189-192` with `value = str(value)` leaves 628 tests
      passing, and under the mutation `entries = [5]` reports `expected a characteristic
      adjustment, a skill grant, or a bare skill reference` — the unrecognized-entry-form
      report that contracts/notation.md's clause and FR-004a's typing exist to prevent —
      instead of `found an integer; expected a notation string`. The rule governs
      `tables.*.entries`, `tables.*.requires`, `ranks[].bonus` and `mustering-out.benefits`,
      and `tests/unit/test_careers.py::TestPlainNumericFieldsNeverRoutedThroughNotation` covers
      only the mirror direction, a string in a numeric field (FR-004a, FR-020b,
      contracts/notation.md) (partial)
- [X] T100 Settle whether the whitespace before a specialty group is mandatory, which the
      grammar says and the skill path does not enforce: contracts/notation.md line 19 writes
      `name := text [ WS "(" text ")" ]`, but `_SPECIALTY` at `src/cetools/notation.py:104` and
      `_parse_name` at `:143-150` split on the parenthesis without requiring the space, so
      `Blade(Cutlass)`, `Blade  (Cutlass)` and `Blade (Cutlass)` all return the identical
      `SkillReference(name='Blade', specialty='Cutlass')`. T087 settled exactly this widening
      for `BenefitItem` on the grounds that inserting or collapsing a space widens the notation
      the way case folding does, which FR-013 forbids; its amended paragraph justifies leaving
      the skill path alone only by "there is nothing to reassemble", which answers a different
      question than whether the missing space should parse. Either make `WS` optional in the
      grammar or reject the space-free form, and pin whichever is chosen — the property
      strategy at `tests/property/test_invariants.py:167-181` always renders with a space, so
      it cannot find this. While settling it, decide the mirror case the contract records for
      benefit items and leaves open for skills: `parse_skills` accepts a registry key such as
      `Gun Combat (Slug Rifle)` (`src/cetools/registries.py:159-189`) that no career entry can
      ever match, since any career writing it parses to base and specialty and resolves
      `UNRECOGNIZED_SKILL` (FR-006, FR-013, contracts/notation.md) (contradicts)
- [X] T101 Decide what happens when the location named on the command line is itself a
      dot-prefixed file, which today reports success and does nothing:
      `cetools validate <dir>/.navy.toml` prints `Rules data is valid.`, `Files: 5`,
      `Rules: packaged`, and exits 0, because the single-file branch at
      `src/cetools/rules.py:468` routes through `_collect_entry`, whose leading-dot carve-out
      at `:379-380` returns early. Making that branch bypass the dot check also leaves 628
      tests passing, so nothing pins either answer, while the control case — a dot file found
      *inside* a directory override — is killed by `tests/unit/test_composition.py:48`. The
      letter of FR-032b is followed and its rationale is not: "a file the author did not write
      is not a mistake the author needs told about" does not describe a path the author typed,
      and the outcome is verbatim the mistyped-path-that-appears-to-succeed failure FR-028
      names as the one this feature exists to remove. This is the same reasoning that moved
      `/dev/null` under T067 and `.git/` under T078; decide it the same way, amend FR-032b and
      contracts/data-files.md rule 3 if the line moves, and pin the result (FR-032b, FR-028,
      FR-040, contracts/data-files.md) (partial)
- [X] T102 Finish T086's move of `provenance.ignored` from basenames to paths within the
      override, which left two contracts and one docstring behind: `data-model.md:203` and
      `contracts/json-output.md:53` both still type the field as "Basenames of files in an
      override location", while `contracts/data-files.md` rule 4 and
      `contracts/library-api.md:54` correctly say the path — verified against the real package,
      where an override holding `a/notes.md` and `b/notes.md` yields
      `('a/notes.md', 'b/notes.md')` in both the text block and `--json`. Two smaller
      consequences of the same drift: `contracts/cli.md:81` and `:94-96` describe the file
      column as padded to "the longest basename present", as does the `_provenance_lines`
      docstring at `src/cetools/render.py:22-23`, where the code pads to the longest *name*
      across both lists, which is right for paths and no longer what the prose says (FR-032a,
      FR-035, data-model.md, contracts/json-output.md, contracts/cli.md) (contradicts)
- [X] T103 Close the blind spot T072 narrowed but did not remove: both coverage checks
      self-limit to the paths they could ever fail on, so an Open Game Content file shipped
      outside `src/`, or one that is not a `.toml`, is covered by neither. Writing an
      OGC-designated `tests/fixtures_ogc.toml` leaves all 628 tests passing, and the file
      really does ship — it appears in the built sdist, `tests/` being in the `include` list at
      `pyproject.toml:40` — because `tests/unit/test_licensing.py:231-234` globs
      `(repo_root / "src").rglob("*.toml")` and `tests/guards/test_packaging.py:194-196`
      filters `relative.startswith("src/")`. An OGC-designated `src/cetools/data/tables.md`
      likewise leaves the suite green. SC-016 asks the obligation to be derived from the data
      files the distribution actually contains, which is what SC-014 already does for the
      designation guard; derive it from the built artifact's whole file list rather than from a
      prefix, and key on the designation comment rather than on the extension (FR-047, SC-016,
      SC-014, Constitution Licensing & Distribution) (partial)
- [X] T104 Finish T080's widening in the two files it did not reach: `CLAUDE.md:14-18` still
      tells a contributor that a new SRD-derived data file must be "named in the README
      licensing section", which `README.md:92-96` no longer does per file, having moved to
      designating the whole directory — the identical contradiction T080 reconciled in
      `CONTRIBUTING.md:136-143` — and its glob `src/cetools/data/*.toml` matches only
      `tasks.toml`, missing the four files this feature added under `careers/` and
      `registries/`. While there, refresh `CONTRIBUTING.md:78`, whose test-directory table
      still describes `tests/guards/` as "The seed-reproducibility contract"; this feature
      added `test_data_layout.py`, `test_no_outside_reads.py` and `test_documented_version.py`
      to that directory, so five of its six files are not the seed contract (FR-046, FR-047,
      Constitution Licensing & Distribution) (contradicts)
- [X] T105 Pin the looping that T076 was measured against, which is asserted in neither
      sibling parser: changing `continue` to `break` at `src/cetools/registries.py:126`
      (`parse_characteristics`) and at `:235` (`parse_benefits`) each leaves 628 tests passing.
      T076's fix to `parse_skills` was justified by the asymmetry with these two — "both of
      those looping and reporting each element" — so the standard it was held to can regress
      in the two places it was compared with. Both are correct today, three bad characteristic
      labels yielding three problems and `benefits = [5, 7, 9]` yielding three, and FR-021 with
      SC-003's "the number of runs needed to find every problem in a file is always one" is
      what forbids the first-one-only form (FR-021, SC-003) (partial)
- [X] T106 Close the two clauses of `contracts/library-api.md` that survive removal, and the
      reason they can: restoring a working `load_task_parameters` to `src/cetools/__init__.py`
      leaves 628 tests passing, although FR-044 requires the old reader replaced rather than
      kept alongside and the contract lists it under **Public surface removed**; and removing
      `FileProvenance` from the imports and `__all__` also leaves 628 passing, because every
      test reaches that type through `cetools.provenance` rather than through `cetools`, which
      is precisely the reaching-past-the-package that T064 closed for `NotationProblem` and
      `SkillResolution`. Both survive for one underlying reason — `rg __all__ tests/` returns
      nothing, so `cetools.__all__` is never compared against the contract's list as a set in
      either direction. Compare it as a set, which closes both clauses and every future one
      (FR-043, FR-044, SC-013, contracts/library-api.md) (missing)
- [X] T107 Reconcile the four worked examples that no longer match what the tool emits, as
      T089 did for the fifth: `contracts/cli.md:137` and `contracts/json-output.md:120` show
      `found unrecognized skill name 'Vac Suit'` where the tool emits `found Vac Suit`;
      `cli.md:139` shows `found an unrecognized key 'chash'; expected one of cash, benefits`
      against the emitted `found unrecognized key 'chash'; expected one of: benefits, cash`;
      `cli.md:140` shows `found no entries; expected at least one` against
      `found an empty table; expected at least one entry`; and `cli.md:152` shows
      `found invalid TOML at line 12, column 3` against the tomllib message the code passes
      through. Both contracts do say the wording of `found` and `expected` is not fixed, so
      this is drift rather than a defect — but the hand-built fixtures at
      `tests/contract/test_json_contract.py:203` and
      `tests/integration/test_validate_cli.py:35` pin the *contract's* wording rather than the
      code's, so neither side currently checks the other (contracts/cli.md,
      contracts/json-output.md) (contradicts)
- [X] T108 Pin the malformed-entry rows and bare-name paths that collapse into one another
      with the suite green, each verified by mutation: deleting the empty-entry guard at
      `src/cetools/notation.py:173-174`, the balanced-parenthesis check at `:136-137`, or the
      one-group check at `:138-139` leaves 628 tests passing, because
      `tests/unit/test_notation.py::TestMalformedEntries` asserts only
      `isinstance(result, NotationProblem)` for those five cases and pins the detail of just
      one, `Pilot -`; dropping the specialty's `.strip()` at `:147` also leaves 628 passing
      while turning `Blade ( Cutlass )` from a valid reference into an unrecognized specialty,
      although its sibling `base` strip one line above *is* covered; and both the
      `trailing is not None` guard at `:189` and the `\s+` in `_TRAILING_TOKEN` at `:99` can be
      loosened with the suite green, each flipping whitespace-free entries such as `Zero-G2`,
      `T2` and `-` from the accepted bare names the grammar requires into malformed ones —
      which is the untested complement of the case T074 decided. `contracts/notation.md`'s
      malformed-entry table is the artifact all of these are pinned to (FR-006, FR-009,
      contracts/notation.md) (partial)
- [X] T109 Write a parenthesized specialty into `src/cetools/data/careers/navy.toml`, which
      contains none: the four skills that have specialties in
      `src/cetools/data/registries/skills.toml` (`Gun Combat`, `Gunnery`, `Melee Combat`,
      `Vehicle`) all appear bare, so the shipped career exercises FR-008's owed-choice case and
      never FR-006's base-and-specialty split nor a fully-specified reference. FR-018 requires
      the shipped career to exercise every element of the schema, and the split is proved only
      by unit fixtures, which is the gap FR-018 exists to close — a fixture's author can
      unconsciously avoid the hard parts, and real content cannot. Whichever entry gains one,
      it must stay faithful to the source material, per T060 (FR-018, FR-006, SC-004) (partial)
- [X] T110 Add cases for the four committed-shape clauses that survive mutation, all in the
      otherwise best-proved area of the feature: the inner key order of `provenance.files[]`,
      reorderable at `src/cetools/render.py:56` with the suite green because
      `tests/contract/test_json_contract.py` builds only *packaged* provenance and so never
      sees a populated entry, while `contracts/json-output.md` states that key order is part of
      the contract; `ensure_ascii=False` at `render.py:223`, the one clause of that invariant
      whose siblings `indent=2` and the trailing newline are both killed; the help strings
      `contracts/cli.md:174-178` requires, since setting `help=None` on `--rules-data`
      (`cli.py:102`) or on `validate`'s `PATH` (`cli.py:135-136`) leaves 628 passing because
      the two help tests assert only the option-name set; and `check`'s keyword-only signature
      at `src/cetools/tasks.py:109` together with `CheckResult`'s field order at `:103-104`,
      both of which T032 and `contracts/library-api.md:159-168` fix and both of which can be
      changed with the suite green (FR-041, FR-043, contracts/json-output.md, contracts/cli.md,
      contracts/library-api.md) (missing)
- [X] T111 Justify or drop the five behaviors no requirement or contract asks for, surfaced
      for review rather than for deletion: `src/cetools/careers.py:544` sorts a ladder's ranks
      by position and `tests/unit/test_careers.py:358-367` pins it, although FR-016 requires
      only that positions be non-negative and distinct and contracts/data-files.md's rank table
      says nothing about order — it is the one mutation in the career schema killed by a test
      that traces to no requirement; `_require_string` at `careers.py:137` rejects an empty
      `name`, `ranks[].title` or `ladders[].name`, strictness neither required nor proved,
      since relaxing it to a bare `isinstance` check leaves 628 passing; the symlink-cycle
      guard at `src/cetools/rules.py:429-431` is removable with the suite green and is
      necessary only because T071 chose to follow symlinked directories, and a regression there
      hangs rather than fails (note also that `stat()` and `iterdir()` run before the `seen`
      check, so a revisited directory is listed redundantly); `file_provenance.sort()` at
      `rules.py:495` is genuinely dead, the list being built from `sorted(candidates.items())`
      at `:474`, so the ordering guarantee data-model.md:202 states rests on the upstream sort
      rather than on the line that appears to provide it; and `pyproject.toml:53-57` configures
      `rumdl`, which is in no dependency group, no CI workflow, and no CONTRIBUTING section,
      beside a stale `.ruff_cache/` with no ruff config either (Principle VI, FR-016,
      data-model.md) (unrequested)
- [X] T112 Qualify the last stale cross-reference of the class T066 closed, and document or
      remove one private seam: `src/cetools/tasks.py:21-22` says the leading underscore is
      "the convention contracts/library-api.md states", but a search of `specs/` finds that
      statement only at `specs/001-dice-task-engine/contracts/library-api.md:124` — this
      feature's contract says nothing about it, so a bare contract-file reference in a
      docstring T066 already visited now resolves to the wrong feature's contract, exactly as
      the bare `FR-NNN` references did. Separately, `src/cetools/cli.py:10` imports the private
      `_problem_line` from `render.py`, a library-to-CLI seam no contract in this feature
      documents; either name it in `contracts/library-api.md` or give it a public spelling
      (contracts/library-api.md, Constitution I) (contradicts)
- [X] T113 Make the constitution's two Development Workflow clauses checkable, neither of
      which anything enforces: changing `pyproject.toml`'s `version` from `2026.08.1` to
      `2026.8.1`, or to `1.2.3`, or to `2026.13.1`, each leaves 628 tests passing, because
      PEP 440 normalizes the zero-padded and unpadded forms to the same string and the
      `tests/guards/test_documented_version.py` drift guard compares the normalized values —
      so nothing anywhere asserts the *declared* string matches the `YYYY.0M.INC1` shape the
      constitution fixes, which is the very distinction T063 had to reconcile in the rendered
      output. Likewise, renaming the `## 2026.08.1 (unreleased)` heading in `CHANGELOG.md` to
      `## 9999.99.9 (unreleased)` leaves 628 passing, so a release cut without its changelog
      entry ships silently against the constitution's requirement that every release ship one
      (Constitution Development Workflow) (missing)
- [X] T114 Correct two wordings in the Open Game Content designation, neither of which is an
      exposure and both of which say something not quite true: `LICENSE-OGL.txt:137-138` names
      the covered files as `cetools rules data (src/cetools/data/)`, a path that exists in no
      wheel — the wheel ships them at `cetools/data/`, and `src/` appears nowhere in it, which
      is why `tests/guards/test_packaging.py:108-112` has to fabricate the prefix as
      `f"src/{name}"` to make its check line up, papering over the mismatch rather than
      reporting it. And the directory-wide designation that replaced the per-file list sweeps
      in `src/cetools/data/__init__.py`, which ships in the wheel: `README.md:92-94` and
      `LICENSE-OGL.txt:137` both say everything under that directory is Open Game Content,
      while `CONTRIBUTING.md:134-137` says Python source is GPL-3.0 and that Open Game Content
      cannot be sublicensed under the GPL. The file is empty so nothing copyrightable is
      double-licensed, but the constitution requires the designation to be unambiguous;
      qualifying both statements to every `.toml` under the directory settles it (FR-046,
      FR-047, Constitution Licensing & Distribution) (partial)
