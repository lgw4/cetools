# Tasks: NPC Generator

**Input**: Design documents from `/specs/003-npc-generator/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Test tasks are **mandatory** here, not optional. Constitution Principle III is
non-negotiable and SC-016 requires expected values committed in a change that *precedes* the
implementing change. Every `[TEST]` task is its own commit, observed failing, before the
implementation task that follows it.

**Organization**: Tasks are grouped by user story. The Foundational phase is unusually large
because this feature adds four modules, twenty-one data files, and three schema versions
before any story can run a single walk.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

Single project: `src/cetools/`, `tests/` at repository root.

## Standing rules for every task below

- **Tidy First**: structural and behavioral changes never share a commit; structural goes
  first; the commit message says which it is.
- **Commit discipline**: commit only with the whole suite green and no lint warnings.
  Conventional Commits with a scope, e.g. `feat(npc): …`, `refactor(render): …`.
- **CHANGELOG**: every user-visible change adds a `CHANGELOG.md` entry in the same commit.
  T009 additionally needs a **Breaking changes** heading.
- **Do not regenerate `tests/golden/check_*.txt` or the existing JSON fixtures.** They are
  SC-014's evidence.
- Run `uv run pytest -m "not slow"` after each step; run the whole suite before each commit.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Test-harness affordances the rest of the feature depends on.

- [X] T001 [P] Register the `slow` marker in `pyproject.toml` beside the two existing markers, and document `uv run pytest -m "not slow"` as the inner loop (research R14)
- [X] T002 [P] Add a `tests/golden/npc_*.txt` rule to `.gitattributes` pinning LF and marking the files binary-safe so no tool rewrites their tabs or line endings (research R7)
- [X] T003 Add a `read_golden_bytes` fixture to `tests/conftest.py` that reads a golden file with `Path.read_bytes()`, leaving the existing `read_golden` untouched (research R7)

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

### Phase 2A: Tidy First — structural changes, before any behavior

These rearrange code without changing output. Each is its own commit, says "structural" in
its message, and the suite is green before and after.

- [X] T004 [P] Hoist `DESIGNATION` and `_uncovered` into `tests/conftest.py` (keeping the two-adjacent-bytes-literals form) and import them from there in `tests/unit/test_licensing.py` and `tests/guards/test_packaging.py` (structural, research R9)
- [X] T005 [P] Add an `indent` parameter to `render._provenance_lines` in `src/cetools/render.py` and pass the existing indentation from both current call sites (structural)
- [X] T006 Add a keyword-only `full: bool = False` to `as_text` in `src/cetools/render.py`; every existing registration and the dispatch fallback accept it and raise `CetoolsError` when it is true, with a test for each in `tests/unit/test_render.py` (structural)
- [X] T007 Convert the per-kind blocks in `rules._validate` to a `kind -> parse function` mapping and one loop in `src/cetools/rules.py`, before the kind count goes from four to eleven (structural)
- [X] T008 [P] Rename `tables.advanced` to `tables.specialist` in `src/cetools/careers.py`, `src/cetools/data/careers/navy.toml`, and `tests/unit/test_careers.py` (structural; nothing reads it yet)
- [X] T009 Move `Band` and the characteristic modifier bands from `src/cetools/tasks.py` to `src/cetools/registries.py`: `TaskParameters` loses `characteristic_bands` and `characteristic_dm`, `CharacteristicRegistry` gains `bands` and `characteristic_dm`, `check` reads `rules.characteristics.characteristic_dm(...)`, `src/cetools/data/tasks.toml` drops `[characteristic-dms]` and rises to `schema-version = 2`, `src/cetools/data/registries/characteristics.toml` gains `[modifier-dms]` and rises to `schema-version = 2`, and `src/cetools/__init__.py` re-exports `Band` from its new home (structural, **breaking library change**, FR-039)
- [X] T010 Verify SC-014: assert in `tests/integration/test_golden.py` and `tests/contract/test_json_contract.py` that every committed `tests/golden/check_*.txt` and every existing JSON fixture is byte-identical after T009, with no fixture regenerated
- [X] T011 Confirm the module-level `_PARAMETERS = load_rules().task_parameters` in `tests/property/test_invariants.py` still reads only `difficulty_dms` after T009, and record the check rather than assuming it

**Checkpoint**: structural work complete, suite green, no output changed.

### Phase 2B: Seeds and the characteristics registry

- [X] T012 [P] [TEST] Write `tests/unit/test_seeds.py` cases for `derive_seed`: it folds a seed and parts through the existing blake2b digest, returns a value `resolve_seed` accepts, round-trips as a decimal string, and is stable across runs
- [X] T013 Implement `derive_seed(seed: int, *parts: int | str) -> int` in `src/cetools/seeds.py`, reusing the existing `rng_seed` fold rather than introducing a second digest (research R2), unexported
- [X] T014 [TEST] Extend `tests/unit/test_registries.py` for `CharacteristicRegistry`: `classes` mapping, `pseudo_hex_minimum`, `pseudo_hex`, `symbol(score)` raising `RulesDataError` naming the score and the range when outside it, and `floor()` returning `pseudo_hex_minimum`
- [X] T015 Implement `classes`, `pseudo_hex_minimum`, `pseudo_hex`, `symbol()`, and `floor()` on `CharacteristicRegistry` in `src/cetools/registries.py`, and parse `characteristics.<CODE>.label` / `.class` and `[pseudo-hex]` at schema version 2 (FR-039, research R12, R13)

### Phase 2C: The universal chargen tables (`chargen.py`)

- [X] T016 [TEST] Write `tests/unit/test_chargen.py` cases for `DraftTable`: `roll` rejects the `d66` literal, `careers` is non-empty, row order is preserved (FR-005)
- [X] T017 Implement `DraftTable` and its parse function in `src/cetools/chargen.py`
- [X] T018 [P] [TEST] Add `tests/unit/test_chargen.py` cases for `AgingTable`, `AgingRow`, and `ClassEffect`: `range` accepts `N`, `N-M`, `N+` including negatives, exactly one row unbounded above, the lowest row is a floor, `effects` may be empty, `modifier` accepts only `terms-served`
- [X] T019 Implement `AgingTable`, `AgingRow`, and `ClassEffect` with their parse functions in `src/cetools/chargen.py`
- [X] T020 [P] [TEST] Add `tests/unit/test_chargen.py` cases for `MishapTable`, `MishapRow`, `InjuryRow`, and `MishapEffect`: the closed `kind` set, `amount` accepting both `"-1d6"` and `"10000"` as text, and `injuries` reachable only from a `roll-injury` effect
- [X] T021 Implement `MishapTable`, `MishapRow`, `InjuryRow`, and `MishapEffect` with their parse functions in `src/cetools/chargen.py`
- [X] T022 [P] [TEST] Add `tests/unit/test_chargen.py` cases for `BackgroundSkills`: three non-empty notation lists in skill-table context, duplicates across `law-level` and `trade-code` preserved as meaningful weighting (research R5)
- [X] T023 Implement `BackgroundSkills` and its parse function in `src/cetools/chargen.py`
- [X] T024 [P] [TEST] Add `tests/unit/test_chargen.py` cases for `MedicalTiers` and `MedicalThreshold`: distinct tier names, thresholds sorted highest-target-first, `paid-percent` in 0–100, a total below every threshold paying nothing, `rank-dm` declared not assumed
- [X] T025 Implement `MedicalTiers` and `MedicalThreshold` with their parse function in `src/cetools/chargen.py`
- [X] T026 [TEST] Add `tests/unit/test_chargen.py` cases for `ChargenParameters`: every key in `contracts/data-files.md` is required, every table is a closed key set, and a misspelled key is reported rather than defaulted
- [X] T027 Implement `ChargenParameters` in `src/cetools/chargen.py`, exposing every scalar as a named attribute so a misspelling is an `AttributeError` at import rather than a `KeyError` mid-walk (FR-038)

### Phase 2D: The name table schemas and the name roll (`names.py`)

This phase is the code that reads a name table. The shipped tables themselves are Phase 2I,
behind the licensing work of Phase 2H.

- [X] T028 [TEST] Write `tests/unit/test_names.py` schema cases: `GivenNameTable` and `SurnameTable` key sets are closed so a `gender` key is rejected (FR-043b), `source` is required and non-empty (FR-043e), an empty `names` array is rejected naming the file (FR-043h), `SurnameEntry.people` is optional (FR-043d)
- [X] T029 Implement `GivenNameTable`, `SurnameTable`, `SurnameEntry`, and their parse functions in `src/cetools/names.py`
- [X] T030 [TEST] Add `tests/unit/test_names.py` cases for `roll_name`: a region is selected uniformly over the tables in force, then a surname within it, then a given name independently; `Name.full` is `f"{given} {surname}"` and is never reordered (FR-043f, FR-043g, FR-047a)
- [X] T031 Implement `Name` and `roll_name(roller, given, surnames)` in `src/cetools/names.py`, unexported (contracts/library-api.md)

### Phase 2E: Career schema v2

- [X] T032 [TEST] Extend `tests/unit/test_careers.py` for schema version 2: `medical-tier` required, `always-available` and `re-enterable` defaulting to `false`, `throws.promotion` optional, `tables.advanced-education` required with its own `requires` gate, and `ladders[].role` required as `"entry"` or `"commissioned"` with exactly one `entry` and at most one `commissioned`
- [X] T033 Implement the v2 changes on `CareerDefinition` and its parse function in `src/cetools/careers.py`, raising the declared schema version (FR-034, FR-035, FR-036, FR-007b)

### Phase 2F: Loader integration (`rules.py`)

- [X] T034 [TEST] Extend `tests/unit/test_rules.py` for the eleven singleton kinds and the second repeatable kind: `_SINGLETON_KINDS` grows to eleven, `surnames` is keyed by file stem, `RulesData` gains its eight fields, and `sorted(_CANONICAL_FILE) == sorted(_SINGLETON_KINDS)` still holds
- [X] T035 Register the seven new singleton kinds and the `surnames` repeatable kind in `src/cetools/rules.py`, add the eight `RulesData` fields, and route each through the T007 dispatch table
- [X] T036 [TEST] Add `tests/integration/test_validation_categories.py` cases for the six new cross-file rules: an unresolvable draft-table career (FR-005), a career naming a medical tier that does not exist (FR-034), two surname tables declaring one region naming both files, no surname table in force (FR-043j), a characteristic class no registry declares (FR-040a), and a career whose ladders violate the `entry`/`commissioned` rule (FR-007b) — each failing the whole data set before any character is produced
- [X] T037 Implement the six cross-file rules in `src/cetools/rules.py` alongside the two the previous feature has
- [X] T038 [TEST] Add `tests/unit/test_rules_agreement.py` cases asserting every skill any new shipped table can grant resolves against the skills registry (FR-040) and every characteristic class resolves (FR-040a)

### Phase 2G: The shipped Open Game Content data files

Basenames must stay unique tree-wide; `tests/guards/test_data_layout.py` enforces it
(FR-041). Every file carries exactly one designation line.

Every file in this phase is Open Game Content, so the existing licensing guards pass
unchanged throughout it. The eight name tables are **not** in this phase: they are the first
shipped data the Open Game Content designation does not reach, and they cannot land until
the guards can tell the two designations apart. That is Phase 2H, and it comes first.

- [X] T039 [P] Author `src/cetools/data/chargen/draft.toml` (OGC designation, `1d6`, six careers in row order — Aerospace Defense, Marine, Maritime Defense, **Navy**, Scout, Surface Defense, which is rows 1 through 6 — career-table spellings not the source's parenthetical aliases; row order is significant because the die that reads it is positional, FR-005, research R6)
- [X] T040 [P] Author `src/cetools/data/chargen/aging.toml` (OGC designation, `2d6`, `modifier = "terms-served"`, eight banded rows from `-6` to `1+`)
- [X] T041 [P] Author `src/cetools/data/chargen/mishaps.toml` (OGC designation, `1d6`, six mishap rows with structured effects, plus the injury table and `injury-roll`; rows 4 and 5 carry `forfeit-career-benefits` and the extra years — research R10 items 5 and 6)
- [X] T042 [P] Author `src/cetools/data/chargen/background-skills.toml` (OGC designation; 4 law-level, 14 trade-code, 15 education entries; not named `skills.toml` because the registry holds that basename)
- [X] T043 [P] Author `src/cetools/data/chargen/medical-tiers.toml` (OGC designation, `2d6`, `rank-dm = true`, tiers `service`, `professional`, `fringe` with a comment recording that two of the three names are this project's labels — research R5)
- [X] T044 [P] Author `src/cetools/data/chargen/chargen-parameters.toml` (OGC designation; every key enumerated in `contracts/data-files.md`, including `mustering-out.cash-choice-roll` and `.cash-choice-target`, which are the throw FR-016 requires for the cash-against-material decision; not named `parameters.toml`)
- [X] T045 Rewrite `src/cetools/data/registries/characteristics.toml` to the v2 table-per-characteristic shape with `label` and `class`, keeping `[modifier-dms]` from T009 and adding `[pseudo-hex]` with `minimum = 0` and thirty-four symbols skipping I and O (research R13)
- [X] T046 Grow `src/cetools/data/registries/skills.toml` to cover the fifteen education skills, the homeworld skills, the skills the seven new careers use, and the cascade specialties, at schema version 1 unchanged (FR-040)
- [X] T047 Grow `src/cetools/data/registries/benefits.toml` to cover every material benefit the eight careers' tables name, at schema version 1 unchanged
- [X] T048 Bring `src/cetools/data/careers/navy.toml` to career schema v2: `medical-tier = "service"`, `ladders[].role`, `tables.advanced-education` required. Navy is **Draft row 4**, the one row T049–T053 do not cover, so its `name` must match `draft.toml`'s fourth entry exactly (FR-005)
- [X] T049 [P] Author `src/cetools/data/careers/aerospace-defense.toml` (career v2, service tier, both throws, Draft row 1)
- [X] T050 [P] Author `src/cetools/data/careers/marine.toml` (career v2, service tier, both throws, Draft row 2)
- [X] T051 [P] Author `src/cetools/data/careers/maritime-defense.toml` (career v2, service tier, both throws, Draft row 3)
- [X] T052 [P] Author `src/cetools/data/careers/scout.toml` (career v2, service tier, **neither** commission nor promotion, Draft row 5, a rank-zero bonus on a ladder naming no title)
- [X] T053 [P] Author `src/cetools/data/careers/surface-defense.toml` (career v2, service tier, both throws, Draft row 6)
- [X] T054 [P] Author `src/cetools/data/careers/drifter.toml` (career v2, fringe tier, neither throw, `always-available = true`, `re-enterable = true`, a rank zero granting no bonus)
- [X] T055 [P] Author `src/cetools/data/careers/merchant.toml` (career v2, professional tier, both throws, a civilian rank ladder, the lowest re-enlistment target — research R6)

**Checkpoint**: eighteen Open Game Content files in place, every one passing the existing
licensing guards unchanged.

### Phase 2H: Licensing — two designations that the checks can tell apart

**⚠️ This phase must complete before the first name table lands in Phase 2I.**
`_assert_shipped_rules_data` in `tests/guards/test_packaging.py` today asserts
`"Open Game Content" in text` of every `.toml` in the wheel and the sdist. The first
GPL-designated file turns that assertion red and keeps it red until T059 widens it, and the
project's commit discipline does not permit a commit with the suite failing. Authoring the
name tables first would put eight-plus commits on the wrong side of that rule. Every task
here passes with the data set as Phase 2G leaves it — an exactly-one-of-two check over files
that all carry the first designation is satisfied by them, and the GPL mirror is satisfied
vacuously — so this phase is green before, during, and after.

- [X] T056 [TEST] Add `tests/unit/test_licensing.py` cases for the GPL-3.0 designation constant: a shipped data file carries exactly one designation, both is a failure, neither is a failure, asserted against planted files so the cases stand before any name table exists (FR-042, SC-015)
- [X] T057 Narrow the Section 15 game-data notice in `LICENSE-OGL.txt` from the data root to the OGC subtrees (`registries/`, `chargen/`, `careers/`, and `tasks.toml`), keeping the `_NOTICE_PATH` parenthesized-path and `_NOTICE_SUFFIX` "every `.toml` file" shapes parseable, and update `SECTION_15_NOTICES[-1]` in `tests/conftest.py` in the same commit. The narrowed wording names no path under `names/`, so it is already correct when that directory arrives (research R9)
- [X] T058 Add the second designation constant to `tests/conftest.py`, assembled from two adjacent bytes literals so the test source does not designate itself
- [X] T059 Turn `_assert_shipped_rules_data` in `tests/guards/test_packaging.py` into an exactly-one-of-two check over every `.toml` in the wheel and the sdist (FR-042a). **This is the task the name tables wait on.**
- [X] T060 Extend `_uncovered` in `tests/conftest.py` with its mirror: every GPL-designated file must be claimed by neither the notice's paths nor its suffix, so a name table drifting into an OGC directory fails
- [X] T061 Add the SC-015a fail-ability siblings to `tests/unit/test_licensing.py`, extending `test_the_coverage_check_sees_a_designated_file_the_old_scan_missed`: an OGC file planted outside the covered subtrees must fail the coverage check, and a GPL-designated file planted inside them must fail the mirror, each unlinked in a `finally`
- [X] T062 [P] Update the licensing section of `README.md` and the "Licensing, which is not optional" section of `CONTRIBUTING.md`, both of which state that every `.toml` under `src/cetools/data/` is OGC and both of which become false the moment the first name table lands — so they change **before** it does, not after

**Checkpoint**: the guards distinguish the two designations, the notice covers the OGC
subtrees and nothing else, and the suite is green with the data set still wholly OGC.

### Phase 2I: The shipped name tables — the first data that is not Open Game Content

Depends on Phase 2H. These are the files the widened checks were widened for.

- [X] T063 [P] Author `src/cetools/data/names/given-names.toml` (GPL-3.0 designation, `source` recorded, at least sixty gender-neutral entries — FR-043b, FR-043e, FR-043i)
- [X] T064 [P] Author `src/cetools/data/names/surnames-africa.toml` (GPL-3.0 designation, `region`, `source`, at least forty entries)
- [X] T065 [P] Author `src/cetools/data/names/surnames-asia.toml` (same shape)
- [X] T066 [P] Author `src/cetools/data/names/surnames-central-america.toml` (same shape)
- [X] T067 [P] Author `src/cetools/data/names/surnames-europe.toml` (same shape)
- [X] T068 [P] Author `src/cetools/data/names/surnames-north-america.toml` (same shape)
- [X] T069 [P] Author `src/cetools/data/names/surnames-south-america.toml` (same shape)
- [X] T070 [P] Author `src/cetools/data/names/surnames-indigenous.toml` (GPL-3.0 designation; every entry carries `people` — FR-043d)
- [X] T071 Verify the shipped surname tables differ in size by enough that a weighting taken over names rather than over regions would put at least one region outside SC-019's band, and record the sizes in `tests/unit/test_names.py`
- [X] T072 [P] Add `tests/unit/test_name_tables.py` for SC-015b: every name table records a `source`, every indigenous-peoples entry names its people, no name table carries a gender field, the given names table holds ≥60 entries and each surname table ≥40
- [X] T073 Extend `tests/integration/test_validate_cli.py` and `tests/guards/test_data_layout.py` for twenty-six files, unique basenames tree-wide, and the two new subdirectories traversing without `__init__.py`

### Phase 2J: The produced value (`character.py`)

- [X] T074 [TEST] Write `tests/unit/test_character.py` for the seven types: field names and order per `contracts/library-api.md`, frozen and slotted, `HistoryStep.kind` and `StepEffect.kind` closed sets, `StepThrow.total == sum(faces) + modifiers`, a table-reading throw carrying `target = 0` and `success = True`. The closed `StepEffect.kind` set is where FR-028 is enforced: the eleven kinds are exactly the consequences the chain carries, and a twelfth would be the chain running past the numbers on the sheet, so the closed-set assertion is what makes FR-028 fail rather than merely be intended
- [X] T075 Implement `Character`, `CharacterSkill`, `CareerService`, `HistoryStep`, `StepThrow`, `StepEffect`, and `CharacterBatch` in `src/cetools/character.py`

### Phase 2K: Public surface and guards

- [X] T076 Extend the contract parser in `tests/unit/test_library_api.py` to read `specs/003-npc-generator/contracts/library-api.md` as a third contract, taking `## Public surface added` and `## Public surface removed` from it — **before** any export lands, or the suite fails with a set difference that does not say why
- [X] T077 Add the new exports to `src/cetools/__init__.py` per `contracts/library-api.md`, keeping `Band` re-exported from `registries`
- [X] T078 [P] Add a no-`locale` guard to `tests/guards/` asserting that nothing under `src/` imports `locale`, which is what makes SC-012 unfalsifiable by omission (research R8)
- [X] T079 [P] Add `generate_character` and `generate_batch` to the manual library list in `tests/guards/test_seed_contract.py`, so a stray `random` call in the walk is guarded

**Checkpoint**: the data set validates at twenty-six files, every schema parses, every
cross-file rule fires, both designations are enforced, and the produced value exists. User
story work can begin.

---

## Phase 3: User Story 1 - Get a usable NPC from a seed (Priority: P1) 🎯 MVP

**Goal**: One command, one seed, one finished character sheet in the source material's own
format, alive and internally consistent, with the seed and provenance on standard error.

**Independent Test**: `cetools npc --seed session-alpha` produces a sheet byte-identical to a
committed reference; the same seed twice produces the same bytes; a thousand seeds each
produce a living, consistent character.

### Tests for User Story 1 ⚠️ written and observed failing first

- [X] T080 [P] [US1] [TEST] Write `tests/unit/test_generator.py` cases for the opening of the walk: characteristics rolled one per registry entry (FR-002), background skill count `base + EDU DM` floored at one with one background skill meaning one homeworld skill (FR-003), and the homeworld draw uniform over the concatenated law-level and trade-code lists
- [X] T081 [P] [US1] [TEST] Add `tests/unit/test_generator.py` cases for career entry: random selection over careers in force, qualification failure routing to the draft up to `draft-entries-allowed` and to the always-available career beyond it (FR-004), the draft resolving positionally over the Draft table (FR-005), Drifter thrown for when selected and automatic as fallback (FR-006), basic training granting the whole service table on a first career and `subsequent-career-count` entries later (FR-007a), and the rank-zero bonus granted on entry (FR-007)
- [X] T082 [P] [US1] [TEST] Add `tests/unit/test_generator.py` cases for the term loop in FR-008's order: survival with `natural-failure` always failing (FR-008a), commission attempted once per career and barred in a drafted character's first term (FR-012, FR-012a), a commission moving the character to the commissioned ladder at its lowest rank with that rank's bonus granted (FR-007b), advancement, skill acquisition, and aging
- [X] T083 [P] [US1] [TEST] Add `tests/unit/test_generator.py` cases for skill rolls: one per term, two in a career declaring neither throw, plus `on-commission` and `on-advancement` extras (FR-009); selection over the **eligible** tables only, a characteristic gate excluding rather than failing (FR-010); and the cascade rule choosing a permitted specialty and recording it (FR-011)
- [X] T084 [P] [US1] [TEST] Add `tests/unit/test_generator.py` cases for the always-living guarantee: a failed survival throw resolving on the Survival Mishaps table without death (FR-019, FR-022); a mishap-ended term costing two years, counting toward the cap and the aging modifier, and forfeiting that term's benefit roll, all three (FR-020); a mishap deferring to the injury table recorded as a step of its own (FR-024); and no path that discards and re-rolls (FR-023)
- [X] T085 [P] [US1] [TEST] Add `tests/unit/test_generator.py` cases for characteristic floors: a reduction clamping at `CharacteristicRegistry.floor()`, the history recording both the reduction called for and the amount applied when they differ, and a score above the declared range raising `RulesDataError` naming the score and the range (research R13)
- [X] T086 [P] [US1] [TEST] Add `tests/unit/test_generator.py` cases for career end and multi-career: continuation decided by throw, re-enlistment still applying, the cap forcing mustering out regardless (FR-014); an accumulating qualification penalty counting careers **entered**; a career already entered unavailable again except Drifter (FR-015)
- [X] T087 [P] [US1] [TEST] Add `tests/unit/test_generator.py` cases for mustering out: benefit count from terms and rank with the rank bonus **not** cumulative, each roll taken as cash or as material by the `cash-choice` throw read from data rather than by arithmetic the engine holds, the cash-roll cap after which the throw is not made at all, the material rank modifier (FR-016), the retired cash modifier applying exactly when the pension was qualified for (FR-017), and a pension earned in a **single** career with three terms in each of two careers paying nothing (FR-018)
- [X] T088 [P] [US1] [TEST] Add `tests/unit/test_generator.py` cases for debts: an aging crisis becoming a debt of throw times multiplier, settling it restoring every covered characteristic to `crisis-restores-to` and leaving them floored when unsettled (FR-021); medical bills from the career's tier with the character owing the remainder (FR-025); debts settling in the order they arose with a partly covered bill restoring points in an order the walk decides and records, funds never negative (FR-025a, FR-026)
- [X] T089 [P] [US1] [TEST] Write `tests/unit/test_render_character.py` cases for the Universal Character Format per `contracts/cli.md`: four lines, exactly one tab between fields, the title-space-name rule with no leading separator when untitled, the pseudo-hex profile in registry order, `Age N`, `Name (N terms)` comma separated with singular at one, `Cr` with thousands separators, `Name-Level` skills including level zero sorted by `(casefold, codepoint)`, a cascade specialization written `Gun Combat (Slug Rifle)-1`, benefit items with repeats collapsed to `Name (x2)` and the line omitted when there are none, and the species-traits line never emitted (FR-044, FR-044a, FR-045, FR-046)
- [X] T090 [P] [US1] [TEST] Add `tests/unit/test_render_character.py` cases for FR-047c: a character titled by an earlier career and untitled by a later one keeps the earlier title, and no two ladders are ever compared. Add the FR-048 case beside it: the only title any rendering may write is a rank title from a ladder, so a career granting a noble title renders none of it, on the name line or anywhere else. The assertion is worth committing even though no shipped career can produce one, because FR-048 is a rule about the renderer rather than about the shipped data, and an override could supply what the shipped data cannot
- [X] T091 [US1] [TEST] Commit the six golden reference files SC-009 requires under `tests/golden/`, compared as bytes: `npc_titled.txt`, `npc_untitled.txt`, `npc_no_benefits.txt`, `npc_multi_career.txt`, `npc_titled_then_untitled.txt`, `npc_cascade.txt`. Each is rendered from a **hand-constructed `Character` literal** committed beside it in `tests/unit/test_render_character.py`, not from a seed: which character a seed produces is unknowable until the walk exists, and a golden captured from a finished implementation is not an expected value written before it (SC-016). Six constructed characters, six hand-authored byte strings, the renderer in between — that is what makes these references test-first and what makes SC-009's "byte-faithful" claim mean something
- [X] T092 [P] [US1] [TEST] Write `tests/integration/test_npc_cli.py` cases for FR-051 and FR-054: standard output carries exactly the sheet, the seed and version and provenance go to standard error, a failed run writes nothing at all to standard output, and exit codes are 0, 1, and 2 as `contracts/cli.md` states
- [X] T093 [P] [US1] [TEST] Write `tests/integration/test_npc_naming.py` for FR-047b and SC-018: the same seed generated with and without a supplied name compared field by field, differing in `name`, `given_name`, `surname`, `surname_region` and in nothing else — written before the walk exists, because the natural implementation fails exactly this and passes everything else (research R3)

- [X] T093a [P] [US1] [TEST] Write `tests/integration/test_npc_determinism.py` for **SC-001**, which is Constitution Principle IV made concrete and the criterion the rest of this feature rests on: over several fixed seeds, generate each seed repeatedly and assert zero differences — every field of the `Character` compared one by one, and **both** rendered text forms compared as bytes rather than as text. Assert it across process boundaries as well, by running the command twice per seed and comparing stdout bytes, so that anything seeded per-process is caught rather than hidden by one process's stable hash. No other task performs this check: T110's property invariants assert bounds rather than equality, T123 compares batch positions against one another rather than a seed against itself, and T093 compares two runs that are meant to differ
- [X] T093b [P] [US1] [TEST] Add a `tests/unit/test_generator_batch.py` case for **FR-053b reached from the library**: `generate_batch(None, rules)` produces a character and records the seed it drew, and that seed quoted back reproduces it. `resolve_seed(None)` already draws 64 bits from `secrets` and `generate_batch` already accepts `int | str | None`, so the capability belongs to the library; FR-055 and SC-017 require it reachable without the command line, and a second draw implemented in `cli.py` would be the CLI-only rule FR-053a was rewritten to avoid

### Implementation for User Story 1

- [X] T094 [US1] Implement the walk's opening in `src/cetools/generator.py`: `generate_character(roller, rules, *, name=None)`, characteristics, background skills, and the name drawn from `Roller(derive_seed(roller.seed, "name"))` which the walk's own roller never touches (research R1, R3)
- [X] T095 [US1] Implement career selection, qualification, draft routing, the always-available fallback, basic training, and the rank-zero bonus in `src/cetools/generator.py`
- [X] T096 [US1] Implement the term loop in `src/cetools/generator.py`: survival, commission, advancement, skill acquisition, aging, in FR-008's order, reading as a generator of history steps
- [X] T097 [US1] Implement skill acquisition in `src/cetools/generator.py`: eligible-table selection, the cascade choice, and the roll counts including the commission and advancement extras
- [X] T098 [US1] Implement mishaps, injuries, characteristic-class effects, and the floor clamp in `src/cetools/generator.py`
- [X] T099 [US1] Implement continuation, re-enlistment, the term cap, the accumulating qualification penalty, and multi-career selection in `src/cetools/generator.py`
- [X] T100 [US1] Implement mustering out, benefit rolls, the pension, medical bills, and ordered debt settlement in `src/cetools/generator.py`, with the cash-against-material choice made by the `mustering-out.cash-choice` throw from `chargen-parameters.toml` — never by a coin flip the engine holds, which FR-038 forbids however evenly it falls
- [X] T101 [US1] Record a `HistoryStep` for every decision and throw in the walk, with `StepThrow` itemizing modifiers and `StepEffect` naming what moved, so every number on the sheet traces to a step (FR-030, FR-030a) — in `src/cetools/generator.py`
- [X] T102 [US1] Implement `generate_batch(seed, rules, *, count=1, name=None)` in `src/cetools/generator.py` with `character_seed(master, i)` returning `master` at position 0, and raise `CetoolsError` for `count < 1` and for a name with `count > 1` (research R2, FR-053a)
- [X] T103 [US1] Register `as_text` for `Character` in `src/cetools/render.py` producing the Universal Character Format, with the `(casefold, codepoint)` sort key and no `locale` import anywhere
- [X] T104 [US1] Register `as_text` for `CharacterBatch` in `src/cetools/render.py`, sheets separated by exactly one blank line and nothing else, a batch of one rendering byte-identically to its single character (FR-048a)
- [X] T105 [US1] Add the `npc` command to `src/cetools/cli.py` with `--seed`, `--name`, and `--rules-data`, passing `--seed` straight through to `generate_batch` — including `None` when it is omitted, which `resolve_seed` already resolves by drawing 64 bits from `secrets`, so the CLI adds no draw of its own (FR-053b, T093b) — calling `generate_batch(..., count=1)`, writing the sheet to stdout and the seed/version/provenance to stderr via `_provenance_lines(indent=0)`, rejecting an empty or whitespace-only `--name` as a usage error (FR-053c)
- [X] T106 [US1] Wire the golden comparisons in `tests/integration/test_golden.py` through `read_golden_bytes` for the six T091 references, comparing them against `as_text(character).encode("utf-8")` for the six constructed characters. Then add the one assertion that ties the command to them: for a generated seed, `stdout.encode("utf-8")` equals `as_text(character).encode("utf-8") + b"\n"` for the character that seed produces. That is a derivation the CLI owes the renderer, checkable without a committed expectation, and it is what keeps the byte goldens meaningful at the command line without pretending a captured sheet was authored in advance
- [X] T107 [P] [US1] Add the SC-003/SC-004 sampled audit in `tests/integration/test_npc_sample.py`, marked `slow`: one thousand seeds, none excluded, every one alive and complete, with the consistency audit reading the character's own fields — age against terms and how each ended, every rank on a ladder of a career joined, benefit rolls against terms and rank, a pension against a single career's terms, funds non-negative, no consequence no step produced
- [X] T108 [P] [US1] Add the SC-006/SC-007/SC-008 coverage assertions to `tests/integration/test_npc_sample.py`: at least five distinct term counts with no more than a quarter at `terms.cap` **read from the loaded chargen parameters, never written as seven in the test**, two-career and three-career characters both present, every Draft row reached, both Drifter routes taken, both commission shapes and every medical tier the data declares exercised. The tiers and the cap are both counted from the data for the same reason SC-008 gives: FR-038 puts them in files a referee may edit, and a check that hard-codes either contradicts the requirement it is checking
- [X] T108a [P] [US1] Add the SC-020 assertions to `tests/integration/test_npc_sample.py`: over the same sample, every field the default rendering is required to carry is non-empty on every character, and no rendered default sheet contains a seed, a package version, a provenance line, a history step, a step kind, a throw, or a debt or pension figure. The first says the format's own lines are filled; the second says nothing from the walk leaks onto them
- [X] T109 [P] [US1] Add the SC-019 weighting check to `tests/integration/test_npc_sample.py`, marked `slow`: ten thousand rolled names, each region's share within 0.9/7 and 1.1/7, counted from the `surname_region` field and never from a split rendered name
- [X] T110 [P] [US1] Add walk invariants to `tests/property/test_invariants.py` over Hypothesis-drawn seeds: always alive, always named, at least one career, `funds >= 0`, `debt >= 0`, every characteristic within the declared pseudo-hex range, non-empty history
- [X] T111 [P] [US1] Add the SC-012 cross-locale comparison to `tests/integration/test_npc_cli.py`: a subprocess with `LC_ALL` set to a locale whose collation differs, calling `locale.setlocale(locale.LC_ALL, "")` before generating, comparing bytes, skipping with a reason when the locale is absent (research R8)

**Checkpoint**: a referee can generate one usable NPC from a seed. The MVP is deliverable.

---

## Phase 4: User Story 2 - Tell a wrong engine from interesting dice (Priority: P2)

**Goal**: The fuller text rendering and the machine-readable document expose the walk that
produced a character, so a surprising sheet is diagnosed from output rather than a debugger.

**Independent Test**: Request `--full` and `--json` for a character and confirm every
characteristic, skill, credit, career, and item on the sheet traces to a recorded step whose
parts are separately addressable.

### Tests for User Story 2 ⚠️ written and observed failing first

- [X] T112 [P] [US2] [TEST] Write `tests/unit/test_render_character.py` cases for the fuller sheet: the Universal Character Format, a blank line, then `Debt:` reading `none` rather than `Cr0`, `Pension:` likewise, and `History:` with each line **composed from the step's named parts** and columns padded to the longest value present (FR-049, `contracts/cli.md`)
- [X] T113 [P] [US2] [TEST] Add a `tests/unit/test_render_character.py` case asserting no field of a `HistoryStep` holds a line composed from the step's other parts, which is what makes FR-030a checkable from the record's shape
- [X] T114 [US2] [TEST] Commit `tests/golden/npc_full.txt` for a character carrying debt, pension, and history, compared as bytes and rendered from a hand-constructed `Character` literal for the same reason T091's six are
- [X] T115 [P] [US2] [TEST] Write `tests/contract/test_npc_json.py` against `contracts/json-output.md`: top-level key order `kind`, `seed`, `provenance`, `characters`; the character key order; the skill, career-service, history-step, throw, and effect key orders; every key present unconditionally; both seeds emitted as strings; `specialty` as `null` never `""`; `json.dumps(indent=2, ensure_ascii=False)` with a trailing newline and non-ASCII names emitted as themselves
- [X] T116 [P] [US2] [TEST] Add a `tests/contract/test_npc_json.py` case asserting `as_dict(batch)["characters"][i] == as_dict(batch.characters[i])` and that `total == sum(faces) + modifier values` in every throw
- [X] T117 [P] [US2] [TEST] Add SC-005's traceability audit to `tests/integration/test_npc_sample.py`, marked `slow`: over the same thousand-seed sample, every characteristic, skill, career, credit, and item traces to a step, read from the steps' named parts and never from rendered text
- [X] T118 [P] [US2] [TEST] Add `tests/integration/test_npc_cli.py` cases for `--json`: standard error is silent on success, `--full` with `--json` is accepted and changes nothing, and `--json` never changes an exit code (FR-053d)

### Implementation for User Story 2

- [X] T119 [US2] Implement `as_text(character, full=True)` in `src/cetools/render.py`: the format, a blank line, debt, pension, and the history composed from each step's parts, dispatching on step and effect kinds with pattern matching
- [X] T120 [US2] Implement `as_text(batch, full=True)` in `src/cetools/render.py`, fuller sheets separated by exactly one blank line
- [X] T121 [US2] Register `as_dict` for `Character` and `CharacterBatch` in `src/cetools/render.py` in the committed key order, with `as_json` following from it
- [X] T122 [US2] Add `--full` and `--json` to the `npc` command in `src/cetools/cli.py`, with `--full`'s help string saying it changes nothing under `--json`, and machine-readable mode putting the seed, version, and provenance in-document rather than on standard error

**Checkpoint**: Stories 1 and 2 both work. A surprising sheet is diagnosable from output.

---

## Phase 5: User Story 3 - Populate a table, a crew, or a ward in one go (Priority: P3)

**Goal**: One seed yields many characters, reproducibly, and quoting that seed reproduces the
whole table.

**Independent Test**: Request a batch, request it again and compare; confirm a batch of twelve
begins with the batch of three, and that a batch of one is byte-identical to the single
character of that seed.

### Tests for User Story 3 ⚠️ written and observed failing first

- [X] T123 [P] [US3] [TEST] Write `tests/unit/test_generator_batch.py` for FR-057: the first characters of a larger batch equal a smaller batch from the same seed, compared field by field across several seeds and count pairs, and position 0 equals the single character of that seed (research R2)
- [X] T124 [P] [US3] [TEST] Add a `tests/unit/test_generator_batch.py` case for FR-050a: each character's recorded derived seed, fed back as a master, regenerates that character alone
- [X] T125 [P] [US3] [TEST] Add `tests/integration/test_npc_cli.py` usage-error cases: `--count 0` and a negative count naming `--count`, and `--name` with `--count 12` naming both, each exiting 2 with nothing on standard output (FR-053a)
- [X] T126 [US3] [TEST] Commit `tests/golden/npc_batch.txt` for SC-011: a `CharacterBatch` of hand-constructed characters whose rendered bytes are exactly its sheets with one blank line between consecutive ones and no other text, plus the CLI assertion that a redirected `--count N` run's stdout equals `as_text(batch).encode("utf-8") + b"\n"` for the batch that seed produces
- [X] T127 [P] [US3] [TEST] Add the whole-set help assertion for `npc` to `tests/integration/test_cli.py`: `options_in_help(["npc"]) == {"--seed", "--count", "--name", "--rules-data", "--full", "--json", "--help"}`. **Depends on T122 as well as on T128**: `--full` and `--json` are added in US2, so this one task in US3 is not independent of it. It asserts the command's finished surface rather than this story's contribution to it, and a whole-set assertion has no smaller honest form — narrowing it to the options US3 adds would defeat the purpose the existing per-command assertions serve, which is that an option added later breaks the test deliberately. Where US2 is skipped, this task moves to Polish with the rest of the finished-surface work

### Implementation for User Story 3

- [X] T128 [US3] Add `--count` to the `npc` command in `src/cetools/cli.py`, passing it to `generate_batch` and turning the library's two `CetoolsError` refusals into usage errors naming the options at fault
- [X] T129 [US3] Add help strings for `npc` and every option in `src/cetools/cli.py`, with no help string naming the trademark as something this tool works with

**Checkpoint**: all three referee-facing stories work independently.

---

## Phase 6: User Story 4 - Change the rules without changing the code (Priority: P4)

**Goal**: A referee points the tool at their own data files and generates characters under
their rules, with the provenance saying so and no code edited.

**Independent Test**: Generate a seed from packaged data, generate it again with an override
changing one value, and confirm the character changes accordingly and the provenance reports
the override.

### Tests for User Story 4 ⚠️ written and observed failing first

- [X] T130 [P] [US4] [TEST] Add SC-013's five demonstrations to `tests/integration/test_data_driven.py`: a Draft table row, an aging table entry, a Survival Mishaps entry, a career's medical tier, and the term cap, each changed in an override and each changing the generator's behavior accordingly with no code edit
- [X] T131 [P] [US4] [TEST] Add `tests/integration/test_overrides.py` cases for the npc command: an override supplying a career that did not ship can be entered and is reported as `added`, a replaced file is reported as `replaced`, and the provenance block appears on standard error in text mode and in-document under `--json` (FR-058)
- [X] T132 [P] [US4] [TEST] Add `tests/integration/test_overrides.py` cases for name-table overrides: replacing a shipped region leaves the weighting unchanged, adding an eighth region gives it the same weight as each of the others, and neither the sixty/forty floors nor either designation is imposed on an override (FR-043f, FR-043i, FR-042)
- [X] T133 [P] [US4] [TEST] Add `tests/integration/test_npc_cli.py` cases for inconsistent override data: the run fails before any character exists, exits 1, writes nothing to standard output, and names what could not be resolved

### Implementation for User Story 4

- [X] T134 [US4] Make whatever the tests above show missing in `src/cetools/cli.py` and `src/cetools/generator.py` — the override path is the previous feature's mechanism reaching new data, so this task is expected to be small, and anything it turns out to need is a defect in the loader integration of Phase 2F rather than new capability

**Checkpoint**: every user story is independently functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T135 [P] Add the `npc` command, both text renderings, and the batch document to `README.md`, including the licensing sentence that now distinguishes the two designations
- [X] T136 [P] Write the `CHANGELOG.md` entry set for this feature, with a **Breaking changes** heading covering the `TaskParameters` move (T009) and a note that any change reordering, adding, or removing a draw changes every character a seed produces (FR-056b)
- [X] T137 [P] Verify SC-017 by listing each capability in this feature against a test that exercises it without invoking the command line, recorded in `tests/unit/test_library_api.py`
- [X] T138 Run every scenario in `specs/003-npc-generator/quickstart.md` by hand and correct any drift between it and the shipped behavior
- [X] T139 Confirm SC-016 from the git history: for each behavior in the functional requirements, the commit carrying the expected values precedes the commit carrying the implementation — **not fully satisfied**; six commits bundle or invert the ordering, recorded as a Recorded Deviation in `plan.md` rather than fixed by rewriting history
- [X] T140 Run the complete suite including `-m slow`, confirm zero skips that a criterion depends on, and confirm no `tests/golden/check_*.txt` or existing JSON fixture was modified anywhere in the branch

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies
- **Foundational (Phase 2)**: depends on Setup; **blocks every user story**
  - 2A structural must complete before any of 2B–2K, per Tidy First
  - 2B–2E are largely parallel with one another
  - 2F depends on 2C, 2D, 2E (it registers their kinds)
  - 2G depends on 2F (schemas validate the files); the data files come after the schemas
    that validate them and before the walk that reads them
  - **2H depends on 2G and blocks 2I.** The licensing checks are widened while every shipped
    data file still carries one designation, so they are green as they land. Running 2I first
    would put the first name table in front of a guard that asserts every packaged `.toml`
    is Open Game Content, leaving the suite red across the whole of it
  - 2I depends on 2H and on 2D (the `names.py` schemas validate the files)
  - 2J is independent of 2C–2I and can run alongside them
  - 2K depends on 2J (exports need the types)
- **US1 (Phase 3)**: depends on all of Phase 2
- **US2 (Phase 4)**: depends on US1 — it renders the history the walk records and the
  character the walk produces
- **US3 (Phase 5)**: depends on US1 (`generate_batch` lands there at `count=1`); independent
  of US2 **except T127**, whose whole-set help assertion names `--full` and `--json` and so
  waits on T122. The Implementation Strategy below ships US2 before US3, so in the intended
  order nothing waits; the exception is recorded because "independent of US2" read without it
  would have US3's suite failing on an option US3 never adds
- **US4 (Phase 6)**: depends on US1; independent of US2 and US3
- **Polish (Phase 7)**: depends on every story that ships

### Within Each User Story

Tests are written, committed, and observed failing before the implementation. Data before the
walk that reads it. The walk before the renderings of what it produces. The renderings before
the command that writes them.

### Parallel Opportunities

- T001, T002 in Setup
- T004, T005, T008 in 2A (T006, T007, T009 touch shared files and are sequential)
- The `[TEST]` halves of 2C's six kinds (T018, T020, T022, T024) after T016 establishes the
  module
- All twenty-one data-file authoring tasks T039–T044, T049–T055, and T063–T070 — different
  files, no dependency on one another once the schemas exist. The eight in T063–T070 are
  additionally gated on the whole of 2H, which the other thirteen are not
- T072 in 2I; T078, T079 in 2K
- Every US1 test task T080–T090, T092, T093, T093a, T093b — separate concerns, and T091's
  goldens are one file set
- The sampled and property suites T107, T108, T108a, T109, T110, T111
- US2's test tasks T112, T113, T115–T118
- US3's T123, T124, T125, T127
- All four US4 test tasks
- T135, T136, T137 in Polish

---

## Parallel Example: User Story 1

```bash
# The walk's test halves, all in tests/unit/test_generator.py's sibling concerns:
Task: "T081 career entry, draft routing, basic training, rank-zero bonus"
Task: "T084 mishaps, the two-year term, the forfeited benefit roll"
Task: "T087 mustering out, the non-cumulative rank bonus, the single-career pension"
Task: "T088 aging crisis debt, medical bills, ordered settlement"

# The rendering and CLI tests, separate files:
Task: "T089 the Universal Character Format, tabs and sort key"
Task: "T092 the stream split and exit codes"
Task: "T093 naming a character changes nothing else"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 Setup
2. Phase 2 Foundational — the long pole, and unavoidable: no walk can run until the data
   exists and validates
3. Phase 3 User Story 1
4. **STOP and VALIDATE**: `cetools npc --seed session-alpha` against the committed goldens,
   then the thousand-seed audit
5. That is the whole of the value for a referee who wants one usable NPC

### Incremental Delivery

1. Setup + Foundational → the data set validates at twenty-six files
2. US1 → a referee generates one usable NPC (MVP)
3. US2 → a maintainer diagnoses a surprising sheet from output
4. US3 → a referee populates a table from one seed
5. US4 → a referee runs their own rules

### Traps to re-read before starting each phase

`plan.md`'s "Traps worth naming now" collects every place the obvious implementation is
wrong. The four that cost the most if missed:

- The name roller is **derived**, never drawn from the walk's roller (T093 before T094)
- `character_seed(master, 0)` is `master` itself, not a derivation (T102)
- `tests/unit/test_library_api.py`'s parser must learn this feature's contract **before**
  any export lands (T076 before T077)
- The committed check goldens are not regenerated in this feature (T010, T140)
- **The licensing checks widen before the first name table lands, not after** (Phase 2H
  before Phase 2I). The existing packaging guard asserts every shipped `.toml` is Open Game
  Content, so authoring a GPL-designated file first turns the suite red and keeps it red for
  the length of the phase, which the commit discipline does not allow
- **The npc goldens are rendered from hand-constructed characters, not captured from a seed**
  (T091, T114, T126). Which character a seed produces is unknowable until the walk exists, so
  a captured sheet is not an expected value written before the implementation, and SC-016 asks
  for one that is

---

## Notes

- 143 tasks: 3 Setup, 76 Foundational, 35 US1, 11 US2, 7 US3, 5 US4, 6 Polish
- Three tasks were added after the cross-artifact analysis of 2026-08-21 and carry lettered
  IDs — T093a (SC-001), T093b (FR-053b from the library), T108a (SC-020) — so that no existing
  task ID moved. The same analysis reordered Phases 2G through 2I, which reassigned T056–T073
  among themselves and left every other ID where it was. This is the same convention the specification uses for FR-007a and SC-015a,
  and for the same reason: an ID that moves is an ID that breaks every reference to it
- `[P]` tasks touch different files and depend on nothing incomplete
- `[TEST]` tasks are separate commits from the implementation they precede (SC-016)
- Stop at any checkpoint to validate a story independently

---

## Phase 8: Convergence

Appended by `/speckit-converge` against the finished branch. Every item below was confirmed
against the code as it stands, most of them by running the walk over a sampled population;
the counts quoted are from that sample and are what a fix should move. The whole suite passes
under `uv run python -m pytest`, so every defect here is latent rather than a known failure —
which is itself why T152 and T153 are on the list.

The standing rules at the top of this file still apply: test-first, one commit per logical
unit, structural before behavioral, a CHANGELOG entry for every user-visible change. T141 and
T144 change the draw order of the walk, so both need the **Breaking changes** note FR-056b
requires; the committed `npc_*.txt` goldens are hand-constructed and do not move with them,
but `tests/integration/test_golden.py`'s seed-derived assertions do.

- [X] T141 **CRITICAL** Move the `2d6` of the qualification, survival, commission, advancement, and re-enlistment throws out of `_2D6` in `src/cetools/generator.py:37` and into the career throw schema beside `target` and `characteristic`, so that no die anywhere in the walk is held in engine code; raise the career schema version and bring all eight shipped careers to it per FR-038 and Constitution V (contradicts)
- [X] T142 **CRITICAL** Restore `uv run pytest` — the command `.github/workflows/ci.yaml:27` and `CONTRIBUTING.md:41` both run — to a collectable suite: `tests/guards/test_packaging.py:22` and `tests/unit/test_licensing.py:7` import `tests.conftest`, which resolves only when the repository root is on `sys.path`, so the whole suite errors at collection on every platform CI covers per Constitution III (contradicts)
- [X] T143 Bill medical care at the per-point cost times the points actually reduced in `_raise_medical_bill` (`src/cetools/generator.py:846-855`), rather than one point per characteristic currently at the floor: track the raw reduced-point total per characteristic through the term loop so that an injury reducing a score without flooring it raises a bill, and so that an aging-floored characteristic is not billed to the employer, per FR-025 (contradicts)
- [X] T144 Record debt settlement in the generation history in `_Walk.settle_debts` (`src/cetools/generator.py:236-258`): the amount paid, which characteristics were restored and by how much, and the order the points were considered in, so that funds and characteristics on the sheet replay from the history; and rename the step emitted at crisis-debt creation (`:797`) so `debt-settled` names settlement, per FR-030, FR-025a, and US2 acceptance scenario 4 (missing)
- [X] T145 Forfeit a mishap-ended term's benefit roll exactly once — `src/cetools/generator.py:565` increments `forfeited_terms` for the data effect and `:572` increments it again for the mishap-ended term, so a row carrying `forfeit-term-benefit` forfeits twice — deciding whether the effect or the unconditional rule owns it, and correcting `src/cetools/data/chargen/mishaps.toml` to match, per FR-020 (contradicts)
- [X] T146 Trigger an aging crisis only where the aging effect actually reduced the characteristic: `src/cetools/generator.py:770` and `:909` test the post-state (`score <= floor and amount < 0`) rather than the applied delta, so a characteristic already at the floor and chosen again raises a fresh throw-times-multiplier debt for a reduction that did not occur, per FR-021 (contradicts)
- [X] T147 Cap the rolls taken as cash per character rather than per career service — `cash_taken` is a local of `muster_out_service` (`src/cetools/generator.py:966`) and resets for every `CareerService`, so a multi-career character exceeds `mustering-out.maximum-cash-rolls` — per FR-016's "how many of **a character's** rolls" (contradicts)
- [X] T148 Refuse an empty or whitespace-only name in `generate_batch`/`generate_character` on the same terms `cli.py:186` refuses it, so that the library cannot produce a character whose `name` is `""` and whose sheet renders a dangling title separator, per FR-047, FR-053c, and SC-018 — the same reasoning FR-053a gives for the name-with-count refusal (partial)
- [X] T149 Replace the `source` line of all eight files under `src/cetools/data/names/` with a source a reviewer can find and read the terms of — a named public-domain or open-data list, a government or census release, or a source under a redistribution-permitting license — rather than the present description of what the entries are, and extend `tests/unit/test_name_tables.py` beyond its truthiness assertion, per FR-043e (partial)
- [X] T150 Apply the medical tier's rank modifier, declared and required at `src/cetools/data/chargen/medical-tiers.toml:12` and `src/cetools/chargen.py:1000` and read by nothing: carry the character's rank at the time the bill is raised into `_raise_medical_bill` (`src/cetools/generator.py:837-840`), which today declines it for want of a rank snapshot, per FR-025 (missing)
- [X] T151 Emit the five `StepEffect` kinds the walk declares and never produces — `age`, `benefit-roll-forfeit`, `career`, `commission`, `rank` — so that the forfeited benefit roll of FR-020, the commission and rank movement of FR-007b, and a mishap's extra years each leave an addressable effect; or drop the unreachable ones from the closed set in `src/cetools/character.py:49-63` and from `data-model.md`, per FR-030a (partial)
- [X] T152 Extend SC-004's audit in `tests/integration/test_npc_sample.py` to the four things the criterion enumerates that it does not check: age against the terms served *and how each ended* (today only `age >= starting_age`), the benefit rolls taken against the terms served and the rank reached, a pension against a single career's terms, and every skill tracing to a table the character could reach in a term they served, per SC-004 (partial)
- [X] T153 Strengthen SC-005's traceability check in `tests/integration/test_npc_sample.py` from subject presence to value reconciliation — replaying the history's characteristic and credit effects must reproduce the sheet's characteristics and funds — which is what makes the check able to fail on T144, per SC-005 (partial)
- [X] T154 Agree the sheet's and the machine-readable document's skill ordering: `_skills_line` sorts on `f"{label}-{level}"` (`src/cetools/render.py:237-238`) while `as_dict` sorts on the label alone (`:504`), where `contracts/cli.md:128` pins the key to the rendered name-and-specialty; and replace `tests/contract/test_npc_json.py:148`, which asserts casefold order rather than comparing against the sheet, per FR-046 (contradicts)
- [X] T155 Give at least one shipped career an entry ladder with ranks above zero: every two-ladder career declares a single rank 0 on its entry ladder, so `ranks_above` is always empty for an uncommissioned character (`src/cetools/generator.py:629-630`), advancement is never attempted off the commissioned ladder, and every uncommissioned service ends at rank 0 — a shape the engine handles that no shipped career exercises, per FR-033 and FR-007b (partial)
- [X] T156 Make SC-020's completeness half assert what the criterion states — every field the default rendering is required to carry is non-empty — rather than `assert text`, and run it over the whole sample rather than `sample[:200]` (`tests/integration/test_npc_sample.py:147`), per SC-020 (partial)
- [X] T157 Carry the remainder of a partly covered medical bill across settlements: `points = payment // debt.cost_per_point` (`src/cetools/generator.py:253`) discards each payment's remainder, so two payments that together cover a point restore none, per FR-025a's "the points restored MUST be those the covered amount pays for" (partial)
- [X] T158 Assert in SC-019's weighting check that every surname table in force appears in the sample: `tests/integration/test_npc_sample.py:161` iterates only the regions that were drawn, so a weighting mistake that drops a region entirely passes the criterion it exists to catch, per SC-019 (partial)

---

## Phase 9: Convergence

The second convergence round, against the branch as Phase 8 left it. The whole suite is green
(`uv run pytest`: 1173 passed, no deselections, the two `slow` sampled audits included), so
every item below is latent rather than a known failure. Each was confirmed against the code as
it stands, most of them by walking a sampled population and reading the resulting history; the
counts quoted are from those samples and are what a fix should move.

Every Phase 8 fix was re-verified and holds. This phase does not revisit any of them.

The standing rules at the top of this file still apply: test-first, one commit per logical
unit, structural before behavioral, a CHANGELOG entry for every user-visible change. T160,
T161, T162, T164, T165, T169 and T170 change the draw order or the draw count of the walk, so
each needs the **Breaking changes** note FR-056b requires. The committed `npc_*.txt` goldens are
hand-constructed and do not move with them; `tests/integration/test_golden.py`'s seed-derived
assertions do, and so do the sampled audits that pin counts.

- [X] T159 **CRITICAL** Render the characteristic profile from the rules in force rather than from the packaged data: `_characteristic_profile` (`src/cetools/render.py:208-226`) calls `load_rules()` with no override for its pseudo-hex symbols, so a character generated under `--rules-data` renders against packaged symbols while the provenance beside it reports the override — swapping data does not change the output, which is what Constitution V promises it does. `as_text`'s signature is pinned by `contracts/library-api.md`, so the seam is either the symbol carried on the character or the registry carried on the batch; decide which and record it, per Constitution V, FR-043 and FR-058 (partial)
- [X] T160 Trigger an aging crisis only from the aging path (`src/cetools/generator.py:997`), not from `_apply_class_effect` (`:851-852`), which also serves the mishap term loop (`:600`) and `_roll_injury` (`:903`): FR-021 defines the crisis as arising from an aging effect, and the edge case says "where the bottom was reached by aging". Today an injury that floors a characteristic raises both a crisis debt and a medical bill over the same points, each claiming to restore them — seed 51 shows a `medical-crisis` of Cr20,000 following a mishap with no aging step anywhere before it, and 429 of 4,000 sampled characters carry a crisis no aging step preceded, per FR-021 and FR-028 (contradicts)
- [X] T161 Restore the characteristic points a settled medical bill actually paid for: `_raise_medical_bill` charges `cost_per_point x points x share owed` (`src/cetools/generator.py:929-934`) but hands `_Debt` the **full** `cost_per_point` (`:945`), so `settle_debts` (`:289`) restores `owed // full_cost` points and a fully paid bill for three points restores none. Base restoration on the character's own per-point share so that paying the bill in full restores every point it covered. Separately, the `owed <= 0` early return (`:935-936`) fires after the tier throw has been rolled (`:913`), so an employer paying 100% leaves the reduction permanent and the throw unrecorded — record the throw and restore the points, per FR-024's "MUST persist **unless** the character's medical bills are paid", FR-025 and FR-025a (contradicts)
- [X] T162 Raise a medical bill for a mishap's direct characteristic reduction: the term loop discards `_apply_class_effect`'s returned reduction map (`src/cetools/generator.py:598-600`) while `_roll_injury` feeds the same map to `_raise_medical_bill` (`:903-906`), so mishap row 1 "Injured in action" (`src/cetools/data/chargen/mishaps.toml:16-18`) reduces a characteristic that no payment can ever reverse — 532 occurrences over 6,000 seeds, none billed. FR-024 says a reduction arriving by **either route** persists unless the bills are paid, which presupposes a bill exists to pay, per FR-024 and FR-025 (partial)
- [X] T163 Append the `aging` history step before the crisis it causes: `_apply_aging_if_due` calls `_trigger_medical_crisis` inside the effect loop (`src/cetools/generator.py:997-998`) and appends the `aging` step only afterwards (`:999-1008`), so the crisis and its debt precede their own cause. Seed 267 reads `medical-crisis ... Cr40,000` and then `aging ... END -1`; 24 of 5,000 seeds file a crisis ahead of the aging step that raised it. FR-030 requires the steps in the order the walk occurred, which is what makes a surprising sheet diagnosable, per FR-030 and US2 acceptance scenario 4 (contradicts)
- [X] T164 Record a debt's creating step before its settlement step: `add_debt` settles immediately (`src/cetools/generator.py:311-314`) while every caller appends its own step after the call — `_trigger_medical_crisis` (`:859` against `:869`), `_raise_medical_bill` (`:940` against `:950`), and the mishap `debt` branch (`:603` against `:604`). `cetools npc --seed 51 --full` prints `debt-settled Cr20,000 debt, END 1` above the `medical-crisis` that created it, and an in-order replay drives debt or funds negative for 89 of 5,000 seeds — which is exactly the reconciliation T153 strengthened SC-005 to perform, per FR-030 (contradicts)
- [X] T165 Distinguish the called-for reduction from the applied one in the record itself: `_apply_characteristic_delta` (`src/cetools/generator.py:105-120`) emits both as `StepEffect(kind="characteristic", subject=code, amount=...)`, so a floor clamp renders `END -5, END -4` and nothing in the record says which is which. The disambiguating convention is written in a test helper (`tests/integration/test_npc_sample.py:54-98`) rather than in the record, and it cannot tell a clamp pair from two genuine reductions of one characteristic — under an aging override with two `physical` effects in a row, which US4 acceptance scenario 1 supports, 33 of 2,000 characters stop replaying to their sheet. FR-030a requires the parts be separately addressable and the check be made from the record's shape, per FR-030a and SC-005 (partial)
- [X] T166 Add the cross-file rule that at least one career in force is `always-available` and at least one is `re-enterable`: `src/cetools/generator.py:474` and `:483` take a bare `next(...)` over an invariant nothing validates, and `rules.py:815-902` checks the draft table, the medical tiers, the commissioned ladders and the characteristic classes but not these. An override clearing both flags on Drifter makes `cetools validate` report `Rules data is valid.` and exit 0, then makes `cetools npc` dump a traceback ending `RuntimeError: generator raised StopIteration` for 475 of 3,000 seeds. The run must fail before any character is produced, naming what could not be resolved, per FR-004, FR-006, US1 acceptance scenario 3 and US4 acceptance scenario 4 (missing)
- [X] T167 Assert the GPL mirror over the real files, not only over a planted one: `_wrongly_covered` (`tests/conftest.py:128-140`) has exactly one call site, `tests/unit/test_licensing.py:356`, which plants its own violating file and asserts the helper flags it — so the helper is proved and the tree is not. `tests/guards/test_packaging.py:22` imports only `_uncovered`, so neither the wheel nor the sdist is mirrored either. Assert `_wrongly_covered(...) == []` over the working tree and over both distributions, so that a name table drifting into `chargen/`, `careers/` or `registries/` — where it would still load and still be basename-unique — fails the suite instead of shipping under a notice that does not cover it, per SC-015 and SC-015a (partial)
- [X] T168 Forfeit the rank-derived benefit rolls along with the rest when a mishap forfeits a career's benefits: `src/cetools/generator.py:794` sets `benefit_rolls = 0` for `forfeit_all`, but `:1054` computes `rolls = benefit_rolls + rank_bonus`, so a character dishonorably discharged or imprisoned at a high rank still takes one to three mustering-out rolls from that career — 55 such services in 20,000 characters. `CareerService.benefit_rolls` also records 0 while rolls were taken; `tests/integration/test_npc_sample.py:185` encodes the present arithmetic and moves with the fix, per FR-019's "MUST carry the mishap's consequence" and FR-016 (contradicts)
- [X] T169 Attempt the advancement throw whenever the career declares `throws.promotion`, rather than only when a higher rank exists on the current ladder: `src/cetools/generator.py:677-682` gates the whole step on `ranks_above`, a precondition no data declares. FR-008 conditions the step on the career offering the throw, and FR-009 grants a skill roll on a successful one, so an uncommissioned character in a promotion-offering career is denied both — 757 of 2,658 survived terms over 2,000 seeds make no advancement throw at all. Leave the rank unchanged where the ladder has nothing above, per FR-008, FR-009 and FR-038's rule against a rule held in engine code (partial)
- [X] T170 Refuse a supplied name carrying a tab or a newline, in the library and at the command line on the same terms the empty-name refusal of T148 uses: `src/cetools/cli.py:186-189` and `src/cetools/generator.py:1193-1194` check only `strip()`, and `render.py:261-262` interpolates the name verbatim, so `--name $'Alex\tRivera'` puts three tabs on a line FR-046 requires to hold exactly two, and `--name $'Alex\n\nRivera'` writes a blank line inside a sheet, which under FR-048a is the separator between sheets. FR-047 requires a supplied name verbatim, so the name that cannot be rendered verbatim is the one to refuse, per FR-044, FR-046, FR-048a and FR-053c (missing)
- [X] T171 Give the `TITLED_THEN_UNTITLED` reference the shape SC-009 names: its second `CareerService` carries `title="Drifter"` (`tests/unit/test_render_character.py:145-173`), so no committed reference covers "a multi-career character holding a titled rank in an earlier career **and none in a later one**" — and as built it is a character FR-047c could not produce, since a later career that does name a title supplies it. Setting the later service's `title=""` fixes it without moving a golden byte, the renderer reading only `character.title`. Add beside it the generator-level assertion FR-047c has nowhere: the shipped data titles every ladder's ending rank, so the "an earlier title survives" branch (`src/cetools/generator.py:1161-1163`) is never taken by ordinary generation and is today asserted only against a hand-built literal, per SC-009 and FR-047c (contradicts)
- [X] T172 Compare the fuller rendering for determinism: `tests/integration/test_npc_determinism.py:25-26` asserts `as_text(first) == as_text(second)` and then `as_text(first, full=False) == as_text(second, full=False)`, which is the same call twice (`as_text`'s default is pinned at `tests/unit/test_render.py:585`). The `full=True` form — the only one that renders the history block — is compared nowhere, in process or across processes, so a history line ordered by set iteration would vary under hash randomization and pass the whole suite. Extend `_run` (`:29-35`) to a `--full` invocation as well, per SC-001's "both rendered forms byte for byte" (partial)
- [X] T173 Demonstrate the medical tier reaching the generator: `tests/integration/test_data_driven.py:203-215` asserts only that the loader reports the overridden `medical_tier` and that the two tier tables differ, where the Draft-row, aging, mishap and term-cap cases beside it each generate a character and compare against a baseline. A generator that ignored `career.medical_tier` and hard-coded a tier at `src/cetools/generator.py:912` would pass this case, and would also pass SC-008's tier check (`tests/integration/test_npc_sample.py:288-291`), which reads the tier off the career rather than off what was charged, per SC-013's "changes the generator's behavior" (partial)
- [X] T174 File an injury's characteristic reduction as an `injury` step rather than a `mishap` one: `_apply_class_effect` hard-codes `kind="mishap"` on the step it appends (`src/cetools/generator.py:841-850`) and `_roll_injury` calls it (`:903`), so the reduction an injury row produced is recorded under the wrong kind. FR-030a requires each step name which kind of step it was, per FR-030a (partial)
- [X] T175 Bring the rendering inside the command's error handling: `src/cetools/cli.py:213` calls `as_text(batch, full=full)` outside the `try/except CetoolsError` at `:197-206`, and `CharacteristicRegistry.symbol` (`src/cetools/registries.py:64-81`) raises `RulesDataError` for a score outside the declared range. A render-time failure therefore writes a traceback rather than the reason FR-054 requires, after `Seed:` and `Rules:` have already gone to standard error. T159 makes this reachable rather than remote, since the profile will then read an override's own symbol table, per FR-054 (partial)
- [X] T176 Count the surname region each **character** records in SC-019's weighting check: `tests/integration/test_npc_sample.py:355-372` calls `roll_name(...)` ten thousand times and tallies `name.region`, so nothing anywhere asserts that a generated character's `surname_region` is the region of the table its surname came from — a defect at `src/cetools/generator.py:1204` would pass both SC-018 and SC-019. The criterion names the field deliberately, to keep the check off the rendered text, per SC-019 and FR-047d (partial)
- [X] T177 Check a multi-character run against the JSON contract: `_BATCH` in `tests/contract/test_npc_json.py:83-85` holds exactly one character and every assertion in the file runs against it, so the "a run of one character and a run of twelve emit the same document shape, verified by checking both against one contract" half of the criterion is verified by nothing, per SC-010 and FR-050a (missing)

---

## Phase 10: Convergence

The third convergence round, against the branch as Phase 9 left it. The whole suite is green
(`uv run pytest`: 1200 passed, 0 skipped, the nine `slow` sampled audits included), so every
item below is latent rather than a known failure. Every one was confirmed by running the
code — generating sampled populations, building override data sets under `/tmp`, and
invoking the command — and the counts quoted are from those runs and are what a fix should
move. Every Phase 8 and Phase 9 fix was re-verified and holds; this phase revisits none of
them.

The theme of this round is **data the loader accepts and the walk does not honor**. T178,
T185 and T186 are three instances of one shape: a field is parsed, validated, unit-tested,
and then read by nothing, so a referee edits it and the character does not change — which is
the promise Constitution V exists to make. T180, T181 and T182 are the T166 shape again:
`cetools validate` reports `Rules data is valid.` and the walk then fails per-seed, twice
with a bare Python traceback rather than the reason FR-054 requires.

Seven further candidates were examined and deliberately **not** appended, so a later round
does not rediscover and re-litigate them: the `--full` CLI-to-renderer derivation (`cli.py`
has one shared `typer.echo` for both renderings), the seed-contract guard's command list,
the no-outside-reads hook's scope, the no-`locale` guard's depth, `README.md`'s omission of
`--rules-data` from the `npc` section, basename uniqueness asserted over the working tree
rather than over the distributions, and SC-015b's checks keyed on a filename glob. Each is
unpinned-but-correct behavior or documentation drift rather than a defect, and converge
carries defects only.

The standing rules at the top of this file still apply: test-first, one commit per logical
unit, structural before behavioral, a CHANGELOG entry for every user-visible change. On the
**Breaking changes** note FR-056b requires, stated precisely rather than blanket-claimed,
since Phase 9's preamble over-claimed it: **T178 and T187 change what a seed produces**
(throw totals and benefit-table rows respectively) and need it; **T183, T184, T188 and T189
change the `Character` value or the emitted document** without changing the draw sequence,
and need a note saying which; **T179, T180, T181, T182, T185 and T186 change no shipped
behavior at all** — the shipped data already satisfies every rule they add — and must not
be flagged as breaking. The hand-constructed `npc_*.txt` goldens move only for T183 and
T192; `tests/integration/test_golden.py`'s seed-derived assertions move with T178 and T187.

- [X] T178 **CRITICAL** Stop discarding the modifier a dice notation declares: `_dice` in `src/cetools/generator.py:42-44` unpacks `parse_notation` as `count, sides, _modifier` and returns `roller.dice(count, sides)`, so all sixteen call sites — the five career throws, the characteristics roll, draft, mishaps, injuries, continuation, medical crisis, medical tiers, aging, and the three mustering-out reads — compare `sum(faces)` against a target while ignoring what the file asked for. An override setting `dice = "2d6+6"` on every Navy throw makes `cetools validate` report `Rules data is valid.`, is carried on the loaded object (`careers['navy'].throws['qualification'].dice == '2d6+6'`), and produces 300 of 300 byte-identical sheets; the identical notation on `task.roll` is honored and itemized by `src/cetools/tasks.py:120-127`, so one package reads one notation two ways. Either add the modifier to the total everywhere and record it in `StepThrow.modifiers` — which exists and is `()` at every one of these sites — or reject a modifier in `chargen._require_roll` and `careers._require_roll` while leaving `task.roll` permissive; decide which and record it in `contracts/data-files.md:251,288`, per Constitution V, SC-013, US4 acceptance scenarios 1 and 3 (contradicts)
- [X] T179 **CRITICAL** Move the benefit-roll-per-term count into data: `src/cetools/generator.py:812` computes `benefit_rolls = 0 if forfeit_all else max(0, terms - forfeited_terms)`, an implicit one-roll-per-term rate held in engine code, while the rank thresholds it is paired with read from `mustering-out.rank-benefits`. FR-038 enumerates "the benefit-roll count rule **and** its rank thresholds" as one item and only the second half reached a file, so a referee whose setting pays two rolls a term edits code — which is what FR-009's four analogous counts were all put in data to avoid. Add `mustering-out.per-term`, raise the `chargen-parameters` schema version, read it at `:812`, document it in `contracts/data-files.md:508-518`, and add it to SC-013's demonstrated set, per FR-038, FR-016 and Constitution V (contradicts)
- [X] T180 Validate that the characteristic modifier bands in force cover every score they can be asked for: `src/cetools/registries.py:207-219` checks only that exactly one band is unbounded and then sorts by `minimum`, and `rules.py:817-925` — which validates the draft rows, the medical tiers, the commissioned ladders, the characteristic classes, and T166's two career flags — has no rule for the band table. An override dropping `"6-8" = 0` from `characteristics.toml` makes `cetools validate` report `Rules data is valid.` and then fails **429 of 500 seeds** with `no characteristic band covers score 8` (`registries.py:56-62`), and breaks the previous feature's `cetools check` command on the same data. Add a cross-file rule asserting the bands cover every integer from `pseudo_hex_minimum` up to the unbounded band with no gap; decide separately whether an overlap is an error or first-match-wins and say so, because `"7-10" = 4` beside `"6-8" = 0` also validates clean today and is silently unreachable, resolved by nothing but TOML file order, per US4 acceptance scenario 4, FR-039 and Constitution V (missing)
- [X] T181 Report an out-of-range positional table read rather than raising `IndexError`: `src/cetools/generator.py:443` (`draft.careers[row - 1]`), `:583` (`mishaps.rows[sum(mishap_faces) - 1]`) and `:913` (`mishaps.injuries[sum(faces) - 1]`) index straight off a throw total with no guard, so a `roll = "2d6"` over `draft.toml`'s six rows validates clean and then dumps a Rich traceback ending `IndexError: tuple index out of range` — 184 of 3,000 seeds for draft, 241 of 3,000 for a five-row mishap table. `contracts/data-files.md:291-293` already settles the treatment — "a die that can produce a total outside the array is a data problem **reported when it is read**, not at load, for the same reason a characteristic outside the pseudo-hex range is" — and `CharacteristicRegistry.symbol` (`src/cetools/registries.py:64-81`) is the shape to copy: raise `RulesDataError` naming the file, the total and the row count, which `cli.py`'s `try/except CetoolsError` then reports as FR-054 requires now that T175 brought rendering inside it, per FR-054, FR-005 and `contracts/data-files.md:291` (missing)
- [X] T182 Require every ladder declaring `role = "entry"` to declare rank 0: `run()` calls `_grant_rank_bonus(career.name, 1, entry_ladder, 0)` at `src/cetools/generator.py:1242` and `_grant_rank_bonus` takes a bare `next(r for r in ladder.ranks if r.rank == rank)` at `:373`, over an invariant nothing validates — `careers.py:556-600` checks that ranks are distinct and sorts them, and `rules.py:815-880` has no rule for it. An override whose Scout entry ladder starts at rank 1 makes `cetools validate` report valid and then raises `RuntimeError: generator raised StopIteration` on seed 3. This is the same bare-`next`-over-an-unvalidated-invariant that T166 was raised as CRITICAL for, left for this precondition; FR-007's rank-zero bonus granted at entry is what makes rank 0 mandatory rather than conventional, per FR-007, FR-007b and US4 acceptance scenario 4 (missing)
- [X] T183 Record the throw on every step that made one: `data-model.md:155-158` states the convention — "a table-reading roll, where there is no target to beat, carries `target = 0` and `success = True`, and the row it read is in `selected`" — and only `_draft` (`src/cetools/generator.py:449`) and `_apply_aging_if_due` (`:1076`) follow it. Over 3,000 seeds, 12,026 `skill-roll` steps (`:1099`, which rolls a die at `:1087` to choose the table and again at `:1088` to read the row), 6,032 `benefit` steps (`:1158` and `:1191`, which throw the FR-016 cash-choice die at `:1149` and the benefit-table die at `:1153`/`:1169`), 3,000 `characteristics` steps (`:328`), 3,000 `background-skills` steps (`:355`), 4,983 `basic-training` steps (`:523`, which draws on a later career) and 986 mishap and injury reduction steps (`:866`, whose `-1d6`/`-2d6` amount is rolled at `:857`) all carry `throw=None` — which `data-model.md:119` defines as "`None` for a step that **decided rather than threw**", so the record states something false about itself. 54 die draws per character, 19 of them recorded. US2 exists so that "an admiral with no Tactics" is diagnosable from output, and a benefit roll landing on the wrong row is the case it cannot diagnose, per FR-030, FR-030a and `data-model.md:155` (partial)
- [X] T184 Emit `characteristic_symbols` in `as_dict(Character)`: T159 added the field at `src/cetools/character.py:170` and `src/cetools/render.py:495-511` still emits fifteen of the sixteen — verified as the **only** field-versus-emitted mismatch across all six produced types, the other five agreeing exactly. The two lists are pinned independently and disagree by exactly this field (`tests/unit/test_character.py:71-89` asserts sixteen dataclass fields, `tests/contract/test_npc_json.py:109-127` asserts fifteen JSON keys, and nothing relates them), which is why the suite is green. The consequence is the defect T159 removed: a `--json` consumer rendering FR-044's profile line under `--rules-data` must reload the packaged symbol table, while the text path now follows the override. Emit it after `characteristics`, extend `contracts/json-output.md:114-137` and its key-order line, amend FR-029's field list in `spec.md:590-596`, and add the guard that would have caught it — `set(as_dict(x)) == {f.name for f in dataclasses.fields(type(x))}` — which passes for every other type today, per FR-050 and FR-029 (contradicts)
- [X] T185 Perform an injury row's non-characteristic effects, or refuse them at load: `_roll_injury` (`src/cetools/generator.py:926-933`) loops `for effect in row.effects` with a single `if effect.kind == "characteristic-class"` and no `else`, while the mishap loop at `:601-631` dispatches `debt`, `years`, `forfeit-career-benefits` and `roll-injury` as well — and `chargen.py:697-744` parses both arrays with the same row parser, `contracts/data-files.md:372` writing the closed kind set as `*[].effects[].kind` with the `*` covering both. An injury row given `years = 10`, `debt = 99000` and `forfeit-career-benefits` validates clean, is rolled by 116 of 4,000 characters, and changes not one character's age, debt or funds. The contract's stated purpose for the closed set — "a misspelling is caught rather than becoming a new effect nothing performs" — is defeated by a correctly spelled effect nothing performs, per FR-019, FR-024 and SC-013 (partial)
- [X] T186 Honor a bounded aging row's upper bound, or require the rows to be contiguous: `AgingRow.maximum` is parsed, validated, and unit-tested, and `src/cetools/generator.py:1031-1034` matches on `minimum` alone — `rg '\.maximum' src/` finds it only at `chargen.py:445`'s "exactly one unbounded row" check and at `registries.py:60`, where the analogous modifier-band lookup *does* honor it. `contracts/data-files.md:300-320` admits `N`, `N-M` and `N+` and imposes no contiguity rule, and its own worked example is a gapped table; used verbatim as an override it validates clean and sends **166 of 838 aging steps** — every modified total from −5 to −1, falling in no row — down to the `-6` row, reducing four characteristics apiece. Either match on `minimum <= modified <= maximum` with the documented lowest-row floor and an explicit failure for an uncovered result, or add a contiguity rule to `rules.py`; say which in `contracts/data-files.md:330`, per FR-013, FR-037 and SC-013 (partial)
- [X] T187 Stop swallowing the mustering-out modifiers at the top of the table: `src/cetools/generator.py:1154` and `:1170` compute `index = max(0, min(len(...) - 1, sum(faces) + dm - 1))`, an engine-invented clamp stated in no requirement, contract or data file — and the opposite of the treatment `contracts/data-files.md:291-293` gives the same shape elsewhere. It is live on shipped data rather than hypothetical: seven of the eight careers ship six-entry `cash` and `benefits` tables while only `navy.toml` ships seven, so with `retired-cash-dm = 1` or `material-rank-dm = [{ rank = 5, dm = 1 }]` a natural 6 lands on the same row as a natural 5 in every career but Navy — reached by 402 pensioned characters and 1,330 characters holding rank 5 or above per 20,000. FR-017 requires the cash modifier to apply exactly when the pension was qualified for, and a modifier whose only effect at the top of the table is nil does not. Decide whether the seven six-row tables are a row short of what a `1d6` plus a DM needs, or whether the clamp is a rule that belongs in `chargen-parameters.toml` and the contract, per FR-016, FR-017 and FR-038 (contradicts)
- [X] T188 Record on `CareerService.benefit_rolls` the rolls actually taken: `src/cetools/generator.py:812` sets the field from the term count alone while `:1141` rolls `benefit_rolls + rank_bonus`, so the field understates by 1 to 3 in **467 of 8,288 career services** over 5,000 seeds (107 at rank 4, 345 at rank 5, 15 at rank 6). T155's rank-5 enlisted ladder makes this ordinary on Navy rather than confined to commissioned officers. `data-model.md:99` documents the field as "Taken at mustering out" and `contracts/json-output.md:53,167` publishes it, so a consumer reading it is told the wrong number; `tests/integration/test_npc_sample.py:167` adds `rank_bonus` back rather than catching the gap, and moves with the fix. This is T168's shape — the rank-derived half of a benefit count going where the term-derived half does not, per FR-016, SC-004 and `data-model.md:99` (contradicts)
- [X] T189 Record the draft's substitution as a step of its own: `enter_career` (`src/cetools/generator.py:479-486`) replaces the drafted career with the first `re-enterable` one when the Draft table names a career already entered, leaving `entered_by` fixed at `"drafted"` from `:475` and the `draft` step at `:444-453` still naming the original — so the history reads `draft → Marine` immediately followed by `career-entered → Drifter (drafted)`, for a career the Draft table does not name at all (`src/cetools/data/chargen/draft.toml:12-13`), with nothing between explaining it. **163 of 5,000 characters**, e.g. seeds 15, 35, 55 and 58. The comment at `:480` concedes the routing is a rule held in engine code, which is what the FR-005 edge case rejects for the neighboring collision: "a fallback here would be a rule in engine code that has no reason to exist once the data is complete." Record the substitution, or give it its own `entered_by` value, and settle in the spec whether FR-005 or FR-015 governs the collision rather than leaving it to a code comment, per FR-030, FR-005 and FR-006 (contradicts)
- [X] T190 Correct the changelog's own statement of what a seed promises: `CHANGELOG.md:35-40` reads "**Nothing here changes the draw order of the NPC generator's lifepath walk**", and is contradicted under the same `### Breaking changes` heading by `:49-58` (T155, "which reorders the draw sequence: every character a seed produces that serves in Navy without commissioning changes from this version forward"), `:59-70` (T149) and `:71-80` (T160). Separately, `:8-9` and `:35-40` each state the rule that a breaking change gets its own heading, and eight entries then sit under `### Fixed` with only an inline marker (`:379`, `:393`, `:409`, `:425`, `:446`, `:459`) or, for T161 at `:354-370`, with no marker at all. FR-056b makes this bullet the project's statement of what a referee quoting a seed is promised, so a false one is a requirement violation rather than drift. Rewrite it to state the promise without the false claim, lift or cross-reference the eight, and add a guard so it stops drifting: `tests/guards/test_documented_version.py` checks the version heading and nothing about section structure, per FR-056b and the constitution's Development Workflow (contradicts)
- [X] T191 Record in the licensing documents where the name entries came from: six of the eight tables cite CC BY-SA 4.0 Wikipedia and Wiktionary material in their own `source` field (`given-names.toml:9`, `surnames-africa.toml:7`, `surnames-asia.toml:7`, `surnames-europe.toml:12`, `surnames-indigenous.toml:11`, `surnames-north-america.toml:7`, `surnames-south-america.toml:8`), while `README.md:143-152` describes every file under `src/cetools/data/names/` as "this project's own content" licensed GPL-3.0-only, and `rg -i 'creative commons|CC BY|BY-SA'` over `README.md`, `LICENSE`, `LICENSE-OGL.txt`, `CONTRIBUTING.md` and the constitution returns nothing. `CHANGELOG.md:59-70` states the provenance plainly, so the project knows; the licensing documents a downstream redistributor reads first are the only place it is absent. The defect is the silence, not the license choice — CC BY-SA 4.0 is one-way compatible with GPLv3 and a bare list of names may not be copyrightable at all — so the work is a sentence in `README.md`'s licensing section and `CONTRIBUTING.md`'s licensing rules recording the source kinds and the position taken, per FR-042's "the designation MUST match what the file actually is" and FR-043e (partial)
- [X] T192 Give SC-010's fuller-rendering reference the character the criterion names: SC-010 asks the fuller rendering to carry debt, pension and history "for a character that has **all three**", and the `FULL` fixture (`tests/unit/test_render_character.py:248-270`) overrides `debt=1200` while inheriting `pension=0` from `:67`, so `tests/golden/npc_full.txt:7` reads `  Pension: none` and the only pension assertion in the file (`:423-425`) asserts exactly that. `src/cetools/render.py:347`'s `f"Cr{character.pension:,}"` is therefore never evaluated with a non-zero value by any test and `render.py:297-298`'s `case "pension"` in `_effect_text` is reached by none at all, though the walk produces both (seed `p88` renders `  Pension: Cr10,000`). Give the fixture a non-zero pension and a `pension` history step, regenerate `tests/golden/npc_full.txt` in the same commit, and assert the currency prefix and thousands separator on both lines, per SC-010 and FR-049 (partial)
- [X] T193 Search SC-020's sampled sheets for the values the criterion enumerates, not six label strings: `tests/integration/test_npc_sample.py:334` asserts `leak not in text` for `"Seed:"`, `"Rules:"`, `"cetools"`, `"Debt:"`, `"Pension:"` and `"History:"`, while SC-020 enumerates seven things the sheets "are searched for each" — no seed, no package version, no provenance, no history step, no step kind, no throw, and no debt or pension figure. A renderer appending the debt to line 2 as `Cr55,000 (Cr12,000)` would keep the two-field assertion at `:302-305` intact and contain no `"Debt:"`, so it would pass the criterion written to catch it. Assert `str(character.seed) not in text`, that no `step.kind` in the character's own history appears, and that a non-zero `debt` or `pension` does not appear in its formatted `Cr` form. T156 fixed the completeness half of this criterion in Phase 9; the absence half was not revisited, per SC-020 (partial)

---

## Phase 11: Convergence

The fourth convergence round, against the branch as Phase 10 left it. The whole suite is
green (`uv run pytest`: 1229 passed, 0 skipped, every `slow` sampled audit included), so
every item below is latent rather than a known failure. Every one was confirmed by running
the code — sampled populations, override data sets built under a scratch directory, and the
command itself — and the counts quoted are from those runs and are what a fix should move.
Every Phase 8, 9 and 10 fix was re-verified; this phase revisits none of them except where a
prior fix landed incompletely, which is recorded as such below.

Two themes. The first is **a throw whose record does not add up**: `contracts/json-output.md`
states `total == sum(faces) + the modifier values` and calls it "the same arithmetic invariant
the `check` payload carries", and four separate sites break it or evade it. That invariant is
the whole of US2 — a benefit roll landing on a row the record cannot explain is exactly the
case "an admiral with no Tactics" was written to make diagnosable. The second is the T166 /
T180 / T182 shape once more: **`cetools validate` reports `Rules data is valid.` and the walk
then fails per seed**, twice with a bare Python traceback that no `CetoolsError` handler
catches, which FR-054 forbids.

Two candidates were examined and deliberately **not** appended, so a later round does not
rediscover and re-litigate them. `characteristics.<CODE>.label` is required, validated,
unit-tested and read by nothing — genuinely inert, but no requirement asks a label to be
rendered anywhere, so surfacing it would be new capability rather than a fix. And the seven
Phase 10 declined stand declined. Separately checked and clean, so no task is owed for them:
the licensing designations and the Section 15 chain, basename uniqueness, the absence of both
Product Identity strings, the compatibility-attribution clause (CONTRIBUTING.md records that
the README makes no compatibility claim and therefore owes none), FR-056's determinism
(verified byte-identical across four `PYTHONHASHSEED` values in separate subprocesses), the
absence of any out-of-scope content, and the whole of FR-044 through FR-058, where every
enumerated line, key order, separator, exit code and refusal was checked against the
contracts and held.

The standing rules at the top of this file still apply: test-first, one commit per logical
unit, structural before behavioral, a CHANGELOG entry for every user-visible change. On the
**Breaking changes** note FR-056b requires, stated precisely rather than blanket-claimed:
**T202 changes what a seed produces** (a cash roll reads a different row for a character
pensioned in an earlier career) and needs it; **T196, T197, T198, T200 and T201 change the
`Character`'s history record or the emitted document** without changing the draw sequence,
and need a note saying which; **T194, T195, T199, T203 and T204 change no shipped behavior at
all** — the shipped data already satisfies every rule they add — and must not be flagged as
breaking; **T205 and T206 are documentation and a guard**. T200's dropped-entry half changes
what a seed produces only if a shipped career's service table holds a non-skill entry, so
check the eight files before claiming either way. The hand-constructed `npc_*.txt` goldens do
not move for any task here; `tests/integration/test_golden.py`'s seed-derived assertions move
with T200 and T201, and `tests/contract/test_npc_json.py`'s payload assertions move with
T196, T197 and T201.

- [X] T194 **CRITICAL** Validate `background-skills.characteristic` against the characteristics registry: `src/cetools/chargen.py:1151` parses it with `_require_string` alone and `src/cetools/rules.py`'s cross-file section has no rule for it, where `careers.py:343` does check every `throws.*.characteristic`. `src/cetools/generator.py:385` hands it to `characteristic_dm`, which indexes `self.characteristics[code]` at `:294` — a bare `KeyError` that no `except CetoolsError` catches. A referee writing `characteristic = "Intellect"` (the label `characteristics.toml` shows, rather than the code) makes `cetools validate` report `Rules data is valid.` and exit 0, then makes `cetools npc` dump a Rich traceback ending `KeyError: 'Intellect'` on **200 of 200 seeds** — it is the second step of every walk, so no seed escapes. Add the cross-file rule, worded like the existing `medical-tier` one, so the run fails before any character is produced naming what could not be resolved, per US4 acceptance scenario 4, FR-054 and FR-003 (missing)
- [X] T195 **CRITICAL** Honor the `characteristic` a career declares on its re-enlistment throw, or refuse the key: `src/cetools/generator.py:851-854` computes `total_r = sum(faces_r) + roll_mod_r` and never reads `re_enlist.characteristic`, while all four sibling throws build `Modifier(f"Characteristic {...}", self.characteristic_dm(throw.characteristic))` — qualification at `:462-466`, survival at `:625-634`, commission at `:730-738`, promotion at `:777-785`. `careers.py:331-353` accepts and registry-validates `characteristic` for every name in `_ALL_THROWS`, re-enlistment included, so the loader actively promises the value is understood: `characteristic = "ZZZ"` is refused by name, and `characteristic = "SOC"` added to all eight careers makes `cetools validate` report valid and then produces **500 of 500 byte-identical sheets across 518 re-enlistment throws**; a 5,000-character sample carries 4,617 re-enlistment throws, every one with an empty `modifiers` tuple. This is the T141 / T178 / T185 / T186 shape — a field parsed, validated, unit-tested and read by nothing. Either add the DM and itemize the `Modifier` as the other four do (no shipped career declares one, so no shipped seed changes), or reject `characteristic` at the re-enlistment position in `careers._parse_throw`; decide which and record it in `contracts/data-files.md:213-215`, which documents neither today, per Constitution V, FR-038 and FR-014 (contradicts)
- [X] T196 Itemize the two modifiers the walk applies to a throw's total but names nowhere, and give the invariant a check that can fail: `src/cetools/generator.py:1126` computes the aging total as `sum(faces) + roll_modifier - self.total_terms_served` and records it at `:1190-1198` with only the notation modifier in `modifiers`, and `:1034-1035` adds `rank_bonus` to the medical-tier total and records it at `:1058-1064` the same way. `contracts/json-output.md:187-188` states "`total` equals `sum(faces)` plus the modifier values… which a contract test asserts", and `contracts/data-files.md:325` and `:445` declare `modifier = "terms-served"` and `rank-dm` as modifiers of the total in exactly those words. Over seeds 0-999, **437 steps in 201 of 1,000 characters** violate it (aging 406, medical-bills 31): `--seed 6 --json` emits `"faces": [6, 6], "modifiers": [], "total": 8`, and `--full` renders the unexplained delta as a bare `= -1`. It is latent because `tests/contract/test_npc_json.py:258-259` iterates `_CHARACTER.history`, a hand-constructed fixture, and never a generated character — so the assertion the contract says exists has never run against the walk. Append the two `Modifier`s and extend that test over generated characters, per FR-030a, FR-030 and `contracts/json-output.md:187` (partial)
- [X] T197 Record the mustering-out modifier that chose the row: `src/cetools/generator.py:1296` computes `dm = params.mustering_out_retired_cash_dm if …` and `:1331` the material rank DM, both used at `:1301` to index the table and neither itemized in the `StepThrow` built at `:1315-1321`, which sets `total=sum(all_faces) + sum(m.value for m in modifiers)` over an empty `modifiers`. Seed 12's pensioned Merchant records `faces=(4, 6), modifiers=(), total=10` for a read that actually landed on row `6 + 0 + 1 = 7` of `(1000, 5000, 10000, 20000, 20000, 40000, 40000)` — so a consumer holding `faces`, `modifiers` and `total` cannot reach the `Cr40,000` the effect reports. `:1305` additionally concatenates two different throws into one `faces` tuple — the 1d6 cash-choice face and the 1d6 table face — so the recorded step describes a throw that was never made. Itemize both DMs and include them in `total`, and split the FR-016 cash-choice roll into its own step rather than merging its face into the table throw's, per FR-030a, FR-016, FR-017 and `contracts/cli.md:196` (partial)
- [X] T198 Record the characteristics roll's own notation modifier — the sixteenth `_dice` call site, which T178 fixed for the other fifteen: `src/cetools/generator.py:361-363` adds `modifier` to every rolled score but builds its `StepThrow` at `:371-377` as `faces=tuple(all_faces), modifiers=(), total=sum(all_faces)`. `rg -c "_roll_modifier\(" src/cetools/generator.py` returns 16 against 16 `_dice` sites — one definition and fifteen uses. With `[characteristics] roll = "2d6+2"` in an override, `cetools validate` reports valid and seed 7 grants `STR 7, DEX 12, END 4, INT 8, EDU 10, SOC 8` summing to **49** while the recorded throw reads **`total: 37, modifiers: ()`**; the `+12` the file asked for is applied to the sheet and absent from the record. `contracts/data-files.md:251` records T178's chosen remedy as "added to the throw's total **and itemized in the recorded step's modifiers**", so this site contradicts the decision the contract already carries, per FR-030a, FR-030 and `contracts/data-files.md:251` (partial)
- [X] T199 Require the unbounded characteristic modifier band to hold the highest minimum — T180's gap-and-overlap check never reaches a band declared above it, because the loop at `src/cetools/rules.py:895-902` does `if previous.maximum is None: break` at `:896-897`. `registries._parse_bands` requires exactly one unbounded band but never requires it to be last, and `characteristic_dm` (`registries.py:60`) returns the first match, so every row above it is dead data. A referee capping the ladder at `"9+" = 1` while leaving `"12-14" = 2` through `"33-35" = 9` in place makes `cetools validate` report `Rules data is valid.` and then silently gives score 12 a DM of 1 instead of 2, score 16 a 1 instead of 3, and score 20 a 1 instead of 4 — feeding qualification, survival, commission, promotion and the background-skill count, and the previous feature's `cetools check` besides. No error is raised anywhere. Report any band whose `minimum` exceeds the unbounded band's in the same cross-file check, per US4 acceptance scenario 4, FR-039 and Constitution V (contradicts)
- [X] T200 Apply the entry basic training actually drew, and stop the step's record claiming no die was thrown: `src/cetools/generator.py:583-584` filters `if not isinstance(reference, SkillReference): continue`, so a later career's drawn entry that is a characteristic adjustment is discarded after its die was rolled and recorded — `_roll_skills` reads the identical entry from the identical table correctly through `_apply_entry` (`:1213`). With a `"END +1"` entry in Drifter's service table, **24 of 500 seeds** produce a `basic-training` step carrying `throw=StepThrow(faces=(6,), total=6, …)` and `effects=()`: a die thrown, an entry selected, and nothing granted, with a history step that cannot be replayed. FR-007a's later-career clause says "a number of entries drawn from that same table" and admits no discard, where the first-career "every entry at level zero" clause arguably does. Separately, the comment at `:573-575` — "No die is rolled: every entry of the table is granted, so this step decided rather than threw" — is false: `_resolve_specialty` (`:76-89`) rolls `roller.die(len(specialties))` for every bare grant whose skill has specialties, so `--seed 15 --full` renders `Gun Combat (Energy Rifle) 0, Melee Combat (Natural Weapons) 0, Vehicle (Watercraft) 0` from three unrecorded dice against `marine.toml:39`'s bare entries, on **1,769 of 2,000 seeds** (5,150 unrecorded draws). Route the drawn entry through `_apply_entry`, keep the filter only on the first-career branch, and either record the specialty dice or correct the comment to say what is actually true, per FR-007a, FR-030a and `data-model.md:155` (partial)
- [X] T201 Name the substitute in the draft-substitution step, not the career it replaced: `src/cetools/generator.py:536-555` appends `HistoryStep(kind="career-selected", selected=candidate.name, …)` before the reassignment on the following line, so the step names the **drafted** career — the same one the immediately preceding `draft` step already names — and the substitute appears nowhere as a `selected` value. `cetools npc --seed 15 --full` reads `draft  2  Marine` / `career-selected  Marine` / `career-entered  Drifter  t1  drafted`, so Drifter is still unexplained and the only thing added between the draft and the entry restates Marine; seeds 35, 55 and 58 show the same shape, **163 of 5,000 characters**. `entered_by` also stays `"drafted"` for a career the Draft table does not name, and reusing the closed `career-selected` kind (`data-model.md:123`, which documents no second meaning) adds 163 spurious entries to any consumer counting selection attempts. FR-015a requires the substitution recorded "as its own step in the generation history, **distinct from the step naming the career the draft or the fallback actually named**"; this one duplicates it, per FR-015a, FR-030 and FR-030a (contradicts)
- [X] T202 Apply the retired cash modifier when **the character** qualified for the pension, not when the current service did: `src/cetools/generator.py:1266` sets `qualifies_for_pension = terms >= params.pension_minimum_terms` from this `CareerService`'s terms and `:1296` reads it for the DM. FR-017 says the modifier "MUST apply exactly when **the character** qualified for the pension, and MUST NOT be applied on any other reading of 'retired'" — the same character scope FR-016 uses for the cash cap, which T147 fixed for exactly this reason. Over seeds 0-19,999, **90 characters qualified for a pension in an earlier career and then mustered out of a later one, taking 34 of 21,804 cash rolls without the modifier**; seeds 547 (Scout 5 terms then Drifter 1), 921, 1669 and 3709 each carry `pension = 10000` and take an undiscounted roll. With T187's seven-row tables the DM shifts the row, so it is money rather than arithmetic. Hoist the flag to `_Walk` where the pension is granted (`:1372-1376`) and read it at `:1296`; if the per-service reading is preferred instead, it must be recorded in `contracts/data-files.md`, which gives `retired-cash-dm` no parameter-table entry of its own today, per FR-017 and FR-016 (contradicts)
- [X] T203 Fail nameably when every one of a career's skill tables is gated out: `src/cetools/generator.py:1208-1209` calls `self.roller.die(len(eligible))` over `_eligible_tables` (`:209-218`), which may legitimately return empty, and nothing in `rules.py` requires a career to keep one table its characters can always reach. The shipped edge case settles what **one** gated table does — "a gate excludes rather than fails" — and nothing covers all of them being gated. An override gating all four of Navy's tables at `EDU 12+` makes `cetools validate` report `Rules data is valid.` and then fails **32 of 300 seeds**; because `DiceError` is a `CetoolsError` the exit code and the empty stdout are already correct, but the message reads `sides must be an integer of at least 1, got 0` and names neither the career, the tables, nor the characteristic that excluded them. Either add a cross-file rule requiring one ungated table per career, or raise a `RulesDataError` at `:1208` naming the career and the gates, per US4 acceptance scenario 4, FR-010 and FR-054 (missing)
- [X] T204 Reject a mishap or injury `amount` whose notation the walk cannot evaluate: `src/cetools/chargen.py:527` validates `_valid_amount_text` with its own regex (`chargen.py:27`'s `_AMOUNT_DICE`) rather than through `_check_dice`, so `"d66"` passes load and reaches `src/cetools/generator.py:199`, where `count, sides, modifier = parse_notation(body)` unpacks the `None` that `parse_notation` answers `d66` with. `tasks.py:15`'s `_check_dice` docstring names this exact trap — "accepting it would surface as a `TypeError` that no `CetoolsError` handler catches" — and every `roll` field in the package is guarded against it; the `amount` field is the one that is not. A mishap row given `amount = "d66"` makes `cetools validate` report `Rules data is valid.` and then raises an uncaught `TypeError: cannot unpack non-iterable NoneType object` on **22 of 300 seeds**. Route `_valid_amount_text` through `_check_dice`, which also closes `"0d6"` and `"1d0"` — both pass the regex and reach the walk as an undiagnosed `DiceError` — per FR-054, US4 acceptance scenario 4 and FR-019 (missing)
- [X] T205 Correct the aging-row contiguity sentence T186 added, which contradicts the example it points at: `contracts/data-files.md:327` reads "Gaps between the rest of the rows are permitted — **the worked example above has none**, but nothing requires it", while the worked example at `:300-320` ships rows `"-6"`, `"0"` and `"1+"`, a five-value gap from -5 to -1 — the same gap `CHANGELOG.md` correctly describes as "its own worked example is a gapped table". Used verbatim as an override the example validates clean and then fails **200 of 3,000 seeds** with `aging.toml: a throw modified to -3 falls in a gap no row covers`, so the contract hands a referee an example that cannot be run and a sentence asserting it can. T186's code fix is correct and stays; the work is the sentence and, if the example is meant to be runnable, its missing rows, per FR-013, FR-037 and T186's own recorded decision (contradicts)
- [X] T206 Add the changelog-structure guard T190 required and did not land: the prose half was done — the false "Nothing here changes the draw order" claim is gone from `CHANGELOG.md:35-43` and the eight mis-filed entries now sit under `### Breaking changes` — but the task's third clause, "add a guard so it stops drifting", was not, and `tests/guards/test_documented_version.py` still checks the version heading and nothing about section structure. `rg -i breaking tests/` finds nothing outside an unrelated comment. FR-056b makes the seed promise the project's statement to a referee quoting a seed to another referee, and the drift that made it false once is unguarded against making it false again, per FR-056b and the constitution's Development Workflow (missing)

---

## Phase 12: Convergence

The fifth convergence round, against the branch as Phase 11 left it. The whole suite is
green (`uv run pytest -q`: 1245 passed, 0 skipped, every `slow` sampled audit included), so
every item below is latent rather than a known failure. Every one was confirmed by running
the code: sampled populations of 3,000 to 20,000 seeds, override data sets built under a
scratch directory, a draw-counting `Roller` subclass that attributes every draw to the step
it landed in, and the command itself. The counts quoted are from those runs and are what a
fix should move.

**Every one of Phase 11's thirteen tasks was re-verified clause by clause and every clause
landed.** That check was run first and deliberately, because T206 exists only because T190's
third clause did not land; the pattern did not recur. This phase revisits none of them.

Two of the five dimensions swept came back with nothing, and both are recorded below as
closed rather than as unexamined, so a later round does not redo them.

The theme of what remains is narrow: **a die the walk drew and the record does not carry**.
T207 and T208 are the last two sites, and they are the same defect T183 fixed at six others.
Between them they account for every unrecorded draw in the walk except `_resolve_specialty`'s,
which T200 settled by correcting the comment rather than recording the dice. T209 is the
T180 / T199 shape once more, at the one remaining precondition that is decidable at load and
unchecked.

Deliberately **not** appended, so a later round does not rediscover and re-litigate them.
`_resolve_specialty`'s 44,865 unrecorded specialty dice per 10,000 characters: T200 offered
"either record the specialty dice or correct the comment" and the comment was corrected, so
the decision is made. The `tables.service` characteristic adjustment silently discarded under
`basic-training.first-career-all = true` (0 of 245 first-career Navy steps apply a `SOC +3`
entry that validates clean, against 64 of 360 with the flag off): T200 directed keeping the
filter on the first-career branch, reasoning from FR-007a's "every entry **at level zero**",
which an adjustment has no form of. The always-empty `mustering-out` step appended after the
benefits of its own service (`generator.py:1467-1476`, 100% of 16,419 instances): nothing in
the spec, `data-model.md` or the contracts pins its position or its content. `aging.modifier`,
a required field with exactly one legal value: real tension with
`contracts/data-files.md:546`, but documentation phrasing rather than a defect.
`benefits.toml`'s items and the name tables' `source` and `people` fields, all inert by
design: they are a validation whitelist and a reviewer's record respectively, and no
requirement asks the walk to read them. `max(1, background_skills_base + edu_dm)`
(`generator.py:389`), a floor held in engine code but documented at
`contracts/data-files.md:543` and unreachable from shipped data. `--name` accepting a
carriage return where it refuses a tab and a newline: a supplied name forces `count == 1`, so
it cannot forge FR-048a's separator, and refusing it widens into `\v`, `\f` and `U+2028` on
no requirement's authority. A score inflated past the pseudo-hex top by rank bonuses or
benefits rather than by the roll: not decidable at load, and `registries.py:64-72` with T175
already settle its reporting. `roll_name`, `Name`, `character_seed`, `derive_seed` and
`resolve_seed` importable but absent from `__all__`: FR-055 binds this feature's
capabilities, and all six are exported and were exercised programmatically. And the Phase 10
and Phase 11 declines all stand, `characteristics.<CODE>.label` among them.

Separately checked and clean, so no task is owed for them, and a later round can start from
here. **The whole of the names, licensing, seeds, batch, CLI and rendering surface**:
FR-042 through FR-043j, FR-047 through FR-047d, FR-048a, FR-050, FR-050a, FR-051, FR-052
through FR-055, FR-056a, FR-057, FR-058, SC-015, SC-015a, SC-015b, SC-018 and SC-019, each
exercised against override data sets rather than read, including an eighth surname region
taking an equal share on 5 entries against Europe's 105, the FR-043i floors correctly not
imposed on an override, every FR-054 failure path writing zero bytes to standard output, and
byte-identical sheets under four `LC_ALL` values over data containing non-ASCII names.
**Every rules constant FR-038 enumerates**, all 23, traced to a data field with a live read
site; all 36 `ChargenParameters` attributes proved to change output under an override; the
only integer literal in `generator.py` other than `0`, `1` and `-1` is the `100` that is
`paid-percent`'s own unit. **The record's arithmetic and its replay**: `total == sum(faces) +
modifiers` holds on every throw-carrying step over 10,000 characters, and replaying every
history effect reproduces every sheet's characteristics, skills, funds, debt, pension and
benefits exactly, 0 failures. **Seven separate ordering invariants**, 0 violations over 3,000
characters. **All 25 declared `HistoryStep` kinds and all 7 declared `StepEffect` kinds are
reachable**, so T151's concern is fully closed and no rendering case is dead. **No uncaught
traceback is producible from any data set `validate` accepts**: roughly 19,000 walks over
roughly 1,000 validate-clean override sets, every failure a `CetoolsError` with exit 1 and an
empty standard output. **FR-056 determinism** across four `PYTHONHASHSEED` values in separate
processes, for `--full` and `--json` alike. **FR-008's term order, FR-008a's natural failure,
FR-018's single-career pension** (0 violations in 5,000), **FR-020's four consequences,
FR-023's single fixed path, FR-026's non-negativity** (0 in 4,000), and **FR-032 and FR-033's
shipped coverage**.

One methodological note worth carrying forward, because it produced a false reading before it
was caught: the three `medical.crisis-*` parameters look inert at 3,000 seeds only because no
crisis fires in that sample. Anything crisis-touching needs 5,000 seeds or more to be
conclusive.

The standing rules at the top of this file still apply: test-first, one commit per logical
unit, structural before behavioral, a CHANGELOG entry for every user-visible change. On the
**Breaking changes** note FR-056b requires, stated precisely rather than blanket-claimed:
**no task here changes what a seed produces.** T207 and T208 record dice the walk already
draws, so the draw sequence is untouched and only the history record and the emitted document
move; each needs a note saying which. **T209 changes no shipped behavior at all**, the
shipped `roll = "2d6"` already satisfying the rule it adds, and must not be flagged as
breaking. No hand-constructed `npc_*.txt` golden carries a `career-selected` or an `aging`
step, so none of them moves; `tests/contract/test_npc_json.py` and `tests/unit/test_generator.py`
move with T207 and T208, and `contracts/cli.md:184` moves with T207.

- [X] T207 Record the die that chose the career on the `career-selected` step, and stop the draft substitution sharing that step's shape: `_select_career` throws `self.roller.die(len(available))` at `src/cetools/generator.py:458` while `enter_career` records the step with `throw=None` at `:518-527`, which `data-model.md:119` defines as "`None` for a step that **decided rather than threw**" and whose `selected` column `data-model.md:120` defines as "what was chosen **at random**". All 16,419 selection draws over 10,000 characters are unrecorded, 100% of them, so "why did this person end up a Drifter" is unanswerable from the record and an eligibility defect inside `die(len(available))` is invisible; `_draft` (`:498-513`) records its own throw correctly, so the two entry routes are held to different standards. This is T183's defect at a site T183 did not enumerate. Compounding it, T201's substitution step (`:552-563`) reuses the same `career-selected` kind and produces a byte-identical record (`throw=None`, `career=""`, `term=0`, `effects=()`), so **104 of 3,000 characters** carry more `career-selected` steps than careers entered (seeds 15, 35, 55, 58, 91), a consumer counting selection attempts double-counts, and the two are separable today only by adjacency to the `draft` step, which FR-030a's "separately addressable parts" rules out. Recording the selection throw separates them by shape; decide whether that suffices or whether the substitution needs a kind of its own, extend the closed set in `src/cetools/character.py:21-49` and `data-model.md:123` if it does, and correct `contracts/cli.md:184`, whose own worked excerpt prints the throwless line, per FR-030, FR-030a, FR-015a and `data-model.md:119` (partial)
- [X] T208 Record the dice that chose which characteristics an aging effect reduced: `_apply_aging_if_due` draws `self.roller.die(len(remaining))` once per chosen characteristic at `src/cetools/generator.py:1215` and builds its `StepThrow` at `:1234-1241` from the aging-table faces alone, while `_apply_class_effect`, which performs the identical selection for mishaps and injuries, concatenates them as `tuple(choice_faces) + tuple(amount_faces)` at `:966-980`. Two sites do one job and one of them records it. **1,602 selection draws over 10,000 characters go unrecorded, across 100% of the aging steps that reduce anything** (1,235 of 3,934; the `1+` row reduces nothing and draws nothing), and the consequence is that the record cannot say what was reduced: over 3,000 seeds **50 of the 52 distinct recorded aging throws map to more than one outcome**, the worst of them to eight. `cetools npc --seed 6 --json` records `faces=[1, 1], modifiers=[Terms served -5], total=-3` against an effect of `STR -2`, and the identical record elsewhere in the population yields DEX, END, INT, EDU and SOC instead; `--full` renders it `1, 1 (sum 2) Terms served -5 = -3   STR -2`, with nothing saying why STR. Note that this step's throw carries `total = modified` against the aging table, so the choice faces cannot simply be appended without breaking the `total == sum(faces) + the modifier values` invariant `contracts/json-output.md:187` states and T196 made checkable: give the selection its own step or its own recorded parts, and record which in `data-model.md`, per FR-030, FR-030a and `contracts/json-output.md:187` (partial)
- [X] T209 Validate that the characteristics roll cannot produce a score the characteristics registry does not cover: `[characteristics] roll` is parsed in `src/cetools/chargen.py` and rolled at `src/cetools/generator.py:361`, and the cross-file section at `src/cetools/rules.py:815` onward, which now checks the draft rows, the medical tiers, the commissioned ladders, the characteristic classes, T166's two career flags, T180's band coverage, T194's background-skill characteristic and T199's band ordering, has no rule relating the two. Both ends are statically decidable: `parse_notation` yields `(count, sides, modifier)`, so the roll spans `count + modifier` through `count * sides + modifier`, and the registry declares `pseudo_hex_minimum` and `pseudo_hex`. `src/cetools/registries.py:69-71` states the invariant in its own docstring, "whose declared range covers every score a reduction can floor at or a throw can produce", and nothing enforces it. An override changing that one field to `roll = "2d6-3"` makes `cetools validate` report `Rules data is valid.` and exit 0, then makes **21 of 200 seeds** fail while the other 179 produce a sheet: 17 with `characteristic must be non-negative, got -1`, a `TaskError` raised at `registries.py:56-58` and phrased for `cetools check --characteristic`, naming neither the file nor the field the author edited, and 4 with `characteristic score -1 is outside the declared pseudo-hex range 0-33`. `3d6-10` fails 186 of 200 and `1d6+28` fails 135 of 200 against the top of the range. Exit code and empty standard output already hold, so this is US4 acceptance scenario 4's other half: the run must fail **before any character is produced**, naming what could not be resolved, rather than per seed after most seeds have already succeeded. Scope the rule to the decidable roll-versus-registry relation and leave run-time inflation past the top alone, which is not decidable at load and which `registries.py:64-72` and T175 already settle, per US4 acceptance scenario 4, FR-039 and FR-054 (missing)

---

## Phase 13: Convergence

The sixth convergence round, against the branch as Phase 12 left it. The whole suite is green
(`uv run pytest -q`: 1250 passed, 0 skipped, every `slow` sampled audit included), so both
items below are latent rather than known failures. Each was confirmed by running the code —
sampled populations of 3,000 to 60,000 seeds, roughly 1,650 override data sets built under a
scratch directory, and the command itself — and the counts quoted are from those runs and are
what a fix should move.

**Phase 12's three tasks were re-verified clause by clause and every clause landed**, the
"decide which and record it in `<doc>`" clauses included: T207's decision to separate the draft
substitution by shape rather than by a new kind is recorded at `data-model.md:138-145`, T208's
split representation at `data-model.md:146-156`, and T209's rule at `contracts/data-files.md:543`.
That check was run first and deliberately, for the reason Phase 12 gave — T206 exists only
because T190's third clause did not land — and the pattern has now failed to recur twice.

This round is the first to return **almost nothing**, and the negative results are the
substance of it. Recorded so a later round starts from here rather than redoing them.

- **The career and term machinery is clean.** FR-004 through FR-015a, thirteen requirements,
  0 violations: 8,288 entry episodes and 3,099 failed qualifications over 5,000 seeds (FR-004),
  2,029 draft reads against the table's own row order (FR-005), 7,421 terms against FR-009's
  skill-roll arithmetic, 0 first-term commission attempts among 202 drafted entries (FR-012a),
  an exact age replay including mishap `years` (FR-013), and 163 FR-015a substitutions. Six
  override sets confirmed the constants are read rather than held: `drafted-first-term-barred`,
  `terms.cap`, `draft-entries-allowed`, `first-career-all`, `subsequent-career-count`, and a
  `throws.promotion` added to Drifter, which drops its base skill rolls from two to one.
- **The consequence chain is clean.** Replaying every history effect reproduces every sheet's
  funds, debt, pension, characteristics and benefits over **20,000 seeds, 0 failures**, with
  funds never negative at any point. FR-016 and FR-017 hold across roughly 33,000 career
  services (2,855 material rank DMs and 937 retired-cash DMs, each matching exactly); every one
  of 4,505 characteristic reductions is billed (FR-024) and every `owed` figure recomputes from
  the career's declared tier (FR-025); FR-021's crises were pushed to 60,000 seeds to be
  conclusive, per Phase 12's own methodological note, and all 240 hold. Seventeen override sets
  proved every constant in this slice moves output — none inert.
- **No uncaught traceback is producible from any data set `validate` accepts**, re-confirmed
  independently of Phases 11 and 12 and at larger scale: roughly 1,600 randomized validating
  override sets plus 50 hand-built adversarial ones, about 75,000 walks with `--full` rendering
  and `--json` serialization inside the loop, zero non-`CetoolsError` exceptions.
- **Every field the four schema parsers accept has a live read site**, enumerated exhaustively
  rather than sampled; the only inert ones are the three already declined. Phase 12's two
  headline claims both survive independent re-verification, all 36 `ChargenParameters`
  attributes included — `medical.crisis-restores-to`, which looks inert below 5,000 seeds,
  changes all five fully-paid crisis sheets in 20,000.
- **The success criteria have evidence that can fail**, SC-002 through SC-020 walked one at a
  time against the test that claims each, with T152's, T156's, T158's, T172's, T176's, T177's
  and T193's fixes re-checked at their new strength. One exception, which is T211 below.

Deliberately **not** appended, so a later round does not rediscover and re-litigate them. A
mishap or injury `amount` carrying a notation modifier (`"-1d6+3"`) validates clean, is honored
on the sheet, and is not itemized in the step's `modifiers`: unlike T198's site the applied
magnitude is already addressable as the step's own `characteristic` effect, the
`total == sum(faces) + the modifier values` invariant still holds, no shipped seed changes, and
`contracts/data-files.md:376` records no opposing remedy for `amount` as
`contracts/data-files.md:251` does for `roll`. `medical.crisis-restores-to = 99` is decidable at
load and fails 2 of 6,000 seeds, but it is the pseudo-hex-inflation shape Phase 12 declined and
T209 explicitly scoped out, and it already fails as a `CetoolsError` naming the score and the
range. A duplicate `rank` in `mustering-out.rank-benefits` and a `commissioned` ladder in a
career declaring no `throws.commission` are both dead data that validates clean, but neither is
a plausible referee edit and no requirement binds either direction; a duplicate career `name`
across two files is likewise unvalidated and harmless. `subsequent-career-all` does not exist,
but both constants FR-007a's normative sentence names are in data, so that is rationale drift
rather than a violated MUST. A mishap-ended term takes no skill roll, which FR-020 does not
enumerate but FR-008's stated term order and the spec's own edge case both require. And every
Phase 10, 11 and 12 decline stands.

The standing rules at the top of this file still apply: test-first, one commit per logical unit,
structural before behavioral, a CHANGELOG entry for every user-visible change. On the
**Breaking changes** note FR-056b requires: **neither task here changes what a seed produces,
and neither may be flagged as breaking.** The shipped `aging.toml` already satisfies T210's rule
— eight rows rising to one unbounded row at the top, no overlap and nothing above it — and T211
is test evidence only. No hand-constructed golden moves;
`tests/integration/test_validation_categories.py` and `tests/unit/test_chargen.py` move with
T210, and `tests/integration/test_npc_sample.py` with T211.

- [X] T210 Reject an aging table whose rows overlap, or whose unbounded row does not hold the highest minimum — the one positional range table in the package that gets neither check: `src/cetools/chargen.py:445-455` counts unbounded rows and nothing else, then sorts stably by `minimum` at `:459`, and `src/cetools/rules.py:929-970` carries the gap, overlap and above-the-unbounded rules for `characteristics.modifier-dms` while `aging.rows` reaches `rules.py` only at `:992-1000`, for its class names; `src/cetools/generator.py:1188-1196` then takes the first row whose range contains the modified total, so a tie or an overlap is resolved by nothing but TOML file order. This is the T180 / T199 shape at the file FR-037 names as the whole reason overrides are per-kind ("a referee with a house aging table MUST NOT have to restate the draft table"). An override changing `range = "1+"` to `"-1+"` — one character, and the natural way to say "aging stops hurting at -1" — makes `cetools validate` report `Rules data is valid.` and exit 0, then leaves the `"-1"` row overlapping the unbounded row and the `"0"` row sorted above it and therefore dead: over 3,000 seeds **148 of 1,215 aging row-lookups read a row the author did not write**, **114 reduce a physical characteristic on a total of -1 that the author's own row declares harmless**, and **132 of 3,000 sheets differ from packaged, not one of them in the direction the edit asked for**. `cetools npc --seed 6 --full --rules-data <dir>` shows it as `Terms served -7 = -1   END -1`. No error is raised anywhere. Add the rule beside the band check in `rules.py`, worded as `chargen.py:452`'s own `expected` string already promises — "exactly one row unbounded **above**", which the parser only counts — and record the decision in `contracts/data-files.md:328`, which settles gaps today and says nothing about either overlap or ordering, per FR-013, FR-037, US4 acceptance scenario 4 and Constitution V (missing)
- [X] T211 Make SC-004's skill clause assert what the criterion states: `tests/integration/test_npc_sample.py:190-196` checks only `step.career in served | {""}`, a career-label membership test, where SC-004 requires every skill to trace "to a table the character **could reach in a term they served** or to a grant they were entitled to". T152 enumerated four additions and three landed strong — the age replay at `:136-150` reads how each term ended, the benefit rolls at `:152-173` read the rank as well as the terms, and the pension at `:175-186` reads a single career's terms — while the fourth landed as a near-tautology. With `step.career` still correct it cannot catch a skill drawn from a table belonging to another career, a table the character's characteristics gate out being drawn anyway, a grant in a term outside the terms served, or a `rank-bonus` skill no rank of that career's ladders declares; `_eligible_tables` is unit-tested in isolation at `tests/unit/test_generator.py:318`, but nothing checks that what the walk actually granted came from an eligible table, and `rg 'step\.term' tests/` finds no comparison against a service's terms anywhere. All four stronger properties hold on the shipped data today, 0 mismatches over 3,000 seeds, so this is missing evidence rather than wrong behavior — which is the same reason T152, T153, T156, T158, T172, T176, T177 and T193 were appended. Assert for a `skill-roll` step that the granted skill is an entry of the table its own `selected` names, that the table was gate-eligible for that character, that `step.term` lies within the service's terms, and that a `rank-bonus` skill matches a bonus the reached ladder rank declares, per SC-004 (partial)
