# Tasks: Parse Context Carrier

**Input**: Design documents from `/specs/007-parse-context-carrier/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/parse-context.md](contracts/parse-context.md),
[quickstart.md](quickstart.md), [inventory.md](inventory.md)

**Tests**: REQUIRED. Constitution Principle III is non-negotiable and the plan
makes the adapted `test_schema.py`, the new `test_parse_context.py`, and both
guards load-bearing (FR-023, FR-026, FR-027). Every test task below is written
and watched fail before the code that satisfies it.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

Single project: `src/cetools/`, `tests/` at repository root. Scratchpad work
(the mutation harness and its output) lives outside the repository and is never
committed (research R10, FR-016b).

## How this decomposes

The feature is a behavior-preserving migration, so the work decomposes by the
seven-commit sequence FR-019 mandates rather than into independently shippable
slices. The phases below follow that sequence, and every task carries the story
it serves so traceability survives:

| Phase | Commit | Story served |
|---|---|---|
| 1 — Setup | *(pre-commit)* | US1's evidence apparatus |
| 2 — Foundational | 1: the carrier, delegating | US2, US3 |
| 3 — US1 | *(standing gate)* | US1 |
| 4 — US2 | 2–6: one parser each | US2, gated by US1 |
| 5 — US3 | 7: delete the superseded path | US3, closes US2 |
| 6 — US4 | *(continuous, finalized here)* | US4 |
| 7 — Polish | *(pre-merge)* | all |

**Every commit is structural** (FR-018). No commit carries a `CHANGELOG.md`
entry (FR-018a). Commit messages follow Conventional Commits with a scope and
say `structural` explicitly.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Build and prove the evidence apparatus FR-016b makes mandatory for
every commit, and capture the baseline every later diff is taken against. None
of this is committed to the repository.

- [X] T001 Write the mutation harness at `<scratchpad>/mutate.py` following the recipe in [quickstart.md](quickstart.md) §1b: walk every `src/cetools/data/**/*.toml`, apply delete/retype/empty to each path, validate each mutant through `cetools.rules.validate_rules` against a temporary override directory, and print one sorted `file|path|kind|p.file|p.location|p.found|p.expected` line per problem
- [X] T002 Prove the harness is deterministic: run `uv run --with tomli-w python <scratchpad>/mutate.py` twice against the unmodified tree and confirm the two outputs are byte-identical — a non-deterministic harness makes every later diff noise rather than evidence
- [X] T003 Capture the full baseline sweep from the merge-base with `main` into `<scratchpad>/before-full.txt` using `uv run --with tomli-w python <scratchpad>/mutate.py`
- [X] T004 Capture per-module baselines into `<scratchpad>/before-names.txt`, `before-rules.txt`, `before-registries.txt`, `before-careers.txt`, and `before-chargen.txt` by restricting the harness's outer loop to the files each parser reads, so each parser commit has a fast gate to run
- [X] T005 Record the pre-feature state: `.venv/bin/python -m pytest` green, and `git diff --stat main -- tests/golden tests/contract tests/integration` empty, so FR-016's "unedited corpora" claim has a starting point

**Checkpoint**: The evidence apparatus exists, is proven deterministic, and has
a baseline. No repository file has changed.

---

## Phase 2: Foundational (Commit 1 — the carrier, delegating)

**Purpose**: `ParseContext`, `HEADER_KEYS`, and `require_list` exist; the seven
inherited checks forward to the free functions that already exist, so this
commit *cannot* have moved a message. Nothing calls the carrier yet.

**⚠️ CRITICAL**: No parser conversion can begin until this phase is complete.

### Tests for Commit 1 (write first, watch fail) ⚠️

> Each task below is one test, run to failure before the next is written, per
> the constitution's "one test at a time".

- [X] T006 [US2] Adapt `tests/unit/test_schema.py` in place to the method call shape: every existing case keeps transcribing its row of [`006-validation-vocabulary/contracts/schema-vocabulary.md`](../006-validation-vocabulary/contracts/schema-vocabulary.md), rewritten to build a `ParseContext` and call the method. Row-for-row parity with that contract is the FR-026 criterion; no case may be dropped because the carrier now supplies context. Watch it fail on import
- [X] T007 [US2] Add the `require_list` condition table to `tests/unit/test_schema.py` from [contracts/parse-context.md](contracts/parse-context.md) §`require_list`: key absent → `found="missing"`, `expected=expected_missing or expected`, returns `None`; value not a `list` → `found=type_name(value)`, `expected=expected`, returns `None`; value `[]` → `found="an empty array"`, `expected=expected_empty or expected`, returns `None`; non-empty `list` → no problem, returns the list. Watch it fail
- [X] T008 [US2] Add the `require_list` `allow_empty=True` case to `tests/unit/test_schema.py`: an empty list is accepted and returned, and no problem is recorded. Watch it fail
- [X] T009 [P] [US1] Write `tests/unit/test_parse_context.py` covering location construction across several levels of nested descent and through array indices, per the table in [contracts/parse-context.md](contracts/parse-context.md) §*Construction and descent*: `""`+`"task"`→`"task"`, `"task"`+`"roll"`→`"task.roll"`, `"names"`+`0`→`"names[0]"`, `"tables.service"`+`("entries", 3)`→`"tables.service.entries[3]"`, `"rows[2].effects[0]"`+`"class"`→`"rows[2].effects[0].class"`. Watch it fail
- [X] T010 [US1] Add the empty-parent case to `tests/unit/test_parse_context.py`: a top-level key at location `""` yields the bare key, never a leading dot (FR-003, FR-027 — the case a naive join gets wrong invisibly). Watch it fail
- [X] T011 [US1] Add the shared-collection case to `tests/unit/test_parse_context.py`: a problem reported on a child carrier is visible through the parent's `problems`, and the collection is shared by reference rather than copied (FR-004). Watch it fail
- [X] T012 [US1] Add the per-scope failure cases to `tests/unit/test_parse_context.py`: `failed` is `False` on a carrier derived after a sibling scope already recorded a problem, `True` once anything is recorded within this carrier's own scope, and `True` for a problem recorded by a descendant (FR-005, FR-027). Watch it fail
- [X] T013 [US1] Add the loader case to `tests/unit/test_parse_context.py`: a carrier constructed over a list that already holds problems takes its watermark from the list's current length, so `failed` is `False` at construction (research R4, needed by `_class_effect_problems`). Watch it fail

### Implementation for Commit 1

- [X] T014 [US2] Add `HEADER_KEYS = frozenset({"schema", "schema-version"})` at module level in `src/cetools/schema.py`, bare-named per research R9
- [X] T015 [US2] Implement `ParseContext.__init__(self, file: str, location: str = "", problems: list[ValidationProblem] | None = None)` in `src/cetools/schema.py`, adopting `problems` **by reference** and computing the private watermark as the collection's current length
- [X] T016 [US2] Implement `ParseContext.at(self, *parts: str | int) -> "ParseContext"` in `src/cetools/schema.py`: a `str` part joins with `.` except against an empty location where it joins with nothing; an `int` part joins as `[n]`. The child shares `file` and the collection object and takes a fresh watermark
- [X] T017 [US2] Implement `ParseContext.report(self, *, found: str, expected: str) -> None`, the `problems` property returning the whole shared collection as a tuple in insertion order, and the `failed` property returning `len(collection) > watermark`, in `src/cetools/schema.py`. `report` is keyword-only (research R3)
- [X] T018 [US2] Implement the seven inherited checks as two-line forwarding methods on `ParseContext` in `src/cetools/schema.py` — `require_int(container, key, *, minimum=None)`, `require_string(container, key)`, `require_bool(container, key)`, `require_roll(container, key)`, `require_dict(value, *, expected)`, `optional_bool(container, key, *, default=False)`, `unrecognized_keys(data, allowed)` — each calling the existing free function with `self.file` and the location it already reports at. The six container-and-key checks report at `self.at(key)`; `require_dict` reports at `self.location`; `unrecognized_keys` appends each extra key's problem at `self.at(key)` instead of returning a list, preserving the existing sort by key name
- [X] T019 [US2] Implement `require_list(container, key, *, expected, expected_missing=None, expected_empty=None, allow_empty=False)` directly on `ParseContext` in `src/cetools/schema.py` — it has no free function to delegate to (research R8). Absence is detected by membership (`key not in container`), not by a `None` value

### Guard relaxation for Commit 1

- [X] T020 [US3] Rewrite `tests/guards/test_no_duplicate_checks.py` to walk `ast.ClassDef` for `ParseContext` in `src/cetools/schema.py` and every module top level under `src/`, requiring each of the eight check names to be defined exactly once as a method of that class
- [X] T021 [US3] Carry the existing "the guard can fail" and underscore-prefixed-copy meta-tests over into `tests/guards/test_no_duplicate_checks.py`, retargeted at a planted class body
- [X] T022 [US3] Add the temporary tolerance to `tests/guards/test_no_duplicate_checks.py`: exactly one extra definition per check name, and only in `src/cetools/schema.py` — the free function being delegated to. The tolerance MUST state in the guard itself that it is temporary and that the final commit closes it (FR-020)
- [X] T023 [US1] Gate commit 1: run `.venv/bin/python -m pytest`, then the full mutation sweep diffed against `<scratchpad>/before-full.txt`. An empty diff is the pass condition and is not optional (FR-016b). Commit as structural — `refactor(schema): add ParseContext carrier delegating to existing checks`

**Checkpoint**: The carrier exists and every forwarding call reaches the code
the parsers already reach. US3's first acceptance scenario is now checkable
rather than asserted.

---

## Phase 3: User Story 1 - The reports do not move (Priority: P1)

**Goal**: Establish the standing per-commit gate and pin the two named
scenarios, so "nothing the tool reports changes" has evidence behind it at
every step rather than only at the end.

**Independent Test**: Run the frozen corpora and the mutation comparison against
the tree as it stands; the corpora pass unedited and the comparison diffs empty.
Confirm `git diff --stat main -- tests/golden tests/contract` is empty.

- [X] T024 [US1] Confirm the standing gate is present as the final task of every commit group — T036, T043, T054, T062, T072, and T082 — and that each states the same two conditions: `.venv/bin/python -m pytest` green, plus the mutation diff for that commit's scope empty. A commit group without its gate is a commit whose central claim has no evidence behind it (FR-016b)
- [X] T025 [P] [US1] Confirm US1 scenario 2 stays pinned: `.venv/bin/python -m pytest tests/integration/test_validation_categories.py -k "cycle"` — a skills file with a cycle and one unrelated bad field still does not report the cycle, because the gate at `src/cetools/registries.py:463` still skips (FR-017)
- [X] T026 [P] [US1] Confirm US1 scenario 3 stays pinned: `.venv/bin/python -m pytest tests/integration/test_validation_categories.py -k "duplicate"` — two career files declaring the same name still produce a problem naming one file in `file` and both in `found`, the shape the carrier deliberately cannot describe (FR-012)
- [X] T027 [US1] Confirm the frozen corpora are untouched: `git diff --stat main -- tests/golden tests/contract tests/integration` is empty. FR-016 makes a failure here a signal to stop and revert, never to adjust a fixture

**Checkpoint**: The gate is defined, proven against commit 1, and the two named
scenarios have a command a reviewer can point at.

---

## Phase 4: User Story 2 - A contributor stops threading context (Priority: P1)

**Goal**: Every parser descends with a carrier. No parsing-layer function takes
a file name, builds a location by concatenation, or chooses a problem-passing
convention.

**Independent Test**: On a scratch branch, add a checked field to one data-file
kind (say `[pension] maximum-terms` to `chargen-parameters`) and confirm
`git diff | grep -nE '\bfile\b|f"\{location\}|problems\.(append|extend)|_HEADER_KEYS'`
produces no output.

**Order**: smallest module first, which is 006's order and for 006's reason —
the pattern is established four times before it reaches the module holding a
third of the sites. Each module is one commit, and the modules are strictly
sequential because `rules._SINGLETON_PARSERS` holds one signature at a time.

**Inventory obligation**: a wording disagreement or questionable gate noticed
while converting is recorded in [inventory.md](inventory.md) as a new `I-n`
entry in the same commit (FR-021), never fixed. See Phase 6.

### Commit 2 — `names.py` (4 signatures, 7 problems, 2 array sites, 3 scopes)

- [X] T028 [US2] Convert the entry points `parse_given_names` and `parse_surnames` in `src/cetools/names.py` to `(data: Mapping[str, object], ctx: ParseContext) -> Value | None`, returning the value or `None` and no longer returning a problem list (research R6)
- [X] T029 [US2] Convert the helpers in `src/cetools/names.py` — `_require_name_array` and `_parse_surname_entry` — to take a carrier in place of `file`, `location`, and `problems`
- [X] T030 [US2] Replace every location-building f-string in `src/cetools/names.py` with `ctx.at(...)` descent, including the `names[i]` descent that feeds `_parse_surname_entry`
- [X] T031 [US2] Convert the 2 array sites in `src/cetools/names.py` to `require_list` per [data-model.md](data-model.md) rows 13 and 14: `names.py:21` (given names) and `names.py:159` (surnames), both `expected="at least one entry"`, `expected_missing="an array"`
- [X] T032 [US2] Convert the 7 hand-built `ValidationProblem(...)` constructions in `src/cetools/names.py` to `ctx.report(found=..., expected=...)`, supplying only `found` and `expected` (FR-009)
- [X] T033 [US2] Convert the 3 emptiness questions in `src/cetools/names.py` to `ctx.failed`: `names.py:77` (`parse_given_names`) on the **file** carrier, `names.py:124` (`_parse_surname_entry`) on the **fragment** carrier for one surname entry, and `names.py:179` (`parse_surnames`) on the **file** carrier. Note that `names.py:124` is written `if name is None or problems:` with the emptiness test second, so a grep for `if problems` misses it
- [X] T034 [US2] Delete `_HEADER_KEYS` at `src/cetools/names.py:15` and import `HEADER_KEYS` from `src/cetools/schema.py`
- [X] T035 [US2] Update `rules._validate` in `src/cetools/rules.py` to build one carrier per given-names and surnames file over a fresh list, call the converted entry point, and extend its run-wide list from `ctx.problems`; update the `_SINGLETON_PARSERS` entry for `given-names` and the direct call for `parse_surnames`. The `problems.sort()` at `src/cetools/rules.py:1058` MUST NOT move (FR-015)
- [X] T036 [US1] Gate commit 2: `.venv/bin/python -m pytest` green, and the restricted sweep over `names/*.toml` diffed empty against `<scratchpad>/before-names.txt`. Commit as structural — `refactor(names): descend with ParseContext`

### Commit 3 — `rules.py` (2 signatures, 2 problems, 1 scope, the loader's carriers)

- [X] T037 [US2] Convert `parse_task_parameters` at `src/cetools/rules.py:148` to `(data, ctx)`, replacing its `unrecognized_key_problems` / `require_dict` / `require_roll` calls with the carrier form shown in [contracts/parse-context.md](contracts/parse-context.md) §*Worked example*
- [X] T038 [US2] Convert the 2 hand-built problems in `parse_task_parameters` to `ctx.report(found=..., expected=...)`, and convert the emptiness question at `src/cetools/rules.py:206` to `ctx.failed` on the **file** carrier
- [X] T039 [US2] Convert `_class_effect_problems` at `src/cetools/rules.py:1019` to take a carrier: it is a cross-file rule that reports at `rows[i].effects[j].class` inside one named file, so FR-012a places it inside the carrier's territory. The loader builds one carrier for the aging file and one for the mishap file and passes them in. Its single `ValidationProblem(` construction is the 103rd of SC-006 — the one in-file problem that does not sit in a per-file parser — and both carriers are built over the loader's run-wide list at the point the check runs today, taking their watermark from its current length (T013, research R4)
- [X] T040 [US2] Leave `_unreadable` at `src/cetools/rules.py:248` exactly as it is, taking its own `file` parameter. It builds the problem for a file that could not be opened, which FR-012 places outside the carrier — there is no carrier to report through. This is the one exclusion from FR-011 (research R7), and SC-002 is 53 → 1
- [X] T041 [US2] Delete `_HEADER_KEYS` at `src/cetools/rules.py:63` and import `HEADER_KEYS` from `src/cetools/schema.py`
- [X] T042 [US2] Update the `_SINGLETON_PARSERS` entry for `task-parameters` at `src/cetools/rules.py:223` and its dispatch at `src/cetools/rules.py:663` to the `(data, ctx)` signature, and confirm the other twenty-eight cross-file problems in `src/cetools/rules.py` still build their own `ValidationProblem` unchanged (SC-006: 0 of 28 go through a carrier). The twenty-eight are the 24 in `_validate` plus one each in `_unreadable`, `_unlistable`, `_not_a_regular_file`, and `_compose`; `_class_effect_problems`' one is not among them and converts in T039
- [X] T043 [US1] Gate commit 3: `.venv/bin/python -m pytest` green, and the restricted sweep over the task-parameters, aging, and mishap files diffed empty against `<scratchpad>/before-rules.txt`. Commit as structural — `refactor(rules): give the loader and task parameters a ParseContext`

### Commit 4 — `registries.py` (7 signatures, 16 problems, 1 array site + 2 bare guards, 5 scopes)

- [X] T044 [US2] Convert the entry points `parse_characteristics`, `parse_skills`, and `parse_benefits` in `src/cetools/registries.py` to `(data, ctx)` returning the value or `None`, and convert the remaining helpers to take a carrier in place of `file`, `location`, and `problems`
- [X] T045 [US2] Replace every location-building f-string in `src/cetools/registries.py` with `ctx.at(...)` descent
- [X] T046 [US2] Convert `_parse_pseudo_hex` in `src/cetools/registries.py` so it takes the **file-level** carrier, derives `ctx.at("pseudo-hex")` internally for its field checks, and calls `ctx.unrecognized_keys(...)` on the file-level carrier. This reproduces today's bare location (`"typo"`, not `"pseudo-hex.typo"`) at `src/cetools/registries.py:239`, which FR-014 requires. Add a code comment citing [inventory.md](inventory.md) entry I-1
- [X] T047 [US2] Convert the array site at `src/cetools/registries.py:245` (`pseudo-hex.symbols`) to `require_list` with `expected="a non-empty array of strings"` and no other keyword — the one row of the fifteen that inlines a three-way conditional rather than the two-line twin, so a mechanical rewrite will not match it ([data-model.md](data-model.md) row 15)
- [X] T048 [US2] Convert the 2 bare array guards in `src/cetools/registries.py` to `require_list`: `registries.py:429` (`skills.<name>`) with `expected="an array of strings"` and `allow_empty=True` — it accepts an empty array today and must continue to, citing [inventory.md](inventory.md) I-4 in a comment — and `registries.py:474` (`benefits`) with `expected="an array of strings with at least one entry"` and `expected_empty="at least one entry"`, citing I-5
- [X] T049 [US2] Convert the 16 hand-built `ValidationProblem(...)` constructions in `src/cetools/registries.py` to `ctx.report(found=..., expected=...)`, including `_acyclic_problems`, which today returns a list — one of the three conventions SC-004 removes
- [X] T050 [US2] Convert the 5 emptiness questions in `src/cetools/registries.py` to `ctx.failed`: `registries.py:201` (`_parse_bands`) on the **fragment** carrier for the band list; `registries.py:328`, `registries.py:459`, and `registries.py:510` on the **file** carrier
- [X] T051 [US2] Convert the cross-reference gate at `src/cetools/registries.py:463` to `ctx.failed` on the **file-level** carrier, so one bad field anywhere in the skills file still skips the cycle check exactly as today (FR-017). Do not narrow it; the question of whether it is correct is [inventory.md](inventory.md) entry I-6
- [X] T052 [US2] Leave `bad` at `src/cetools/registries.py:454` as an ordinary comprehension-local list reaching the accumulator by the path it uses today. It is not one of SC-007's seventeen and does not become a scope; counting it would make the number eighteen, the looser reading SC-007 declines
- [X] T053 [US2] Delete `_HEADER_KEYS` at `src/cetools/registries.py:26`, import `HEADER_KEYS` from `src/cetools/schema.py`, and update the `_SINGLETON_PARSERS` entries for `characteristics`, `skills`, and `benefits` in `src/cetools/rules.py`
- [X] T054 [US1] Gate commit 4: `.venv/bin/python -m pytest` green, and the restricted sweep over `registries/*.toml` diffed empty against `<scratchpad>/before-registries.txt`. Commit as structural — `refactor(registries): descend with ParseContext`

### Commit 5 — `careers.py` (12 signatures, 37 problems, 5 array sites, 1 scope)

- [X] T055 [US2] Convert the entry point `parse_career` in `src/cetools/careers.py` to `(data, ctx, ...)` keeping its three registry arguments and returning the value or `None`, and convert all 12 of the module's file-name-taking functions to take a carrier
- [X] T056 [US2] Convert `_parse_ranks` and every other helper in `src/cetools/careers.py` that takes a caller-owned `problems` list to record through the carrier instead (SC-004)
- [X] T057 [US2] Replace every location-building f-string in `src/cetools/careers.py` with `ctx.at(...)` descent, including the `ladders[i]` and `tables.<t>.entries[i]` forms
- [X] T058 [US2] Convert the 5 array sites in `src/cetools/careers.py` to `require_list` per [data-model.md](data-model.md) rows 8–12: `careers.py:342` (`tables.<t>.entries`, `expected="at least one entry"`, `expected_missing="a non-empty array"`); `careers.py:483` (`ladders[i].ranks`, `expected="at least one rank"`); `careers.py:607` (`ladders`, `expected="at least one ladder"`); `careers.py:714` (`mustering-out.cash`, `expected="at least one amount"`, `expected_missing="a non-empty array"`); `careers.py:767` (`mustering-out.benefits`, `expected="at least one benefit"`, `expected_missing="a non-empty array"`). For rows 9 and 10 the caller now passes the container and the key so the single call covers both the absent and the wrong-type case
- [X] T059 [US2] Convert the 37 hand-built `ValidationProblem(...)` constructions in `src/cetools/careers.py` to `ctx.report(found=..., expected=...)`
- [X] T060 [US2] Convert the emptiness question at `src/cetools/careers.py:885` (`parse_career`) to `ctx.failed` on the **file** carrier
- [X] T061 [US2] Delete `_HEADER_KEYS` at `src/cetools/careers.py:45`, import `HEADER_KEYS` from `src/cetools/schema.py`, and update the direct `parse_career` call in `rules._validate`
- [X] T062 [US1] Gate commit 5: `.venv/bin/python -m pytest` green, and the restricted sweep over `careers/*.toml` diffed empty against `<scratchpad>/before-careers.txt`. Commit as structural — `refactor(careers): descend with ParseContext`

### Commit 6 — `chargen.py` (20 signatures, 40 problems, 7 array sites + 2 bare guards, 7 scopes)

- [X] T063 [US2] Convert the six entry points in `src/cetools/chargen.py` — `parse_draft_table`, `parse_aging_table`, `parse_mishap_table`, `parse_background_skills` (keeping its skills-registry argument), `parse_medical_tiers`, `parse_chargen_parameters` — to `(data, ctx, ...)` returning the value or `None`
- [X] T064 [US2] Convert the remaining 14 file-name-taking helpers in `src/cetools/chargen.py` to take a carrier, including `_parse_chargen_group`, whose `field_location` variable is `f"{location}.{key}"` and is exactly what `self.at(key)` reproduces
- [X] T065 [US2] Resolve the mixed convention in `parse_mishap_table`: `src/cetools/chargen.py:601` returns a pair and `src/cetools/chargen.py:602` extends a caller-owned list, four lines apart. Both become the shared collection (SC-004)
- [X] T066 [US2] Replace every location-building f-string in `src/cetools/chargen.py` with `ctx.at(...)` descent, including the `rows[i].effects[j]` and `<section>[i]` forms
- [X] T067 [US2] Convert the 7 array sites in `src/cetools/chargen.py` to `require_list` per [data-model.md](data-model.md) rows 1–7: `chargen.py:68` (`careers`, `expected="at least one entry"`, `expected_missing="a non-empty array"`); `chargen.py:282` (`rows`, `expected="at least one row"`, `expected_missing="an array"`); `chargen.py:559` (`mishaps`/`injuries`, `expected="at least one row"`, `expected_missing="an array"`); `chargen.py:692` (`law-level`/`trade-code`/`education`, `expected="at least one entry"`, `expected_missing="an array"`); `chargen.py:835` (`tiers[i].thresholds`, same); `chargen.py:897` (`tiers`, same); `chargen.py:1079` (`mustering-out.rank-benefits`/`.material-rank-dm`, same). For rows 3, 4, and 7 the caller now passes the container and the key so the single call covers both the absent and the wrong-type case
- [X] T068 [US2] Convert the 2 bare array guards in `src/cetools/chargen.py` to `require_list` with `expected="an array"` and `allow_empty=True`: `chargen.py:188` (`rows[i].effects`) and `chargen.py:490` (`<section>[i].effects`). Both accept an empty array today and must continue to — converting them without `allow_empty` would start reporting a file that validates clean, which FR-014 forbids. Add a comment citing [inventory.md](inventory.md) entry I-4
- [X] T069 [US2] Convert the 40 hand-built `ValidationProblem(...)` constructions in `src/cetools/chargen.py` to `ctx.report(found=..., expected=...)`
- [X] T070 [US2] Convert the 7 emptiness questions in `src/cetools/chargen.py` to `ctx.failed`: `chargen.py:474` (`_parse_mishap_effect`) on the **fragment** carrier for one mishap effect; `chargen.py:95`, `chargen.py:315`, `chargen.py:619`, `chargen.py:737`, `chargen.py:929`, and `chargen.py:1162` on the **file** carrier
- [X] T071 [US2] Delete `_HEADER_KEYS` at `src/cetools/chargen.py:28`, import `HEADER_KEYS` from `src/cetools/schema.py`, and update the five `_SINGLETON_PARSERS` entries plus the direct `parse_background_skills` call in `rules._validate`
- [X] T072 [US1] Gate commit 6: `.venv/bin/python -m pytest` green, and the restricted sweep over `chargen/*.toml` diffed empty against `<scratchpad>/before-chargen.txt`. Commit as structural — `refactor(chargen): descend with ParseContext`

**Checkpoint**: All five parsers descend with a carrier. SC-003 (5 → 1),
SC-004 (3 → 1), SC-005 (15 → 0), SC-006 (103 through the carrier, 0 of 28),
and SC-007 (17 scoped) hold. SC-002 does not yet, because the seven free
functions in `schema.py` still take a file name — commit 7 closes that.

---

## Phase 5: User Story 3 - A reviewer reads the migration one parser at a time (Priority: P2)

**Goal**: The superseded path is gone, the four counts are held by a guard that
can demonstrably fail, and the sequence reads as seven green, independently
reviewable, structural-only commits.

**Independent Test**: `git switch --detach <commit> && .venv/bin/python -m pytest`
for each of the seven; every one passes, and every diff changes structure only.

### Commit 7 — delete the superseded path (red step first)

- [X] T073 [US3] Write `tests/guards/test_parsing_layer_shape.py` holding SC-002: no function in `src/cetools/careers.py`, `chargen.py`, `names.py`, `registries.py`, or `schema.py` has a parameter named `file`; in `src/cetools/rules.py` only `_unreadable` may, and the guard names it with FR-012 as the reason. Run it now — it MUST fail, because the seven free functions still take a file name. That failure is this commit's red step
- [X] T074 [P] [US3] Add SC-003 to `tests/guards/test_parsing_layer_shape.py`: the name `HEADER_KEYS` (or `_HEADER_KEYS`) is assigned at module level exactly once under `src/`, in `schema.py`
- [X] T075 [P] [US3] Add SC-004 to `tests/guards/test_parsing_layer_shape.py`: in the five parser modules, no function annotates a parameter as `list[ValidationProblem]` and no return annotation contains `list[ValidationProblem]`. The loader's bare `-> ValidationProblem` helpers are unaffected
- [X] T076 [P] [US3] Add SC-005 to `tests/guards/test_parsing_layer_shape.py`: no module under `src/` but `schema.py` contains a string constant equal to `"an empty array"`. Implement it as an AST walk comparing `ast.Constant` values for equality, skipping module, class, and function docstrings — `src/cetools/errors.py:37` names the phrase inside prose describing the vocabulary, so a `grep` for the quoted string would fail on it forever and get "fixed" by weakening the guard. Run it now — it MUST fail, because the literal still sits in a free function body as well as in the class
- [X] T077 [US3] Add a planted-violation self-test for each of the four counts in `tests/guards/test_parsing_layer_shape.py` — a function taking `file`, a second `HEADER_KEYS`, a `list[ValidationProblem]` parameter, a stray `"an empty array"` literal — each confirming its own detector rejects the shape and then removing it. One self-test covering the guard as a whole is not enough (FR-023)
- [X] T078 [US3] Move the seven free-function bodies into `ParseContext` in `src/cetools/schema.py` and delete `require_int`, `require_string`, `require_bool`, `require_roll`, `require_dict`, `optional_bool`, and `unrecognized_key_problems` as module-level functions. `unrecognized_keys` keeps appending rather than returning, and its sort by key name is unchanged
- [X] T079 [US3] Tighten `tests/guards/test_no_duplicate_checks.py` to the single-definition rule and delete the temporary tolerance and its expiry note
- [X] T080 [US3] Demonstrate FR-020's closure the way the relaxation was made visible: `.venv/bin/python -m pytest tests/guards/ -k "can_fail"` passes, the expiry note is gone from `tests/guards/test_no_duplicate_checks.py`, and its planted-violation self-test still shows the guard can fail
- [X] T081 [US3] Add a single line to `specs/006-validation-vocabulary/contracts/schema-vocabulary.md` stating that its signatures are superseded by [contracts/parse-context.md](contracts/parse-context.md), and make no other edit — not even incidental reflow (FR-025)
- [X] T082 [US1] Gate commit 7: `.venv/bin/python -m pytest` green, and the **full** mutation sweep diffed empty against `<scratchpad>/before-full.txt`. Commit as structural — `refactor(schema): fold the check bodies into ParseContext and delete the free functions`

### Sequence audit

> The guard of FR-022 holds four counts. SC-006, SC-007, and FR-015 are the
> three claims no guard covers, so they are checked here by hand, once, against
> the finished tree. A claim with no check behind it is a claim a reviewer can
> only take on trust.

- [X] T083 [US2] Verify SC-006 against the finished tree: `ValidationProblem(` is constructed **0** times in `src/cetools/careers.py`, `chargen.py`, `names.py`, and `registries.py`, and **28** times in `src/cetools/rules.py` — 24 in `_validate` and one each in `_unreadable`, `_unlistable`, `_not_a_regular_file`, and `_compose`. Resolve the 28 by enclosing function with an `ast` walk rather than by eye, and confirm `_class_effect_problems` and `parse_task_parameters` construct none, because they now report through a carrier
- [X] T084 [US2] Verify SC-007 against the finished tree: **17** `ctx.failed` reads across **16** functions, matching [data-model.md](data-model.md)'s table site for site, with `parse_skills` asking twice and exactly three of the seventeen reading a fragment carrier (`registries._parse_bands`, `names._parse_surname_entry`, `chargen._parse_mishap_effect`). If conversion corrected the count in either direction, confirm data-model.md and SC-007 were corrected in the commit that found it, per the spec's own assumption
- [X] T085 [US1] Verify FR-015 against the finished tree and across the sequence: `src/cetools/rules.py` contains exactly one `problems.sort()`, it still sits in `_validate` immediately before the `ValidationReport(` construction, and `git log -p main..HEAD -- src/cetools/rules.py` shows no commit moved it, removed it, or added a second reporting path around it. The sort is what erases the insertion-order change a shared collection introduces, so a commit that touched it invalidates every empty mutation diff behind it
- [X] T086 [US3] Confirm `rg -n "def (require_|optional_bool|unrecognized)" src/cetools/schema.py` shows exactly eight definitions, all indented inside `ParseContext`
- [X] T087 [US3] Walk the sequence: for each of the seven commits, `git switch --detach <commit> && .venv/bin/python -m pytest` passes, and each diff changes structure only, never behavior (FR-018, FR-019). Confirm each commit message names its scope and says it is structural

**Checkpoint**: The superseded path is gone, all four counts are guarded, and
each guard can be shown to fail.

---

## Phase 6: User Story 4 - Wording problems are written down, not fixed (Priority: P3)

**Goal**: The next reviewer inherits a list rather than a memory, and nothing in
it has been acted on.

**Independent Test**: Every entry in `specs/007-parse-context-carrier/inventory.md`
names a concrete site and carries a stable identifier; `git diff main -- src/cetools/`
shows no entry has been acted on, where "acted on" means changing what a site
reports or which rule it applies (FR-021).

**Note**: entries I-7 onward are added *during* Phase 4, in the commit that
finds them. The tasks here finalize and verify.

- [X] T088 [US4] Append each disagreement noticed during Phase 4 to `specs/007-parse-context-carrier/inventory.md` as an `I-n` entry naming the concrete site and stating the question without answering it, in the same commit that reads the site
- [X] T089 [US4] Confirm every deliberately preserved anomaly cites its entry by identifier in a code comment: I-1 at `src/cetools/registries.py` (`_parse_pseudo_hex`), I-4 at `src/cetools/chargen.py:188`, `chargen.py:490`, and `src/cetools/registries.py:429`, and I-5 at `src/cetools/registries.py:474`
- [X] T090 [US4] Confirm [contracts/parse-context.md](contracts/parse-context.md) records every anomaly the migration deliberately preserved, so a later reader cannot mistake a wart for an oversight (FR-024). Add any I-7+ anomaly that the contract does not already cover
- [X] T091 [US4] Confirm nothing in `specs/007-parse-context-carrier/inventory.md` was acted on: no `found` or `expected` string changed, and no site applies a different rule. A keyword argument added only so two sites keep saying the different things they already say preserves the inconsistency and is required by FR-014, not forbidden by FR-021

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T092 [P] Run the documented lint commands over `src tests` — `black --check`, `isort --check-only`, `flake8` — and resolve every warning before the branch merges
- [X] T093 [P] Confirm no commit in the sequence touches `CHANGELOG.md`: `git log --oneline main..HEAD -- CHANGELOG.md` is empty. Nothing a library user or a data-file author can see has changed, so an entry would be noise (FR-018a)
- [X] T094 [P] Confirm `src/cetools/data/` is untouched: `git diff --stat main -- src/cetools/data/` is empty. No `.toml` file is added, edited, or moved, so no OGC or licensing question arises (Principle V)
- [X] T095 [P] Confirm the public surface is unchanged: `.venv/bin/python -m pytest tests/unit/test_library_api.py tests/contract` passes and `cetools/__init__.py`'s `__all__` does not mention `ParseContext` or `HEADER_KEYS` (Principle I, FR-028)
- [X] T096 Run the full [quickstart.md](quickstart.md) validation end to end — §1a, §1b, §1c, §US2's scratch-branch grep, §US3's per-commit walk, §US4's inventory check, and §*The guards can fail* — and record the result
- [X] T097 Delete the scratchpad: the mutation harness and its baselines are a verification step, not a committed corpus (research R10, FR-016b). Confirm nothing under `<scratchpad>/` was added to the repository

---

## Phase 8: Convergence

- [X] T098 [US4] Add `allow_empty: bool = False` to the `require_list` signature block and to the condition table in [contracts/parse-context.md](contracts/parse-context.md) §`require_list` per FR-024 (partial). The keyword is implemented at `src/cetools/schema.py:230` and used at `src/cetools/chargen.py:165`, `chargen.py:382`, and `src/cetools/registries.py:353`, but the contract's signature omits it and its table states unconditionally that `[]` reports `found="an empty array"`, so a reader working from the contract would conclude `require_list` always rejects empty. Record the empty-acceptance divergence it preserves by citing [inventory.md](inventory.md) entry I-4 alongside the existing pointer to the wording divergences, naming the three sites. Documentation only — no source file changes, and no reported wording, location, or order moves, so the standing FR-016b gate is `.venv/bin/python -m pytest` green alone

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies; must complete before commit 1, because FR-016b makes the comparison mandatory from commit 1 onward
- **Foundational (Phase 2)**: depends on Setup. **Blocks every parser conversion** — nothing can descend with a carrier that does not exist
- **US1 (Phase 3)**: depends on Foundational. Its gate then runs inside every later commit
- **US2 (Phase 4)**: depends on Foundational and on US1's gate being defined. The five module commits are **strictly sequential**, not parallel — see below
- **US3 (Phase 5)**: depends on all five module commits, because the free functions cannot be deleted while any parser still calls them
- **US4 (Phase 6)**: entries accrue during Phase 4; verification depends on Phase 4 completing
- **Polish (Phase 7)**: depends on everything

### Why the five module commits cannot run in parallel

`rules._SINGLETON_PARSERS` at `src/cetools/rules.py:223` maps ten entry points
by kind through one table, and a table cannot hold two signatures at once
(research R6). Each module's commit therefore updates its own dispatch, and two
modules converting at the same time would collide in `rules._validate`. This is
the one place where the usual "different files, no dependencies" rule does not
apply, and it is why no module commit carries a `[P]`.

### Within each module commit

Signatures → descent → array sites → bespoke problems → scopes → header keys →
dispatch → gate. The gate is last and is not optional.

### Parallel Opportunities

- None in Setup. T001 through T004 are a chain: the harness must exist before it can be proven deterministic, and both baselines restrict *its* outer loop, so neither can be captured before it runs
- T009 is independent of T006–T008 (different files); the rest of Phase 2's tests are sequential by the constitution's "one test at a time"
- T025 and T026 in Phase 3
- T074, T075, T076 in Phase 5 (three independent facts added to one new file — parallel in authoring, serialized in the edit)
- T092 through T095 in Phase 7

### Parallel Example: Phase 2 tests

```bash
# T009 touches a new file and can be written alongside the test_schema.py work:
Task: "Write tests/unit/test_parse_context.py covering nested descent and array indices"
Task: "Adapt tests/unit/test_schema.py to the method call shape"
```

---

## Implementation Strategy

### MVP (Commits 1–2)

1. Phase 1: the evidence apparatus and baseline
2. Phase 2: the carrier, delegating — commit 1
3. Phase 3: the standing gate, proven against commit 1
4. Commit 2: `names.py` converted
5. **STOP and VALIDATE**: the suite is green, the mutation diff is empty, and one parser reads the way US2 describes. If the pattern is wrong, it is wrong across four functions rather than a hundred sites

### Incremental Delivery

Each of commits 3–6 adds one parser, and each is a complete, green,
independently reviewable increment. Commit 7 is not optional: FR-020 makes the
feature incomplete without it, and the migration would otherwise end with every
check existing twice forever.

### Solo Strategy

The sequence is inherently serial and is meant to be. There is no parallel team
strategy here: the dispatch table serializes the module commits, and the value
of the ordering — smallest module first, so the pattern is established four
times before it reaches the module holding a third of the sites — depends on
them happening in order.

---

## Notes

- `[P]` = different files, no dependencies. Module commits never carry it
- Every task's gate is the same: the suite green **and** the mutation diff empty. A green suite alone is not evidence — it pins 7 of 77 distinct `expected` wordings exactly, and the golden corpus pins none (FR-016a)
- A report difference at any gate is a signal to stop and revert, never to adjust a fixture (FR-016)
- The `problems.sort()` at `src/cetools/rules.py:1058` is immovable (FR-015), and T085 checks across the whole sequence that no commit moved it
- The guard of FR-022 holds SC-002 through SC-005. SC-006, SC-007, and FR-015 have no guard, so T083, T084, and T085 check them by hand against the finished tree
- Verify each test fails before implementing it (Principle III)
- Commit at each named commit boundary, and say `structural` in the message
