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

- [ ] T004 [P] Hoist `DESIGNATION` and `_uncovered` into `tests/conftest.py` (keeping the two-adjacent-bytes-literals form) and import them from there in `tests/unit/test_licensing.py` and `tests/guards/test_packaging.py` (structural, research R9)
- [ ] T005 [P] Add an `indent` parameter to `render._provenance_lines` in `src/cetools/render.py` and pass the existing indentation from both current call sites (structural)
- [ ] T006 Add a keyword-only `full: bool = False` to `as_text` in `src/cetools/render.py`; every existing registration and the dispatch fallback accept it and raise `CetoolsError` when it is true, with a test for each in `tests/unit/test_render.py` (structural)
- [ ] T007 Convert the per-kind blocks in `rules._validate` to a `kind -> parse function` mapping and one loop in `src/cetools/rules.py`, before the kind count goes from four to eleven (structural)
- [ ] T008 [P] Rename `tables.advanced` to `tables.specialist` in `src/cetools/careers.py`, `src/cetools/data/careers/navy.toml`, and `tests/unit/test_careers.py` (structural; nothing reads it yet)
- [ ] T009 Move `Band` and the characteristic modifier bands from `src/cetools/tasks.py` to `src/cetools/registries.py`: `TaskParameters` loses `characteristic_bands` and `characteristic_dm`, `CharacteristicRegistry` gains `bands` and `characteristic_dm`, `check` reads `rules.characteristics.characteristic_dm(...)`, `src/cetools/data/tasks.toml` drops `[characteristic-dms]` and rises to `schema-version = 2`, `src/cetools/data/registries/characteristics.toml` gains `[modifier-dms]` and rises to `schema-version = 2`, and `src/cetools/__init__.py` re-exports `Band` from its new home (structural, **breaking library change**, FR-039)
- [ ] T010 Verify SC-014: assert in `tests/integration/test_golden.py` and `tests/contract/test_json_contract.py` that every committed `tests/golden/check_*.txt` and every existing JSON fixture is byte-identical after T009, with no fixture regenerated
- [ ] T011 Confirm the module-level `_PARAMETERS = load_rules().task_parameters` in `tests/property/test_invariants.py` still reads only `difficulty_dms` after T009, and record the check rather than assuming it

**Checkpoint**: structural work complete, suite green, no output changed.

### Phase 2B: Seeds and the characteristics registry

- [ ] T012 [P] [TEST] Write `tests/unit/test_seeds.py` cases for `derive_seed`: it folds a seed and parts through the existing blake2b digest, returns a value `resolve_seed` accepts, round-trips as a decimal string, and is stable across runs
- [ ] T013 Implement `derive_seed(seed: int, *parts: int | str) -> int` in `src/cetools/seeds.py`, reusing the existing `rng_seed` fold rather than introducing a second digest (research R2), unexported
- [ ] T014 [TEST] Extend `tests/unit/test_registries.py` for `CharacteristicRegistry`: `classes` mapping, `pseudo_hex_minimum`, `pseudo_hex`, `symbol(score)` raising `RulesDataError` naming the score and the range when outside it, and `floor()` returning `pseudo_hex_minimum`
- [ ] T015 Implement `classes`, `pseudo_hex_minimum`, `pseudo_hex`, `symbol()`, and `floor()` on `CharacteristicRegistry` in `src/cetools/registries.py`, and parse `characteristics.<CODE>.label` / `.class` and `[pseudo-hex]` at schema version 2 (FR-039, research R12, R13)

### Phase 2C: The universal chargen tables (`chargen.py`)

- [ ] T016 [TEST] Write `tests/unit/test_chargen.py` cases for `DraftTable`: `roll` rejects the `d66` literal, `careers` is non-empty, row order is preserved (FR-005)
- [ ] T017 Implement `DraftTable` and its parse function in `src/cetools/chargen.py`
- [ ] T018 [P] [TEST] Add `tests/unit/test_chargen.py` cases for `AgingTable`, `AgingRow`, and `ClassEffect`: `range` accepts `N`, `N-M`, `N+` including negatives, exactly one row unbounded above, the lowest row is a floor, `effects` may be empty, `modifier` accepts only `terms-served`
- [ ] T019 Implement `AgingTable`, `AgingRow`, and `ClassEffect` with their parse functions in `src/cetools/chargen.py`
- [ ] T020 [P] [TEST] Add `tests/unit/test_chargen.py` cases for `MishapTable`, `MishapRow`, `InjuryRow`, and `MishapEffect`: the closed `kind` set, `amount` accepting both `"-1d6"` and `"10000"` as text, and `injuries` reachable only from a `roll-injury` effect
- [ ] T021 Implement `MishapTable`, `MishapRow`, `InjuryRow`, and `MishapEffect` with their parse functions in `src/cetools/chargen.py`
- [ ] T022 [P] [TEST] Add `tests/unit/test_chargen.py` cases for `BackgroundSkills`: three non-empty notation lists in skill-table context, duplicates across `law-level` and `trade-code` preserved as meaningful weighting (research R5)
- [ ] T023 Implement `BackgroundSkills` and its parse function in `src/cetools/chargen.py`
- [ ] T024 [P] [TEST] Add `tests/unit/test_chargen.py` cases for `MedicalTiers` and `MedicalThreshold`: distinct tier names, thresholds sorted highest-target-first, `paid-percent` in 0–100, a total below every threshold paying nothing, `rank-dm` declared not assumed
- [ ] T025 Implement `MedicalTiers` and `MedicalThreshold` with their parse function in `src/cetools/chargen.py`
- [ ] T026 [TEST] Add `tests/unit/test_chargen.py` cases for `ChargenParameters`: every key in `contracts/data-files.md` is required, every table is a closed key set, and a misspelled key is reported rather than defaulted
- [ ] T027 Implement `ChargenParameters` in `src/cetools/chargen.py`, exposing every scalar as a named attribute so a misspelling is an `AttributeError` at import rather than a `KeyError` mid-walk (FR-038)

### Phase 2D: The name table schemas and the name roll (`names.py`)

This phase is the code that reads a name table. The shipped tables themselves are Phase 2I,
behind the licensing work of Phase 2H.

- [ ] T028 [TEST] Write `tests/unit/test_names.py` schema cases: `GivenNameTable` and `SurnameTable` key sets are closed so a `gender` key is rejected (FR-043b), `source` is required and non-empty (FR-043e), an empty `names` array is rejected naming the file (FR-043h), `SurnameEntry.people` is optional (FR-043d)
- [ ] T029 Implement `GivenNameTable`, `SurnameTable`, `SurnameEntry`, and their parse functions in `src/cetools/names.py`
- [ ] T030 [TEST] Add `tests/unit/test_names.py` cases for `roll_name`: a region is selected uniformly over the tables in force, then a surname within it, then a given name independently; `Name.full` is `f"{given} {surname}"` and is never reordered (FR-043f, FR-043g, FR-047a)
- [ ] T031 Implement `Name` and `roll_name(roller, given, surnames)` in `src/cetools/names.py`, unexported (contracts/library-api.md)

### Phase 2E: Career schema v2

- [ ] T032 [TEST] Extend `tests/unit/test_careers.py` for schema version 2: `medical-tier` required, `always-available` and `re-enterable` defaulting to `false`, `throws.promotion` optional, `tables.advanced-education` required with its own `requires` gate, and `ladders[].role` required as `"entry"` or `"commissioned"` with exactly one `entry` and at most one `commissioned`
- [ ] T033 Implement the v2 changes on `CareerDefinition` and its parse function in `src/cetools/careers.py`, raising the declared schema version (FR-034, FR-035, FR-036, FR-007b)

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

- [ ] T056 [TEST] Add `tests/unit/test_licensing.py` cases for the GPL-3.0 designation constant: a shipped data file carries exactly one designation, both is a failure, neither is a failure, asserted against planted files so the cases stand before any name table exists (FR-042, SC-015)
- [ ] T057 Narrow the Section 15 game-data notice in `LICENSE-OGL.txt` from the data root to the OGC subtrees (`registries/`, `chargen/`, `careers/`, and `tasks.toml`), keeping the `_NOTICE_PATH` parenthesized-path and `_NOTICE_SUFFIX` "every `.toml` file" shapes parseable, and update `SECTION_15_NOTICES[-1]` in `tests/conftest.py` in the same commit. The narrowed wording names no path under `names/`, so it is already correct when that directory arrives (research R9)
- [ ] T058 Add the second designation constant to `tests/conftest.py`, assembled from two adjacent bytes literals so the test source does not designate itself
- [ ] T059 Turn `_assert_shipped_rules_data` in `tests/guards/test_packaging.py` into an exactly-one-of-two check over every `.toml` in the wheel and the sdist (FR-042a). **This is the task the name tables wait on.**
- [ ] T060 Extend `_uncovered` in `tests/conftest.py` with its mirror: every GPL-designated file must be claimed by neither the notice's paths nor its suffix, so a name table drifting into an OGC directory fails
- [ ] T061 Add the SC-015a fail-ability siblings to `tests/unit/test_licensing.py`, extending `test_the_coverage_check_sees_a_designated_file_the_old_scan_missed`: an OGC file planted outside the covered subtrees must fail the coverage check, and a GPL-designated file planted inside them must fail the mirror, each unlinked in a `finally`
- [ ] T062 [P] Update the licensing section of `README.md` and the "Licensing, which is not optional" section of `CONTRIBUTING.md`, both of which state that every `.toml` under `src/cetools/data/` is OGC and both of which become false the moment the first name table lands — so they change **before** it does, not after

**Checkpoint**: the guards distinguish the two designations, the notice covers the OGC
subtrees and nothing else, and the suite is green with the data set still wholly OGC.

### Phase 2I: The shipped name tables — the first data that is not Open Game Content

Depends on Phase 2H. These are the files the widened checks were widened for.

- [ ] T063 [P] Author `src/cetools/data/names/given-names.toml` (GPL-3.0 designation, `source` recorded, at least sixty gender-neutral entries — FR-043b, FR-043e, FR-043i)
- [ ] T064 [P] Author `src/cetools/data/names/surnames-africa.toml` (GPL-3.0 designation, `region`, `source`, at least forty entries)
- [ ] T065 [P] Author `src/cetools/data/names/surnames-asia.toml` (same shape)
- [ ] T066 [P] Author `src/cetools/data/names/surnames-central-america.toml` (same shape)
- [ ] T067 [P] Author `src/cetools/data/names/surnames-europe.toml` (same shape)
- [ ] T068 [P] Author `src/cetools/data/names/surnames-north-america.toml` (same shape)
- [ ] T069 [P] Author `src/cetools/data/names/surnames-south-america.toml` (same shape)
- [ ] T070 [P] Author `src/cetools/data/names/surnames-indigenous.toml` (GPL-3.0 designation; every entry carries `people` — FR-043d)
- [ ] T071 Verify the shipped surname tables differ in size by enough that a weighting taken over names rather than over regions would put at least one region outside SC-019's band, and record the sizes in `tests/unit/test_names.py`
- [ ] T072 [P] Add `tests/unit/test_name_tables.py` for SC-015b: every name table records a `source`, every indigenous-peoples entry names its people, no name table carries a gender field, the given names table holds ≥60 entries and each surname table ≥40
- [ ] T073 Extend `tests/integration/test_validate_cli.py` and `tests/guards/test_data_layout.py` for twenty-six files, unique basenames tree-wide, and the two new subdirectories traversing without `__init__.py`

### Phase 2J: The produced value (`character.py`)

- [ ] T074 [TEST] Write `tests/unit/test_character.py` for the seven types: field names and order per `contracts/library-api.md`, frozen and slotted, `HistoryStep.kind` and `StepEffect.kind` closed sets, `StepThrow.total == sum(faces) + modifiers`, a table-reading throw carrying `target = 0` and `success = True`. The closed `StepEffect.kind` set is where FR-028 is enforced: the eleven kinds are exactly the consequences the chain carries, and a twelfth would be the chain running past the numbers on the sheet, so the closed-set assertion is what makes FR-028 fail rather than merely be intended
- [ ] T075 Implement `Character`, `CharacterSkill`, `CareerService`, `HistoryStep`, `StepThrow`, `StepEffect`, and `CharacterBatch` in `src/cetools/character.py`

### Phase 2K: Public surface and guards

- [ ] T076 Extend the contract parser in `tests/unit/test_library_api.py` to read `specs/003-npc-generator/contracts/library-api.md` as a third contract, taking `## Public surface added` and `## Public surface removed` from it — **before** any export lands, or the suite fails with a set difference that does not say why
- [ ] T077 Add the new exports to `src/cetools/__init__.py` per `contracts/library-api.md`, keeping `Band` re-exported from `registries`
- [ ] T078 [P] Add a no-`locale` guard to `tests/guards/` asserting that nothing under `src/` imports `locale`, which is what makes SC-012 unfalsifiable by omission (research R8)
- [ ] T079 [P] Add `generate_character` and `generate_batch` to the manual library list in `tests/guards/test_seed_contract.py`, so a stray `random` call in the walk is guarded

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

- [ ] T080 [P] [US1] [TEST] Write `tests/unit/test_generator.py` cases for the opening of the walk: characteristics rolled one per registry entry (FR-002), background skill count `base + EDU DM` floored at one with one background skill meaning one homeworld skill (FR-003), and the homeworld draw uniform over the concatenated law-level and trade-code lists
- [ ] T081 [P] [US1] [TEST] Add `tests/unit/test_generator.py` cases for career entry: random selection over careers in force, qualification failure routing to the draft up to `draft-entries-allowed` and to the always-available career beyond it (FR-004), the draft resolving positionally over the Draft table (FR-005), Drifter thrown for when selected and automatic as fallback (FR-006), basic training granting the whole service table on a first career and `subsequent-career-count` entries later (FR-007a), and the rank-zero bonus granted on entry (FR-007)
- [ ] T082 [P] [US1] [TEST] Add `tests/unit/test_generator.py` cases for the term loop in FR-008's order: survival with `natural-failure` always failing (FR-008a), commission attempted once per career and barred in a drafted character's first term (FR-012, FR-012a), a commission moving the character to the commissioned ladder at its lowest rank with that rank's bonus granted (FR-007b), advancement, skill acquisition, and aging
- [ ] T083 [P] [US1] [TEST] Add `tests/unit/test_generator.py` cases for skill rolls: one per term, two in a career declaring neither throw, plus `on-commission` and `on-advancement` extras (FR-009); selection over the **eligible** tables only, a characteristic gate excluding rather than failing (FR-010); and the cascade rule choosing a permitted specialty and recording it (FR-011)
- [ ] T084 [P] [US1] [TEST] Add `tests/unit/test_generator.py` cases for the always-living guarantee: a failed survival throw resolving on the Survival Mishaps table without death (FR-019, FR-022); a mishap-ended term costing two years, counting toward the cap and the aging modifier, and forfeiting that term's benefit roll, all three (FR-020); a mishap deferring to the injury table recorded as a step of its own (FR-024); and no path that discards and re-rolls (FR-023)
- [ ] T085 [P] [US1] [TEST] Add `tests/unit/test_generator.py` cases for characteristic floors: a reduction clamping at `CharacteristicRegistry.floor()`, the history recording both the reduction called for and the amount applied when they differ, and a score above the declared range raising `RulesDataError` naming the score and the range (research R13)
- [ ] T086 [P] [US1] [TEST] Add `tests/unit/test_generator.py` cases for career end and multi-career: continuation decided by throw, re-enlistment still applying, the cap forcing mustering out regardless (FR-014); an accumulating qualification penalty counting careers **entered**; a career already entered unavailable again except Drifter (FR-015)
- [ ] T087 [P] [US1] [TEST] Add `tests/unit/test_generator.py` cases for mustering out: benefit count from terms and rank with the rank bonus **not** cumulative, each roll taken as cash or as material by the `cash-choice` throw read from data rather than by arithmetic the engine holds, the cash-roll cap after which the throw is not made at all, the material rank modifier (FR-016), the retired cash modifier applying exactly when the pension was qualified for (FR-017), and a pension earned in a **single** career with three terms in each of two careers paying nothing (FR-018)
- [ ] T088 [P] [US1] [TEST] Add `tests/unit/test_generator.py` cases for debts: an aging crisis becoming a debt of throw times multiplier, settling it restoring every covered characteristic to `crisis-restores-to` and leaving them floored when unsettled (FR-021); medical bills from the career's tier with the character owing the remainder (FR-025); debts settling in the order they arose with a partly covered bill restoring points in an order the walk decides and records, funds never negative (FR-025a, FR-026)
- [ ] T089 [P] [US1] [TEST] Write `tests/unit/test_render_character.py` cases for the Universal Character Format per `contracts/cli.md`: four lines, exactly one tab between fields, the title-space-name rule with no leading separator when untitled, the pseudo-hex profile in registry order, `Age N`, `Name (N terms)` comma separated with singular at one, `Cr` with thousands separators, `Name-Level` skills including level zero sorted by `(casefold, codepoint)`, a cascade specialization written `Gun Combat (Slug Rifle)-1`, benefit items with repeats collapsed to `Name (x2)` and the line omitted when there are none, and the species-traits line never emitted (FR-044, FR-044a, FR-045, FR-046)
- [ ] T090 [P] [US1] [TEST] Add `tests/unit/test_render_character.py` cases for FR-047c: a character titled by an earlier career and untitled by a later one keeps the earlier title, and no two ladders are ever compared. Add the FR-048 case beside it: the only title any rendering may write is a rank title from a ladder, so a career granting a noble title renders none of it, on the name line or anywhere else. The assertion is worth committing even though no shipped career can produce one, because FR-048 is a rule about the renderer rather than about the shipped data, and an override could supply what the shipped data cannot
- [ ] T091 [US1] [TEST] Commit the six golden reference files SC-009 requires under `tests/golden/`, compared as bytes: `npc_titled.txt`, `npc_untitled.txt`, `npc_no_benefits.txt`, `npc_multi_career.txt`, `npc_titled_then_untitled.txt`, `npc_cascade.txt`. Each is rendered from a **hand-constructed `Character` literal** committed beside it in `tests/unit/test_render_character.py`, not from a seed: which character a seed produces is unknowable until the walk exists, and a golden captured from a finished implementation is not an expected value written before it (SC-016). Six constructed characters, six hand-authored byte strings, the renderer in between — that is what makes these references test-first and what makes SC-009's "byte-faithful" claim mean something
- [ ] T092 [P] [US1] [TEST] Write `tests/integration/test_npc_cli.py` cases for FR-051 and FR-054: standard output carries exactly the sheet, the seed and version and provenance go to standard error, a failed run writes nothing at all to standard output, and exit codes are 0, 1, and 2 as `contracts/cli.md` states
- [ ] T093 [P] [US1] [TEST] Write `tests/integration/test_npc_naming.py` for FR-047b and SC-018: the same seed generated with and without a supplied name compared field by field, differing in `name`, `given_name`, `surname`, `surname_region` and in nothing else — written before the walk exists, because the natural implementation fails exactly this and passes everything else (research R3)

- [ ] T093a [P] [US1] [TEST] Write `tests/integration/test_npc_determinism.py` for **SC-001**, which is Constitution Principle IV made concrete and the criterion the rest of this feature rests on: over several fixed seeds, generate each seed repeatedly and assert zero differences — every field of the `Character` compared one by one, and **both** rendered text forms compared as bytes rather than as text. Assert it across process boundaries as well, by running the command twice per seed and comparing stdout bytes, so that anything seeded per-process is caught rather than hidden by one process's stable hash. No other task performs this check: T110's property invariants assert bounds rather than equality, T123 compares batch positions against one another rather than a seed against itself, and T093 compares two runs that are meant to differ
- [ ] T093b [P] [US1] [TEST] Add a `tests/unit/test_generator_batch.py` case for **FR-053b reached from the library**: `generate_batch(None, rules)` produces a character and records the seed it drew, and that seed quoted back reproduces it. `resolve_seed(None)` already draws 64 bits from `secrets` and `generate_batch` already accepts `int | str | None`, so the capability belongs to the library; FR-055 and SC-017 require it reachable without the command line, and a second draw implemented in `cli.py` would be the CLI-only rule FR-053a was rewritten to avoid

### Implementation for User Story 1

- [ ] T094 [US1] Implement the walk's opening in `src/cetools/generator.py`: `generate_character(roller, rules, *, name=None)`, characteristics, background skills, and the name drawn from `Roller(derive_seed(roller.seed, "name"))` which the walk's own roller never touches (research R1, R3)
- [ ] T095 [US1] Implement career selection, qualification, draft routing, the always-available fallback, basic training, and the rank-zero bonus in `src/cetools/generator.py`
- [ ] T096 [US1] Implement the term loop in `src/cetools/generator.py`: survival, commission, advancement, skill acquisition, aging, in FR-008's order, reading as a generator of history steps
- [ ] T097 [US1] Implement skill acquisition in `src/cetools/generator.py`: eligible-table selection, the cascade choice, and the roll counts including the commission and advancement extras
- [ ] T098 [US1] Implement mishaps, injuries, characteristic-class effects, and the floor clamp in `src/cetools/generator.py`
- [ ] T099 [US1] Implement continuation, re-enlistment, the term cap, the accumulating qualification penalty, and multi-career selection in `src/cetools/generator.py`
- [ ] T100 [US1] Implement mustering out, benefit rolls, the pension, medical bills, and ordered debt settlement in `src/cetools/generator.py`, with the cash-against-material choice made by the `mustering-out.cash-choice` throw from `chargen-parameters.toml` — never by a coin flip the engine holds, which FR-038 forbids however evenly it falls
- [ ] T101 [US1] Record a `HistoryStep` for every decision and throw in the walk, with `StepThrow` itemizing modifiers and `StepEffect` naming what moved, so every number on the sheet traces to a step (FR-030, FR-030a) — in `src/cetools/generator.py`
- [ ] T102 [US1] Implement `generate_batch(seed, rules, *, count=1, name=None)` in `src/cetools/generator.py` with `character_seed(master, i)` returning `master` at position 0, and raise `CetoolsError` for `count < 1` and for a name with `count > 1` (research R2, FR-053a)
- [ ] T103 [US1] Register `as_text` for `Character` in `src/cetools/render.py` producing the Universal Character Format, with the `(casefold, codepoint)` sort key and no `locale` import anywhere
- [ ] T104 [US1] Register `as_text` for `CharacterBatch` in `src/cetools/render.py`, sheets separated by exactly one blank line and nothing else, a batch of one rendering byte-identically to its single character (FR-048a)
- [ ] T105 [US1] Add the `npc` command to `src/cetools/cli.py` with `--seed`, `--name`, and `--rules-data`, passing `--seed` straight through to `generate_batch` — including `None` when it is omitted, which `resolve_seed` already resolves by drawing 64 bits from `secrets`, so the CLI adds no draw of its own (FR-053b, T093b) — calling `generate_batch(..., count=1)`, writing the sheet to stdout and the seed/version/provenance to stderr via `_provenance_lines(indent=0)`, rejecting an empty or whitespace-only `--name` as a usage error (FR-053c)
- [ ] T106 [US1] Wire the golden comparisons in `tests/integration/test_golden.py` through `read_golden_bytes` for the six T091 references, comparing them against `as_text(character).encode("utf-8")` for the six constructed characters. Then add the one assertion that ties the command to them: for a generated seed, `stdout.encode("utf-8")` equals `as_text(character).encode("utf-8") + b"\n"` for the character that seed produces. That is a derivation the CLI owes the renderer, checkable without a committed expectation, and it is what keeps the byte goldens meaningful at the command line without pretending a captured sheet was authored in advance
- [ ] T107 [P] [US1] Add the SC-003/SC-004 sampled audit in `tests/integration/test_npc_sample.py`, marked `slow`: one thousand seeds, none excluded, every one alive and complete, with the consistency audit reading the character's own fields — age against terms and how each ended, every rank on a ladder of a career joined, benefit rolls against terms and rank, a pension against a single career's terms, funds non-negative, no consequence no step produced
- [ ] T108 [P] [US1] Add the SC-006/SC-007/SC-008 coverage assertions to `tests/integration/test_npc_sample.py`: at least five distinct term counts with no more than a quarter at `terms.cap` **read from the loaded chargen parameters, never written as seven in the test**, two-career and three-career characters both present, every Draft row reached, both Drifter routes taken, both commission shapes and every medical tier the data declares exercised. The tiers and the cap are both counted from the data for the same reason SC-008 gives: FR-038 puts them in files a referee may edit, and a check that hard-codes either contradicts the requirement it is checking
- [ ] T108a [P] [US1] Add the SC-020 assertions to `tests/integration/test_npc_sample.py`: over the same sample, every field the default rendering is required to carry is non-empty on every character, and no rendered default sheet contains a seed, a package version, a provenance line, a history step, a step kind, a throw, or a debt or pension figure. The first says the format's own lines are filled; the second says nothing from the walk leaks onto them
- [ ] T109 [P] [US1] Add the SC-019 weighting check to `tests/integration/test_npc_sample.py`, marked `slow`: ten thousand rolled names, each region's share within 0.9/7 and 1.1/7, counted from the `surname_region` field and never from a split rendered name
- [ ] T110 [P] [US1] Add walk invariants to `tests/property/test_invariants.py` over Hypothesis-drawn seeds: always alive, always named, at least one career, `funds >= 0`, `debt >= 0`, every characteristic within the declared pseudo-hex range, non-empty history
- [ ] T111 [P] [US1] Add the SC-012 cross-locale comparison to `tests/integration/test_npc_cli.py`: a subprocess with `LC_ALL` set to a locale whose collation differs, calling `locale.setlocale(locale.LC_ALL, "")` before generating, comparing bytes, skipping with a reason when the locale is absent (research R8)

**Checkpoint**: a referee can generate one usable NPC from a seed. The MVP is deliverable.

---

## Phase 4: User Story 2 - Tell a wrong engine from interesting dice (Priority: P2)

**Goal**: The fuller text rendering and the machine-readable document expose the walk that
produced a character, so a surprising sheet is diagnosed from output rather than a debugger.

**Independent Test**: Request `--full` and `--json` for a character and confirm every
characteristic, skill, credit, career, and item on the sheet traces to a recorded step whose
parts are separately addressable.

### Tests for User Story 2 ⚠️ written and observed failing first

- [ ] T112 [P] [US2] [TEST] Write `tests/unit/test_render_character.py` cases for the fuller sheet: the Universal Character Format, a blank line, then `Debt:` reading `none` rather than `Cr0`, `Pension:` likewise, and `History:` with each line **composed from the step's named parts** and columns padded to the longest value present (FR-049, `contracts/cli.md`)
- [ ] T113 [P] [US2] [TEST] Add a `tests/unit/test_render_character.py` case asserting no field of a `HistoryStep` holds a line composed from the step's other parts, which is what makes FR-030a checkable from the record's shape
- [ ] T114 [US2] [TEST] Commit `tests/golden/npc_full.txt` for a character carrying debt, pension, and history, compared as bytes and rendered from a hand-constructed `Character` literal for the same reason T091's six are
- [ ] T115 [P] [US2] [TEST] Write `tests/contract/test_npc_json.py` against `contracts/json-output.md`: top-level key order `kind`, `seed`, `provenance`, `characters`; the character key order; the skill, career-service, history-step, throw, and effect key orders; every key present unconditionally; both seeds emitted as strings; `specialty` as `null` never `""`; `json.dumps(indent=2, ensure_ascii=False)` with a trailing newline and non-ASCII names emitted as themselves
- [ ] T116 [P] [US2] [TEST] Add a `tests/contract/test_npc_json.py` case asserting `as_dict(batch)["characters"][i] == as_dict(batch.characters[i])` and that `total == sum(faces) + modifier values` in every throw
- [ ] T117 [P] [US2] [TEST] Add SC-005's traceability audit to `tests/integration/test_npc_sample.py`, marked `slow`: over the same thousand-seed sample, every characteristic, skill, career, credit, and item traces to a step, read from the steps' named parts and never from rendered text
- [ ] T118 [P] [US2] [TEST] Add `tests/integration/test_npc_cli.py` cases for `--json`: standard error is silent on success, `--full` with `--json` is accepted and changes nothing, and `--json` never changes an exit code (FR-053d)

### Implementation for User Story 2

- [ ] T119 [US2] Implement `as_text(character, full=True)` in `src/cetools/render.py`: the format, a blank line, debt, pension, and the history composed from each step's parts, dispatching on step and effect kinds with pattern matching
- [ ] T120 [US2] Implement `as_text(batch, full=True)` in `src/cetools/render.py`, fuller sheets separated by exactly one blank line
- [ ] T121 [US2] Register `as_dict` for `Character` and `CharacterBatch` in `src/cetools/render.py` in the committed key order, with `as_json` following from it
- [ ] T122 [US2] Add `--full` and `--json` to the `npc` command in `src/cetools/cli.py`, with `--full`'s help string saying it changes nothing under `--json`, and machine-readable mode putting the seed, version, and provenance in-document rather than on standard error

**Checkpoint**: Stories 1 and 2 both work. A surprising sheet is diagnosable from output.

---

## Phase 5: User Story 3 - Populate a table, a crew, or a ward in one go (Priority: P3)

**Goal**: One seed yields many characters, reproducibly, and quoting that seed reproduces the
whole table.

**Independent Test**: Request a batch, request it again and compare; confirm a batch of twelve
begins with the batch of three, and that a batch of one is byte-identical to the single
character of that seed.

### Tests for User Story 3 ⚠️ written and observed failing first

- [ ] T123 [P] [US3] [TEST] Write `tests/unit/test_generator_batch.py` for FR-057: the first characters of a larger batch equal a smaller batch from the same seed, compared field by field across several seeds and count pairs, and position 0 equals the single character of that seed (research R2)
- [ ] T124 [P] [US3] [TEST] Add a `tests/unit/test_generator_batch.py` case for FR-050a: each character's recorded derived seed, fed back as a master, regenerates that character alone
- [ ] T125 [P] [US3] [TEST] Add `tests/integration/test_npc_cli.py` usage-error cases: `--count 0` and a negative count naming `--count`, and `--name` with `--count 12` naming both, each exiting 2 with nothing on standard output (FR-053a)
- [ ] T126 [US3] [TEST] Commit `tests/golden/npc_batch.txt` for SC-011: a `CharacterBatch` of hand-constructed characters whose rendered bytes are exactly its sheets with one blank line between consecutive ones and no other text, plus the CLI assertion that a redirected `--count N` run's stdout equals `as_text(batch).encode("utf-8") + b"\n"` for the batch that seed produces
- [ ] T127 [P] [US3] [TEST] Add the whole-set help assertion for `npc` to `tests/integration/test_cli.py`: `options_in_help(["npc"]) == {"--seed", "--count", "--name", "--rules-data", "--full", "--json", "--help"}`. **Depends on T122 as well as on T128**: `--full` and `--json` are added in US2, so this one task in US3 is not independent of it. It asserts the command's finished surface rather than this story's contribution to it, and a whole-set assertion has no smaller honest form — narrowing it to the options US3 adds would defeat the purpose the existing per-command assertions serve, which is that an option added later breaks the test deliberately. Where US2 is skipped, this task moves to Polish with the rest of the finished-surface work

### Implementation for User Story 3

- [ ] T128 [US3] Add `--count` to the `npc` command in `src/cetools/cli.py`, passing it to `generate_batch` and turning the library's two `CetoolsError` refusals into usage errors naming the options at fault
- [ ] T129 [US3] Add help strings for `npc` and every option in `src/cetools/cli.py`, with no help string naming the trademark as something this tool works with

**Checkpoint**: all three referee-facing stories work independently.

---

## Phase 6: User Story 4 - Change the rules without changing the code (Priority: P4)

**Goal**: A referee points the tool at their own data files and generates characters under
their rules, with the provenance saying so and no code edited.

**Independent Test**: Generate a seed from packaged data, generate it again with an override
changing one value, and confirm the character changes accordingly and the provenance reports
the override.

### Tests for User Story 4 ⚠️ written and observed failing first

- [ ] T130 [P] [US4] [TEST] Add SC-013's five demonstrations to `tests/integration/test_data_driven.py`: a Draft table row, an aging table entry, a Survival Mishaps entry, a career's medical tier, and the term cap, each changed in an override and each changing the generator's behavior accordingly with no code edit
- [ ] T131 [P] [US4] [TEST] Add `tests/integration/test_overrides.py` cases for the npc command: an override supplying a career that did not ship can be entered and is reported as `added`, a replaced file is reported as `replaced`, and the provenance block appears on standard error in text mode and in-document under `--json` (FR-058)
- [ ] T132 [P] [US4] [TEST] Add `tests/integration/test_overrides.py` cases for name-table overrides: replacing a shipped region leaves the weighting unchanged, adding an eighth region gives it the same weight as each of the others, and neither the sixty/forty floors nor either designation is imposed on an override (FR-043f, FR-043i, FR-042)
- [ ] T133 [P] [US4] [TEST] Add `tests/integration/test_npc_cli.py` cases for inconsistent override data: the run fails before any character exists, exits 1, writes nothing to standard output, and names what could not be resolved

### Implementation for User Story 4

- [ ] T134 [US4] Make whatever the tests above show missing in `src/cetools/cli.py` and `src/cetools/generator.py` — the override path is the previous feature's mechanism reaching new data, so this task is expected to be small, and anything it turns out to need is a defect in the loader integration of Phase 2F rather than new capability

**Checkpoint**: every user story is independently functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T135 [P] Add the `npc` command, both text renderings, and the batch document to `README.md`, including the licensing sentence that now distinguishes the two designations
- [ ] T136 [P] Write the `CHANGELOG.md` entry set for this feature, with a **Breaking changes** heading covering the `TaskParameters` move (T009) and a note that any change reordering, adding, or removing a draw changes every character a seed produces (FR-056b)
- [ ] T137 [P] Verify SC-017 by listing each capability in this feature against a test that exercises it without invoking the command line, recorded in `tests/unit/test_library_api.py`
- [ ] T138 Run every scenario in `specs/003-npc-generator/quickstart.md` by hand and correct any drift between it and the shipped behavior
- [ ] T139 Confirm SC-016 from the git history: for each behavior in the functional requirements, the commit carrying the expected values precedes the commit carrying the implementation
- [ ] T140 Run the complete suite including `-m slow`, confirm zero skips that a criterion depends on, and confirm no `tests/golden/check_*.txt` or existing JSON fixture was modified anywhere in the branch

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
