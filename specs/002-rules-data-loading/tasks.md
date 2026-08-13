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

- [ ] T001 Copy `tests/golden/check_difficult.txt`, `tests/golden/check_unskilled.txt`, `tests/golden/roll_1d6.txt`, `tests/golden/roll_2d6_plus1.txt`, and `tests/golden/roll_d66.txt` verbatim into `tests/golden/pre-loader/` and commit them before any other change; this directory is never regenerated (plan.md Implementation Notes, research R12, SC-009)
- [ ] T002 Add a package-version placeholder constant and a normalization helper fixture to `tests/conftest.py` so golden files and JSON fixtures can hold the version as a placeholder substituted at comparison time (SC-009)

**Checkpoint**: The pre-loader evidence is committed and cannot be destroyed by a later regeneration.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The problem type, the notation, the registries, the career types, and the
provenance types. Every user story builds on these.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

**Build order** follows plan.md: `errors` → `notation` → `registries` → `careers` → `provenance`.

- [ ] T003 [P] Write failing tests for `ValidationProblem` fields, its `(file, location)` sort order, the empty-string location a problem about a file as a whole carries, and `RulesDataError.problems` including the message-only construction, in `tests/unit/test_errors.py` (FR-022, data-model.md)
- [ ] T004 Add `ValidationProblem` as a frozen slotted dataclass, its `location` a `str` that is empty for a problem about a file as a whole rather than an optional field, and extend `RulesDataError` with a `problems` field in `src/cetools/errors.py` (FR-022, data-model.md) (depends on T003)
- [ ] T005 [P] Write failing tests for `parse_entry` covering the four forms, tail-anchored precedence, names with spaces/apostrophes/slashes/hyphens, parenthesized specialties, the three `EntryContext` subsets, and every malformed case in `contracts/notation.md`, in `tests/unit/test_notation.py` (FR-004, FR-006, FR-009, FR-009a)
- [ ] T006 Implement `parse_entry`, `EntryContext`, `SkillReference`, `CharacteristicCheck`, `CharacteristicAdjustment`, `SkillGrant`, and `BenefitItem` in `src/cetools/notation.py`; parsing does no registry lookup (depends on T005)
- [ ] T007 [P] Write failing tests for the three registry types and their file schemas, including exact case-sensitive matching and the four `SkillRegistry` resolution outcomes, one of which is a bare name for a skill that has specialties remaining distinguishable from a fully-specified reference, in `tests/unit/test_registries.py` (FR-007, FR-008, FR-010, FR-011, FR-012, FR-013)
- [ ] T008 Implement `CharacteristicRegistry`, `SkillRegistry`, `BenefitRegistry` and the `characteristics`, `skills`, and `benefits` file schemas in `src/cetools/registries.py`, returning collected problems and never raising (depends on T004, T007)
- [ ] T009 [P] Write failing tests for `Disposition`, `FileProvenance`, `Provenance`, `is_packaged`, and the SHA-256-over-raw-bytes fingerprint in `tests/unit/test_provenance.py` (FR-033, FR-033a, FR-034, FR-035, FR-036, research R4)
- [ ] T010 Implement `Disposition`, `FileProvenance`, `Provenance`, and the fingerprint function in `src/cetools/provenance.py`, reading the package version from `importlib.metadata` and hashing bytes without decoding (FR-033, FR-033a, FR-036) (depends on T009)
- [ ] T011 [P] Write failing tests for the career file schema covering every required and optional element, closed throw and table name sets, positive targets, non-negative distinct rank positions, distinct ladder names, non-empty tables, and each notation-bearing field validated against the registry its position implies, including a characteristic adjustment in a mustering-out benefits entry checked against the characteristics registry rather than the benefit items registry; assert too that the plain numeric fields, the throw targets and the mustering-out cash amounts, are typed by position and never routed through the notation, so a target written as a string reports a bad type rather than an unrecognized entry form, in `tests/unit/test_careers.py` (FR-004a, FR-005, FR-014 through FR-019a)
- [ ] T012 Implement `CareerDefinition`, `Throw`, `SkillTable`, `RankLadder`, `Rank`, `MusteringOut` and the `career` file schema in `src/cetools/careers.py`, resolving each notation-bearing field against the registry its position or its form implies, typing the throw targets and cash amounts as plain values outside the notation, and returning collected problems (FR-004a, FR-005) (depends on T004, T006, T008, T011)
- [ ] T013 [P] Add a guard asserting that basenames are unique across every `.toml` under `src/cetools/data/` in `tests/guards/test_data_layout.py`; this is the premise basename positioning rests on, and it fails the moment a second `navy.toml` is added under another directory (FR-029, plan.md trap list)

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

- [ ] T014 [P] [US1] Rewrite `tests/unit/test_rules.py` for discovery of every `.toml` under `cetools/data/`, composition keyed by basename, the task-parameters schema restated as collected problems, `RulesData`, `ValidationReport`, `load_rules`, and `validate_rules`; assert the supported schema version for each kind is a literal constant that is neither read from nor derived from the package release version (FR-003, FR-020a, FR-021, FR-024, FR-025, FR-026, FR-044)
- [ ] T015 [P] [US1] Write `tests/unit/test_composition.py` for how an override location composes, at library level and before any command exists: a basename matching a packaged file replaces it, a basename matching nothing is admitted as an addition, a non-`.toml` file is recorded as ignored without failing the load, a dot-prefixed file is passed over silently and appears nowhere including when its extension is also wrong, an override holding only ignored files still composes as packaged while listing them, an existing but empty location composes as packaged, and a location that does not exist is a usage error naming it (FR-028, FR-029, FR-032, FR-032a, FR-032b)
- [ ] T016 [P] [US1] Write `tests/integration/test_validation_categories.py` with one case per category in SC-002's closed list: unrecognized name, unrecognized key, malformed entry, well-formed entry in a context that does not admit it, missing required element, wrong value type, unsupported schema version (asserting no other problem from that file), missing or unrecognized kind declaration, replacement kind mismatch, unreadable or malformed TOML, two careers declaring one name, duplicate or absent single-instance kind, and two override files sharing a basename; assert that each whole-file category reports its file with an empty location rather than a fabricated one (SC-002, FR-022)
- [ ] T017 [P] [US1] Write `tests/integration/test_reference_career.py` removing each required element of the shipped career in turn and asserting a specific rejection naming what is missing (SC-004, FR-018, FR-019)
- [ ] T018 [P] [US1] Write `tests/unit/test_rules_agreement.py` asserting `validate_rules` and `load_rules` agree on the same inputs, valid and invalid alike (FR-023, SC-015)
- [ ] T019 [P] [US1] Write `tests/guards/test_no_outside_reads.py` installing a `sys.addaudithook` hook at module import, arming it around a packaged load, and asserting every opened path lies inside the installed package; import everything before arming and filter `__pycache__` (SC-007, research R6)
- [ ] T020 [P] [US1] Widen `tests/guards/test_packaging.py` to iterate over every `.toml` under `cetools/data/` in the built wheel and sdist instead of naming `tasks.toml`, asserting each carries its Open Game Content designation and neither Product Identity string, and additionally asserting that the data set read from the built artifact validates without a single problem, since SC-001 asks about the installed package rather than the source tree and a file present in the tree but missing from the wheel would otherwise pass (SC-001, SC-014, FR-046)
- [ ] T021 [P] [US1] Rewrite the notice-chain check in `tests/unit/test_licensing.py` to derive what the Section 15 game-data line must cover from the data files actually present rather than comparing against a fixed expected text, so adding a data file without widening the notice fails (FR-047, SC-016)

### Implementation for User Story 1

- [ ] T022 [US1] Implement discovery and composition in `src/cetools/rules.py`: walk `importlib.resources.files("cetools.data")` recursively for `*.toml` sorted, collect an override directory or single file, refuse a nonexistent location as a usage error naming it, discard dot-prefixed names before the extension filter, record non-`.toml` names as ignored, and key everything by basename (FR-027, FR-028, FR-029, FR-032, FR-032a, FR-032b, research R5, plan.md trap list) (depends on T015)
- [ ] T023 [US1] Implement the task-parameters schema, the kind and schema-version header check with version mismatch suppressing every other problem from that file, the validation driver over the composed set, `RulesData`, `ValidationReport`, `load_rules` and `validate_rules` in `src/cetools/rules.py`; remove `load_task_parameters` (FR-001, FR-001a, FR-002, FR-002a, FR-003, FR-020, FR-020b, FR-021, FR-023, FR-025, FR-044) (depends on T022)
- [ ] T024 [US1] Implement the cross-file rules in `src/cetools/rules.py`, checked after every file has been read: duplicate career names, duplicate and absent single-instance kinds, and duplicate override basenames, each naming both files where two are implicated (FR-010a, FR-019b, FR-029a) (depends on T023)
- [ ] T025 [P] [US1] Author `src/cetools/data/registries/characteristics.toml` with its OGC designation comment, `schema`, and `schema-version`
- [ ] T026 [P] [US1] Author `src/cetools/data/registries/skills.toml` with its OGC designation comment, `schema`, `schema-version`, and an explicit specialty list for every skill
- [ ] T027 [P] [US1] Author `src/cetools/data/registries/benefits.toml` with its OGC designation comment, `schema`, and `schema-version`
- [ ] T028 [US1] Author `src/cetools/data/careers/navy.toml` from the source material, not from the illustrative values in `contracts/data-files.md`, exercising a commission, a second rank ladder, at least one rank bonus, and a characteristic-gated table (FR-018) (depends on T025, T026, T027)
- [ ] T029 [P] [US1] Add the `schema = "task-parameters"` and `schema-version = 1` header lines to `src/cetools/data/tasks.toml`
- [ ] T030 [US1] Widen this project's game-data copyright line in `LICENSE-OGL.txt` to cover the whole `src/cetools/data/` directory, and update the matching entry in `SECTION_15_NOTICES` in `tests/conftest.py` in the same change (FR-047)
- [ ] T031 [US1] Repoint the autouse cache-clearing fixture in `tests/conftest.py` from `load_task_parameters` to `load_rules.cache_clear()` (plan.md trap list)
- [ ] T032 [US1] Add the `provenance` field to `CheckResult` after `seed`, and change `check` to take keyword-only `rules: RulesData | None` in place of `parameters:`, in `src/cetools/tasks.py` (FR-037, FR-045, research R8)
- [ ] T033 [US1] Add the packaged provenance block to the `CheckResult` registrations of `as_text`, `as_dict`, and `as_json` in `src/cetools/render.py`, keeping the label column seven characters wide and appending `provenance` last in the JSON key order (contracts/cli.md, contracts/json-output.md)
- [ ] T034 [US1] Update the `check` command in `src/cetools/cli.py` to load rules and pass `rules=`, with no new option yet (FR-044)
- [ ] T035 [US1] Update `src/cetools/__init__.py` to export the added public surface and drop `load_task_parameters` (contracts/library-api.md, FR-043)
- [ ] T036 [US1] Regenerate `tests/golden/check_difficult.txt` and `tests/golden/check_unskilled.txt` with the version held as a placeholder, leaving the three `roll` goldens and all of `tests/golden/pre-loader/` untouched (SC-009)
- [ ] T037 [US1] Update the `check` payload expectations in `tests/contract/test_json_contract.py` for the appended `provenance` key, holding the version as a placeholder (contracts/json-output.md)
- [ ] T038 [US1] Add the SC-009 comparison to `tests/integration/test_golden.py`: each check golden equals its `tests/golden/pre-loader/` counterpart with exactly the provenance block added, each roll golden is byte-identical, and the dice, modifiers and labels, total, target, outcome, and seed compare field by field

**Checkpoint**: The shipped data set validates, a corrupted copy is rejected with every problem located, every SC-002 category including the cross-file ones is covered, and existing seeds resolve identically. This is the MVP.

---

## Phase 4: User Story 2 - Author rules data with fast, complete feedback (Priority: P2)

**Goal**: One command reports everything wrong with a data set, in either output mode,
with meaningful exit codes.

**Independent Test**: Run the command against the shipped data set and see it pass; run
it against a file seeded with four distinct mistakes and see all four reported in one run.

### Tests for User Story 2 ⚠️ Write first, observe failing

- [ ] T039 [P] [US2] Write `tests/integration/test_validate_cli.py` for `cetools validate` with no argument: exit 0 on the packaged set, exit 1 when any problem is found, exit 2 for a usage error, the same outcome in both output modes, and four distinct problems reported from a single run (SC-003, SC-010, FR-038, FR-039, FR-041)
- [ ] T040 [P] [US2] Add `ValidationReport` rendering expectations to `tests/unit/test_render.py` for the valid summary, the one-problem-per-line form, the file-as-a-whole form that drops `:LOCATION`, and the `(file, location)` sort order (contracts/cli.md, FR-022)
- [ ] T041 [P] [US2] Add the `validation` payload expectations to `tests/contract/test_json_contract.py` with key order `kind`, `valid`, `file_count`, `provenance`, `problems`, and `problems[].location` present but empty for a problem about a file as a whole rather than absent or null (contracts/json-output.md, FR-022)

### Implementation for User Story 2

- [ ] T042 [US2] Register `ValidationReport` with `as_text`, `as_dict`, and `as_json` in `src/cetools/render.py` (FR-041, FR-043)
- [ ] T043 [US2] Add the `cetools validate` command to `src/cetools/cli.py` with `--json`, problems on stdout, usage errors on stderr, and exit codes 0/1/2 (FR-038, FR-039, FR-041)
- [ ] T044 [US2] Print the problems of a failed load to stderr in the same one-line form and exit 1 at the existing single catch site in `src/cetools/cli.py` (contracts/cli.md, FR-025)

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

- [ ] T045 [P] [US3] Write `tests/integration/test_overrides.py` for a house rule reaching a result: an overridden survival throw changes what a resolved check produces, a value present in the packaged file and omitted from the override that replaces it is absent rather than inherited, every file the override does not contain still comes from the packaged data, an unrecognized name in an override file fails the load with the same diagnostics a shipped file would produce, and an override file carrying no Open Game Content designation loads without complaint because FR-046 binds shipped files only (SC-005, SC-006, FR-030, FR-031, FR-046)
- [ ] T046 [P] [US3] Write `tests/integration/test_data_driven.py` demonstrating a behavior change with no code edit for a career throw, a skill table entry, a rank bonus, and a registry entry, the last by removing a skill name and observing every career reference to it fail (SC-011, FR-013)

### Implementation for User Story 3

- [ ] T047 [US3] Add `--rules-data PATH` to the `check` command in `src/cetools/cli.py` (FR-042)
- [ ] T048 [US3] Add the optional `PATH` argument to the `validate` command in `src/cetools/cli.py`, accepting a directory or a single file and positioning it by basename alone (FR-040, FR-040a)

**Checkpoint**: House rules take effect through data alone, and a misspelled filename is visible rather than silent.

---

## Phase 6: User Story 4 - Tell whether a result is reproducible (Priority: P4)

**Goal**: Anyone handed a seed and a result can tell what data produced it, and what was
modified if anything was.

**Independent Test**: Load with and without an override and compare the reported
provenance; alter the content of an override file at the same location and confirm the
reported fingerprint changes.

### Tests for User Story 4 ⚠️ Write first, observe failing

- [ ] T049 [P] [US4] Write `tests/unit/test_provenance_reporting.py` asserting identical content at two different locations fingerprints identically, differing content fingerprints differently, the reported value is reproducible with `shasum -a 256`, and the reported version equals the installed package version asserted directly rather than through a placeholder (SC-008, FR-036)
- [ ] T050 [P] [US4] Write `tests/integration/test_provenance_cli.py` for the overridden text block in both `check` and `validate`: file column padded to the longest basename, disposition column to the longest disposition, effective files first sorted by name then ignored files sorted by name, an ignored line ending at the disposition, and an override holding only ignored files still reading `packaged` while listing them (contracts/cli.md, FR-032a, FR-035)

### Implementation for User Story 4

- [ ] T051 [US4] Render the overridden provenance text block with its per-file disposition, fingerprint, and ignored lines in `src/cetools/render.py` (FR-035, FR-037)
- [ ] T052 [US4] Emit the provenance JSON object with key order `source`, `version`, `files`, `ignored` and `files[]` sorted by `file` in `src/cetools/render.py` (contracts/json-output.md) (depends on T051)

**Checkpoint**: All four stories are independently functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T053 [P] Add notation round-trip invariants to `tests/property/test_invariants.py`: a rendered entry parses back to an equal value for each of the four forms (plan.md Testing)
- [ ] T054 [P] Add `tests/unit/test_library_api.py` exercising every capability in this feature through `import cetools` without invoking the command line (SC-013, FR-043)
- [ ] T055 [P] Record the removal of `load_task_parameters` and the `parameters=` keyword under **Breaking changes**, and the added surface under additions, in `CHANGELOG.md` (contracts/library-api.md)
- [ ] T056 [P] Document `cetools validate` and `--rules-data` in `README.md`, with no help or prose text naming the trademark as something this tool works with (contracts/cli.md)
- [ ] T057 Walk every scenario in `specs/002-rules-data-loading/quickstart.md` by hand and confirm each expected outcome
- [ ] T058 Run the full suite plus the project's lint and type checks and resolve anything outstanding

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
