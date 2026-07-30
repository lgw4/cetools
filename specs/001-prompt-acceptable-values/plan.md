# Implementation Plan: Acceptable Values at Interactive Ship Prompts

**Branch**: `001-prompt-acceptable-values` | **Date**: 2026-07-29 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-prompt-acceptable-values/spec.md`

## Summary

Every interactive question with a closed set of answers will name that set in its prompt, spelled
the way it may be typed, narrowed to the hull in hand—and the armour options that exist in the
rules and in the design format but have never been askable become askable.

The technical approach has three parts and one new capability:

1. **The engine publishes each question's value set.** Eleven one-expression accessors join the
   validators they pair with in `engine/ships/generator.py` and are exported from
   `cetools.engine.ships`. This is what makes FR-003 structural: the prompt and the acceptance check
   read one table, so a table edit moves the prompt (SC-006). It is also what keeps `cli/` free of
   game logic, since `tables.py` is not on the package's public surface.
2. **A new `cli/prompts.py` composes the text.** Five pure functions: the underscore-to-space
   spelling (FR-014), its inverse for input (FR-015), evenly-spaced-run collapsing (FR-005), the
   greedy longest-match split for an answer naming several values (FR-015, FR-018—a value may itself
   contain a space, so `self sealing` and `hull class` must survive the split), and the
   `question (values) [default]:` composition. Nothing here consults a rule.
3. **`cli/ship.py`'s readers show and check against the published set.** Each closed-set reader—the
   numeric ones as well as the word ones—raises its own refusal in the displayed spelling and the
   displayed notation (FR-016) and hands the stored key on to the engine record that has always
   ruled on it.
4. **Armour options become a question**, following the armour type-and-percent question and folded
   into the same `ArmorFit`. Everything downstream (validation, cost, description, TOML round-trip)
   already exists and was verified rather than assumed.

The one prompt exempt from the two-line budget is the revise question, which names all sixteen
answers and takes three lines (FR-007). Every other prompt was measured against every table in the
repository before the format was chosen; all fit (research.md Decision 6).

## Technical Context

**Language/Version**: Python 3.13 (`match`-free; PEP 695 generics already used in
`_ask_until_understood`)

**Primary Dependencies**: `typer` (CLI), `pytest` + `pytest-cov` (tests), `uv` (dependencies). No
new dependency.

**Storage**: TOML design files via `engine/ships/design.py`. Unchanged—`ArmorFit.options` already
loads (design.py:174) and dumps (design.py:417).

**Testing**: pytest, mirroring source layout. Touched: `tests/test_cli.py` (session behaviour and
the `displayed == accepted` contract), `tests/test_ship_generator.py` (the accessors), new
`tests/test_prompts.py` (spelling, run collapsing and the multi-value split),
`tests/test_ship_design.py` (the armour-options round trip), `tests/test_ship_description.py` (one
assertion that the SRD's hyphenation survives the prompts' spacing, FR-014).

**Target Platform**: terminal, 80 columns assumed for SC-005. stderr for all prompts, stdout for the
design only.

**Project Type**: single-project CLI over a library engine.

**Performance Goals**: N/A. Every accessor is a dict walk over a table of at most 18 rows, once per
prompt.

**Constraints**:

- SC-005: no prompt over two lines at 80 columns, save the revise question. Verified by measurement
  for every prompt (research.md Decision 6) and to be held by a length test.
- FR-008: prompts on stderr only, so `--interactive` keeps composing with `--toml` and `--out`.
- SC-007: Enter at every question still produces the same ship from the same seed as generation
  without `--interactive`. No `RollName` and no draw order changes.

**Scale/Scope**: 21 prompts (18 in the design walk, 2 in the revise loop, 1 new), of which FR-001
lists 18 as closed-set questions and FR-006 leaves 3 open. 39 published word
values across 10 tables, plus 4 numeric sets. One new CLI module (~55 lines), 11 new engine
accessors (~40 lines), most of `cli/ship.py`'s 20 readers touched, 31 existing prompt-string
assertions rewritten.

## Constitution Check

*GATE: passed before Phase 0 research; re-checked after Phase 1 design—see below.*

### I. Cepheus Engine SRD Fidelity

**Pass.** No rule and no table changes. Every displayed set is read from a table already transcribed
from the SRD, and the two SRD-hyphenated terms (`pop-up`, `self-sealing`) keep their SRD spelling in
the description renderer while the prompt shows a space, per FR-014's scoping of that rule to prompts
and refusals. The prompt's list is explicitly a statement about what the *question* accepts, not a
promise the ship will build—**FR-023**, promoted from an assumption in the checklist review because
FR-002's completeness claim rests on it: `build_ship` stays the sole authority on rules legality, and
no rule is duplicated outward to shorten a list. Armour's multiple-of-5 rule and the
distributed-hull fuel-scoop refusal continue to surface at assembly.

### II. CLI First, Logic Decoupled

**Pass, and the reason the engine gains a surface.** `cli/` may not hold game logic, and callers
must import from an engine package rather than reach into its modules—so `cli/ship.py` cannot
`import tables`. Two of the sets are not a table's bare keys (the fitting question excludes
vehicle-sized fittings per **FR-024**; the small-craft weapon set is filtered by the plant's energy
allowance), so computing them in `cli/` would *be* game logic. The accessors put that judgment beside the validator
that already makes it. `engine/` imports nothing from `cli/`; `prompts.py` imports nothing from the
engine.

The CLI's own membership check (research.md Decision 3) is input-domain validation against an
engine-published set, not a rule: the engine record still rules on the accepted key. It exists
because FR-016 requires the refusal to be spelled the way the prompt spelled it, and the engine's
messages must keep naming stored keys for library callers.

### III. Test-First (NON-NEGOTIABLE)

**Pass, with one hazard called out.** 31 existing assertions already contain the old prompt strings.
Rewriting one to the new string and finding it green would mean the prompt never changed—so each
rewritten assertion must be run and *seen to fail* before the reader moves, exactly as step 2
requires for a new test. This is the step most easily skipped here and is the one most worth
observing, because the failure mode is a test that looks like evidence and is not.

Coverage floor 85% on `src/cetools`. New code is CLI text composition, fully exercised by the
contract test.

### IV. Deterministic by Construction

**Pass.** No new randomness, no `RollName` change, no change to what is drawn or to draw order.
`_ARMOR_CHOICES`, `_TURRET_MOUNTS`, `_TURRET_WEAPONS` and `_SMALL_CRAFT_TURRET_MOUNTS` are roll
tables and are left alone—in particular the small-craft mount narrowing stays a narrowing of what
is *drawn*, so all five mounts are still named at the prompt. SC-007's seed parity is a test in
Scenario 7 of the quickstart.

### V. Simplicity

**Pass, with two additions justified in Complexity Tracking.** No record is introduced for a
Prompt or a value set—a tuple and two functions do the whole job. `DesignConstraints` gains no
field: armour options live inside the `armor` field, which is what makes FR-021 fall out for free and
keeps `_REVISABLE` at the sixteen names the spec counts.

### Development Workflow and Quality Gates

**Pass.** All five gate commands run before commit. `scripts/check_docs.py` obliges the README
update (FR-022) to keep every backticked symbol resolving; its module map covers `engine/` only, so
`cli/prompts.py` needs no map entry.

### Post-design re-check

Re-evaluated after Phase 1: **no new violations.** The design added one CLI module and eleven engine
one-liners and no records, no fields, no rules and no rolls. The two Complexity Tracking rows below
were both known before Phase 0 and neither grew.

### Re-check after the 2026-07-30 analysis review

Three artifact gaps were closed and none of them moves a principle:

- **A fifth function in `prompts.py`** (`split_values`). Still presentation: it splits an answer
  into words and matches them against a set handed in, and consults no rule (II). It is shared by
  the two questions that take several values rather than written twice (V).
- **The numeric readers own their refusals**, as the word readers already did. Same seam, same
  reason: the engine's messages keep their bare lists for library callers (II, Decision 3).
- **`hardpoints` accepts an unpinned tonnage** and the turret count is refused above the ruleset
  maximum where today it is not. This is the one *behaviour* change outside the prompts, and it is
  required by FR-002—a prompt that names `1-50` and accepts 51 displays a set it does not accept.
  No table, validator or roll changes (I, IV): the maximum is derived from `HULLS`, and
  `validate_turret_count` is untouched.

## Project Structure

### Documentation (this feature)

```text
specs/001-prompt-acceptable-values/
├── spec.md                          # Input
├── plan.md                          # This file
├── research.md                      # Phase 0: 10 decisions, all unknowns resolved
├── data-model.md                    # Phase 1: the five entities onto existing code
├── quickstart.md                    # Phase 1: 8 runnable validation scenarios
├── contracts/
│   ├── prompt-contract.md           # Phase 1: every prompt string, exact
│   └── engine-accessors.md          # Phase 1: the 11 new public functions
└── tasks.md                         # Phase 2 (/speckit-tasks—not created here)
```

### Source Code (repository root)

```text
src/cetools/
├── cli/
│   ├── ship.py                      # MODIFIED: readers show and check the published set;
│   │                                #   armour-options question; _read_fields rewritten
│   └── prompts.py                   # NEW: spell / key / numbers / split_values / offer
└── engine/ships/
    ├── generator.py                 # MODIFIED: 11 accessors beside their validators;
    │                                #   _hardpoints_for exposed as hardpoints
    ├── __init__.py                  # MODIFIED: export the 11
    ├── models.py                    # UNCHANGED (ArmorFit.options already validates)
    ├── tables.py                    # UNCHANGED
    ├── design.py                    # UNCHANGED (options already round-trip)
    ├── builder.py                   # UNCHANGED (already charges options)
    └── description.py               # UNCHANGED (already names options)

tests/
├── test_prompts.py                  # NEW: mirrors cli/prompts.py
├── test_cli.py                      # MODIFIED: 31 prompt assertions rewritten;
│                                    #   displayed==accepted contract; length budget
├── test_ship_generator.py           # MODIFIED: accessor/validator agreement
├── test_ship_design.py              # MODIFIED: armour-options round trip
└── test_ship_description.py         # MODIFIED: SRD hyphenation survives (FR-014)

README.md                            # MODIFIED: FR-022
```

**Structure Decision**: the existing single-project layout is kept—`src/cetools/engine/` for
rules, `src/cetools/cli/` for I/O binding, `tests/` mirroring both. The one structural addition is
`src/cetools/cli/prompts.py`, added because run collapsing and the spelling round trip deserve unit
tests over lists of integers and strings rather than scripted sessions, and because `ship.py` is
already 721 lines and this feature touches nearly every reader in it.

## Phase 0 output

[research.md](./research.md)—ten decisions, no NEEDS CLARIFICATION remaining:

1. The engine publishes each question's value set; the CLI never reads a table.
2. A `cli/prompts.py` module holds the text composition.
3. The CLI owns the refusal message for closed-set questions.
4. The revise prompt spaces its names, and `_read_fields` is rewritten. **(User decision,
   2026-07-29—this is the one spec ambiguity that changed the work.)**
5. `displayed == accepted` is enforced by a table-driven contract test.
6. The prompt format is `question (values) [default]:`, and it fits—measured.
7. Armour options live inside the `armor` field; `DesignConstraints` is unchanged.
8. `none` is named inside the value list, not as separate prose.
9. FR-012's empty narrowed set is reachable on exactly one path.
10. Existing prompt-text tests are rewritten, not extended.

## Phase 1 output

- [data-model.md](./data-model.md)—the spec's entities (Acceptable value set, Value spelling,
  Prompt, Armour options, Revisable answer) mapped onto existing code, with the invariants each
  carries. No new record; `ArmorFit.options` already exists.
- [contracts/prompt-contract.md](./contracts/prompt-contract.md)—every prompt string exactly as
  displayed, the three narrowing phrasings, the accepted answer forms, the refusal shape, and the
  `displayed == accepted` test that holds it all.
- [contracts/engine-accessors.md](./contracts/engine-accessors.md)—signatures, ordering, empty-set
  behaviour, and the accessor/validator agreement tests for the eleven new public functions.
- [quickstart.md](./quickstart.md)—eight runnable scenarios: one per user story, plus the revise
  loop, the length budget, seed parity and stream discipline, and the exhaustive invariant.

## Risks and how the design answers them

| Risk | Answer |
|---|---|
| A prompt displays a value it refuses—worse than displaying nothing (US3 rationale) | The contract test types every displayed value back at every prompt; SC-002's two counts are both asserted, and the table's completeness is asserted too |
| A rewritten prompt test passes without the prompt changing | Constitution III step 2 is called out explicitly above: each of the 31 rewritten assertions is run red first |
| A question added later escapes the invariant | The contract test is driven from one table of rows and asserts it covers every closed-set reader in `ship.py` |
| The two-line budget breaks as tables grow | Run collapsing keeps the numeric sets short; a length test per prompt is the regression guard |
| FR-012's empty-set branch looks like dead code and gets deleted | research.md Decision 9 records the one reachable session, and the quickstart tests it through that session |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 11 new public functions on `cetools.engine.ships` (Principle V) | FR-003 and SC-006 require the prompt and the acceptance check to read one table; Constitution II forbids `cli/` reading `tables.py`. Each accessor is a single expression sitting beside the validator it pairs with, so the shared-source property is structural rather than a convention | Exporting the raw tables would put two real judgments in `cli/`—which fittings a bare kind can install, and which weapons a plant can run—and those are game logic, which Constitution II forbids there. Deriving the sets by feeding every table key through the validator in a `try`/`except` reads the table anyway and turns a lookup into exception control flow |
| New module `src/cetools/cli/prompts.py` (Principle V) | Run collapsing (FR-005) and the `key(spell(k)) == k` round trip (FR-014, FR-015) are properties best asserted over lists of integers and strings; reaching them only through a scripted session would need a rules table of a particular shape to exist | Keeping it in `ship.py` was rejected on testability rather than size. Putting it in the engine was rejected because nothing in it consults a rule, and a library caller passes stored keys—an engine that spells values for a terminal spells them for nobody |
