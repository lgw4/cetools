# Tasks: Acceptable Values at Interactive Ship Prompts

**Input**: Design documents from `/specs/001-prompt-acceptable-values/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Tests**: **Required, not optional.** Constitution III (Test-First, NON-NEGOTIABLE) governs this
repository: every behaviour change is written test-first, and the failing test MUST be run and its
failure observed before the implementation moves. This feature has one hazard the constitution check
calls out by name (plan.md, Principle III): 31 assertions in `tests/test_cli.py` already contain the
*old* prompt strings, so a rewritten assertion that is green on first run means the prompt never
changed. Every rewrite task below therefore ends in "observe it fail".

**Organization**: Tasks are grouped by user story so each can be implemented, tested and delivered
independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Exact file paths are given in every task

## Path Conventions

Single project, per plan.md: `src/cetools/` for the package, `tests/` mirroring it at the
repository root. Every path below is relative to the repository root.

## Reference strings

Every prompt string, refusal shape and accepted answer form this feature produces is fixed exactly
in [contracts/prompt-contract.md](./contracts/prompt-contract.md). Every new engine signature,
ordering rule and paired validator is fixed in
[contracts/engine-accessors.md](./contracts/engine-accessors.md). Do not invent a string; copy it.

## The three traps this list exists to keep you out of

Named here because each is a place where the obvious implementation produces a prompt that lies, and
each was found by cross-artifact analysis rather than by writing code (spec.md, Clarifications
2026-07-30):

1. **A value may contain a space.** `self sealing` and `hull class` are single values at questions
   that take several values in one answer. Splitting the answer on whitespace makes them unknown
   tokens, so the prompt refuses a spelling it just displayed. `prompts.split_values` is the one
   place that is decided (T010, T034, T046).
2. **A refusal must match the prompt's notation, not just its spelling.** The numeric prompts'
   refusals name their sets as bare Python lists today. A prompt reading `100-1000 by 100, …` above
   a refusal reading `[100, 200, …]` is the two-different-sets failure FR-016 exists to prevent
   (T025, T030).
3. **The turret count is unchecked when the tonnage is unpinned.** `_read_turret_count` skips
   validation entirely when `hull_tons is None` (ship.py:349), so a prompt naming `1-50` would
   accept 51. This is the feature's one behaviour change outside prompt text (T026, T033).

---

## Phase 1: Setup

**Purpose**: Establish the baseline the reds will be measured against.

- [X] T001 Run the five-command gate on the clean branch and record it green, so a later red is
      unambiguously this feature's: `uv run isort . && uv run black . && uv run flake8 src tests && uv run pytest && uv run python scripts/check_docs.py`
- [X] T002 Create `src/cetools/cli/prompts.py` containing only its module docstring, and
      `tests/test_prompts.py` containing only its import of `cetools.cli.prompts`, so the Phase 2
      reds fail on a missing function rather than a missing file

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The engine's published value sets and the CLI's text composition. Every user story
reads from both.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

### Engine accessors (contracts/engine-accessors.md)

- [X] T003 [P] Write the accessor/validator agreement tests for the eight table accessors
      (`hull_tonnages`, `armor_options`, `computer_models`, `electronics_packages`, `bay_kinds`,
      `screen_kinds`, `turret_mounts`, `turret_weapons`) in `tests/test_ship_generator.py`,
      asserting both invariants from contracts/engine-accessors.md—accessor-accepts (every
      returned value passes its paired validator) and accessor-complete (every value the validator
      accepts is returned)—plus the documented ordering; run
      `uv run pytest tests/test_ship_generator.py -k accessor --no-cov` and observe them fail on the
      missing names
- [X] T004 [P] Write the accessor tests for `fitting_kinds`, `small_craft_weapons` and `hardpoints`
      in `tests/test_ship_generator.py`, including that `fitting_kinds()` omits every fitting whose
      table `tons` is `None` (so `vehicle_hangar` is absent and the exclusion is derived, not
      listed—FR-024), that `small_craft_weapons` narrows by the plant's energy allowance and by
      the mount, that `hardpoints` agrees with `validate_turret_count` for a pinned tonnage, and
      that `hardpoints(hull_class, None)` returns the ruleset maximum—50 for a starship and 1 for
      a small craft, each derived from the tables (`max(HULLS) // 100`) rather than written down;
      run and observe them fail
- [X] T005 Implement `hull_tonnages`, `armor_options`, `computer_models`, `electronics_packages`,
      `bay_kinds`, `screen_kinds`, `turret_mounts` and `turret_weapons` in
      `src/cetools/engine/ships/generator.py`, each a single expression placed beside the validator
      it pairs with; preserve table order for the word sets and sort the numeric sets ascending
- [X] T006 Implement `fitting_kinds` and `small_craft_weapons` and expose `_hardpoints_for` as the
      public `hardpoints(hull_class, hull_tons: int | None)` in
      `src/cetools/engine/ships/generator.py`, deriving the vehicle-sized exclusion from the table
      row rather than from a hard-coded name, and returning the ruleset's largest hardpoint count
      when the tonnage is `None`—the widening `available_ratings` has always had, and what FR-011
      needs at the turret question. `validate_turret_count` is **not** widened and its logic does
      not change
- [X] T007 Export the eleven accessors from `src/cetools/engine/ships/__init__.py`—add them to the
      `from cetools.engine.ships.generator import (...)` list and to `__all__`, both alphabetical—
      then run `uv run pytest tests/test_ship_generator.py --no-cov` green

### Prompt text composition (research.md Decision 2)

- [X] T008 [P] Write failing tests for `spell(key)` and `key(answer)` in `tests/test_prompts.py`:
      underscore to space, lowercasing, space and hyphen to underscore, surrounding whitespace
      ignored, an internal whitespace run counting as one space, and `key(spell(k)) == k`; run
      `uv run pytest tests/test_prompts.py --no-cov` and observe them fail
- [X] T009 [P] Write failing tests for `numbers(values)` run collapsing in `tests/test_prompts.py`
      covering FR-005 exactly: three or more evenly spaced values collapse to `first-last` or
      `first-last by step`; a two-element run collapses only when its step is 1 (`1, 2` → `1-2`) and
      is otherwise enumerated (`1, 3` stays `1, 3`); several runs are named in ascending order
      (`100-1000 by 100, 1200-2000 by 200, 3000-5000 by 1000`); a value in no run is enumerated in
      its place; run and observe them fail
- [X] T010 [P] Write failing tests for `split_values(answer, known)` in `tests/test_prompts.py`—
      the greedy longest-match scan FR-015 requires for an answer naming several values. Cover:
      a two-word value survives the split (`reflec self sealing` → `["reflec", "self_sealing"]`);
      commas and whitespace separate alike; the underscored and hyphenated spellings of a multi-word
      value are accepted; a word run matching nothing raises naming that run; and the span limit is
      derived from `known` rather than hard-coded, so a three-word value in `known` matches with no
      edit. This is trap 1—the naive `answer.split()` passes every single-word case and fails
      exactly on the values the prompt displays with a space; run and observe them fail
- [X] T011 [P] Write failing tests for `offer(question, values, note=...)` in
      `tests/test_prompts.py`: composes `"{question} ({values}{note})"`, returns `question`
      unchanged when values are empty and no note is given, and emits the note alone when values are
      empty (FR-012's phrasing); run and observe them fail
- [X] T012 Implement `spell`, `key`, `numbers`, `split_values` and `offer` in
      `src/cetools/cli/prompts.py`—five pure functions importing nothing from `cetools.engine`—
      and run `uv run pytest tests/test_prompts.py --no-cov` green

**Checkpoint**: the engine publishes every closed set and the CLI can spell one, collapse one and
split an answer that names several. User stories can now begin.

---

## Phase 3: User Story 1 - Every closed question names its answers (Priority: P1) 🎯 MVP

**Goal**: Every interactive question whose answers come from a table or an enum names them in the
prompt, spelled with spaces, with `none` last where the question accepts it. The three open
questions gain their `none` note and no list.

**Independent Test**: quickstart.md Scenario 1—press Enter through a starship session and a
small-craft session and read stderr against contracts/prompt-contract.md §1. Every listed question
names its set; the fitting list omits the small craft hangar; the computer models read `1-7`.

**Scope note**: each reader in this phase also *accepts* what it displays, via `prompts.key`, and
raises its refusal in the displayed spelling (research.md Decision 3). That is what keeps US1 honest
rather than a prompt that lists values it would reject. US3 is the exhaustive proof of it, not its
first appearance.

### Tests for User Story 1 ⚠️

- [X] T013 [P] [US1] Rewrite the parametrised prompt table at `tests/test_cli.py:1033-1040`
      (`configuration`, `computer`, `electronics`, `staterooms`, `fitting`, `bay`, `screen`, `name`)
      to the exact strings in contracts/prompt-contract.md §1; run
      `uv run pytest tests/test_cli.py --no-cov` and observe every rewritten row fail
- [X] T014 [P] [US1] Rewrite the remaining single-prompt assertions in `tests/test_cli.py` for
      `Hull class` (1471), `Armor` (1872, 1941, 1952), `Screen` in both the `[roll]` (1513) and the
      small-craft `[none]` (1502) forms, `Turret N mount` (1657, 1659), `Turret N weapon` (1658),
      `Purpose` (1100) and the `Staterooms` assertion inside the revise test (1274)—that last one
      sits outside the parametrised table and is the assertion the earlier count of 29 missed; run
      and observe them fail
- [X] T015 [P] [US1] Add tests in `tests/test_cli.py` asserting that the fitting prompt does **not**
      name a vehicle hangar (AS 1.4, FR-024) and that the computer prompt shows `1-7` rather than
      seven enumerated models (AS 1.5, FR-005); run and observe them fail
- [X] T016 [P] [US1] Add tests in `tests/test_cli.py` for FR-006's three open questions:
      `Staterooms (a count, or none) [roll]: `, `Name (any text, or none) [roll]: `, and that
      `Purpose [none]: ` names no `none` and gains no list; run and observe them fail
- [X] T017 [P] [US1] Add refusal tests in `tests/test_cli.py` (FR-016): a bad answer at the
      electronics, fitting, screen and turret-mount questions is refused with the values named in the
      *displayed* spelling, in the same order the prompt used, `none` included where accepted, and
      the question is asked again (AS 1.7, AS 3.5); run and observe them fail

### Implementation for User Story 1

- [X] T018 [US1] In `src/cetools/cli/ship.py`, import `cetools.cli.prompts` and the new accessors
      from `cetools.engine.ships`, and add the one shared helper that takes a question and a value
      set and returns both the composed prompt and the displayed-spelling refusal message, so no
      reader spells its own list. Take a rendering callable (`prompts.spell` for words,
      `prompts.numbers` for numeric runs) so the same helper serves Phase 4's numeric readers
- [X] T019 [US1] Rewrite the enum-backed readers in `src/cetools/cli/ship.py`—`_read_hull_class`,
      `_read_configuration`, `_read_armor`—to normalise the answer with `prompts.key`, refuse in
      the displayed spelling, and compose their questions at the `_ask_constraints` call sites; the
      armour prompt carries its shape note (`each with a percent, or none`) and `none` last, and the
      multiple-of-5 rule stays in `build_ship` (FR-023).

      `_read_armor` needs its parse changed, not just its normalisation: it requires exactly two
      whitespace-separated parts today (ship.py:232), and a displayed type is two words. Per
      contract §5 the **last** token is the percent and everything before it is the type, so
      `bonded superdense 15`, `bonded_superdense 15` and `Bonded-Superdense 15%` are one answer and
      an answer of fewer than two tokens earns the existing `give an armor type and a percent`
      refusal
- [X] T020 [US1] Rewrite the table-backed readers in `src/cetools/cli/ship.py`—`_read_computer`,
      `_read_electronics`, `_read_fitting`, `_read_bay`, `_read_screen`—to check membership against
      `computer_models()`, `electronics_packages()`, `fitting_kinds()`, `bay_kinds()` and
      `screen_kinds()`, and compose their questions at the `_ask_constraints` call sites with `none`
      last (research.md Decision 8)
- [X] T021 [US1] Compose the turret mount and weapon questions in `_ask_turrets` in
      `src/cetools/cli/ship.py` from `turret_mounts()` and `turret_weapons()`, and rewrite
      `_read_turret_mount` and `_read_turret_weapon` to accept the displayed spelling; all five
      mounts are named on a small craft too, since `_SMALL_CRAFT_TURRET_MOUNTS` narrows what is
      *drawn* rather than what may be pinned (contract §8)
- [X] T022 [US1] Add FR-006's notes to the two open questions in `src/cetools/cli/ship.py`—
      `Staterooms (a count, or none)` and `Name (any text, or none)`—and leave `Purpose` exactly as
      it is, its `[none]` label already saying it
- [X] T023 [US1] Run `uv run pytest --no-cov` and bring the whole suite green, then
      `uv run black . && uv run flake8 src tests`

**Checkpoint**: a referee can pin armour, configuration, electronics, computer, fitting and screen
without consulting the SRD (SC-003). US1 is independently demonstrable.

---

## Phase 4: User Story 2 - Hull-dependent questions name what this hull can take (Priority: P2)

**Goal**: The questions whose sets follow from the hull name the narrowed set, say so when the hull
was left to the dice, and say the hull can take none of them when the set is empty. Their refusals
name the set in the same notation. The revise question names all sixteen answers.

**Independent Test**: quickstart.md Scenario 2 and Scenario 5—pin a 40-ton small craft and read
`Maneuver rating (1-3)`; pin a 200-ton starship and read `Turrets (1-2, none)`; press Enter at hull
tonnage and read the `on some starship hull` qualifier; reach the empty form through the revise loop.

### Tests for User Story 2 ⚠️

- [X] T024 [P] [US2] Rewrite the hull-tonnage, jump/manoeuvre/power-rating and turret-count prompt
      assertions in `tests/test_cli.py` (including `Power plant rating (at least N)` at lines 1791,
      1802 and 1820, `Hull tonnage [roll]:` at 1960 and 2007, and the `Turrets [roll]:` assertions at
      1275, 1647 and 1734) to the narrowed and unnarrowed forms of contracts/prompt-contract.md §4,
      with the floor clause inside the same parentheses **where the pinned drives establish one**
      (FR-013) and absent where none is pinned; run and observe them fail
- [X] T025 [P] [US2] Add refusal-notation tests in `tests/test_cli.py` for the numeric prompts
      (FR-016, trap 2). A refused hull tonnage names `valid: 100-1000 by 100, 1200-2000 by 200,
      3000-5000 by 1000`; a refused rating on a 400-ton hull names `available: 1-6`; a refused
      turret count on a 200-ton hull names `available: 1-2, none`, where its message names no set at
      all today. Assert the collapsed notation, not merely that a set appears—the reason sentences
      are unchanged, so the existing assertions at 1536, 1633, 1733, 2006 and 2030 stay green and
      these are what must go red; run and observe them fail
- [X] T026 [P] [US2] Add the unnarrowed turret-count tests in `tests/test_cli.py` (FR-011, trap 3):
      with Enter at hull tonnage the prompt reads `Turrets (1-50 on some starship hull, none)
      [roll]: ` on a starship and `Turrets (1 on some small craft hull, none) [roll]: ` on a small
      craft, and a count of `51` is **refused** with `available: 1-50, none` and the question asked
      again—where today it is accepted, no count being checked without a pinned tonnage; run and
      observe them fail
- [X] T027 [P] [US2] Add a test in `tests/test_cli.py` driving the one session that reaches an empty
      narrowed set (research.md Decision 9): Enter at hull tonnage, pin a manoeuvre rating, revise
      `hull tons` to 10 and revise `power rating`. Assert
      `Power plant rating (a 10-ton hull can carry none, at least 6) [roll]: `, that it names no
      value, and that a typed answer is **refused with that same reason** rather than accepted
      (FR-012); run and observe it fail
- [X] T028 [P] [US2] Rewrite the revise-prompt assertion in `tests/test_cli.py` to the sixteen
      spaced names of contract §3, and add `_read_fields` acceptance tests for all four forms—
      `hull class, hull tons`, `hull class hull tons`, `hull_class hull_tons`, and mixed case—plus
      a rejection naming the unknown answer; run and observe them fail

### Implementation for User Story 2

- [X] T029 [US2] Add the three narrowing phrasings to the prompt composition in
      `src/cetools/cli/ship.py`: bare values when a tonnage is pinned (FR-010), the
      `on some {ruleset} hull` qualifier when it was left to the dice (FR-011), and the
      `a {n}-ton hull can carry none` form naming no value when the set is empty (FR-012)—and make
      an empty set refuse every typed answer with that same reason
- [X] T030 [US2] Route the numeric readers in `src/cetools/cli/ship.py`—`_read_hull_tons`,
      `_read_rating` and its two narrowing wrappers, `_read_turret_count`—through T018's helper so
      each checks membership against its accessor first and raises the reason with the set rendered
      by `prompts.numbers` (FR-016). Keep each engine sentence word for word and change only the set
      beside it; the engine's own messages keep their bare lists for library callers (research.md
      Decision 3). The power-plant **floor** refusal is not a set refusal and is left alone
- [X] T031 [US2] Compose the hull-tonnage question in `src/cetools/cli/ship.py` from
      `hull_tonnages(hull_class)` through `prompts.numbers`, so a starship reads
      `100-1000 by 100, 1200-2000 by 200, 3000-5000 by 1000` and a small craft reads `10-95 by 5`
      (FR-009, FR-005)
- [X] T032 [US2] Compose the jump, manoeuvre and power-plant rating questions in
      `src/cetools/cli/ship.py` from `available_ratings`, `small_craft_maneuver_ratings` and
      `small_craft_power_ratings`, choosing the phrasing by narrowing state, and keep `power_floor`'s
      clause inside the same parentheses in all three states **when it returns a floor**, omitting it
      when it returns `None` (FR-013). The sets are computed where the question is asked, so a
      question re-asked after a revised tonnage names the new set (FR-010)
- [X] T033 [US2] Compose the turret-count question in `_ask_turrets` in `src/cetools/cli/ship.py`
      from `hardpoints(hull_class, hull_tons)` with `none` last, passing the tonnage through
      unpinned so the unnarrowed form names the ruleset maximum with its qualifier; make
      `_read_turret_count` refuse a count above the named maximum **in both states**, which is the
      `hull_tons is not None` guard at ship.py:349 going away. Narrow each turret's weapon set with
      `small_craft_weapons(hull_tons, power_rating, mount)` using that turret's own mount (FR-010,
      FR-011, contract §1 notes on #13 and #13b)
- [X] T034 [US2] Name the sixteen revisable answers in spaced spelling at the revise prompt in
      `src/cetools/cli/ship.py`, and rewrite `_read_fields` to call `prompts.split_values` against
      `_REVISABLE`, still accepting today's underscored form (research.md Decision 4, FR-007)
- [X] T035 [US2] Run `uv run pytest --no-cov` green, then `uv run black . && uv run flake8 src tests`

**Checkpoint**: US1 and US2 both hold. Every closed-set question now names its set, narrowed where
the hull narrows it, and refuses in the notation it displayed.

---

## Phase 5: User Story 3 - Answers may be typed the way they are shown (Priority: P3)

**Goal**: Prove exhaustively, rather than case by case, that the set a prompt displays is the set it
accepts—in every spelling a referee may reach for—and that a question added later cannot escape
the check.

**Independent Test**: quickstart.md Scenario 3 and Scenario 8—type each displayed spelling back and
see it accepted; then run `uv run pytest tests/test_cli.py -k acceptable_values -v --no-cov` and see
every closed-set prompt covered.

### Tests for User Story 3 ⚠️

- [X] T036 [P] [US3] Add alternate-spelling acceptance tests in `tests/test_cli.py` (FR-015):
      `pop up`, `pop_up`, `pop-up`, `Pop Up` and `POP_UP` are one answer at the turret-mount
      question; `bonded superdense 15` and `bonded_superdense 15` are one answer at the armour
      question; `basic  civilian` with a doubled space is the value `basic civilian`; run and observe
      them fail
- [X] T037 [US3] Fix in `src/cetools/cli/ship.py` any reader T036 catches that does not accept all
      four forms, routing it through `prompts.key`; run T036's tests green

      T036 passed immediately: Phase 3/4 already routed every closed-set reader through
      `prompts.key`, so no fix was needed here. Verified rather than assumed.

### The invariant (contracts/prompt-contract.md §7)

- [X] T038 [US3] Add the `(prompt, accessor, reader)` table and the parametrised
      `acceptable_values` test in `tests/test_cli.py` asserting §7's four clauses per row: every
      displayed value typed back verbatim is accepted; its stored and hyphenated spellings are
      accepted; `set(displayed) == set(accessor(...))`; and a value outside the set is refused with
      the set named in displayed spelling **and displayed notation**. Expand a displayed range into
      its members, and exclude the Enter label, the narrowing qualifier, the floor clause and a
      compound answer's shape note (FR-002). Give a hull-dependent prompt a row per narrowing state
      it can reach, so the turret count is covered both narrowed and unnarrowed

      Found and fixed a real gap while building this: on the small-craft turret-weapon path,
      `_read_small_craft_weapon` delegated an unknown weapon to `validate_small_craft_weapon`,
      whose message named the engine's bare, unnarrowed `turret_weapons()` list rather than the
      displayed, narrowed `small_craft_weapons(...)` set. Fixed by giving the reader its own
      `known` parameter (as every other closed-set reader has) and falling back to the engine's
      message only when the value *is* a real turret weapon that the plant can't run.
- [X] T039 [US3] Add the completeness assertion in `tests/test_cli.py` that the §7 table names every
      closed-set reader in `src/cetools/cli/ship.py`, and observe it red by temporarily deleting one
      row before restoring it—this is the assertion that stops a question added later escaping the
      invariant (research.md Decision 5)
- [X] T040 [US3] Add the exhaustive `key(spell(k)) == k` property in `tests/test_prompts.py` over
      every **word** value the accessors publish—the eight word accessors plus `ArmorType`,
      `Configuration` and `HullClass`, 39 values in all—and observe it red by temporarily feeding
      it a value containing a character `key` does not round-trip. The numeric accessors are outside
      it: `key(spell(100))` is the string `"100"` and a numeric answer is read with `int()`
- [X] T041 [US3] Assert in `tests/test_cli.py` that `0` is accepted as an alternate spelling of
      `none` at the two count questions and is **not** named in either list (FR-002); run green

**Checkpoint**: SC-002's two counts of exceptions are both zero, and asserted rather than read.

---

## Phase 6: User Story 4 - Armour options can be pinned (Priority: P4)

**Goal**: A new question, asked only after an armour type is pinned, takes any number of reflec,
self sealing and stealth in one answer and carries them to the built ship and the emitted TOML.

**Independent Test**: quickstart.md Scenario 4—pin `crystaliron 10` then `reflec stealth`, and find
`options = ["reflec", "stealth"]` under `[[armor]]` in the emitted TOML, round-tripping identically.

**Note**: everything downstream already exists and was verified rather than assumed (research.md
Decision 7): `ArmorFit.options`, `_validate_armor_fit`'s two refusals, the builder's charge, the
description's naming, and design.py's load and dump. This phase adds a reader and a question only.

### Tests for User Story 4 ⚠️

- [X] T042 [P] [US4] Add tests in `tests/test_cli.py` for the question itself: it appears directly
      after a pinned armour type as `Armor options (reflec, self sealing, stealth) [none]: `
      (AS 4.1); Enter pins the layer with no options (AS 4.3); `none` does the same though the prompt
      does not name it (FR-018); `reflec stealth` and `reflec, stealth` both pin both (FR-018); and
      the case trap 1 breaks—`self sealing` typed exactly as displayed is **one** option, and
      `reflec self sealing` is two options rather than three unknown words; run and observe them fail
- [X] T043 [P] [US4] Add refusal and skip tests in `tests/test_cli.py`: `reflec reflec` is refused
      with the reason and asked again (AS 4.6); `reflec bogus` is refused **whole**, pinning neither
      (FR-018); the question is not asked at all when armour was answered `none` (AS 4.4) or with
      Enter (AS 4.5, FR-019); run and observe them fail
- [X] T044 [P] [US4] Add revise tests in `tests/test_cli.py` (FR-021): revising `armor` re-asks the
      options question under the same rules (AS 4.7); revising `configuration` alone leaves pinned
      options untouched; revising `armor` and answering `none` drops the options with the layer they
      belonged to; run and observe them fail
- [X] T045 [P] [US4] Add the armour-options round-trip test in `tests/test_ship_design.py` (FR-020):
      a design carrying `options` dumps and reloads identically. This may already hold—`design.py`
      loads `options` at line 174 and dumps it at line 417—so observe it red by temporarily dropping
      `options` from the dump at design.py:417 before restoring it

      Confirmed already held: the test passed immediately. Verified rather than assumed by
      temporarily gating the dump line with `and False`, observing the round trip fail, and
      restoring it.

### Implementation for User Story 4

- [X] T046 [US4] Implement `_read_armor_options` in `src/cetools/cli/ship.py` against
      `armor_options()`: split the answer with `prompts.split_values`—**not** with
      `answer.split()`, which would break `self sealing` into two unknown words—accept the literal
      `none` and the empty answer, and refuse an unknown or repeated option whole with the values
      named in displayed spelling
- [X] T047 [US4] Ask the options question in `_ask_constraints` in `src/cetools/cli/ship.py` directly
      after the armour question, only when it produced an `ArmorFit`, and rebuild that fit as
      `ArmorFit(type=…, percent=…, options=…)`. The options live inside the `armor` field, so
      `DesignConstraints` gains no field and `_REVISABLE` stays at sixteen names (research.md
      Decision 7)

      Wiring this in required threading the new question through the existing `answered()` wrapper
      (a nested `ask_armor()` closure), so a revise round that does not name `armor` carries the
      whole fit—options included—unchanged, and one that does re-asks both questions together.

      Unplanned but required: the new question sits after `armor` in every session that pins a real
      type, so the seventeen pre-existing tests in `test_cli.py` that pin one via `_answers()` or a
      raw continuation string needed a slot for it. Added an `armor_options` keyword to `_answers()`
      that inserts the extra line automatically when the armour answer is real (default `""`,
      preserving every prior test's intent unchanged), and added one blank line to the five raw
      continuation strings that revise `armor` to a real type outside that helper. Also added the
      `_read_armor_options` row `test_acceptable_values_table_covers_every_closed_set_reader_in_ship_py`
      (Phase 5, Decision 5) requires of every closed-set reader, which the new function tripped
      immediately.
- [X] T048 [US4] Run `uv run pytest --no-cov` green, then `uv run black . && uv run flake8 src tests`

      Full gate run instead: `uv run isort . && uv run black . && uv run flake8 src tests &&
      uv run pytest && uv run python scripts/check_docs.py`—all five green, 3205 passed, 99.22%
      coverage on `src/cetools`. Manually confirmed end to end: an interactive session pinning
      `crystaliron 10` then `reflec stealth` shows `Armor options (reflec, self sealing, stealth)
      [none]: ` directly after the armour prompt and emits `options = ["reflec", "stealth"]` under
      `[[armor]]` in the TOML.

**Checkpoint**: all four user stories independently functional. SC-004 satisfied—all three armour
options reachable from the session where none was.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T049 [P] Add the SC-005 length-budget test in `tests/test_cli.py`, named so
      `uv run pytest tests/test_cli.py -k prompt_length` selects it: every prompt string the session
      writes—question, values, and the Enter label with its trailing space—is at most 160
      characters at 80 columns, save the revise question, which FR-007 exempts. Include the
      unnarrowed forms, the longest of which is `Turrets (1-50 on some starship hull, none) [roll]: `
      at 51 characters (research.md Decision 6)

      Composed the parametrised rows from the real `ship._closed_set` / `ship._narrowed_numbers`
      calls rather than a retyped table, so the budget is checked against actual composition; all
      29 rows passed immediately (the fitting question, at 114 characters, is the longest)
- [X] T050 [P] Add the SC-007 seed-parity test in `tests/test_cli.py`: an all-Enter session with a
      given seed produces byte-identical output to `generate` without `--interactive` at the same
      seed, so no roll was added and no draw order moved
- [X] T051 [P] Add the FR-008 stream-discipline test in `tests/test_cli.py`: with `--toml`, stdout
      carries valid TOML from its first line and no prompt or refusal text
- [X] T052 [P] Add the FR-023 boundary test in `tests/test_cli.py`: `fuel scoops` is still named at
      the fitting prompt on a distributed hull and still accepted there, the rules refusal arriving
      at assembly with the revise loop as it does today; and armour at a percent that is not a
      multiple of five is still accepted at the prompt. The prompt's list is a statement about what
      the question accepts, not a promise the ship will build—a prompt that shortened its list
      here would be duplicating a rule outward, which Constitution I forbids. This holds once US1
      lands, so observe it red by temporarily filtering `fuel_scoops` out of `fitting_kinds()`

      The armour-percent half was already covered by
      `test_ship_generate_interactive_armor_percent_rule_surfaces_at_assembly_not_the_prompt`
      (Phase 3). Added the fitting/fuel-scoops row and confirmed it red by filtering
      `fuel_scoops` out of `fitting_kinds()`, then restored the accessor
- [X] T053 [P] Add the FR-014 scoping test in `tests/test_ship_description.py`: a built ship's
      description still reads `pop-up turret` and `a self-sealing hull`, the SRD's own spelling,
      though the prompts now show `pop up` and `self sealing`. This is the guard that stops a global
      rename following the spelling rule out of the CLI and into the rules text, so observe it red
      by temporarily spacing `TURRET_MOUNTS["pop_up"].name` before restoring it
- [X] T054 [P] Update the README `--interactive` section in `README.md` (FR-022): describe what a
      prompt now shows, remove the claim that "an answer the tables do not recognise is rejected and
      asked again with the reason" as the referee's route to the acceptable set, and extend the
      armour paragraph to describe the options question
- [X] T055 Run `uv run python scripts/check_docs.py` and resolve every backticked symbol the README
      edit introduces—the eleven accessors must be exported for it to pass; `src/cetools/cli/`
      needs no module-map entry, the map covering `engine/` only

      Passed with no edits needed
- [X] T056 Walk quickstart.md Scenarios 1 through 8 by hand and confirm each expected output,
      including the SC-006 demonstration: add a throwaway key to `SCREENS` at runtime and find it
      named at the prompt with no edit to `src/cetools/cli/ship.py`

      Found and fixed four stale reproduction commands, all predating either the Phase 4 rating
      questions or the Phase 6 armour-options question: Scenario 2's empty-turret-set example, and
      Scenario 3 and 4's armour examples, were each missing the jump/maneuver/power blank lines (and,
      for a pinned real armour type, the new Armor options blank) that a full starship session now
      asks between hull tonnage and armour—so a value meant for the armour prompt was landing on
      Jump rating instead. Scenario 5 forced a tonnage shortfall (an *unmet* constraint, auto-revised
      with no field-choice prompt) where the text claimed it reached "Revise which answers"; that
      prompt is reachable only through a rules-illegal answer (`_ask_which_to_revise`), so the
      scenario was rewritten to force one the same way the passing `test_cli.py` revise-prompt test
      does, with an armour percent that breaks the 5% rule. Every other scenario's command was run
      verbatim and matched its documented expectation exactly
- [X] T057 Run the full gate green:
      `uv run isort . && uv run black . && uv run flake8 src tests && uv run pytest && uv run python scripts/check_docs.py`

      All five green: 3239 passed, 99.22% coverage on `src/cetools`, docs OK. (One flake8 line-length
      fix along the way: T052's test name was shortened.)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies
- **Foundational (Phase 2)**: depends on Setup—**blocks every user story**
- **US1 (Phase 3)**: depends on Phase 2
- **US2 (Phase 4)**: depends on Phase 2, and on T018's helper from Phase 3, which T030 extends to the
  numeric readers. Independent of US1's readers in principle; in practice both rewrite
  `src/cetools/cli/ship.py`, so run them in order rather than in parallel
- **US3 (Phase 5)**: depends on US1 and US2, because its table covers every closed-set prompt those
  phases produce, in every narrowing state
- **US4 (Phase 6)**: depends on Phase 2 only—`armor_options()`, `prompts.key` and
  `prompts.split_values` are all it needs. It may be taken before US2 or US3 if the armour capability
  is wanted early
- **Polish (Phase 7)**: T049–T053 depend on all four stories; T054–T055 depend on Phase 2's exports;
  T056–T057 last

### Within Each User Story

- Tests are written, run, and **seen to fail** before the implementation moves (Constitution III,
  step 2). Five tasks—T039, T040, T045, T052 and T053—verify behaviour that may already hold, so
  each names the specific temporary break that produces its red rather than assuming one
- Engine accessors before CLI readers; readers before their call sites in `_ask_constraints`
- Story green before the next priority begins

### Parallel Opportunities

- **Phase 2**: T003/T004 (`tests/test_ship_generator.py`) run alongside T008–T011
  (`tests/test_prompts.py`)—different files. T005–T007 and T012 are then two independent
  implementation tracks
- **Phase 3**: T013–T017 all edit `tests/test_cli.py` in different regions and can be written
  together, but must be run as one suite to observe the reds. T018–T022 all edit
  `src/cetools/cli/ship.py` and are strictly sequential
- **Phase 4**: T024–T028 together; T029–T034 sequential
- **Phase 6**: T042–T045 together (T045 is a different file entirely); T046–T047 sequential
- **Phase 7**: T049–T054 are six independent files/regions

---

## Parallel Example: Phase 2

```bash
# Two independent test-writing tracks, different files:
Task: "Accessor agreement tests for the eight table accessors in tests/test_ship_generator.py"   # T003
Task: "Accessor tests for fitting_kinds, small_craft_weapons, hardpoints in tests/test_ship_generator.py"  # T004
Task: "spell/key tests in tests/test_prompts.py"                 # T008
Task: "numbers() run-collapsing tests in tests/test_prompts.py"  # T009
Task: "split_values() greedy-scan tests in tests/test_prompts.py"  # T010
Task: "offer() composition tests in tests/test_prompts.py"       # T011

# Then two independent implementation tracks:
Task: "Eight table accessors in src/cetools/engine/ships/generator.py"        # T005
Task: "spell/key/numbers/split_values/offer in src/cetools/cli/prompts.py"    # T012
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1: Setup (T001–T002)
2. Phase 2: Foundational (T003–T012)—**blocks everything**
3. Phase 3: User Story 1 (T013–T023)
4. **STOP and VALIDATE**: run quickstart.md Scenario 1 against both a starship and a small-craft
   session. At this point a referee who does not know the SRD tables can answer the majority of the
   session's questions, which is the population the wizard exists for

### Incremental Delivery

1. Setup + Foundational → the engine publishes every set and the CLI can spell one
2. + US1 → every closed question names its answers (**MVP**)
3. + US2 → hull-dependent questions name what *this* hull can take, and refuse in the same notation
4. + US3 → the `displayed == accepted` invariant is proved exhaustively and cannot be escaped
5. + US4 → armour options become reachable, the one new capability
6. + Polish → README, the boundaries, the three regression budgets, the gate

Each step leaves the suite green and the session usable.

### Notes

- Copy prompt strings from contracts/prompt-contract.md; do not retype them from the spec's prose
- `src/cetools/cli/` holds no game logic: a reader checks membership in an engine-published set and
  hands the stored key on. Two sets carry a real judgment (`fitting_kinds`, `small_craft_weapons`)
  and both are decided in `generator.py` (Constitution II)
- No table, validator, roll or `RollName` changes anywhere in this feature (Constitution IV). The one
  behaviour change outside prompt text is T033's: a turret count above the ruleset maximum is refused
  where the tonnage is unpinned, which FR-002 requires of a prompt that names that maximum
- Commit after each task or logical group, Conventional Commits, one logical change per PR
