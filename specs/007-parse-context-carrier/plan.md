# Implementation Plan: Parse Context Carrier

**Branch**: `007-parse-context-carrier` | **Date**: 2026-09-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/007-parse-context-carrier/spec.md`

## Summary

The rules-data parsers descend into TOML files carrying three things by hand:
which file is open, where in it the reader sits, and the running list of
problems. The file name appears in 53 function signatures, the location is
rebuilt by f-string at every level, and the problem list travels by three
different conventions — two of them four lines apart in the same function.

Replace the hand-carrying with one carrier. `ParseContext` in
`src/cetools/schema.py` holds the file, the location, and one shared problem
collection; `ctx.at("entries", index)` descends; `ctx.report(found=...,
expected=...)` records a bespoke problem; `ctx.failed` answers *did anything in
this scope fail* against the carrier's own watermark. The seven field checks
become methods on it, an eighth — `require_list` — absorbs fifteen copies of a
hand-written idiom and four bare guards, and the five copies of `_HEADER_KEYS`
collapse to one.

Nothing the tool reports changes. That is the whole promise, and it is why the
work lands as seven commits: the carrier first, delegating to the checks that
already exist so that nothing *can* have changed; then one parser per commit;
then a final commit deleting the superseded path and tightening the guards.
Every commit is structural, so no commit carries a `CHANGELOG.md` entry.

This is 006's argument one layer up. 006 gave the checks one home and
explicitly deferred the carrier — its FR-020, and its contract's "the
vocabulary never builds a path; it receives the finished one". This feature
reverses that deferral on purpose, which is why the older contract is annotated
rather than rewritten.

## Technical Context

**Language/Version**: Python 3.13+ (`requires-python = ">=3.13"`)

**Primary Dependencies**: none new. `typer` remains the only runtime
dependency and is untouched. The carrier is standard-library-only ordinary
library code, per Principle VI and the spec's closing assumption.

**Storage**: N/A. Rules content stays in `.toml` files under
`src/cetools/data/`; this feature changes how those files are *read*, never
what they contain, never where they live, and never what is reported about
them. No OGC or licensing question arises.

**Testing**: pytest. `tests/unit/test_schema.py` is adapted in place to the new
call shape (FR-026 — it keeps transcribing the 006 contract row by row and is
not thinned out). `tests/unit/test_parse_context.py` is new and covers what
only a carrier can get wrong (FR-027). `tests/guards/test_no_duplicate_checks.py`
is rewritten to walk the class body; `tests/guards/test_parsing_layer_shape.py`
is new and holds the four counts. The golden, contract, and integration corpora
are the regression net and may not be edited (FR-016); the mutation harness in
[quickstart.md](quickstart.md) covers the phrasings they never name.

**Target Platform**: OS-independent. CI runs Linux, macOS, and Windows against
Python 3.13 and 3.14.

**Project Type**: single project — an importable library plus a thin CLI
consuming it (Principle I).

**Performance Goals**: N/A. Validation runs once over 42 packaged files at load
or on `cetools validate`. A carrier per descent step is a three-field object;
the alternative was an f-string per step.

**Constraints**: no new runtime dependency; no change to the public library
surface or the CLI; no change to any reported file, location, wording, or
order, for any input; the loader's single `problems.sort()` stays exactly where
it is (FR-015).

**Scale/Scope**: 5 parser modules plus the loader. 52 file-name parameters
removed of 53 counted (research R7), 5 header-key constants to 1, 3
problem-passing conventions to 1, 19 array sites to `require_list`, 103
bespoke problems rerouted through the carrier, 17 emptiness questions given an
explicit scope. Roughly 150 lines added to `schema.py`; several hundred removed
across the parsers.

No NEEDS CLARIFICATION remains. The spec left none, and the shape questions the
user input to `/speckit-plan` did not settle are recorded as decisions in
[research.md](research.md).

## Constitution Check

*GATE: passed before Phase 0. Re-checked after Phase 1 design — see below.*

| Principle | Assessment |
|---|---|
| **I. Library-First** | Pass. `ParseContext` is a package-internal library object. The CLI is untouched and gains no logic. |
| **II. CLI Text I/O Protocol** | Pass, vacuously and by design. No command, option, exit code, stream, or byte of output changes — that is FR-014, the feature's central claim. |
| **III. Test-First (NON-NEGOTIABLE)** | Pass, and load-bearing. The adapted `test_schema.py` and the new `test_parse_context.py` are written and watched fail before `ParseContext` exists. Each guard's planted-violation self-test proves it can fail (FR-023). Per-parser commits are pure moves whose test is the existing suite plus the mutation harness, which must diff empty. |
| **IV. Seed-Reproducible Generation** | Pass, vacuously. Nothing here touches `Roller`, `random`, or the clock. Validation is deterministic and stays so: the unrecognized-key sort is unchanged and the loader's single sort over all problems is explicitly immovable. |
| **V. Data-Driven Rules Content** | Pass, and reinforced. No `.toml` file is added, edited, or moved. The *rules about* what data files may contain gain one more piece of shared machinery instead of a sixteenth hand-written copy. |
| **VI. Simplicity (YAGNI)** | Pass, with the reasoning below. |

**Principle VI in detail**, since a "carrier object" feature has to answer for
it. This is deduplication, not speculative abstraction. The three fields the
carrier holds are three things the parsers already carry; the eight methods are
eight checks that already exist, seven of them as functions taking the same
three things as arguments. The deletion test settles it: delete `ParseContext`
and 53 signatures grow a file name back, five modules grow a header-key
constant back, and fifteen copies of an array idiom reappear — which is where
the tree is today.

Two additions do need justifying:

- **`require_list`'s four keyword arguments** (`expected`,
  `expected_missing`, `expected_empty`, `allow_empty`). Three of the four exist
  only because the nineteen converted sites disagree with each other about
  wording and about whether an empty array is acceptable. Each disagreement is
  an [inventory.md](inventory.md) entry, and if any is ever settled the
  corresponding knob collapses with it. The alternative is not a simpler check;
  it is the nineteen hand-written copies this feature removes, or a message
  change FR-014 forbids.
- **The watermark.** One integer, computed in `__init__`, that makes a child
  carrier its own scope. Without it the seventeen emptiness questions would
  each need a caller-held token — a second thing to carry, in a feature about
  not carrying things.

Deliberately *not* attempted, so the boundary is explicit: the carrier is not
extended to describe a glob, a file pair, or an unopenable file (FR-013); no
inventory entry is acted on (FR-021); no `Protocol` or test double is
introduced (the real carrier over a real list is three fields); no snapshot
corpus is committed (research R10).

**Post-Phase-1 re-check**: unchanged. The design produced one class, one
constant, one new check, two test modules, two guard modules, and no new
dependency. No gate is violated, so Complexity Tracking below stays empty.

## Project Structure

### Documentation (this feature)

```text
specs/007-parse-context-carrier/
├── spec.md                       # /speckit-specify
├── plan.md                       # This file
├── research.md                   # Phase 0: ten decisions, with alternatives
├── data-model.md                 # Phase 1: the entity + the full site inventory
├── quickstart.md                 # Phase 1: how to run and verify each story
├── inventory.md                  # FR-021: wordings and gates found, deliberately unfixed
├── contracts/
│   └── parse-context.md          # Phase 1: the carrier, method by method
└── tasks.md                      # Phase 2 (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
src/cetools/
├── errors.py         # unchanged: ValidationProblem, type_name
├── tasks.py          # unchanged: _check_dice
├── schema.py         # ParseContext + HEADER_KEYS; the 7 free functions deleted at the end
├── names.py          # 4 signatures, 7 problems, 2 array sites, 3 scopes
├── rules.py          # parse_task_parameters + _class_effect_problems + the loader's carriers
├── registries.py     # 7 signatures, 16 problems, 1 array site + 2 bare guards, 5 scopes
├── careers.py        # 12 signatures, 37 problems, 5 array sites, 1 scope
├── chargen.py        # 20 signatures, 40 problems, 7 array sites + 2 bare guards, 7 scopes
└── data/             # untouched

tests/
├── unit/test_schema.py            # adapted in place to the method call shape
├── unit/test_parse_context.py     # NEW: descent, sharing, per-scope failure
├── guards/test_no_duplicate_checks.py   # rewritten to walk ast.ClassDef
├── guards/test_parsing_layer_shape.py   # NEW: the four counts
└── golden/, contract/, integration/     # the regression net, unedited

specs/006-validation-vocabulary/contracts/schema-vocabulary.md
                                  # one added line: signatures superseded (FR-025)
```

**Structure Decision**: the existing single-project layout, unchanged. The
carrier goes in `schema.py` rather than a new module: that module is already
the vocabulary's home, its import position is the one the carrier needs, and
splitting the checks from the thing that carries them would only add an import
edge (research R1). Tests follow the directory the project already assigns each
kind — `tests/unit/` for a module's own tests, `tests/guards/` for what
CONTRIBUTING.md calls "whole-repository invariants nothing else can check".

### Import position

```text
errors.py  ──┐
             ├──> schema.py ──> rules.py, careers.py, registries.py,
tasks.py   ──┘                  names.py, chargen.py
```

Unchanged from 006, and it is why `schema.py` cannot fold into `errors.py`:
`require_roll` needs `tasks._check_dice`, and `tasks.py` already imports from
`errors.py`.

## Approach

Seven commits, each green, each independently reviewable (FR-019). All seven
are structural (FR-018), so none carries a changelog entry: the extraction is
invisible to a library user and to a data-file author, and claiming an entry
would put noise in a document that exists to tell readers what changed for them.

### Commit 1 — the carrier, delegating

Tests first, and they fail on import.

1. Adapt `tests/unit/test_schema.py` in place: every case keeps transcribing
   its row of the 006 contract, rewritten to build a `ParseContext` and call
   the method. Add the `require_list` table from
   [contracts/parse-context.md](contracts/parse-context.md).
2. Write `tests/unit/test_parse_context.py`: a location built correctly across
   several levels of nested descent and through array indices, including the
   empty-parent case; a collection genuinely shared between parent and child
   rather than copied; per-scope failure reported correctly when a sibling
   scope has failed and this one has not (FR-027).
3. Write `ParseContext` and `HEADER_KEYS`. The seven inherited checks are
   two-line forwarding calls to the free functions that already exist;
   `require_list` is written directly, since it has nothing to delegate to.
4. Rewrite `tests/guards/test_no_duplicate_checks.py` to walk `ast.ClassDef`,
   carrying over its "the guard can fail" and underscore-prefixed-copy
   meta-tests, retargeted at a planted class body. For the duration of the
   migration it tolerates exactly one extra definition per name — the free
   function being delegated to, and only in `schema.py`. The tolerance states
   in the guard itself that it is temporary and that commit 7 closes it
   (FR-020).

Nothing calls the carrier yet, and every forwarding call reaches the code the
parsers already reach, so this commit *cannot* have moved a message. That is
what makes Story 3's first acceptance scenario checkable rather than merely
asserted.

### Commits 2–6 — one parser at a time

`names.py` (4 signatures), `rules.py` (2), `registries.py` (7), `careers.py`
(12), `chargen.py` (20). Smallest first, which is 006's order and for 006's
reason: the pattern is established four times before it reaches the module
holding a third of the sites.

Each commit does the same six things to one module:

1. Entry points take `(data, ctx)` and return the value or `None`; helpers take
   a carrier in place of `file`, `location`, and `problems` (research R6).
2. `rules._validate` builds one carrier per file for that module's kinds and
   extends its run-wide list from `ctx.problems`. `_SINGLETON_PARSERS` holds
   one signature at a time, so the dispatch for that module's kinds moves in
   this commit.
3. Descent becomes `ctx.at(...)`; every f-string that built a location goes.
4. The module's array sites become `require_list` calls, per the table in
   [data-model.md](data-model.md).
5. The module's emptiness questions become `ctx.failed` on the carrier that
   preserves each one's current meaning — file for fourteen, fragment for the
   three named in the spec, and a fourth if one turns up, in which case
   data-model.md and SC-007's count are corrected in the same commit.
6. The module drops `_HEADER_KEYS` and imports `HEADER_KEYS`.

Then: the whole suite, and the mutation harness diffed against the baseline.
An empty diff is the pass condition, and it is not optional — the suite names a
fraction of the distinct `expected` strings the source emits, and the ones it
never names are concentrated in exactly these conversions.

Two sites need a note in the code as they are converted, both pointing at
[inventory.md](inventory.md): `registries._parse_pseudo_hex`, whose
unrecognized-key call must stay on the file-level carrier to keep reporting at
a bare location (I-1), and the three arrays that accept empty where their
siblings reject it, which convert with `allow_empty=True` (I-4).

### Commit 7 — delete the superseded path

Not optional; the feature is not complete without it (FR-020).

1. Write `tests/guards/test_parsing_layer_shape.py` holding the four counts,
   each with a planted-violation self-test. Run it against the tree as it
   stands: it fails, because the free functions still take a file name and the
   `"an empty array"` literals still sit in `schema.py`'s function bodies as
   well as the class. That failure is this commit's red step.
2. Move the seven bodies into the class and delete the free functions.
3. Tighten `test_no_duplicate_checks.py` to the single-definition rule and
   delete the temporary tolerance and its expiry note.
4. Add the single line to
   `specs/006-validation-vocabulary/contracts/schema-vocabulary.md` saying its
   signatures are superseded by
   [contracts/parse-context.md](contracts/parse-context.md), and make no other
   edit to it (FR-025).
5. Full suite, full mutation sweep, empty diff.

## Risks and how they are handled

| Risk | Handling |
|---|---|
| A converted site moves a message no test names | The mutation harness (research R10, [quickstart.md](quickstart.md)) derives its inputs from the data files rather than from what anyone thought to test, and is diffed per commit. This is the risk the suite cannot cover, and 006 met it with a weaker version of the same tool. |
| A fragment scope is converted to the file scope by accident, so a sibling's failure suppresses this fragment's value | The carrier *is* the scope: `failed` measures against the carrier's own birth length, so a fragment helper that receives a derived carrier gets the fragment answer without asking for it. The three sites are named in [data-model.md](data-model.md), and `test_parse_context.py` pins the sibling-failed case directly. |
| The cross-reference gate is "fixed" while being converted | FR-017 forbids it, [inventory.md](inventory.md) I-6 records the question, and the integration suite's cycle case pins the current behavior. |
| Insertion order changes and a report reorders | One carrier and one collection **per file** (research R5), so files cannot interleave at all; within a file the loader's single sort erases the rest, and FR-015 forbids moving, bypassing, or routing around it. The one carrier that does not own its collection is the class-effect one, which the loader builds over its own run-wide list at the point that check runs today (research R4) — the same list, at the same point, so the insertion order there is the one the tree already produces. |
| Converting the four bare array guards silently starts rejecting an empty array | Caught in planning: three of the four accept empty today, so `require_list` grew `allow_empty` rather than a behavior change. [data-model.md](data-model.md) names them. |
| The pseudo-hex prefix anomaly is normalized away | Caught in planning, preserved deliberately with a comment, recorded as I-1. |
| SC-002's count of 53 cannot reach 0 without dragging the unopenable-file problem into a carrier that cannot describe it | Resolved in research R7 in favor of FR-012: `rules._unreadable` keeps its parameter, the guard names it as the one exclusion, and the plan reports 52 of 53 rather than quietly claiming 53. |
| `chargen.py` carries a third of the sites, so its commit is the riskiest | It goes last, after the pattern is established four times, and `test_chargen.py` plus the 43 cases in `test_validation_categories.py` plus the harness cover it. |
| The migration ends with the free functions still in place, so every check exists twice forever | Commit 7 is a named deliverable of FR-020 and its guard is what proves it landed. The temporary tolerance in guard 1 states its own expiry. |

## Complexity Tracking

No Constitution Check violations. Nothing to justify.
