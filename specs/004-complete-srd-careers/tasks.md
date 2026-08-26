# Tasks: Complete SRD Careers

**Input**: Design documents from `/specs/004-complete-srd-careers/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/data-files.md](./contracts/data-files.md),
[contracts/notation.md](./contracts/notation.md), [quickstart.md](./quickstart.md)

**Tests**: REQUIRED, not optional. Constitution III is test-first, strictly: write the test, watch
it fail, then implement, then run `uv run pytest -q` before moving on. Every implementation task
below is preceded by the test task that must be failing first.

**Organization**: Tasks are grouped by user story. Phases run in **dependency order, not priority
order** — see the note below.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US5)
- Include exact file paths in descriptions

## Path Conventions

Single project: `src/cetools/`, `tests/` at repository root. Data lives in
`src/cetools/data/`; verification artifacts in `specs/004-complete-srd-careers/verification/`.

## ⚠️ Why the phases are not in priority order

US1 (P1) carries the visible value — the complete roster — but the sixteen new careers cannot be
transcribed until the data shape can express an untitled rank, a short table, a rolled quantity,
and a nested cascade (US2), until the vocabularies hold the names those careers grant (US3), and
until the coverage rule makes a short table safe rather than a runtime failure (US4). The spec
says so itself under US2's "Why this priority". So the execution order is:

**US2 (shape) → US3 (vocabularies) → US4 (invariants) → US1 (roster, MVP) → US5 (verification)**

Stopping after US2+US3+US4 leaves a package that still ships eight careers and gains nothing a
user sees. **The MVP is US1, and it is only reachable through the three phases before it.**

## ⚠️ Commit discipline (Constitution, Tidy First)

- Phase 2 is structural. Two commits, in order, suite green before and after each, and neither
  may carry a behavioral change.
- Every commit after that is behavioral, Conventional Commits with a scope, and says so.
- Every user-visible change carries its `CHANGELOG.md` entry in the same commit.
- Commit only with the whole suite green and no lint warnings.

---

## Phase 1: Setup

**Purpose**: Establish the baseline the two regenerations of FR-030 are measured against.

- [X] T001 Run `uv run pytest -q` from the repository root and record the passing count (1253 at
      the branch point) in the branch's working notes; do not use `.venv/bin/python -m pytest`,
      which hides collection failures
- [X] T002 Run `uv run cetools validate` and record the `Files: 26` line. The count rises as the
      sixteen new career files land (T049–T064) and is re-pinned at T077 and T079, reaching
      `Files: 42`

---

## Phase 2: Foundational (Structural — Tidy First, blocking)

**Purpose**: Two behavior-preserving commits that must land before any career content changes.

**⚠️ CRITICAL**: No user story work may begin until this phase is complete, and neither commit
here may change engine behavior.

### Commit 1 — `refactor(golden): re-pin the render fixtures onto source-legal names`

- [X] T003 Re-pin the hand-built `Character` literals in `tests/unit/test_render_character.py`
      onto names the source vocabulary defines: `Pilot` → `Piloting`, `Vehicle (Grav)` →
      `Aircraft (Grav Vehicle)`, `Gambler` → `Gambling`, `Mechanic` → `Mechanics`, `Flyer` and
      `Personal Vehicle` onto source names from research.md R4 and R5. Also re-pin the `CASCADE`
      fixture's `("Vehicle", "Aircraft", 1)` (`:192`) onto a terminal pair such as
      `("Aircraft", "Winged Aircraft", 1)`: `Vehicle (Aircraft)` stays *valid* under the v2
      registry, so nothing fails, but it is the exact shape FR-012 forbids a sheet from carrying
      and quickstart.md states never appears on one — leaving it in the golden would contradict
      the claim the golden exists to evidence
- [X] T004 Update the committed `tests/golden/npc_titled.txt`, `npc_untitled.txt`,
      `npc_titled_then_untitled.txt`, `npc_full.txt`, `npc_cascade.txt`, `npc_multi_career.txt`,
      `npc_batch.txt`, and `npc_no_benefits.txt` to the bytes `as_text` emits for the re-pinned
      fixtures
- [X] T005 Run `uv run pytest -q` and confirm the count matches T001 exactly; a differing count
      means the re-pin became a regeneration (plan.md Known risks) and must be reverted and redone

### Commit 2 — `refactor(careers): rename the three planetary-defense career files`

- [X] T006 `git mv` `src/cetools/data/careers/aerospace-defense.toml` →
      `aerospace-system-defense.toml`, `maritime-defense.toml` → `maritime-system-defense.toml`,
      and `surface-defense.toml` → `surface-system-defense.toml`; the `name` field inside each
      file does **not** change in this commit
- [X] T007 Retarget the basename references the rename breaks:
      `tests/unit/test_generator.py:258` and `:273` (`RULES.careers["aerospace-defense"]`), and
      `tests/integration/test_validation_categories.py:444`, `:446`, `:448`, then run
      `uv run pytest -q` and confirm the count still matches T001. Six shipped career files also
      carry the comment "see `aerospace-defense.toml`'s comment" — `drifter.toml:50`,
      `marine.toml:68`, `merchant.toml:70`, `scout.toml:48`, `maritime-defense.toml:68`,
      `surface-defense.toml:68`. Nothing breaks if they are left stale, and Phase 6 deletes all
      six along with the padded rows they describe, so fixing them here is optional; retarget them
      only if this commit is where you would rather absorb the churn

**Checkpoint**: Structural work done. Every commit from here is behavioral.

---

## Phase 3: User Story 2 - Data that says what the source says (Priority: P2) 🔧 GATE

**Goal**: Make the schema able to express an untitled rank, a table that ends where the source
ends it, a rolled ship-share quantity, and a cascade specialty that is itself a cascade — and
drop the re-enlistment characteristic the walk never read.

**Independent Test**: Remove an invented title and a padded row from a shipped career file and
confirm it loads, validates, and generates; confirm a character holding an untitled rank renders
with no title and no dangling separator, and that a benefit roll never lands past a career's last
real row.

### 3a. Notation: the quantified benefit form (FR-011, contracts/notation.md)

- [X] T008 [P] [US2] Failing test: `parse_entry("1d6 Ship Share", EntryContext.BENEFIT_TABLE)`
      returns `QuantifiedBenefit(dice="1d6", name="Ship Share")`, in `tests/unit/test_notation.py`
- [X] T009 [US2] Add the `QuantifiedBenefit` frozen slots dataclass and leading-token recognition
      to `src/cetools/notation.py`, running before the existing trailing-token match so no entry
      that parsed before parses differently now
- [X] T010 [P] [US2] Failing test: the quantified form is inadmissible in `SKILL_TABLE` and
      `GATE`, reported with the entry as written and the forms the position accepts, in
      `tests/unit/test_notation.py`
- [X] T011 [US2] Extend `_ADMISSIBLE_KINDS` and `_ADMISSIBLE_FORMS` in `src/cetools/notation.py`
      so `quantified` is admitted by `EntryContext.BENEFIT_TABLE` and nowhere else
- [X] T012 [P] [US2] Failing test: `"1d6"` alone is malformed and reported as needing a name after
      the quantity; `"d66 Ship Share"` is rejected by `_check_dice`; a name carrying a specialty
      group (`"1d6 Ship Share (Bulk)"`) is rejected — in `tests/unit/test_notation.py`
- [X] T013 [US2] Implement those three rejections in `src/cetools/notation.py`, routing the dice
      through the same `_check_dice` from `src/cetools/tasks.py` every other dice field uses
- [X] T013a [P] [US2] Failing test (FR-011, contracts/notation.md): a quantity whose minimum total
      is below one is rejected naming the entry and the minimum found — `"0d6 Ship Share"` and
      `"1d6-6 Ship Share"` — while `"1d6-5 Ship Share"` (minimum 1) is accepted, in
      `tests/unit/test_notation.py`
- [X] T013b [US2] Implement the minimum-total check in `src/cetools/notation.py`. `_check_dice`
      does not supply it: a minimum of zero is legitimate for a modifier elsewhere, and FR-011
      constrains the *quantity* specifically, so an award always awards something
- [X] T014 [US2] Export `QuantifiedBenefit` from `src/cetools/__init__.py` and its `__all__`, and
      extend the public-surface assertion in `tests/unit/test_library_api.py`

### 3b. Skill registry: nested cascades and an acyclic graph (FR-012, FR-012a, D4, D5)

- [X] T015 [P] [US2] Failing test: `SkillRegistry.resolve` returns `VALID` for
      `Aircraft (Winged Aircraft)` and `Vehicle (Aircraft)` once a specialty may name another
      entry, in `tests/unit/test_registries.py`
- [X] T016 [P] [US2] Failing test: a specialty chain that revisits a name is reported at
      `skills.<name>` naming the file, the location, and the cycle, in
      `tests/unit/test_registries.py`
- [X] T017 [US2] Implement the acyclic specialty-graph check in `src/cetools/registries.py`, which
      is what guarantees generation-time resolution terminates
- [X] T018 [P] [US2] Failing test: a `skills` file declaring `schema-version = 1` is rejected on
      its header naming the version found and the version supported, and `2` is accepted, in
      `tests/unit/test_rules.py`
- [X] T019 [US2] Bump `skills` to `2` in `rules._SUPPORTED_VERSION` (`src/cetools/rules.py:59`)
      and in the header of `src/cetools/data/registries/skills.toml`

### 3c. Career schema v4 (FR-007, FR-007a, FR-010, FR-013a, D1, D2)

- [ ] T020 [P] [US2] Failing test: a rank table omitting `title` parses to `Rank(title="")`, in
      `tests/unit/test_careers.py`
- [ ] T021 [P] [US2] Failing test: an explicit `title = ""` is rejected, because absence is written
      by omitting the key rather than by writing an empty value, in `tests/unit/test_careers.py`
- [ ] T022 [P] [US2] Failing test: a rank carrying neither `title` nor `bonus` is valid, and an
      entry ladder missing its rank 0 is still rejected (FR-007a), in `tests/unit/test_careers.py`
- [ ] T023 [US2] Make `title` optional in `_parse_rank` (`src/cetools/careers.py:515-553`),
      defaulting to `""` and rejecting an explicit empty value. **In the same commit**, retire
      `tests/unit/test_careers.py::test_a_rank_without_its_title_is_rejected` (`:558-566`), which
      asserts the opposite and cites 003's FR-016; T020 is its replacement.
      `test_an_empty_rank_title` (`:622-627`) stays as written — T021 is what pins it — because
      FR-007 keeps rejecting an explicit `title = ""`
- [ ] T024 [P] [US2] Failing test: `throws.re-enlistment` declaring `characteristic` is rejected
      naming `throws.re-enlistment.characteristic` and the keys the position admits, while the
      other four throw positions still admit it, in `tests/unit/test_careers.py`
- [ ] T025 [US2] Restrict the `re-enlistment` throw position to `target` and `dice` in
      `src/cetools/careers.py`. **In the same commit**, retire the case at
      `tests/unit/test_generator.py:1185-1204`, which builds a career declaring
      `characteristic = "SOC"` on `throws.re-enlistment` and asserts the parser admits it there;
      its fixture stops parsing the moment this lands. Its underlying point — that the walk never
      applies a characteristic to the re-enlistment throw — is now enforced by the parser instead
      of observed in a walk, which is what T024 asserts
- [ ] T026 [P] [US2] Failing test: a `mustering-out.benefits` row holding `"1d6 Ship Share"` parses
      to a `QuantifiedBenefit` whose name resolves against the benefits registry exactly as a bare
      item does, in `tests/unit/test_careers.py`
- [ ] T027 [US2] Widen `mustering-out.benefits` parsing in `src/cetools/careers.py` to admit the
      quantified form and resolve its name, and remove any fixed-length constraint from `cash` and
      `benefits` (both stay non-empty)
- [ ] T028 [P] [US2] Failing test: a `career` file declaring `schema-version = 3` is rejected on
      its header naming the version found and the version supported, and `4` is accepted, in
      `tests/unit/test_rules.py`
- [ ] T029 [US2] Bump `career` to `4` in `rules._SUPPORTED_VERSION` and in the header of all eight
      shipped files under `src/cetools/data/careers/`

### 3d. Generator: recursive cascade and the ship-share draw (FR-011, FR-012, IV)

- [ ] T030 [P] [US2] Failing test: `_resolve_specialty` on a bare `Vehicle` grant continues into
      `Aircraft` or `Watercraft` and returns the innermost cascade with a terminal specialty
      (`Aircraft (Winged Aircraft)`), never `Vehicle (Aircraft)` and never a bare terminal name,
      with each nesting level costing exactly one seeded draw, in `tests/unit/test_generator.py`
- [ ] T031 [US2] Turn `_resolve_specialty` (`src/cetools/generator.py:76`) into the loop
      data-model.md specifies, drawing every step from the walk's `Roller`
- [ ] T032 [P] [US2] Failing test: a `QuantifiedBenefit` row appends the item name once per point
      rolled, the quantity comes from the seeded roller, and the same seed yields the same count,
      in `tests/unit/test_generator.py`
- [ ] T033 [US2] Handle `QuantifiedBenefit` in the mustering-out material branch of
      `src/cetools/generator.py` (near line 1454), rolling `dice` from `self.roller` and appending
      `item.name` that many times to `self.benefits`
- [ ] T034 [US2] FR-009a is **already covered for the renderer** by
      `test_a_later_untitled_career_does_not_erase_an_earlier_title` and
      `test_the_fixture_actually_represents_a_later_career_left_untitled`
      (`tests/unit/test_render_character.py:366-379`), both passing today against
      `tests/golden/npc_titled_then_untitled.txt`; do not rewrite them as failing tests, because
      they cannot fail. What is *not* covered is the generator branch those tests deliberately
      note is unreachable from shipped data. Add the missing half: a deterministic walk through a
      titled career and then an untitled one, asserting `Character.title` still holds the earlier
      ladder's title, in `tests/unit/test_generator.py`. It is unreachable until Phase 6 ships an
      untitled ladder, so write it here against a fixture career and let T073's traversal cases
      cover the shipped path
- [ ] T035 [P] [US2] Failing test (FR-016a): a character holding both `Survival` and
      `Animals (Survival)` renders them as two distinct entries, the specialty form under its named
      cascade, neither merged nor aliased, in `tests/unit/test_render_character.py`. Cover the
      `Sciences` pair in the same test — `Life Sciences-0` alongside `Sciences (Life Sciences)-1`.
      It is the same rule, but it is the case that will actually be seen: the source's education
      background-skill list grants all four `Sciences` specialties bare (R8), and every character
      draws background skills, so this collision is routine output rather than the override-only
      curiosity D6 describes
- [ ] T036 [P] [US2] Contract test: `title` stays a present string carrying `""` for an untitled
      rank, and `benefits` stays an array of plain strings with three identical `"Ship Share"`
      entries for a rolled three, with no quantity field — in `tests/contract/test_npc_json.py`

**Checkpoint**: The schema can express what the source prints. Nothing user-visible has changed
yet, and the suite is green.

---

## Phase 4: User Story 3 - One vocabulary, drawn from one source (Priority: P3)

**Goal**: Both registries hold exactly what the source uses and nothing else.

**Independent Test**: Compare each registry against the source's skill chapter and the set of
items its career tables award, and confirm the two sets match exactly in both directions.

**⚠️ Single-commit constraint**: T039 through T041b land in **one commit**. Rebuilding the
vocabularies removes names that the eight shipped careers, the shipped background-skills table,
and two test fixtures currently grant, so every one of them must be retargeted in the same commit
or the suite is red at that commit, which Constitution commit discipline forbids. The full set of
things the rebuild breaks:

| What breaks | Why | Retargeted by |
|---|---|---|
| The eight shipped career files | grant `Carouse`, `Gambler`, `Mechanic`, `Language`, `Pilot`, … | T041 |
| `chargen/background-skills.toml` | grants eleven removed names across two lists | T041a |
| `tests/integration/test_overrides.py`'s override career | grants `Carouse`, `Gambler`, `Stealth` and asserts the override validates | T041b |
| `tests/unit/test_rules_agreement.py::test_every_background_skill_the_packaged_table_grants_resolves` | pins that every background skill resolves | T038a, T041a |

- [ ] T037 [P] [US3] Failing test: `load_rules().skills.skills` holds exactly the seventy names of
      research.md R4 — the sixty-eight the chapter defines plus `Perception` and `Prospecting` —
      compared in both directions, with the eight cascades carrying exactly R4's specialty lists,
      in `tests/unit/test_rules_agreement.py`
- [ ] T038 [P] [US3] Failing test: `load_rules().benefits.items` holds exactly the eight items of
      research.md R5, compared in both directions, in `tests/unit/test_rules_agreement.py`
- [ ] T039 [US3] Rebuild `src/cetools/data/registries/skills.toml` to those seventy entries with
      `Vehicle` naming `Aircraft` and `Watercraft` as nested cascades; record in the file that
      `Perception` and `Prospecting` are granted by career tables and defined nowhere in the skill
      chapter (FR-016), and that `Jack o' Trades` is the source's own short form of
      `Jack-of-All-Trades` (FR-017a); keep the OGC header and neither Product Identity string
- [ ] T040 [US3] Rebuild `src/cetools/data/registries/benefits.toml` to `Low Passage`,
      `Mid Passage`, `High Passage`, `Weapon`, `Explorers' Society`, `Ship Share`,
      `Courier Vessel`, `Research Vessel`, removing `Armor`, `Personal Vehicle`, and `Trade Goods`.
      Apply FR-015a where a table cell and the prose differ in grammatical number: the entry is
      the **prose's** form, so the source's `1D6 Ship Shares` yields the entry `Ship Share` (what
      the "Material Benefits" prose calls it) plus a quantity, never a second plural entry and
      never an FR-017 misspelling. The same rule governs any such pair T039 meets in the skill
      chapter
- [ ] T041 [US3] In the same commit, retarget every skill and benefit name in the eight shipped
      files under `src/cetools/data/careers/` onto the rebuilt vocabularies (`Carouse` →
      `Carousing`, `Gambler` → `Gambling`, `Mechanic` → `Mechanics`, `Language` → `Linguistics`,
      `Pilot` → `Piloting`, and the rest of R4), noting each FR-017 correction in the file that
      carries it; full field-by-field reconciliation is Phase 6

### 4a. The background-skills table the rebuild breaks (FR-014a, R8)

**⚠️ Same commit as T039–T041.** `chargen/background-skills.toml` grants eleven of the twelve
names T039 removes, and `test_every_background_skill_the_packaged_table_grants_resolves` pins that
they resolve. It is **not** retargeted by substituting a nearest surviving name: reading the source
to do the retarget showed two of its three lists are a different edition's table (R8), so it is
transcribed like a career.

- [ ] T038a [P] [US3] Failing test: `load_rules()`'s background-skills table holds exactly R8's
      three lists — `law-level` 4 rows, `trade-code` 14 rows, `education` 15 rows — compared row by
      row **in printed order and with repeats intact**, so that `Animals` appears three times and
      `Zero-G` three times in `trade-code`; a set comparison MUST NOT be used, because it is
      precisely the repeats that carry the draw's weighting, in
      `tests/unit/test_rules_agreement.py`
- [ ] T041a [US3] Rewrite `src/cetools/data/chargen/background-skills.toml`'s three arrays to R8's
      rows in printed order (`law-level` already matches and is left alone; `trade-code` and
      `education` are replaced wholesale). Keep the OGC header and neither Product Identity string.
      Update the file's header comment: it already states the rule "duplicates are preserved and
      meaningful", which the shipped data broke — say that the rows are the source's printed rows
      and that deduplicating any of them reweights the draw
- [ ] T041b [US3] In the same commit, retarget the override career fixture in
      `tests/integration/test_overrides.py:59-64` off `Carouse`, `Gambler`, and `Stealth` onto
      source names; `test_validate_accepts_the_same_override_location` (`:121-127`) asserts that
      override validates, so it fails the moment the vocabulary shrinks. Sweep the remaining test
      fixtures for removed names in the same pass — `tests/unit/test_careers.py`,
      `test_registries.py`, `test_notation.py`, and `test_generator.py` each carry some, though
      most build their own in-test registries and are unaffected; the check is whether a fixture
      resolves against the *packaged* vocabulary

**Checkpoint**: Both vocabularies match the source in both directions, every shipped file that
references them still resolves, and the suite is green.

---

## Phase 5: User Story 4 - The checks users run enforce what correct career data means (Priority: P4)

**Goal**: Move the mustering-out coverage invariant out of documentation and a fixed-length test
assertion into `cetools validate`, so an override author is subject to it.

**Independent Test**: Feed the validator a career file violating each invariant in turn and
confirm it names the file, the location, what was found, and what was expected; feed it every
shipped career and confirm it reports none.

- [ ] T042 [P] [US4] Failing test: a career whose `mustering-out.cash` is shorter than
      `roll.count * roll.sides + roll.modifier + retired-cash-dm` is rejected at
      `mustering-out.cash` naming the rows found and the rows required, in
      `tests/unit/test_rules.py`
- [ ] T043 [P] [US4] Failing test: a career whose `mustering-out.benefits` is shorter than the
      roll maximum plus the highest `material-rank-dm` row at or below its highest reachable rank
      is rejected at `mustering-out.benefits`; and a career whose ladders stop at rank 0 is bounded
      by the roll alone, so six rows suffice — in `tests/unit/test_rules.py`
- [ ] T044 [US4] Implement the coverage rule as a cross-file rule in `src/cetools/rules.py`,
      reading `roll`, `retired-cash-dm`, and `material-rank-dm` from `chargen-parameters.toml`
      rather than holding a constant, and reusing the existing "highest-ranked row at or below
      this rank, not cumulative" matching; state it over the careers **in force** so overrides are
      subject to it (FR-021)
- [ ] T045 [US4] Replace the fixed `len(...) == 7` assertions at
      `tests/integration/test_data_driven.py:401-402` with the computed coverage bound, which the
      seven short material tables of Phase 6 would otherwise fail
- [ ] T046 [P] [US4] Integration test: `cetools validate <dir>` exits non-zero and names file,
      location, found, and expected for each of the quickstart.md rejections — an unresolvable
      skill name (FR-018), a rank ladder with a gap (FR-019), and a short cash table (FR-020) — in
      both human-readable and `--json` renderings, in `tests/integration/test_validate_cli.py`
- [ ] T047 [P] [US4] Integration test: the coverage problem is reported under the right problem
      category alongside the existing cross-file rules, in
      `tests/integration/test_validation_categories.py`

**Checkpoint**: A short table is safe. Every invariant an override author can break is enforced by
the command they run.

---

## Phase 6: User Story 1 - Generate a character from any career the source publishes (Priority: P1) 🎯 MVP

**Goal**: Twenty-four careers in force, each qualifying in, serving a term, and mustering out.

**Independent Test**: Run a deterministic walk targeted at each career in turn and confirm each
qualifies in, serves a term, and musters out with a sheet naming that career; run a batch large
enough to sample the pool and see careers outside the previously shipped eight.

**Every file below**: OGC header comment, `schema = "career"`, `schema-version = 4`, neither
Product Identity string, values from research.md R1/R3/R4/R5/R6 and the source pages Assumptions
pins, absence written as absence (omit `title`, never pad a table, a zero row is a real row).

**⚠️ Every file below also carries `[tables.advanced-education]` with `requires = "EDU 8+"`.**
`_REQUIRED_TABLES` (`src/cetools/careers.py:41`) makes the table mandatory, and FR-004 fixes its
gate at `Edu 8+` for all twenty-four without exception. **Do not take it from the fourth
slash-field in the task descriptions below** — that field is R1's `Promo.` column, the
*advancement* throw, which varies by career and is commonly written `Edu N+` too. The two are
different fields and the resemblance is the trap. Each task's five slash-fields are, in order:
qualification / survival / commission / **advancement** / re-enlistment.

### 6a. The three long display names (FR-005, R2)

- [ ] T048 [US1] In **one commit**, change `name` to `Aerospace System Defense`,
      `Maritime System Defense`, and `Surface System Defense` in the three renamed files under
      `src/cetools/data/careers/`, and rewrite the `careers` array in
      `src/cetools/data/chargen/draft.toml` to those long names in the source's printed row order;
      the existing cross-file rule requires every draft entry to resolve to a career's declared
      `name`, so these cannot land apart. Update `draft.toml`'s header comment in the same edit —
      it currently reads "Career-table spellings, not the source's parenthetical aliases", which is
      the exact rationale FR-005 overturns; it now takes the career-descriptions list's names,
      and neither the tables' abbreviated headers nor the draft table's parenthetical gloss

### 6b. The sixteen new careers (FR-001)

- [ ] T049 [P] [US1] Create `src/cetools/data/careers/agent.toml` (Soc 6+/Int 6+/Edu 7+/Edu 6+/6+,
      professional, 7 material rows; rank 5 title corrected from `Assistant Directory` to
      `Assistant Director` with the correction noted in the file, D9)
- [ ] T050 [P] [US1] Create `src/cetools/data/careers/athlete.toml` (End 8+/Dex 5+/no commission,
      professional, 6 material rows, untitled rank 0 carrying a grant)
- [ ] T051 [P] [US1] Create `src/cetools/data/careers/barbarian.toml` (End 5+/Str 6+/no commission,
      fringe, 6 material rows, cash row 1 is a real `0`)
- [ ] T052 [P] [US1] Create `src/cetools/data/careers/belter.toml` (Int 4+/Dex 7+/no commission,
      fringe, 6 material rows; grants `Prospecting` on Service 5 and Specialist 4; material row 5
      is `1d6 Ship Share`)
- [ ] T053 [P] [US1] Create `src/cetools/data/careers/bureaucrat.toml` (Soc 6+/Edu 4+/Soc 5+/Int
      8+/5+, professional, 7 material rows; grants `Perception` on Specialist 3)
- [ ] T054 [P] [US1] Create `src/cetools/data/careers/colonist.toml` (End 5+/End 6+/Int 7+/Edu
      6+/5+, fringe, 7 material rows; rank 3 title corrected from `Liaision` to `Liaison` with the
      correction noted in the file)
- [ ] T055 [P] [US1] Create `src/cetools/data/careers/diplomat.toml` (Soc 6+/Edu 5+/Int 7+/Soc
      7+/5+, professional, 7 material rows)
- [ ] T056 [P] [US1] Create `src/cetools/data/careers/entertainer.toml` (Soc 8+/Int 4+/no
      commission, professional, 6 material rows)
- [ ] T057 [P] [US1] Create `src/cetools/data/careers/hunter.toml` (End 5+/Str 8+/no commission,
      professional, 6 material rows; material row 5 is `1d6 Ship Share`)
- [ ] T058 [P] [US1] Create `src/cetools/data/careers/mercenary.toml` (Int 4+/End 6+/Int 7+/Int
      6+/5+, professional, 7 material rows; material row 7 is `1d6 Ship Share`)
- [ ] T059 [P] [US1] Create `src/cetools/data/careers/noble.toml` (Soc 8+/Soc 4+/Edu 5+/Int 8+/6+,
      professional, 7 material rows; commissioned ladder titles `Knight`, `Baron`, `Marquis`,
      `Count`, `Duke`, `Archduke`; material row 7 is `1d6 Ship Share`; header comment recording
      FR-031 — the source's separate Social-Standing nobility table is unimplemented and whatever
      implements it must reconcile with these titles rather than duplicate them)
- [ ] T060 [P] [US1] Create `src/cetools/data/careers/physician.toml` (Edu 6+/Int 4+/Int 5+/Edu
      8+/5+, professional, 7 material rows; ranks 4 and 6 carry `Attending Phys.` and
      `Hospital Admin.` verbatim, D9)
- [ ] T061 [P] [US1] Create `src/cetools/data/careers/pirate.toml` (Dex 5+/Dex 6+/Str 7+/Int 6+/5+,
      professional, 7 material rows; rank 2 grant corrected from `Pilot` to `Piloting` with the
      correction noted; material row 7 is `1d6 Ship Share`)
- [ ] T062 [P] [US1] Create `src/cetools/data/careers/rogue.toml` (Dex 5+/Dex 4+/Str 6+/Int 7+/4+,
      fringe, 7 material rows)
- [ ] T063 [P] [US1] Create `src/cetools/data/careers/scientist.toml` (Edu 6+/Edu 5+/Int 7+/Int
      6+/5+, professional, 7 material rows; material row 7 is `Research Vessel`)
- [ ] T064 [P] [US1] Create `src/cetools/data/careers/technician.toml` (Edu 6+/Dex 4+/Edu 5+/Int
      8+/5+, professional, 7 material rows)

### 6c. The eight shipped careers, reconciled field by field (FR-002, FR-003)

Each task compares **every** field FR-023a enumerates against the source's printed value — display
name, all five throws, medical tier, always-available, re-enterable, every skill-table row, every
rank row's title and grant separately, and every row of both mustering-out tables. The audit in
research.md R7 names known differences; it does not bound the work.

- [ ] T065 [P] [US1] Reconcile `src/cetools/data/careers/scout.toml`: qualification `Int 5+` →
      `Int 6+`, re-enlistment `3+` → `6+`, rank 0 loses its invented `Scout` title and grants
      `Piloting 1` (corrected from `Pilot`, noted in the file), cash becomes
      `[1000, 5000, 10000, 10000, 20000, 50000, 50000]`, the material table drops its padded
      seventh row to six with row 5 `Explorers' Society` and row 6 `Courier Vessel`, and service
      skills become the source's `Comms, Electronics, Gun Combat, Gunnery, Recon, Piloting`
- [ ] T066 [P] [US1] Reconcile `src/cetools/data/careers/drifter.toml`: qualification `End 3+` →
      `Dex 5+`, the advanced-education gate becomes the uniform `Edu 8+` (FR-004), cash becomes
      `[0, 1000, 2000, 5000, 5000, 10000, 10000]` with row 1 a real zero, the material table drops
      its padded seventh row to six, every rank row loses its title (the source prints nothing at
      all across every rank, so rank 0 carries neither title nor bonus, FR-008), and
      `Trade Goods`, `Personal Vehicle`, `Carouse`, `Gambler`, `Stealth` give way to source names
- [ ] T067 [P] [US1] Reconcile `src/cetools/data/careers/navy.toml` (research.md R7 records it
      matching across every field checked; the re-read still enumerates every field)
- [ ] T068 [P] [US1] Reconcile `src/cetools/data/careers/marine.toml`, replacing its
      comment-acknowledged repeated seventh material row with the source's printed row
- [ ] T069 [P] [US1] Reconcile `src/cetools/data/careers/merchant.toml`, replacing its repeated
      seventh material row, correcting the rank 3 grant `Pilot` → `Piloting` with a note, and
      setting material row 5 to `1d6 Ship Share`
- [ ] T070 [P] [US1] Reconcile `src/cetools/data/careers/aerospace-system-defense.toml`, replacing
      its repeated seventh material row (grants `Aircraft` directly, which v2 resolves as a nested
      cascade)
- [ ] T071 [P] [US1] Reconcile `src/cetools/data/careers/maritime-system-defense.toml`, replacing
      its repeated seventh material row (grants `Watercraft` directly)
- [ ] T072 [P] [US1] Reconcile `src/cetools/data/careers/surface-system-defense.toml`, replacing
      its repeated seventh material row

### 6d. Acceptance: traversal and the enlarged pool (FR-026, FR-027, FR-028)

- [ ] T073 [US1] Add `tests/integration/test_traversal.py`: a parameterized deterministic walk per
      career, twenty-four cases, each asserting the character qualifies into that career, completes
      at least one term, and musters out with cash and material benefits drawn from that career's
      own tables, exercising its skill tables, its rank ladder, and its benefit rows
- [ ] T074 [US1] Test: `load_rules().careers` holds exactly twenty-four entries whose `name`
      values are the twenty-four of research.md R1, including the three long names, in
      `tests/integration/test_data_driven.py`
- [ ] T075 [US1] Test (SC-007): a batch large enough to sample career selection produces characters
      from careers outside the previously shipped eight, in `tests/integration/test_npc_sample.py`
- [ ] T076 [US1] Test (SC-005): every cash table has seven rows; `athlete`, `barbarian`, `belter`,
      `drifter`, `entertainer`, `hunter`, and `scout` have six material rows and the other
      seventeen have seven; and those same seven careers, and no others, carry an untitled rank —
      in `tests/integration/test_data_driven.py`
- [ ] T076a [US1] **In the same commit as the career content that falsifies it**, invert
      `tests/unit/test_render_character.py::test_no_shipped_ladder_rank_leaves_a_character_untitled`
      (`:381-395`), which asserts every rank of every shipped ladder declares a title and which
      FR-008 makes false for seven careers. Its premise — recorded in its own comment — was that
      ordinary generation can never reach the "an earlier title survives" branch, so only an
      override could exercise it. That premise is now wrong in the interesting direction: replace
      the assertion with one naming the seven careers whose ladders carry untitled ranks, and note
      that the branch is now reachable from shipped data, which is what T073's traversal cases
      exercise
- [ ] T077 [US1] Update the composed-file-count expectations from 26 to 42 at their actual sites:
      `tests/unit/test_rules.py:245` and `:250` (`report.file_count == 26`) and
      `tests/integration/test_validate_cli.py:93` (`payload["file_count"] == 26`); also
      `tests/unit/test_rules.py:265`, where the override-addition case expects 27 and becomes 43.
      `tests/guards/test_data_layout.py` and `tests/guards/test_packaging.py` need **no** change —
      both compare filename sets built by `rglob` rather than pinning a count. Separately, confirm
      all twenty-four career files carry the OGC header and neither Product Identity string via
      `tests/unit/test_licensing.py`

### 6e. The one regeneration (FR-030, SC-006) — ⚠️ RUNS AFTER PHASE 7's T087

**Two corrections to how this step was scoped.**

*What actually moves.* `tests/golden/npc_*.txt` are **not** generated output. `test_goldens`
(`tests/unit/test_render_character.py:408-418`) renders them from the six hand-built `Character`
literals in that module, so career content cannot move them; they move exactly once, at T004, and
that is the first of SC-006's two changes. What career content *does* move is in
`README.md`: the pinned `cetools npc --seed table-of-twelve --count 3` block, which
`tests/integration/test_golden.py:211-212` re-runs and compares. That is the second change.
`git log -- README.md tests/golden/` therefore shows two commits, which is what quickstart.md
checks — but one file each, not both twice.

*When it runs.* Phase 7's re-read exists to find content errors, and T087 applies every
`corrected` verdict to the data files. Regenerating README before that and correcting after it
would move the pinned block a third time. So **do Phase 7 first, then come back here.** Nothing is
red in the interim: Phase 6 ends green precisely because the goldens are fixtures.

- [ ] T078 [US1] Confirm `tests/golden/npc_*.txt` are **unchanged** since T004 — `git diff` over
      `tests/golden/` from the Phase 2 commit is empty. If any of them moved, a hand-built render
      fixture was edited during Phase 6, which is a mistake: those literals are independent of
      career content and keeping them so is what makes SC-006's count meaningful
- [ ] T079 [US1] Regenerate the pinned output blocks in `README.md` **once**, after all career
      content has landed *and after T087 has applied the re-read's corrections*: the
      `cetools npc --seed table-of-twelve --count 3` block, the `Files: 26` line → `Files: 42`,
      and the prose "eight careers" in the sentence listing what the packaged data holds →
      "twenty-four careers". Keep the `(cetools 2026.8.1)` version strings
      `tests/guards/test_documented_version.py` pins
- [ ] T080 [US1] Confirm the `--json` contract tests still pass unchanged. Their `file_count`
      values (`5`, `6`) are hand-built `ValidationReport` fixtures, not the packaged count, so
      T077's 26 → 42 does not reach them; the contract **shape** must not change either. If
      anything in `tests/contract/test_json_contract.py` or `tests/contract/test_npc_json.py`
      does move, it is a contract change and needs justifying, not updating
- [ ] T081 [US1] Re-run `tests/integration/test_npc_determinism.py` and
      `tests/property/test_invariants.py`, updating any pinned seed expectations, and confirm every
      draw still comes from the seeded `Roller` per `tests/guards/test_seed_contract.py`

**Checkpoint**: MVP. Twenty-four careers in force, all traversable, suite green,
`cetools validate` clean.

---

## Phase 7: User Story 5 - Transcription verified against the source, not against itself (Priority: P5)

**Goal**: A committed, inspectable source-first re-read of every career, plus the roster-level
verification a per-career re-read cannot supply.

**Independent Test**: Open any artifact and confirm it enumerates the source's printed values
first and the committed file's values against them, field by field, with a verdict per field.

**⚠️ FR-023 is what makes this a control rather than a formality**. Each re-read is a **fresh
pass over the source pages**, separate from the transcription pass, consulting the committed file
only to compare against what the source has already been read to say. It MUST NOT reconstruct the
source from research.md, this tasks file, or any other working note of the transcription. Every
artifact and the index carries the same OGC header the shipped career files carry.

**Verdicts are exactly three**: `match`, `corrected`, `deviation`. A discrepancy is resolved by
changing the career file (the default, needing no justification) or, on FR-024's three named
grounds only, recorded as a deviation **in the career data file itself** as well as the artifact.

- [ ] T082 [US5] Write `specs/004-complete-srd-careers/verification/roster.md` (FR-023b):
      enumerate the set of careers from the source's career-descriptions list and tabs, compare
      against the set the package ships, and establish both that none the source publishes is
      missing and that none it does not publish has been invented; this record governs the count in
      spec.md Assumptions rather than being checked against it
The twenty-four are batched **alphabetically by basename**, not by which of the source's four
career-table tabs they appear on. Tab membership is recorded nowhere in this feature's directory —
research.md R1 is alphabetical — so a tab-keyed batch could not be acted on without first
re-deriving the tabs, and the batching is only a way to parallelize the work, not a claim about
the source's layout. Each re-read still reads the source's tables wherever they sit.

- [ ] T083 [P] [US5] Re-read `aerospace-system-defense`, `agent`, `athlete`, `barbarian`, `belter`,
      and `bureaucrat` against the source and write one artifact each under
      `specs/004-complete-srd-careers/verification/`, enumerating display name; qualification,
      survival, commission, promotion, and re-enlistment throws; the advanced-education gate;
      medical-care tier, always-available, and re-enterable (FR-006a); every skill-table row; every
      rank row's title and grant **separately**; and every row of both mustering-out tables —
      including fields where the source prints nothing, each getting its own enumerated field and
      verdict
- [ ] T084 [P] [US5] Same for `colonist`, `diplomat`, `drifter`, `entertainer`, `hunter`, and
      `marine`
- [ ] T085 [P] [US5] Same for `maritime-system-defense`, `mercenary`, `merchant`, `navy`, `noble`,
      and `physician`
- [ ] T086 [P] [US5] Same for `pirate`, `rogue`, `scientist`, `scout`, `surface-system-defense`,
      and `technician`
- [ ] T086a [P] [US5] Write
      `specs/004-complete-srd-careers/verification/background-skills.md` (FR-014a, FR-023a): the
      same source-first treatment for the retargeted background-skills table, enumerating each row
      of all three lists with a verdict per row. Row-by-row, not set-wise — the repeated rows are
      the weighting, and a set comparison would record a match where rows went missing
- [ ] T087 [US5] Apply every `corrected` verdict to the data file it names — a career file, or
      `background-skills.toml` for T086a's verdicts — and re-run `uv run pytest -q` plus
      `uv run cetools validate`; record each `deviation` in that data file with the reason as well
      as in the artifact (FR-024); confirm no deviation stands against a career that fails
      validation (FR-022 admits no exception)
- [ ] T088 [US5] Write `specs/004-complete-srd-careers/verification/index.md` naming each of the
      twenty-four and whether its re-read is complete, so "all twenty-four, none partial" is
      checkable without reading every artifact; also name `roster.md` (FR-023b) and
      `background-skills.md` (FR-014a), so the index covers the whole verification set rather
      than the careers alone
- [ ] T089 [US5] Test: `specs/004-complete-srd-careers/verification/` holds twenty-four career
      artifacts plus `index.md`, `roster.md`, and `background-skills.md` — twenty-seven files —
      each carrying the OGC header, in `tests/unit/test_licensing.py`

**Checkpoint**: SC-003 satisfied. Acceptance rests on the re-read, not on a human diff review
(FR-025).

---

## Phase 8: Polish & Cross-Cutting Concerns

- [ ] T090 Add the `CHANGELOG.md` breaking-changes entry (SC-008, FR-029, FR-033, FR-034, FR-035):
      the seed-output change with no compatibility path, naming **all three** of its causes rather
      than the pool alone (FR-029) — the enlarged career pool, the corrected background-skills
      table (FR-014a), and the extra draw each cascade nesting level now costs (FR-012); the career
      schema 3 → 4 and skills schema 1 → 2 bumps and that an override declaring the old version is
      rejected on its header with no migration; the three renamed composition keys named old and
      new (`aerospace-defense` → `aerospace-system-defense`, `maritime-defense` →
      `maritime-system-defense`, `surface-defense` → `surface-system-defense`); the corrected Scout
      and Drifter data; and that reproducing the previous pool requires shipping it as an override.
      Add a non-breaking note that a sheet may now show a skill twice under different cascades —
      `Life Sciences-0` beside `Sciences (Life Sciences)-1` — which is what the source says and not
      a duplicate-skill bug (FR-016a, research R8)
- [ ] T091 [P] Add the cross-reference in `specs/003-npc-generator/spec.md` at the point where its
      reasoning for excluding Noble is superseded, leaving the rest of that spec intact (FR-032)
- [ ] T092 [P] Confirm `README.md`'s licensing section and the Section 15 game-data notice still
      designate the directory all twenty-four career files live under, and that
      `tests/guards/test_no_outside_reads.py` and `tests/guards/test_no_locale.py` still pass
- [ ] T093 Run every command in [quickstart.md](./quickstart.md) top to bottom and confirm each
      stated expectation: 24 careers listed, `Files: 42`, the three rejections, 70 skills and 8
      benefit items, the background-skills table's three lists with their repeats intact, the
      `cash=7`/`material=6|7`/`untitled` shape, an untitled sheet with no dangling separator,
      `Ship Share (x3)`, no bare `Vehicle (Aircraft)` on any sheet, twenty-seven files under
      `verification/`, and exactly two commits touching `README.md` and `tests/golden/` — one
      each, per T078's note
- [ ] T094 Run `uv run pytest -q` and the project's lint commands
      (`tests/guards/test_lint_commands.py` names them) and confirm both are clean before the final
      commit

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies
- **Foundational (Phase 2)**: depends on Setup. **Blocks everything**, and is two structural
  commits that must land before any behavioral change
- **US2 (Phase 3)**: depends on Phase 2. **Blocks US1 and US3.** Within it, 3a and 3b are
  independent of each other; 3c depends on 3a (the career parser must recognize the quantified
  form); 3d depends on 3a and 3b
- **US3 (Phase 4)**: depends on 3b (the registry must admit nested cascades before `skills.toml`
  declares them). **Blocks US1** — the sixteen new careers grant names only the rebuilt
  vocabularies hold. Its 4a sub-phase is not optional and not deferrable: the vocabulary rebuild
  and every file it breaks land in one commit
- **US4 (Phase 5)**: depends on 3c (tables must be variable-length before a rule bounds them).
  **Blocks US1** — the seven short material tables are unsafe until the rule enforces coverage
- **US1 (Phase 6)**: depends on US2, US3, and US4. Delivers the MVP. **6a–6d only**; 6e is
  deferred past Phase 7, for the reason 6e states
- **US5 (Phase 7)**: depends on 6a–6d — there must be twenty-four committed files to compare
  against. Runs **before** 6e, so the re-read's corrections land before the single README
  regeneration rather than after it
- **6e (the regeneration)**: depends on Phase 7's T087. Last behavioral work in the feature
- **Polish (Phase 8)**: depends on 6e

### Within Each Phase

- The test task always precedes its implementation task and must be failing first
- Run the whole suite after each step, not at the end of a phase
- Registry and notation changes before career parsing; career parsing before generation; data
  content before goldens

### Parallel Opportunities

- T008 / T010 / T012 / T013a (notation tests), T015 / T016 (registry tests), T020 / T021 / T022 /
  T024 / T026 (career-parse tests) — different assertions, and each is written and watched to fail
  before its implementation task
- T037, T038, and T038a — different files
- T042 and T043 — different tables; T046 and T047 — different integration files
- **T049–T064**: all sixteen new career files are independent of each other
- **T065–T072**: all eight reconciliations are independent of each other
- **T083–T086a**: the five verification batches are independent
- T091 and T092 — different files

### Not Parallel

- T023 and its test retirement, T025 and its test retirement, and T076a with the career content
  that falsifies it — each pair is one commit, because each retires a test asserting the opposite
  of the change beside it
- T039–T041b must be one commit (the vocabulary rebuild breaks the shipped eight careers,
  `background-skills.toml`, and two test fixtures until all of them are retargeted)
- T048's two files must be one commit (the draft-name cross-file rule)
- T078–T081 are the single regeneration and must follow **every** content task, T087's re-read
  corrections included — which is why 6e sits after Phase 7

---

## Parallel Example: the sixteen new careers

```bash
# After US2, US3, and US4 are complete, all sixteen can be written concurrently:
Task: "Create src/cetools/data/careers/agent.toml"
Task: "Create src/cetools/data/careers/athlete.toml"
Task: "Create src/cetools/data/careers/barbarian.toml"
Task: "Create src/cetools/data/careers/belter.toml"
# ... through technician.toml
```

## Parallel Example: the eight reconciliations

```bash
Task: "Reconcile src/cetools/data/careers/scout.toml"
Task: "Reconcile src/cetools/data/careers/drifter.toml"
Task: "Reconcile src/cetools/data/careers/navy.toml"
# ... through surface-system-defense.toml
```

---

## Implementation Strategy

### The MVP is US1, reached through three gating phases

1. Phase 1: Setup — record the baseline
2. Phase 2: Foundational — two structural commits, suite count unchanged
3. Phase 3 (US2): the schema can express what the source prints
4. Phase 4 (US3): the vocabularies hold what the source uses, and every file they break is
   retargeted in the same commit
5. Phase 5 (US4): the coverage rule makes a short table safe
6. Phase 6a–6d (US1): **twenty-four careers ship — STOP and VALIDATE**
7. Phase 7 (US5): the re-read that acceptance rests on, and the corrections it finds
8. Phase 6e: the single README regeneration, now that no content will move again
9. Phase 8: changelog, cross-references, quickstart

### Incremental delivery

Phases 3 through 5 are internally complete increments — each leaves the suite green and the
package shipping — but none is user-visible on its own. The first release-worthy stopping point is
the end of Phase 6d. Phase 7 is what makes Phase 6 acceptable, so shipping without it forfeits
SC-003 and, with it, FR-025's substitute for a human diff review — and because 6e now follows
Phase 7, stopping early also leaves `README.md` un-regenerated, which is visible.

---

## Notes

- `uv run pytest`, never `.venv/bin/python -m pytest`
- All randomness through the walk's seeded `Roller`; never `random`, never the clock
- New SRD-derived files: OGC header, under `src/cetools/data/careers/`, and never containing the
  two Product Identity strings
- Human-readable CLI output changes mean `tests/golden/` in the same commit; `--json` changes
  break `tests/contract/`
- New result types go into both `as_text` and `as_dict`/`as_json` in `src/cetools/render.py` —
  this feature adds none, which T036 pins
- Every user-visible change carries its `CHANGELOG.md` entry in the same commit
- Structural and behavioral changes never share a commit
