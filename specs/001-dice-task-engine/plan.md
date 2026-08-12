# Implementation Plan: Dice and Task Check Engine

**Branch**: `001-dice-task-engine` | **Date**: 2026-08-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-dice-task-engine/spec.md`

## Summary

Bootstrap the `cetools` repository and deliver the seeded dice core every later
MVP feature depends on: reproducible randomness, dice throws, and 2D6 task checks
resolved against SRD parameters held in a shipped `tasks.toml`, exposed as library
API and surfaced through `cetools roll` and `cetools check`.

The technical approach is shaped by one decision that constrains everything else:
reproducibility rests only on what the standard library actually guarantees. Text
seeds are folded with blake2b rather than the per-process-salted built-in `hash()`;
every die face is built from `getrandbits` with rejection sampling rather than from
`randint` or `choice`, which the `random` docs decline to keep stable across
versions; and `random.Random` is only ever seeded with an integer, keeping us off
the `version=`-parameterized string-seeding path. All three were verified byte-for-
byte identical on CPython 3.10 through 3.14 before being written down. Randomness
lives in one explicitly-passed `Roller`, so no two callers can share a sequence by
accident, and every result carries the seed that produced it.

Rules content sits in data, not code, including the check's own `2d6` notation, so
a referee's house rule is a data edit. Loading is deliberately minimal and isolated
in one small module that feature 2 will replace rather than extend.

## Technical Context

**Language/Version**: Python 3.13+ (verified against 3.13 and 3.14; the seeded-RNG
recipe additionally verified stable on 3.10 through 3.12)

**Primary Dependencies**: Typer (runtime, sole third-party dependency, ratified in a
prior decision). Standard library otherwise: `random`, `secrets`, `hashlib`,
`tomllib`, `importlib.resources`, `functools`, `dataclasses`, `json`, `re`.

**Storage**: One packaged read-only data file, `src/cetools/data/tasks.toml`. No
database, no user-writable state, no filesystem search path.

**Testing**: pytest, hypothesis (property invariants), Typer's `CliRunner`,
committed golden files, plus two dedicated seed-contract guard tests.

**Target Platform**: Cross-platform CLI and importable library; developed on macOS,
no platform-specific code.

**Project Type**: Single library with a thin CLI (one distribution, per the ratified
library-and-CLI-architecture decision).

**Performance Goals**: None that constrain design. A check is a handful of integer
operations; CLI start-up dominates. Rules data is loaded once and cached.

**Constraints**: Reproducibility across CPython versions is the binding constraint
(FR-007) and rules out the higher-level `random` helpers. The JSON shape is a
committed public interface (FR-028); `seed` is emitted as a JSON **string** because
64-bit seeds exceed 2^53 and would be silently corrupted by a JavaScript consumer,
which the constitution names as a future client.

**Scale/Scope**: Roughly 7 small modules plus 1 data file; on the order of 600 lines
of implementation and a larger test suite. 34 functional requirements, 11 success
criteria.

**Toolchain**: uv for environment and dependency management, hatchling as build
backend, Black + isort (`profile = "black"`) + flake8 as non-gating quality tooling.
flake8 cannot read `pyproject.toml`, so it needs a separate `.flake8` set to
`max-line-length = 88` with `extend-ignore = E203` to agree with Black.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| **I. Library-First** | All game logic in importable modules; CLI contains none | **PASS** - `cli.py` parses arguments, calls the library, prints, sets exit codes. Rendering (text and JSON) lives in `render.py`, not the CLI, so both formats are unit-testable without a command runner and reusable by a future web UI. |
| **II. CLI Text I/O** | Every capability reachable from CLI; both output modes; stdout/stderr split; meaningful exit codes | **PASS** - `roll` and `check` cover every capability; `--json` on both; results to stdout, errors to stderr; 0 success (including a failed check), 1 library error, 2 usage error. |
| **III. Test-First** | Tests written first, confirmed failing, then implementation | **PASS** - task ordering enforces it; expected dice and arithmetic values are written literally before code exists. Lint/format tooling is present but explicitly not a gate, as the principle permits. |
| **IV. Seed-Reproducible** | Seed accepted everywhere; same seed and version give same output; no unseeded randomness | **PASS** - single explicitly-passed `Roller`; `getrandbits`-only derivation; blake2b text folding; seed echoed in every output unconditionally; two guard tests defend the contract. |
| **V. Data-Driven Rules** | SRD content in data files, none hard-coded | **PASS** - target, ladder, unskilled penalty, characteristic bands, and the check's own dice notation all in `tasks.toml`. SC-010 verifies that editing the file changes results with no code change. |
| **VI. Simplicity** | YAGNI; stdlib preferred; runtime dependencies justified | **PASS** - see below. |

**Principle VI in detail.** Typer is the only runtime dependency and was justified
in the ratified library-and-CLI-architecture decision (it derives the CLI from typed
signatures, keeping the CLI layer declarative and nearly logic-free, reinforcing
Principle I; argparse would be hand-written boilerplate growing with every
subcommand). Hypothesis is development-only and so does not engage the runtime-
dependency rule. TOML costs nothing because `tomllib` is standard library on the
supported floor. Deliberate omissions in service of YAGNI: no JSON error envelope,
no golden-file regeneration flag, no `--target` override, no rules-data search path.

**Licensing constraints.** `tasks.toml` opens with its Open Game Content designation
and contains neither "Cepheus Engine" nor "Samardan Press". Full OGL text bundling,
the Section 15 chain, and the compatibility statement belong to `packaging-release`;
only the per-file designation is in scope here, because the file is created here.

**Post-Phase-1 re-check**: still **PASS**. The Phase 1 design introduced no new
dependency and no new hard-coded rules content. The one design choice worth
recording against Principle VI is `ThrowResult` serving both dice throws and `d66`
with an overloaded `total`; a second result type was rejected as more machinery than
the problem needs, and the overload is documented explicitly in the JSON contract.

## Project Structure

### Documentation (this feature)

```text
specs/001-dice-task-engine/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── cli.md           # Command surface, notation grammar, rendering rules
│   ├── json-output.md   # Committed JSON shape
│   ├── library-api.md   # Public importable surface
│   └── tasks-toml.md    # Shipped rules data file
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (/speckit-tasks - NOT created here)
```

### Source Code (repository root)

```text
pyproject.toml           # hatchling, requires-python >=3.13, typer, dev group
.flake8                  # flake8 cannot read pyproject.toml
README.md
LICENSE                  # GPL-3.0

src/
└── cetools/
    ├── __init__.py      # public API re-exports and __all__
    ├── __main__.py      # python -m cetools (needed by the subprocess guard test)
    ├── errors.py        # CetoolsError, DiceError, RulesDataError, TaskError
    ├── seeds.py         # seed resolution and blake2b folding
    ├── dice.py          # Roller, notation grammar, ThrowResult, throw, d66
    ├── tasks.py         # Modifier, CheckResult, check
    ├── rules.py         # tasks.toml loading  <- the seam feature 2 replaces
    ├── render.py        # as_text / as_dict / as_json (singledispatch)
    ├── cli.py           # typer app; the only place CetoolsError is caught
    └── data/
        ├── __init__.py  # makes the directory an importable package
        └── tasks.toml   # Open Game Content

tests/
├── conftest.py
├── unit/                # seeds, dice, d66, tasks, rules, render
├── contract/            # committed JSON shape
├── integration/         # CLI behaviour and golden files
├── guards/              # seed-contract defence
├── property/            # hypothesis invariants
└── golden/              # committed rendered output, reviewed as diffs
```

**Structure Decision**: `src/` layout with a single `cetools` package, matching the
ratified one-distribution decision. `src/` is chosen so tests run against the
installed package rather than the working directory, which is what makes the
`importlib.resources` data loading honest: if packaging fails to include
`tasks.toml`, the test suite fails rather than silently reading it off disk.

Module boundaries follow the responsibilities that need to be independently
testable. `rules.py` is deliberately its own module despite being small, because it
marks the seam that `rules-data-loading` (feature 2) will replace wholesale;
isolating it now keeps that replacement from becoming a refactor. `render.py` is
separate because the library, not the CLI, owns rendering.

## Implementation Notes

Guidance to carry into `/speckit-tasks` and `/speckit-implement`.

**Build order** (each step's tests written and failing first, per Principle III):
`errors` → `seeds` → `dice` (Roller, grammar, throw, d66) → `rules` → `tasks` →
`render` → `cli` → golden files → guard tests → property tests. Seeds and dice come
before everything because the reproducibility contract they establish is what the
rest is tested against.

**Per the project's global instruction**, consult the matching `fluent-python:*`
skills when writing the code. The ones that apply here:

- `choosing-a-data-class-builder` - frozen slotted dataclasses for the result value
  objects
- `designing-function-signatures` - the keyword-only parameters on `check`, which is
  what prevents transposing `characteristic` and `skill`
- `using-functools-and-operator` - `singledispatch` for rendering, `cache` for data
  loading
- `designing-value-objects` - immutability and hashability of results
- `writing-generators-and-iterators` and `using-properties` only if they turn out to
  apply; do not reach for them speculatively

**Traps worth naming now**, each already resolved in the contracts:

- `d66` must be matched before the general notation grammar, or it parses as one
  66-sided die.
- `--dm` splits on the **last** `=`, so labels may contain `=`.
- A malformed `--dm` is a usage error (exit 2), not a library error (exit 1).
- `getrandbits(0)` returning `0` is what makes a 1-sided die work; do not add a
  special case for it.
- Never pass a `str` to `random.Random`; fold it first.

## Complexity Tracking

No constitutional violations requiring justification.

The single third-party runtime dependency, Typer, was justified in a prior ratified
decision and is recorded under the Principle VI note above rather than here, since
Principle VI permits justified dependencies rather than forbidding them.
