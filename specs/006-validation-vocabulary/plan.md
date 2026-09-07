# Implementation Plan: Validation Vocabulary

**Branch**: `006-validation-vocabulary` | **Date**: 2026-09-07 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/006-validation-vocabulary/spec.md`

## Summary

Five modules that parse rules-data TOML files each hand-roll the same
field-checking logic. Sixteen definitions of seven checks are spread across
`rules.py`, `careers.py`, `registries.py`, `names.py`, and `chargen.py`, and
they have already drifted: the integer check exists in three variants and the
string check in two.

Give the checking layer one home. Add `src/cetools/schema.py` owning the seven
checks, and have all five parsers call into it—at the seventy-three named
call sites and at the eleven places that express the same checks inline without
ever naming them.

Two of the divergences are behavioral, because merging forces one wording. Both
ship first, in their own commit with their own tests and one changelog entry,
because there is no single definition to extract until the copies agree on what
to say. A guard under `tests/guards/` then holds the rule, since the
duplication accumulated one locally reasonable copy at a time and a note would
not have stopped the seventeenth.

`errors.py` already gives `ValidationProblem` and `type_name` one home; its
`type_name` docstring states the motive—"Settled here rather than at each site
so the three schema modules cannot drift apart." This feature is that same
argument, applied one layer up, to the checks built on them.

## Technical Context

**Language/Version**: Python 3.13+ (`requires-python = ">=3.13"`)

**Primary Dependencies**: none new. `typer` is the only runtime dependency and
is untouched. The vocabulary uses the standard library only, per Principle VI.

**Storage**: N/A. Rules content lives in `.toml` files under
`src/cetools/data/`; this feature changes how those files are *checked*, never
what they contain and never where they live.

**Testing**: pytest, with `hypothesis` available. New: `tests/unit/test_schema.py`
(the vocabulary's own tests, written first) and
`tests/guards/test_no_duplicate_checks.py` (the FR-014a guard). The existing
suite is the regression net and must pass unchanged apart from the wording
assertions the behavioral commit adds.

**Target Platform**: OS-independent. CI runs Linux, macOS, and Windows against
Python 3.13 and 3.14.

**Project Type**: single project—an importable library plus a thin CLI
consuming it (Principle I).

**Performance Goals**: N/A. Validation runs once over 42 packaged data files at
load or on `cetools validate`; nothing here is on a hot path, and the checks do
the same work they do today.

**Constraints**: no new runtime dependency; no change to the library's public
surface; no change to any validation message beyond the two the spec names; no
change to any `.toml` file, so no licensing or OGC implication.

**Scale/Scope**: 5 modules, 16 definitions removed, 7 added, 73 named call
sites rewired, 11 inline sites converted, 2 wording changes reaching 6 fields
and 13 call sites respectively. Roughly 200 lines added in `schema.py` against
several hundred removed.

No NEEDS CLARIFICATION remains. The three questions that would have been open
were settled in `/speckit-clarify` and are recorded in the spec's Clarifications
section; the design decisions behind the names and signatures are in
[research.md](research.md).

## Constitution Check

*GATE: passed before Phase 0. Re-checked after Phase 1 design—see below.*

| Principle | Assessment |
|---|---|
| **I. Library-First** | Pass. `schema.py` is a library module. The CLI is untouched and gains no logic. |
| **II. CLI Text I/O Protocol** | Pass, vacuously. No command, option, exit code, or output stream changes. Two `expected` strings inside `validate`'s report change, in both the text and JSON renderings, which is the feature. |
| **III. Test-First (NON-NEGOTIABLE)** | Pass, and load-bearing. `tests/unit/test_schema.py` is written before `schema.py` exists and must fail (FR-018). The behavioral commit asserts the new wording before changing the two source lines. The guard's own self-test proves it can fail. |
| **IV. Seed-Reproducible Generation** | Pass, vacuously. Nothing here touches `Roller`, `random`, the clock, or any generator. Validation is deterministic already and stays so; `unrecognized_key_problems` keeps its sort, which is what makes a report stable run to run. |
| **V. Data-Driven Rules Content** | Pass, and reinforced. No rules content moves into code—the opposite: the *rules about* what data files may contain get one home instead of five. No `.toml` file is added, edited, or moved, so no OGC or licensing question arises. |
| **VI. Simplicity (YAGNI)** | Pass, with the reasoning below. |

**Principle VI in detail**, since it is the one a "shared module" feature has to
answer for. This is deduplication, not speculative abstraction: seven checks
already exist sixteen times, and the interface is unchanged from the helpers it
replaces, so no new concept is introduced. The deletion test confirms it—delete
`schema.py` and the complexity reappears in five places, which is where it is
today.

Four adjacent deepenings were considered and deliberately not attempted, each
recorded in FR-020 with its reason in [research.md](research.md): a
`(file, location)` cursor, a shared array check, generalizing
`_CHARGEN_GROUPS` beyond `chargen.py`, and folding in the registry-resolution
helpers. An eighth, value-taking integer check was also considered and rejected
once the two loop sites turned out to be expressible with the existing
signature ([data-model.md](data-model.md), *The two loop sites*).

**Post-Phase-1 re-check**: unchanged. The design produced seven functions with
the signatures they already have, one new module, two new test files, and no
new dependency. No gate is violated, so Complexity Tracking below stays empty.

## Project Structure

### Documentation (this feature)

```text
specs/006-validation-vocabulary/
├── spec.md                          # /speckit-specify + /speckit-clarify
├── plan.md                          # This file
├── research.md                      # Phase 0: eight decisions, with alternatives
├── data-model.md                    # Phase 1: entities + the full migration inventory
├── quickstart.md                    # Phase 1: how to run and verify each story
├── checklists/
│   └── requirements.md              # Spec quality checklist
├── contracts/
│   └── schema-vocabulary.md         # Phase 1: the seven checks, string by string
└── tasks.md                         # Phase 2 (/speckit-tasks—not created here)
```

### Source Code (repository root)

```text
src/cetools/
├── errors.py             # unchanged: ValidationProblem, type_name
├── tasks.py              # unchanged: _check_dice
├── schema.py             # NEW: the seven checks
├── rules.py              # 2 definitions removed, 4 call sites rewired, 3 inline converted
├── careers.py            # 5 definitions removed, 19 call sites rewired, 2 inline converted
├── registries.py         # 2 definitions removed, 7 call sites rewired, 4 inline converted
├── names.py              # 2 definitions removed, 7 call sites rewired
├── chargen.py            # 5 definitions removed, 36 call sites rewired, 2 inline converted
└── data/                 # untouched

tests/
├── unit/
│   └── test_schema.py    # NEW: the vocabulary's own tests, written first
├── guards/
│   └── test_no_duplicate_checks.py   # NEW: the FR-014a guard
├── unit/test_careers.py, test_chargen.py, test_registries.py,
│   test_names.py, test_rules.py      # unchanged but for wording assertions
└── integration/test_validation_categories.py  # 43 tests, the regression net
```

**Structure Decision**: the existing single-project layout, unchanged.
`schema.py` is a flat module beside its four peers in `src/cetools/`, not a
package: seven functions in roughly 200 lines do not need one. Tests follow the
directory the project already assigns each kind—`tests/unit/` for a module's
own tests, `tests/guards/` for what CONTRIBUTING.md calls "whole-repository
invariants nothing else can check".

### Import position

```text
errors.py  ──┐
             ├──> schema.py ──> rules.py, careers.py, registries.py,
tasks.py   ──┘                  names.py, chargen.py
```

`schema.py` cannot be folded into `errors.py`: `require_roll` needs
`tasks._check_dice`, and `tasks.py:8` already imports from `errors.py`, so that
would close a cycle. See [research.md](research.md) R1.

## Approach

Three phases, in this order, because the order is forced rather than chosen.

### Phase A—behavioral: settle the wording (User Story 1, P1)

One commit. Tests first.

1. Assert `"a positive integer"` for a `minimum=1` field that reaches
   `chargen._require_int`; watch it fail. Change `chargen.py:102-111` to match
   `careers.py:192`.
2. Assert `"a non-empty string"` for an absent required text field; watch it
   fail. Change the absent-key branch of `_require_string` in `careers.py`,
   `names.py`, and `chargen.py`.
3. One `CHANGELOG.md` entry, covering both, and nothing else.

Six fields and thirteen call sites are affected; the complete list, and the
evidence that nothing pins either phrasing, is in
[data-model.md](data-model.md).

`require_roll`'s absent-key wording stays `"a string"` (FR-010a).
`test_rules.py:459` asserts it for `task.roll` and must keep passing untouched.

### Phase B—structural: build the vocabulary (User Story 2, P2)

Tests first, and they must fail on import.

1. Write `tests/unit/test_schema.py` from the tables in
   [`contracts/schema-vocabulary.md`](contracts/schema-vocabulary.md). It fails:
   there is no `schema.py`.
2. Write `src/cetools/schema.py`. Six checks are moves of implementations now
   genuinely identical; `optional_bool` is the one new function, written from
   the shape `careers.py:944-972` repeats twice.

No parser has changed yet, and the full suite still passes—which is what
makes this independently verifiable.

### Phase C—structural: migrate the parsers (User Story 3, P3)

Module by module, each its own commit, smallest first so a mistake shows up
where it is cheapest to find: `names.py` (7 sites), `rules.py` (4 + 3 inline),
`registries.py` (7 + 4 inline), `careers.py` (19 + 2 inline), `chargen.py`
(36 + 2 inline). Exact commit granularity is `/speckit-tasks`' call.

Each module: add the import, delete its definitions, rewire its call sites,
convert its inline sites, run the whole suite. The suite passing unchanged is
the proof; nothing else can be.

Then `tests/guards/test_no_duplicate_checks.py`, with its own can-it-fail
self-test, following `tests/guards/test_no_locale.py`'s `ast`-based pattern.

**No changelog entry for Phase B or C.** The extraction is invisible to a
library user, and claiming an entry would put noise in a document that exists to
tell readers what changed for them (FR-019).

## Risks and how they are handled

| Risk | Handling |
|---|---|
| A third divergence is discovered mid-migration and quietly absorbed | FR-013 makes it a finding to raise, not a message to rewrite. The AST comparison in research R6 says there is no third, but that check ran once, against today's tree. |
| A naive `require_dict` merge downgrades three "missing" reports to "NoneType" | Specified against explicitly: the value-taking check reports `None` as missing, and the three sites are named in [data-model.md](data-model.md). |
| The two loop sites look unconvertible and grow an eighth check | Shown convertible in [data-model.md](data-model.md): both iterate `.items()`, so container and key are in hand. |
| The guard passes while duplication grows back inline | Accepted and recorded. The guard catches a *named* definition, not a fresh hand-inlined check. Structural detection is a much larger machine aimed at a rarer mistake; the copies that actually accumulated were copies of a named helper, five times. See research R8, *Known limit*. |
| `chargen.py` carries half the call sites, so its migration is the riskiest | It goes last, after the pattern is established four times, and `test_chargen.py` plus the 43 tests in `test_validation_categories.py` cover it. |

## Complexity Tracking

No Constitution Check violations. Nothing to justify.
