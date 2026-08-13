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

**Declared support is intentionally open-ended.** `requires-python` is `">=3.13"`
with no upper bound, and the CI matrix tracks the released versions inside that
range rather than the package narrowing its declaration to match the matrix. FR-007
binds every version in the declared set, so an unbounded declaration only stays
dischargeable if something notices when the matrix falls behind the range: that is
`tests/guards/test_python_support.py`, which fails when a Python inside
`requires-python` that the suite is actually running on is absent from the matrix in
`.github/workflows/ci.yaml`. The guard keys off the running interpreter rather than a
hard-coded list of releases, so it needs no network and no periodic maintenance: the
first run on a new Python — a developer's local upgrade, or a matrix entry added
without the other jobs following — is what fires it. Recorded 2026-08-12 per T084,
which offered an upper bound as the alternative; the open declaration was chosen
deliberately so that a new Python is usable the day it ships rather than after a
metadata bump.

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
of implementation and a larger test suite. 35 functional requirements, 12 success
criteria.

**Toolchain**: uv for environment and dependency management, hatchling as build
backend, Black + isort (`profile = "black"`) + flake8 as non-gating quality tooling.
flake8 cannot read `pyproject.toml`, so it needs a separate `.flake8` set to the same
line length as Black with `extend-ignore = E203` to agree with it rather than fight it.
That length is **99**, not Black's default of 88: this codebase's signal-carrying lines
are long single expressions (`importlib.resources` reads, Typer option declarations,
keyword-only `check` signatures) that 88 splits across lines without making them
clearer. Both `.flake8` and `[tool.black]` carry `99`; what matters to the decision is
that the two agree, and the specific figure was settled at implementation time.
Amended 2026-08-12 per T075, which found the artifact recording 88 while the repository
shipped 99.

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
| **Licensing & Distribution** | OGC files designated; every distribution bundles the OGL text and Section 15 chain; PI strings absent from OGC data; compatibility claims carry attribution | **PASS** - `tasks.toml` carries its per-file designation; `LICENSE-OGL.txt` ships in both the wheel and the sdist; README states the OGC/GPL split; the README makes no compatibility claim, so no attribution is owed yet. SC-012 verifies all of it automatically. See below. |

**Principle VI in detail.** Typer is the only runtime dependency and was justified
in the ratified library-and-CLI-architecture decision (it derives the CLI from typed
signatures, keeping the CLI layer declarative and nearly logic-free, reinforcing
Principle I; argparse would be hand-written boilerplate growing with every
subcommand). Hypothesis is development-only and so does not engage the runtime-
dependency rule. TOML costs nothing because `tomllib` is standard library on the
supported floor. Deliberate omissions in service of YAGNI: no JSON error envelope,
no golden-file regeneration flag, no `--target` override, no rules-data search path.

**Licensing constraints.** `tasks.toml` opens with its Open Game Content designation
and contains neither "Cepheus Engine" nor "Samardan Press". Beyond that per-file
designation, this feature also ships `LICENSE-OGL.txt` (the full OGL 1.0a text plus
the SRD's complete Section 15 chain extended with this project's own game-data
copyright line) and a README section naming `src/cetools/data/tasks.toml` as the sole
Open Game Content file with everything else under GPL-3.0. Both are included in the
wheel and the sdist.

This is a deliberate correction to the original scoping, which deferred all license
bundling to `packaging-release`. The constitution's bundling clause is written
against *every distribution*, and this feature is the one that first builds a
distribution containing Open Game Content, so the obligation lands here whether or
not a release is cut. What genuinely does belong to `packaging-release` is
everything downstream of building the artifact: the PyPI description, the
compatibility statement as published, and the release process. `README.md` therefore
either carries the trademark attribution and non-affiliation statement or makes no
compatibility claim at all; this feature takes the second route and says only what
the tool does.

**Post-Phase-1 re-check**: still **PASS**. The Phase 1 design introduced no new
dependency and no new hard-coded rules content. The one design choice worth
recording against Principle VI is `ThrowResult` serving both dice throws and `d66`
with an overloaded `total`; a second result type was rejected as more machinery than
the problem needs, and the overload is documented explicitly in the JSON contract.

**Post-analysis re-check (2026-08-12)**: **PASS**, after one repair. `/speckit-analyze`
found the Licensing & Distribution row failing: this plan deferred all OGL bundling to
`packaging-release`, but the constitution binds every *distribution*, and this feature
builds the first one containing Open Game Content. The plan now ships `LICENSE-OGL.txt`
and the README designation, and SC-012 guards both. No principle row changed. The
repair adds two files and one test module and introduces no dependency, so Principle VI
is untouched. The other analysis findings were traceability and coverage gaps in
`tasks.md` and the contracts, not design changes.

**Post-convergence re-check (2026-08-12)**: **PASS**, after two repairs and one
scope decision, all recorded as Phase 8 in `tasks.md`.

1. `README.md` opened by claiming compatibility with the named source rules while
   carrying neither the Compatibility-Statement attribution nor a statement of
   non-affiliation, contradicting the second route this plan committed to above.
   The claim is now dropped from both `README.md` and the `pyproject.toml`
   `description`, and `tests/unit/test_licensing.py` guards both: naming the
   trademark without the attribution and the non-affiliation statement now fails
   the suite. The published compatibility statement remains `packaging-release`'s.
2. The loader accepted a `task.roll` of `d66`, which parses but describes a
   two-digit table die rather than a count and a side count, so the failure
   surfaced as an uncaught `TypeError` out of `check` instead of a
   `CetoolsError` (FR-029). `_task_parameters_from_toml` now raises
   `RulesDataError` for it.

**`CHANGELOG.md` and `CONTRIBUTING.md` are a deliberate early delivery.** FR-028
assigns the changelog to `packaging-release`, and no task in Phases 1-7 called for
either file, but both now exist and `README.md` links to them. They are kept here
rather than deferred, because `CONTRIBUTING.md` carries the licensing constraints
on new files that repair 1 above depends on contributors knowing. `packaging-release`
therefore inherits both files and should extend them rather than create them; its
spec must not restate them as new deliverables.

Packaging is now checked against the built artifact rather than the working tree.
The `src/` layout's justification below — that a wheel omitting `tasks.toml` fails
the suite — was nominal under an editable install, since `importlib.resources`
resolved into the source tree either way. `tests/guards/test_packaging.py` builds
the wheel and inspects it, which is what discharges SC-012 automatically instead of
by the manual T065 inspection.

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
pyproject.toml            # hatchling, requires-python >=3.13, typer, dev group
.flake8                   # flake8 cannot read pyproject.toml
.github/workflows/ci.yaml # pytest across the supported Python versions, on Linux
README.md                 # states the OGC/GPL split; makes no compatibility claim
LICENSE                   # GPL-3.0, covers the code
LICENSE-OGL.txt           # OGL 1.0a + Section 15 chain, covers the OGC data

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
├── integration/         # CLI behavior and golden files
├── guards/              # seed-contract defense
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
