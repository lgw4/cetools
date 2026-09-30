# Implementation Plan: Kind Declarations

**Branch**: `008-kind-declarations` | **Date**: 2026-09-30 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/008-kind-declarations/spec.md`

## Summary

`src/cetools/rules.py` enumerates the thirteen kinds of rules-data file in five
hand-kept structures: `_SUPPORTED_VERSION` (whose keys double as the set of
kinds), `_SINGLETON_KINDS`, `_CANONICAL_FILE` (plus its derived reverse), the
ten `parse_singleton(...)` calls, and the eleven-clause presence check. A
pinning test exists only to catch two of them disagreeing.

Replace all five with one private table, `_KINDS`, of one private record,
`_Kind(name, version, arity, canonical_file, parser)`, declared one line per
kind in `rules.py`. Discovery, the header checks, slot bookkeeping, the
missing/duplicate check, the one-file parse, and the presence check read the
table at call time. One loop over the declarations with a parser replaces the
call list; background skills keeps its explicit step after the substitutes;
careers and surnames keep their loops. The `RulesData(...)` constructor stays
explicit and reads a `dict[kind, value]`.

Nothing a user or library consumer sees changes, so the work lands as three
`refactor(rules):` commits with no `CHANGELOG.md` entry: declare the table and
make the old names views of it; point the readers at the table and delete the
old names; replace the call list with the loop.

## Technical Context

**Language/Version**: Python 3.13+ (`requires-python = ">=3.13"`)

**Primary Dependencies**: none new. Standard library only (`dataclasses`,
`typing.Literal`, `typing.Any`).

**Storage**: N/A. No `.toml` file under `src/cetools/data/` is added, edited,
or moved; no OGC or licensing question arises.

**Testing**: pytest. `tests/unit/test_rules.py` gains three declaration
invariant tests (FR-015), has its pinning test rewritten, and has its two
version-bump patches and one version loop pointed at `_KINDS` (FR-012). No
other test file changes. The golden, contract, and integration corpora are the
regression net and may not be edited; a scratchpad header harness
([quickstart.md](quickstart.md) 1c) covers the kind-machinery reports they do
not name.

**Target Platform**: OS-independent; CI runs Linux, macOS, and Windows on
Python 3.13 and 3.14.

**Project Type**: single project, an importable library plus a thin CLI
(Principle I).

**Performance Goals**: N/A. The loader runs once per load; the table is
thirteen small records, rescanned a handful of times per load.

**Constraints**: no change to any output, report, wording, location, or order
(FR-012); `problems.sort()` stays where it is (FR-013); no change to
`src/cetools/__init__.py` or `contracts/library-api.md` (FR-002, user input);
`rules.py` ends shorter than its 1103 lines at `0074436` (SC-004).

**Scale/Scope**: one source module and one test module. Four module-level
tables (42 lines) become a record type and a 13-line table; ten parse calls
become one loop; eleven presence clauses become one expression.

No NEEDS CLARIFICATION remains. The spec left none; the shape questions the
user input did not settle are decided in [research.md](research.md).

## Constitution Check

*GATE: passed before Phase 0. Re-checked after Phase 1 design; see below.*

| Principle | Assessment |
|---|---|
| **I. Library-First** | Pass. Internal to the library; the CLI is untouched. |
| **II. CLI Text I/O Protocol** | Pass, vacuously and by design: no command, option, stream, exit code, or byte of output changes (FR-012). |
| **III. Test-First (NON-NEGOTIABLE)** | Pass. Commit 1's FR-015 and rewritten pinning tests fail on the missing `_KINDS` before it exists. Commit 2's retargeted version-bump tests fail while the readers still read the derived constant. Commit 3 is the refactor step under a green suite plus the harness (research R8). |
| **IV. Seed-Reproducible Generation** | Pass, vacuously. No `Roller`, `random`, or clock is touched; validation stays deterministic, and parse-order changes are erased by the unmoved sort. |
| **V. Data-Driven Rules Content** | Pass. The table holds loader metadata (schema names, versions, basenames, parsers), not rules content; that metadata lives in `rules.py` today and stays there. No data file changes. |
| **VI. Simplicity (YAGNI)** | Pass; see below. |

**Principle VI in detail.** This removes enumerations rather than adding a
layer: five hand-kept structures become one, and the module gets shorter
(SC-004). The record has exactly the facts its readers ask for; the
`RulesData` field name the architecture review proposed is left out because
the explicit constructor (FR-010) gives it no reader. Deliberately not done: no
dependency mechanism for background skills, no uniform loop for the two
many-file kinds (FR-009), no registry abstraction, no export.

**Post-Phase-1 re-check**: unchanged. The design adds one private dataclass,
one private tuple, and three tests, and deletes four tables, ten calls, and a
pinning assertion. Complexity Tracking stays empty.

## Project Structure

### Documentation (this feature)

```text
specs/008-kind-declarations/
├── spec.md                       # /speckit-specify, /speckit-clarify
├── plan.md                       # This file
├── research.md                   # Phase 0: nine decisions
├── data-model.md                 # Phase 1: the record and the table
├── quickstart.md                 # Phase 1: verification, incl. the header harness
├── contracts/
│   └── kind-declarations.md      # Phase 1: record, readers, invariants
├── checklists/
└── tasks.md                      # Phase 2 (/speckit-tasks; not created here)
```

### Source Code (repository root)

```text
src/cetools/
├── rules.py          # _Kind + _KINDS after parse_task_parameters; readers retargeted;
│                     # four tables deleted; parse loop; presence check; constructor reads values
├── __init__.py       # unchanged
└── data/             # unchanged

tests/
├── unit/test_rules.py            # 3 new invariant tests; pinning test rewritten;
│                                 # :324, :342 patches and :824 loop read _KINDS
└── golden/, contract/, integration/, guards/   # unchanged
```

**Structure Decision**: the existing single-project layout. The table lives in
`rules.py`, its only reader (user input, FR-002). It sits in a new section
after `parse_task_parameters`, because it names that parser and the module
would otherwise fail to import (research R3).

## Approach

Three commits, each green under the full suite and each with an empty header
harness diff (research R8, [quickstart.md](quickstart.md)).

### Commit 1: `refactor(rules): declare each rules-data kind once`

1. Red: add the three FR-015 tests (unique names; arity and canonical file
   agree; one-file kinds without a parser are exactly background skills, and
   many-file kinds have none) and rewrite the pinning test at `:605-623` to
   check each one-file declaration's `canonical_file` against
   `_packaged_kind_map`, with no list comparison and no count. All fail on
   `AttributeError`.
2. Green: add `_Kind` and `_KINDS` (values from [data-model.md](data-model.md)),
   and redefine `_SUPPORTED_VERSION`, `_SINGLETON_KINDS`, `_CANONICAL_FILE`, and
   `_KIND_AT_CANONICAL_FILE` as expressions over `_KINDS`, placed after it.
   Readers untouched.

### Commit 2: `refactor(rules): read kind facts from the declarations`

1. Red: point the `:324` and `:342` monkeypatches at `_KINDS` through a small
   `replace`-based helper, and the `:824` loop at `k.version for k in _KINDS`.
   The two bump tests fail: the readers still read the import-time derived
   `_SUPPORTED_VERSION`.
2. Green: `_packaged_kind_map`, `_singleton_slots`, the header checks (via one
   `{name: _Kind}` lookup built per `_validate` call), and the
   missing/duplicate loop read `_KINDS`. Delete the four derived names. Rewrite
   `_singleton_slots`'s docstring, which cites `_CANONICAL_FILE` and the old
   test name.

### Commit 3: `refactor(rules): parse one-file kinds in one loop`

1. Replace the ten `parse_singleton` calls with one loop over declarations that
   have a `parser`, storing into `values: dict[str, Any]`.
2. Read the cross-file rules' kinds into locals from `values`.
3. Keep the background-skills step explicit, after the substitutes, storing
   into `values["background-skills"]`.
4. Replace the eleven `is None` clauses with
   `any(values.get(k.name) is None for k in _KINDS if k.arity == "one")`,
   keeping `or not surnames`.
5. Build `RulesData(...)` field by field from `values[...]`.
6. Drop the load-bearing-order sentence from `parse_singleton`'s docstring;
   keep its pointer to the single sort.

Then: full suite, header harness diff, 007's body harness diff, line count.

## Risks and how they are handled

| Risk | Handling |
|---|---|
| Parse order changes and a report moves | Per-file carriers plus the unmoved sort make it impossible (research R4); the harness diff on commit 3 checks it. If it ever diffs, stop and reconsider; never adjust tests or move the sort (spec, Assumptions). |
| Unknown-kind wording follows declaration order | Readers join `sorted(...)` names, as today; the harness's unknown-kind cases pin the string. |
| Version-bump tests pass for the wrong reason | Nothing is derived at import (research R2), so patching `_KINDS` reaches every reader. Commit 2's red step proves the patch is what makes them pass. |
| A duplicate declaration collapses silently | The table is a tuple, not a dict, and FR-015 test 1 checks uniqueness. |
| Background skills parsed twice or not at all | FR-015 test 3, plus the presence check failing the packaged load if it is never parsed. |
| The module grows | One-line positional declarations (research R1); `wc -l` against 1103 in the quickstart. |
| A docstring names a deleted table or renamed test | `_singleton_slots`'s docstring is rewritten in commit 2; the quickstart's `rg` for the old names covers `src` and `tests`. |

## Complexity Tracking

No Constitution Check violations. Nothing to justify.
