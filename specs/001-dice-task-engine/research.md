# Phase 0 Research: Dice and Task Check Engine

**Feature**: `001-dice-task-engine` | **Date**: 2026-08-11

All Technical Context unknowns are resolved below. Findings marked **verified**
were confirmed by running code on this machine, not asserted from memory.

## R1: Folding a text seed to an integer

**Decision**: `int.from_bytes(hashlib.blake2b(text.encode("utf-8"), digest_size=8).digest(), "big")`,
producing a 64-bit integer.

**Rationale**: Deterministic across processes, machines, and interpreter versions.
`digest_size=8` places folded text seeds in exactly the same 64-bit space as
freshly drawn seeds (R4), so every seed the tool ever reports has the same shape.
UTF-8 and big-endian are pinned explicitly because both have platform-dependent
alternatives.

**Verified**: identical output (`14333185781139156525` for `"session-alpha"`) on
CPython 3.10, 3.11, 3.12, 3.13, and 3.14, and identical under `PYTHONHASHSEED` of
1, 2, and 3.

**Alternatives considered**: built-in `hash()`, rejected and specifically guarded
against. Verified that `hash("session-alpha")` returns three different values under
three different `PYTHONHASHSEED` settings, which is precisely the silent
irreproducibility the guard test in R12 exists to catch. `hashlib.sha256` truncated
would work equally well; blake2b was chosen because it takes `digest_size` directly
rather than requiring a truncation step that a future editor could get wrong.

## R2: Seeding `random.Random`

**Decision**: always construct `random.Random(n)` with an `int`. Never pass a `str`
or `bytes` seed.

**Rationale**: `Random.seed()` accepts a `version` argument that only applies to
`str`/`bytes` seeds, and that parameter exists because that code path has changed
before. Passing only integers keeps us off it permanently. Integer seeding uses
`init_by_array`, which is fixed by the Mersenne Twister reference implementation.
This is why R1 folds text ourselves rather than handing the string to `Random`.

**Alternatives considered**: `random.Random("session-alpha")` directly. Rejected:
it would work today and quietly move the reproducibility guarantee onto a code path
the standard library reserves the right to revise.

## R3: Deriving die faces

**Decision**: rejection sampling on `getrandbits`:

```
bits = (sides - 1).bit_length()
loop: n = rng.getrandbits(bits); if n < sides: return n + 1
```

**Rationale**: The `random` module documents `random()` and `getrandbits()` as
stable across versions and explicitly declines that guarantee for the higher-level
helpers. Building every face from `getrandbits` means the promise we make to users
rests only on what the standard library promises us. Rejection sampling keeps each
face exactly uniform (no modulo bias), and the variable number of draws is itself
deterministic for a given seed.

**Verified**: `sides=1` is safe, since `(1-1).bit_length()` is `0` and
`getrandbits(0)` returns `0` (valid since 3.9), yielding face `1`. The 12-face
sample sequence was identical on CPython 3.10 through 3.14.

**Alternatives considered**: `randint`/`randrange`/`choice`. Rejected on the
documented-guarantee grounds above.

**Correction to the decisions brief**: the brief justified this choice partly on
the claim that `random.choice` changed behaviour in 3.11. That did not reproduce.
`choice` and `randint` produced identical sequences on 3.10 through 3.14 in a spot
check. The decision is unchanged and still correct, but it rests on the documented
guarantee rather than on that specific incident. Recorded so a future reader does
not go looking for a change that is not there.

## R4: Seed space and unseeded runs

**Decision**: when no seed is supplied, draw `secrets.randbits(64)`.

**Rationale**: Matches the width of a folded text seed (R1), so every reported seed
is a non-negative integer below 2^64 regardless of origin. `secrets` rather than
`random` avoids seeding a generator from a generator.

## R5: Seeds that look like numbers

**Decision**: a seed supplied as text matching `^[+-]?[0-9]+$` is interpreted as
that integer. Every other text is folded per R1. The rule lives in one function and
is applied identically by the library and the CLI.

**Rationale**: Required by the round-trip guarantee (FR-006). Reported seeds are
always decimal integers, so pasting one back must be read as an integer rather than
folded as a label.

**Known consequence**: a session label consisting only of digits (`"2026"`) is
indistinguishable from the integer seed `2026`. Documented rather than worked
around; any escape hatch would complicate the round-trip rule that matters more.

## R6: Seed representation in JSON

**Decision**: emit the seed as a JSON **string** of decimal digits.

**Rationale**: Chosen by the user during planning. Seeds are 64-bit and routinely
exceed 2^53, where IEEE-754 doubles lose precision. The constitution names a future
web UI as a consumer of this same API, and `JSON.parse` would silently corrupt the
low digits, yielding a seed that no longer reproduces its own result. A string
round-trips exactly through every consumer. All other numeric fields (faces,
modifiers, totals, target) remain JSON numbers, since they are small.

**Alternatives considered**: JSON number (natural typing, corrupts in JavaScript);
capping seeds at 53 bits (keeps numeric typing, shrinks the seed space and adds a
non-obvious mask that text folding must also respect).

## R7: `d66` versus a 66-sided die

**Decision**: the literal token `d66` means the two-digit table throw and is
matched before the general grammar. A genuine 66-sided die is written `1d66`.

**Rationale**: The general grammar makes the count optional, so `d66` would
otherwise parse as one 66-sided die. In this game family `d66` unambiguously means
the table throw, so the special case matches user expectation; `1d66` remains
available and is documented.

## R8: Reading the rules data

**Decision**: `tomllib.load` on a handle from
`importlib.resources.files("cetools.data").joinpath("tasks.toml")`, with a small
set of inline checks, cached with `functools.cache`, isolated in a single module
(`rules.py`) that exists to be replaced.

**Rationale**: `tomllib` is standard library on the supported floor, so the ratified
TOML format costs no runtime dependency. `importlib.resources` reads the file
correctly from a wheel, a zip, or a source checkout. Isolating loading in one small
module makes the seam explicit: feature 2 (`rules-data-loading`) owns validated
loading and the compact-string grammar and will replace this module rather than
extend it. No filesystem search path is implemented, per FR-023.

**Verified**: `tomllib`, `importlib.resources.files`, and `secrets` are all
available on CPython 3.13.

**Alternatives considered**: building the validated loader now. Rejected: it belongs
to feature 2, which should design search precedence once, and duplicating it here
would create two loaders to reconcile.

## R9: What lives in the data file

**Decision**: `tasks.toml` holds the target number, the dice notation for a check,
the unskilled penalty, the seven-entry difficulty ladder, and the twelve-band
characteristic table. See [contracts/tasks-toml.md](contracts/tasks-toml.md).

**Rationale**: Principle V. Notably the check's own dice (`roll = "2d6"`) come from
data too, parsed with the same grammar the `roll` command uses, so a referee can
house-rule the core throw without touching code. The characteristic table is a
range table rather than the equivalent `floor(score / 3) - 2` formula precisely so a
flatter or steeper curve is a data edit.

**Corrections to the prototype sketch**: the prototype omits `Simple` (+6) from the
ladder and truncates the characteristic table at `15+`. Both are fixed here: seven
difficulties, and twelve bands ending in an unbounded `33+` at +9.

## R10: CLI shape

**Decision**: one Typer app with two subcommands. `cetools roll NOTATION` and
`cetools check`. Both take `--seed` and `--json`. Situational modifiers use a
repeatable `--dm "label=value"`.

**Rationale**: Typer was ratified in a prior decision. Two subcommands rather than
one keeps each command's `--help` honest, since `--difficulty` and `--skill` are
meaningless to a raw throw. The `label=value` form was chosen by the user during
planning: putting the label first means a negative value never begins the token, so
the parser cannot mistake `--dm "cover=-2"` for an option and no `--` separator or
`=`-attachment trick is needed.

**Also decided**: a `__main__.py` so `python -m cetools` works, which the guard test
in R12 needs in order to run the CLI in a subprocess.

## R11: Errors and exit codes

**Decision**: `CetoolsError` base with three subclasses: `DiceError`,
`RulesDataError`, `TaskError`. The library raises and never prints or exits. `cli.py`
holds the single `except CetoolsError` site, writes the message to stderr, and exits
1. Usage errors exit 2. A failed check exits 0.

**Rationale**: Principle I and II. Exit code 2 comes free: Click's `UsageError` already
uses `exit_code = 2`, so leaving usage handling to Typer produces the required
behaviour without custom code. Three subclasses rather than one per condition keeps
the taxonomy small (Principle VI); specifics such as the list of valid difficulty
names live in the message, which FR-019 requires anyway.

## R12: Testing strategy

**Decision**: pytest for everything, hypothesis for invariants, plus committed
golden files for rendered CLI text and two dedicated guard tests.

- **Literal expected values**: dice and check assertions are written with the
  expected numbers spelled out, before implementation, per Principle III.
- **Property tests** (hypothesis): faces always within range and correct in count;
  total always equals dice sum plus modifiers; success always equals
  `total >= target`; same seed always yields the same result; `d66` digits always
  within 1 to 6.
- **Golden files** for full rendered text output, reviewed as diffs. **No
  regeneration flag will be provided**, deliberately, so that updating a golden file
  requires a human to write the new expected text.
- **Guard test A**: capture `random.getstate()`, run a full CLI invocation, assert
  the state is unchanged. Catches any accidental use of module-level randomness.
- **Guard test B**: run the same text seed through `python -m cetools` in two
  subprocesses with `PYTHONHASHSEED=1` and `PYTHONHASHSEED=2` and compare output.
  Verified above that this test is meaningful: `hash()` genuinely differs under those
  settings, so a regression from blake2b to `hash()` would fail it.
- **Dedicated `d66` tests**, per SC-009, rather than incidental coverage.

**Rationale**: Hypothesis is a development-only dependency, so it does not engage the
constitution's runtime-dependency justification, and it earns its place by checking
uniformity and arithmetic invariants across input ranges that hand-written cases
cannot cover.

## R13: Toolchain

**Decision**: uv for environment and dependency management, hatchling as build
backend, Black, isort (`profile = "black"`), and flake8.

**Practical note**: flake8 cannot read configuration from `pyproject.toml`. It needs
its own `.flake8` file, set to `max-line-length = 88` with `extend-ignore = E203` so
it agrees with Black rather than fighting it. Black and isort are configured in
`pyproject.toml` as normal.

**Constitutional note**: these are quality tooling, which Principle III explicitly
permits but does not mandate. They are not gates on the definition of done; tests
are.

## R14: Licensing touchpoints in this feature

**Decision**: `src/cetools/data/tasks.toml` opens with an inline comment designating
it Open Game Content under OGL 1.0a. The strings "Cepheus Engine" and "Samardan
Press" appear nowhere in the package name or in that data file.

**Rationale**: Constitution, Licensing and Distribution Constraints.

**Correction (post-analysis)**: this entry originally deferred the full OGL text,
the Section 15 chain, and the repository-level OGC/GPL designation to
`packaging-release`, keeping only the per-file designation in scope. That was wrong
on the constitution's own wording, which binds *every distribution* rather than
every release. This feature builds the first wheel and sdist containing Open Game
Content, so the obligation attaches here. `LICENSE-OGL.txt` and the README's
OGC/GPL statement are therefore in scope (FR-035), and SC-012 checks them
automatically. Still deferred, correctly: the PyPI description, the published
compatibility statement, and the release process. The README this feature writes
makes no compatibility claim, so it owes no trademark attribution yet; if a later
edit adds such a claim, the attribution and non-affiliation statement come with it.

## R15: Verifying the cross-version reproducibility claim

**Decision**: a CI matrix running the full suite on every Python version in
`requires-python` and on Linux, macOS, and Windows.

**Rationale**: FR-007 binds reproducibility across every runtime version the package
declares support for, and SC-001 establishes cross-machine identity by running the
same automated check on each supported platform. R1 and R3's verification was a
one-off manual check on this machine; nothing re-ran it, so a regression would be
invisible until a user hit it. The matrix is what converts those findings from
recorded observations into a standing guarantee.

**Verified**: the folded value of `session-alpha` (`14333185781139156525`), the
`session-alpha` 2d6 faces `(1, 5)`, the `--seed 1` 2d6 faces `(2, 5)`, and the
1-sided-die face `1` are all identical on CPython 3.10, 3.11, 3.12, 3.13, and 3.14.
Re-confirmed during the post-analysis pass, on the same five interpreters.

**Note on the floor**: `requires-python` is `>=3.13`, so the matrix is 3.13 and 3.14
today. The recipe's stability on 3.10 through 3.12 is recorded as evidence that it
rests on documented guarantees rather than on a happy accident of one version, not
as a support claim.
