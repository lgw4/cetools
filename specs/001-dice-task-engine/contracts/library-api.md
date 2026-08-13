# Contract: Library API

**Feature**: `001-dice-task-engine`

Everything the CLI does is reachable from `import cetools` (FR-034). The CLI adds
argument parsing, printing, and exit codes, and nothing else.

## Public surface (`cetools/__init__.py`)

```python
from cetools import (
    # errors
    CetoolsError, DiceError, RulesDataError, TaskError,
    # randomness
    Roller,
    # dice
    ThrowResult, parse_notation, throw, throw_dice, d66,
    # tasks
    Modifier, CheckResult, TaskParameters, Band, check,
    # rules data
    load_task_parameters,
    # rendering
    as_dict, as_json, as_text,
)
```

`__all__` is defined explicitly and is the contract; anything not listed is
internal.

## Randomness

```python
class Roller:
    def __init__(self, seed: int | str | None = None) -> None: ...
    seed: int                                  # resolved, public, echoed in results
    def die(self, sides: int) -> int: ...
    def dice(self, count: int, sides: int) -> tuple[int, ...]: ...
```

A `Roller` is passed **explicitly** to everything that needs randomness. No
function creates one implicitly, and no function accepts a raw seed in place of
one. This is what stops two callers from unknowingly drawing from the same
sequence.

## Dice

```python
def parse_notation(notation: str) -> tuple[int, int, int] | None
    # -> (count, sides, modifier), or None for the d66 literal

def throw(roller: Roller, notation: str) -> ThrowResult
def throw_dice(roller: Roller, count: int, sides: int, modifier: int = 0) -> ThrowResult
def d66(roller: Roller) -> ThrowResult
```

`throw` is the notation-driven front door used by the CLI. `throw_dice` is the
structured form for callers that already have numbers, which later features
(skill tables, damage) will use. `d66` is separate because notation cannot express
it.

## Tasks

```python
def check(
    roller: Roller,
    *,
    difficulty: str | None = None,
    characteristic: int | None = None,
    skill: int | None = None,
    modifiers: Sequence[Modifier] = (),
    parameters: TaskParameters | None = None,
) -> CheckResult
```

Everything after `roller` is keyword-only, so no caller can transpose
`characteristic` and `skill` (two adjacent same-typed integers, the classic
transposition bug).

| Parameter | Meaning of the default |
|---|---|
| `difficulty` | `None` resolves through `parameters.default_difficulty()`, the sole rung whose modifier is `0` (`"Average"` in the shipped data). No rung name appears in code. |
| `characteristic` | `None` means **no characteristic modifier at all**, not a score of zero. |
| `skill` | `None` means **untrained**, applying the unskilled penalty. `0` means trained at level 0, applying nothing. |
| `modifiers` | Empty. |
| `parameters` | `None` loads the packaged data. |

**On `parameters`**: passing an explicit `TaskParameters` is an API, not a
filesystem search, so it does not conflict with FR-023. It is how SC-010 gets
tested (swap a value, observe the arithmetic change) and how a future house-rule
consumer supplies its own table without this feature growing a search path.

## Rules data

```python
def load_task_parameters() -> TaskParameters              # public, cached
def _task_parameters_from_toml(text: str) -> TaskParameters   # internal, not cached
```

`load_task_parameters` reads the single packaged `cetools/data/tasks.toml` through
`importlib.resources` and hands the text to `_task_parameters_from_toml`. It
performs no filesystem search (FR-023). Raises `RulesDataError` on missing,
unreadable, malformed, or incomplete data, with no fallback to built-in values
(FR-024).

**On the split.** `_task_parameters_from_toml` holds the TOML parse and the whole
validation table from [tasks-toml.md](tasks-toml.md); `load_task_parameters` holds
only "which bytes, and cache them". The split exists because the validation rules
are the part with many cases and the packaged-file read is the part with one, and a
zero-argument cached function that reads exactly one file has nowhere to put a
fixture. With the seam, every `RulesDataError` path is reachable by passing fixture
text directly, and a valid edited fixture demonstrates SC-010 through the real
loader rather than by constructing a `TaskParameters` by hand.

The leading underscore is the contract: it is not in `__all__` and callers outside
the package must not use it. Only the missing-and-unreadable-file cases need to go
through the public function, by pointing `importlib.resources` at an absent
resource.

`functools.cache` on `load_task_parameters` means tests that do exercise the public
function must call `load_task_parameters.cache_clear()` afterwards, or they will
leak state into whatever runs next. `tests/conftest.py` provides an autouse fixture
that clears it, so no individual test has to remember.

This function and its module are the seam that feature 2 (`rules-data-loading`)
replaces. Both functions are deliberately kept small so replacing them is easy and
so nobody is tempted to extend them.

## Rendering

```python
def as_dict(result: ThrowResult | CheckResult) -> dict
def as_json(result: ThrowResult | CheckResult) -> str
def as_text(result: ThrowResult | CheckResult) -> str
```

Implemented with `functools.singledispatch` on the result type, so adding a future
result type is a registration rather than an edit to a growing `if/elif` chain.

Rendering lives in the library, not the CLI, per the ratified library/CLI boundary
decision. That is what makes both output formats unit-testable without invoking a
command runner, and reusable by a future web UI.

`as_json` returns a complete string including its trailing newline, so the CLI's
job is `print(..., end="")` rather than any formatting decision of its own.

## Errors

```text
CetoolsError
├── DiceError        invalid notation, non-positive count or sides
├── RulesDataError   data file missing, unreadable, malformed, incomplete
└── TaskError        unknown difficulty, negative characteristic, negative skill
```

The library **raises** and never prints, never writes to a stream, and never
exits. `cli.py` holds the only `except CetoolsError` in the codebase.

`TaskError` for an unknown difficulty must list the valid names in its message
(FR-019).

## Invariants a caller may rely on

- No function reads or writes module-level `random` state (FR-001).
- Two `Roller` instances never influence each other (FR-008).
- Given the same `Roller` seed and the same arguments, every function above
  returns an equal result (FR-006).
- Every result carries the `seed` that produced it (FR-005).
