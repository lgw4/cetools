---

description: "Task list for 008-kind-declarations"
---

# Tasks: Kind Declarations

**Input**: Design documents from `/specs/008-kind-declarations/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/kind-declarations.md](contracts/kind-declarations.md),
[quickstart.md](quickstart.md)

**Tests**: REQUIRED. Constitution Principle III is non-negotiable, and FR-015
requires new declaration-invariant tests written before the declarations exist.
FR-012 permits exactly these edits to existing tests: the pinning test rewrite,
the two version-bump patches (with one shared helper), and the literal-version
loop. No other existing test changes, and the golden, contract, and integration
corpora are never edited.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Single project: `src/cetools/`, `tests/` at repository root. Line numbers cite
`src/cetools/rules.py` and `tests/unit/test_rules.py` as they stand at the
start of this feature (unchanged since `0074436`). They drift as commits land;
locate by the quoted code, not the number. Scratchpad work (`<scratchpad>`:
the harnesses and their output) lives outside the repository and is never
committed.

## How this decomposes

The feature is a behavior-preserving refactor in the three commits research R8
fixes. It does not split into independently shippable slices, so the phases
follow the commit sequence and every task names the story it serves:

| Phase | Commit | Story served |
|---|---|---|
| 1: Setup | *(pre-commit)* | US1's evidence apparatus |
| 2: US2 | 1: `refactor(rules): declare each rules-data kind once` | US2, gated by US1 |
| 3: US2 | 2: `refactor(rules): read kind facts from the declarations` | US2, gated by US1 |
| 4: US2, US3 | 3: `refactor(rules): parse one-file kinds in one loop` | US2, US3, gated by US1 |
| 5: Polish | *(pre-merge)* | all |

**Every commit is structural** (FR-014). No commit adds a `CHANGELOG.md` entry.
Every commit is green under the full suite and has an empty header harness diff
before it lands. Commits are made through the `git-ops` agent.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Build the evidence apparatus [quickstart.md](quickstart.md) 1c
requires and capture the baseline every later diff is taken against. No
repository file changes.

- [ ] T001 Record the baseline: `git rev-parse HEAD > <scratchpad>/base.txt`, and confirm `wc -l < src/cetools/rules.py` prints `1103` and `git diff --stat 0074436 HEAD -- src tests` is empty
- [ ] T002 Confirm the starting state is green: `uv run pytest` passes in full, and `git diff --stat main -- tests/golden tests/contract tests/integration` is empty
- [ ] T003 Write the header harness at `<scratchpad>/kinds_harness.py` per [quickstart.md](quickstart.md) 1c. It reads the kind list and each one-file kind's canonical basename from the packaged headers (`tomllib` over `src/cetools/data/**/*.toml`), never from `cetools.rules` internals, so it is byte-identical before and after. For each case it writes a temporary override directory, calls `cetools.rules.validate_rules(override)`, and prints one `case|file|location|found|expected` line per problem. Cases: (a) for each packaged `.toml`, its header mutated each way: `schema` deleted, `schema` set to `"no-such-kind"`, `schema` set to each other kind's name, `schema-version` deleted, `schema-version` raised by one, `schema-version` set to `"1"`, `schema-version` set to `true`, the whole file replaced by invalid TOML, and the whole file replaced by invalid UTF-8 bytes; (b) for each one-file kind, a second file declaring it under a new basename; (c) for each one-file kind, its canonical file replaced by one declaring an unknown kind; (d) for each one-file kind, its canonical file rejected on version while a new basename declares a different valid one-file kind
- [ ] T004 Prove the header harness deterministic: run `uv run python <scratchpad>/kinds_harness.py` twice at the baseline and confirm the two outputs are byte-identical
- [ ] T005 Capture the header baseline into `<scratchpad>/before.txt` with `uv run python <scratchpad>/kinds_harness.py`
- [ ] T006 [P] Rebuild 007's body mutation harness at `<scratchpad>/mutate.py` per [`specs/007-parse-context-carrier/quickstart.md`](../007-parse-context-carrier/quickstart.md) 1b (its earlier scratchpad copy is gone), and capture `<scratchpad>/before-body.txt` with `uv run --with tomli-w python <scratchpad>/mutate.py`

**Checkpoint**: Both harnesses exist and have baselines; the header harness is
proven deterministic. No repository file has changed.

---

## Phase 2: User Story 2, Commit 1 (Declare each kind once) (Priority: P1)

**Goal**: `_Kind` and `_KINDS` exist and are the single source; the four old
tables become expressions computed from `_KINDS`. No reader changes, so no
report can move.

**Independent Test**: The four tests below pass, the full suite passes, and
`diff <scratchpad>/before.txt` against a fresh harness run is empty.

### Tests for Commit 1 (write first, watch fail) ⚠️

> One test at a time: write it, run `uv run pytest -m "not slow"`, watch it
> fail on `AttributeError: ... '_KINDS'`, then write the next. Add the three
> new tests beside the pinning test in `tests/unit/test_rules.py`, importing
> `from cetools import rules as rules_module` inside each, as the neighboring
> tests do. No test asserts a count of kinds (SC-005).

- [ ] T007 [US2] Add `test_declared_kind_names_are_unique` to `tests/unit/test_rules.py`: `names = [k.name for k in rules_module._KINDS]`, then `assert len(set(names)) == len(names)` (FR-015 invariant 1)
- [ ] T008 [US2] Add `test_one_file_kinds_and_only_they_declare_a_canonical_file` to `tests/unit/test_rules.py`: for every `k` in `rules_module._KINDS`, `assert k.arity in ("one", "many")` and `assert (k.arity == "one") == (k.canonical_file is not None)` (FR-015 invariant 2)
- [ ] T009 [US2] Add `test_every_one_file_kind_is_parsed_exactly_once` to `tests/unit/test_rules.py`: `assert [k.name for k in rules_module._KINDS if k.arity == "one" and k.parser is None] == ["background-skills"]` and `assert all(k.parser is None for k in rules_module._KINDS if k.arity == "many")`. Its docstring says the explicit steps call their parsers directly (FR-001) and the presence check fails a load that never parses a kind, which together make this sufficient (FR-015 invariant 3)
- [ ] T010 [US2] Rewrite `test_canonical_file_names_the_packaged_declarer_of_every_single_instance_kind` (`tests/unit/test_rules.py:605-623`) as `test_each_declared_canonical_file_is_the_packaged_declarer_of_its_kind`: keep the `_discover_packaged()` / `assert not problems` / `_packaged_kind_map(packaged)` setup; loop `for k in rules_module._KINDS: if k.arity == "one": assert declarers.get(k.canonical_file) == k.name`; delete the `sorted(...) == sorted(...)` line, the `== 11` assertion, and the comment above it (FR-012, SC-005). Rewrite the docstring to say `_singleton_slots` reads each one-file kind's slot from its declaration, which is sound only while each declared canonical file is the packaged file declaring that kind

### Implementation for Commit 1

- [ ] T011 [US2] In `src/cetools/rules.py`, add a `# --- kind declarations ---` section between the end of `parse_task_parameters` and `# --- discovery ---`, holding `_Kind` exactly as [contracts/kind-declarations.md](contracts/kind-declarations.md) states it (`@dataclass(frozen=True, slots=True)`; `name: str`, `version: int`, `arity: Literal["one", "many"]`, `canonical_file: str | None = None`, `parser: Callable[[Mapping[str, object], ParseContext], object] | None = None`) and `_KINDS: tuple[_Kind, ...]`, one positional line per kind, in the order and with the values of the [data-model.md](data-model.md) table: `task-parameters` 2 `tasks.toml` `parse_task_parameters`; `characteristics` 2 `characteristics.toml` `parse_characteristics`; `skills` 2 `skills.toml` `parse_skills`; `benefits` 1 `benefits.toml` `parse_benefits`; `career` 4 many; `draft-table` 1 `draft.toml` `parse_draft_table`; `aging-table` 1 `aging.toml` `parse_aging_table`; `mishap-table` 1 `mishaps.toml` `parse_mishap_table`; `background-skills` 1 `background-skills.toml` (no parser); `medical-tiers` 1 `medical-tiers.toml` `parse_medical_tiers`; `chargen-parameters` 2 `chargen-parameters.toml` `parse_chargen_parameters`; `given-names` 1 `given-names.toml` `parse_given_names`; `surnames` 1 many. Add `from typing import Literal`. A one-line comment states the order is for readers, grouped by the module owning each parser, and carries no behavior (FR-003). Cross-check every version and basename against the literals at `rules.py:58-99` before deleting them in T012
- [ ] T012 [US2] In `src/cetools/rules.py`, delete the four hand-written tables at `:58-99` and redefine the same four names immediately after `_KINDS` as values computed from it: `_SUPPORTED_VERSION = {k.name: k.version for k in _KINDS}`, `_SINGLETON_KINDS = tuple(k.name for k in _KINDS if k.arity == "one")`, `_CANONICAL_FILE = {k.name: k.canonical_file for k in _KINDS if k.arity == "one"}`, and `_KIND_AT_CANONICAL_FILE` derived from `_CANONICAL_FILE` as today. Touch no reader (FR-011 permits these computed names before the last commit). Run T007-T010 green
- [ ] T013 [US1] Gate commit 1: `uv run pytest -m "not slow"`, then `uv run pytest` in full; `uv run black --check src tests` and `uv run isort --check src tests` clean; `uv run python <scratchpad>/kinds_harness.py > <scratchpad>/after-1.txt && diff <scratchpad>/before.txt <scratchpad>/after-1.txt` empty; `git diff --stat main -- tests/golden tests/contract tests/integration` empty. A non-empty diff means stop and reconsider, never edit a test or move the sort
- [ ] T014 [US2] Commit via `git-ops`: `refactor(rules): declare each rules-data kind once`, body stating the change is structural; `src/cetools/rules.py` and `tests/unit/test_rules.py` only; no `CHANGELOG.md` entry

**Checkpoint**: `_KINDS` is the single source; the old names are views of it.

---

## Phase 3: User Story 2, Commit 2 (Read kind facts from the declarations) (Priority: P1)

**Goal**: every reader reads `_KINDS` at call time, and the four computed names
are gone, so patching `rules._KINDS` patches every reader (research R2).

**Independent Test**: `rg -n '_SUPPORTED_VERSION|_SINGLETON_KINDS|_CANONICAL_FILE|_KIND_AT_CANONICAL_FILE' src tests`
is empty, the full suite passes, and the header harness diff is empty.

### Tests for Commit 2 (write first, watch fail) ⚠️

- [ ] T015 [US2] In `tests/unit/test_rules.py`, add a module-level helper `_kinds_with_version(rules_module, name, version)` returning `tuple(replace(k, version=version) if k.name == name else k for k in rules_module._KINDS)` (`from dataclasses import replace`), and change `test_a_supported_schema_version_is_counted_per_kind`'s patch at `:324` from `monkeypatch.setitem(rules_module._SUPPORTED_VERSION, "benefits", 2)` to `monkeypatch.setattr(rules_module, "_KINDS", _kinds_with_version(rules_module, "benefits", 2))`. Nothing else in the test changes. Watch it fail: the readers still read `_SUPPORTED_VERSION`, computed at import
- [ ] T016 [US2] Make the same change to `test_raising_one_kinds_version_rejects_that_kinds_file_and_no_others`'s patch at `tests/unit/test_rules.py:342`, using the T015 helper. Watch it fail
- [ ] T017 [US2] In `test_supported_schema_version_is_a_literal_not_derived_from_package_version` (`tests/unit/test_rules.py:824`), change `for supported in rules_module._SUPPORTED_VERSION.values():` to `for supported in (k.version for k in rules_module._KINDS):` and update any docstring wording naming `_SUPPORTED_VERSION`. This one stays green; it is retargeted, not a new red

### Implementation for Commit 2

- [ ] T018 [US2] In `_validate`'s header checks (`src/cetools/rules.py:522-536`), build `declared = {k.name: k for k in _KINDS}` once per `_validate` call, before the per-file loop, and use it for the unknown-kind membership test, for `expected=f"one of: {', '.join(sorted(declared))}"` (sorted by name, not declaration order; FR-005), and for `supported = declared[kind].version`. Run T015 and T016 green
- [ ] T019 [US2] In `_packaged_kind_map` (`src/cetools/rules.py:237`), replace `kind in _SUPPORTED_VERSION` with membership in the declared names read from `_KINDS` at call time (FR-004)
- [ ] T020 [US2] In `_singleton_slots` (`src/cetools/rules.py:438-460`), replace `declared in _SINGLETON_KINDS` with a test over one-file declarations in `_KINDS`, and `_KIND_AT_CANONICAL_FILE.get(basename)` with a scan for the one-file `k` whose `canonical_file == basename`, yielding the same slot set for every input (FR-006). Rewrite the docstring passage at `:450` that names `_CANONICAL_FILE` and the old pinning test so it names the declarations and `test_each_declared_canonical_file_is_the_packaged_declarer_of_its_kind`
- [ ] T021 [US2] In `_validate`'s missing/duplicate check (`src/cetools/rules.py:587-593`), iterate `for k in _KINDS: if k.arity != "one": continue`, using `k.name` where `kind` was and `file=k.canonical_file` where `_CANONICAL_FILE[kind]` was; wording, `file`, `found`, and `expected` of every problem unchanged (FR-006)
- [ ] T022 [US2] Delete `_SUPPORTED_VERSION`, `_SINGLETON_KINDS`, `_CANONICAL_FILE`, and `_KIND_AT_CANONICAL_FILE` from `src/cetools/rules.py`; `rg -n '_SUPPORTED_VERSION|_SINGLETON_KINDS|_CANONICAL_FILE|_KIND_AT_CANONICAL_FILE' src tests` is empty, including docstrings and comments
- [ ] T023 [US1] Gate commit 2 exactly as T013, writing `<scratchpad>/after-2.txt`
- [ ] T024 [US2] Commit via `git-ops`: `refactor(rules): read kind facts from the declarations`, body stating the change is structural; no `CHANGELOG.md` entry

**Checkpoint**: discovery, header checks, slot bookkeeping, and the
missing/duplicate check read `_KINDS`; no other kind table exists.

---

## Phase 4: User Story 2 and User Story 3, Commit 3 (Parse one-file kinds in one loop) (Priority: P1/P2)

**Goal**: the ten `parse_singleton` calls become one loop that names no kind,
the eleven-clause presence check reads the declarations, and the module ends
shorter than 1103 lines. This is the refactor step under a green suite: no test
is added because no behavior is (research R8).

**Independent Test**: the full suite passes; both harness diffs are empty
(this is the commit that changes parse order, research R4); `wc -l` is under
1103.

### Implementation for Commit 3

- [ ] T025 [US2] In `_validate` (`src/cetools/rules.py:636-651`), replace the ten `parse_singleton(...)` assignments with `values: dict[str, Any] = {}` and one loop, `for k in _KINDS: if k.parser is not None: values[k.name] = parse_singleton(k.name, k.parser)`, that names no kind (FR-007). Add `Any` to the `typing` import
- [ ] T026 [US2] Directly after the loop, read the kinds the cross-file rules use into typed locals from `values`: `characteristics`, `skills`, `benefits`, `draft`, `aging`, `mishaps`, `medical_tiers`, `chargen` (for example `characteristics: CharacteristicRegistry | None = values["characteristics"]`), so the substitutes and every cross-file rule below read unchanged. Locals for `task_parameters` and `given_names` go only if the presence check and constructor no longer need them
- [ ] T027 [US2] Keep the background-skills step explicit after the substitutes (`src/cetools/rules.py:660-663`), changed only to store into `values["background-skills"] = parse_singleton("background-skills", parse_background_skills, career_skills)`; keep its "parsed after the substitutes" comment (FR-007)
- [ ] T028 [US2] Replace the presence check's eleven `... is None` clauses (`src/cetools/rules.py:1033-1047`) with `problems or any(values.get(k.name) is None for k in _KINDS if k.arity == "one") or not surnames`. Keep `or not surnames`; add no career requirement (FR-008). `problems.sort()` at `:1029` stays exactly where it is (FR-013)
- [ ] T029 [US2] Build `RulesData(...)` field by field as today, reading each one-file field from `values["<kind>"]` (for example `draft=values["draft-table"]`); `careers`, `surnames`, and `provenance` unchanged (FR-010)
- [ ] T030 [US2] Rewrite `parse_singleton`'s docstring (`src/cetools/rules.py:620-627`): drop "so the call order below is the insertion order, and moving a call moves a report"; keep that each file gets its own carrier and that the single `problems.sort()` makes parse order unobservable and stays where it is (FR-011). `rg -n 'load-bearing|moving a call moves a report' src/cetools/rules.py` is empty
- [ ] T031 [US1] Gate commit 3 as T013, writing `<scratchpad>/after-3.txt`, plus the body harness: `uv run --with tomli-w python <scratchpad>/mutate.py > <scratchpad>/after-body.txt && diff <scratchpad>/before-body.txt <scratchpad>/after-body.txt` empty
- [ ] T032 [US3] `wc -l < src/cetools/rules.py` is strictly less than `1103` (SC-004). If not, tighten the new code before committing; never compress unrelated code to hit the number
- [ ] T033 [US2] Run [quickstart.md](quickstart.md)'s User Story 2 checks: `rg -n '"draft-table"' src/cetools/rules.py` and `rg -n '"background-skills"' src/cetools/rules.py` hit only the `_KINDS` declaration and kind-specific code (the background-skills step, a cross-file local, the `RulesData(...)` constructor), never a list enumerating kinds; `rg -n '== 11|len\(.*_KINDS' tests` is empty (SC-002, SC-005)
- [ ] T034 [US2] Commit via `git-ops`: `refactor(rules): parse one-file kinds in one loop`, body stating the change is structural and that parse order now follows declaration order, made unobservable by the unmoved sort; no `CHANGELOG.md` entry

**Checkpoint**: one enumeration of kinds remains, and the loader is shorter.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: confirm the whole branch against the spec before review.

- [ ] T035 Run [quickstart.md](quickstart.md) 1b: `git diff main -- tests/ ':!tests/unit/test_rules.py'` is empty, and `git diff main -- tests/unit/test_rules.py` shows only T007-T010 and T015-T017
- [ ] T036 Run [quickstart.md](quickstart.md)'s commit hygiene: every subject in `git log --format='%s' main..HEAD` after the spec and merge commits starts `refactor(rules):`, and `git diff --stat main -- CHANGELOG.md` is empty (FR-014). Also confirm `git diff main -- src/cetools/__init__.py` is empty (FR-002)
- [ ] T037 Run the optional type check, `uv run mypy src`, and confirm it reports nothing new against the baseline
- [ ] T038 Push the branch and open the PR via `git-ops`, with the body shaped by `sks:pr`: evidence is the suite, the three empty header-harness diffs, the empty body-harness diff, and the line count

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies. T001-T005 are sequential; T006 runs in parallel with T003-T005.
- **Commit 1 (Phase 2)**: depends on Phase 1 baselines.
- **Commit 2 (Phase 3)**: depends on commit 1 (`_KINDS` must exist for the patches to target).
- **Commit 3 (Phase 4)**: depends on commit 2 (the loop and presence check read `_KINDS` alone).
- **Polish (Phase 5)**: depends on commit 3.

### User Story Dependencies

- **US1 (P1)** is the standing gate on every commit (T013, T023, T031), not a slice of its own.
- **US2 (P1)** is delivered across all three commits.
- **US3 (P2)** depends on US2 being complete; it is measured once, at T032.

### Within Each Commit

- Tests are written one at a time and watched fail before the implementation that turns them green (Constitution III); commit 3 has no new test and relies on the green suite and both harnesses.
- Every task in Phases 2-4 edits `src/cetools/rules.py` or `tests/unit/test_rules.py`, so no two run in parallel.

### Parallel Opportunities

- T006 (the body harness) with T003-T005 (the header harness): different scratchpad files, no shared state.
- Nothing else: the feature is one source module and one test module, edited in order.

---

## Parallel Example: Setup

```text
Task: "Write and baseline the header harness, T003-T005, in <scratchpad>/kinds_harness.py"
Task: "Rebuild and baseline 007's body harness, T006, in <scratchpad>/mutate.py"
```

---

## Implementation Strategy

### MVP First

Commit 1 alone is a safe stopping point: drift between the lists becomes
impossible because they are all computed from `_KINDS`, and no reader has
changed. It does not satisfy FR-011 or SC-002 until commits 2 and 3 land, so
the feature is complete only after Phase 4.

### Incremental Delivery

1. Phase 1: baselines. No repository change.
2. Commit 1: single source, old names as views. Gate, commit.
3. Commit 2: readers on `_KINDS`, views deleted. Gate, commit.
4. Commit 3: one loop, one presence expression, shorter module. Gate, commit.
5. Polish, push, PR.

Each commit is independently revertible and leaves the suite green.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps each task to the story it serves
- A harness diff, a corpus failure, or a moved report means stop and
  reconsider; never adjust a test, a fixture, or the position of `problems.sort()`
- Docstrings and comments naming a removed table or renamed test change in the
  same commit as the thing they name
