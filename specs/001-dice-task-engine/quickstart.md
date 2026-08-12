# Quickstart: Dice and Task Check Engine

**Feature**: `001-dice-task-engine`

How to set the project up and prove the feature works end to end. Every scenario
below is a check a reviewer can run by hand; the automated equivalents live in
`tests/`.

## Prerequisites

- Python 3.13 or newer (`uv` will fetch one if needed)
- `uv` on `PATH`

## Setup

```sh
uv sync
uv run pytest
```

`uv sync` creates the environment and installs `cetools` in editable form along
with the development group (pytest, hypothesis, black, isort, flake8).

Optional quality tooling, which is permitted but not a gate (Principle III):

```sh
uv run black --check src tests
uv run isort --check-only src tests
uv run flake8 src tests
```

## Scenario 1: Reproducibility, the load-bearing property

Validates FR-005, FR-006, SC-001, SC-004.

```sh
uv run cetools roll 2d6 --json
```

Note the `seed` in the output, then feed it back:

```sh
uv run cetools roll 2d6 --seed <that seed> --json
```

**Expected**: the second run's `faces` and `total` are identical to the first.
Repeat with `--seed` a third time and the output is byte-identical again.

## Scenario 2: Text seeds survive process restarts

Validates FR-003, SC-002. This is the check that would catch a regression from
blake2b back to the built-in `hash()`.

```sh
PYTHONHASHSEED=1 uv run python -m cetools roll 2d6 --seed session-alpha --json
PYTHONHASHSEED=2 uv run python -m cetools roll 2d6 --seed session-alpha --json
```

**Expected**: byte-identical output from both, including the same numeric `seed`.
With `hash()` in place of blake2b these would differ, silently.

For reference, the folded value of `session-alpha` is `14333185781139156525`, and
`uv run cetools roll 2d6 --seed 14333185781139156525` must produce the same result
as `--seed session-alpha`.

## Scenario 3: The difficulty ladder is a modifier, not a target shift

Validates FR-014, SC-003.

```sh
for d in Simple Easy Routine Average Difficult "Very Difficult" Formidable; do
  uv run cetools check --difficulty "$d" --skill 0 --seed 1 --json
done
```

**Expected**: `target` is `8` in all seven outputs, `faces` are identical in all
seven, and `total` decreases by exactly 2 at each step from `Simple` (+6) down to
`Formidable` (-6). If `target` moves, difficulty has been modelled wrongly.

## Scenario 4: Skill 0 differs from untrained

Validates FR-016.

```sh
uv run cetools check --skill 0 --seed 1        # trained at level 0
uv run cetools check --seed 1                  # no --skill: untrained
```

**Expected**: the first shows a `Skill 0` modifier of `+0`; the second shows an
`Unskilled` modifier of `-3`. Totals differ by exactly 3.

## Scenario 5: The characteristic table, including its unbounded top

Validates FR-015, SC-003.

```sh
for n in 0 2 3 5 6 8 9 11 12 14 15 17 18 20 21 23 24 26 27 29 30 32 33 99 4000; do
  uv run cetools check --characteristic "$n" --skill 0 --seed 1 --json
done
```

**Expected**: the characteristic modifier follows the twelve bands, and scores of
33, 99, and 4000 all yield `+9` rather than erroring or falling off the end.

## Scenario 6: Labelled situational modifiers

Validates FR-017, FR-018.

```sh
uv run cetools check --difficulty Difficult --characteristic 9 --skill 2 \
  --dm "cover=-2" --dm "aided by ally=+1" --seed session-alpha
```

**Expected**: five modifiers listed in fixed order (difficulty, characteristic,
skill, then the two `--dm` values in the order given), each with its label intact,
and `total` equal to the dice sum plus all five values.

## Scenario 7: Exit codes

Validates FR-030, FR-031, FR-032, SC-006.

```sh
uv run cetools check --difficulty Formidable --seed 1 ; echo "failed check -> $?"
uv run cetools check --difficulty Trivial     --seed 1 ; echo "bad difficulty -> $?"
uv run cetools roll  7dQ                      --seed 1 ; echo "bad notation   -> $?"
uv run cetools roll  2d6 --dm "cover=-2"                ; echo "unknown option -> $?"
uv run cetools check --dm "cover"             --seed 1 ; echo "malformed --dm -> $?"
```

**Expected**: `0`, `1`, `1`, `2`, `2` respectively. The first is the important one:
a check that fails to reach the target is the tool working correctly, not an error.
Confirm also that the two error cases wrote nothing to stdout:

```sh
uv run cetools check --difficulty Trivial --seed 1 2>/dev/null | wc -c   # expect 0
```

## Scenario 8: The rules really do live in data

Validates FR-021, FR-022, SC-010.

Temporarily edit `src/cetools/data/tasks.toml`, changing `target = 8` to
`target = 10`, then:

```sh
uv run cetools check --skill 0 --seed 1 --json
```

**Expected**: `target` reads `10` and `success` flips for totals of 8 or 9, with no
code change. Repeat for a difficulty value, `unskilled-dm`, and a characteristic
band. **Revert the file afterwards** so the committed data stays SRD-faithful.

## Scenario 9: `d66`

Validates FR-010, SC-009.

```sh
uv run cetools roll d66 --seed session-alpha
uv run cetools roll 1d66 --seed session-alpha
```

**Expected**: the first reports two faces and a composed two-digit value with both
digits in 1 to 6. The second is a different thing entirely, one 66-sided die, which
is how the ambiguity is resolved.

## Scenario 10: No global randomness contamination

Validates FR-001, SC-005. Covered automatically by the guard test; by hand:

```sh
uv run python -c "
import random
from cetools import Roller, throw
before = random.getstate()
throw(Roller('session-alpha'), '2d6')
print('module state untouched:', random.getstate() == before)
"
```

**Expected**: `True`.

## Test suite map

| Path | Covers |
|---|---|
| `tests/unit/test_seeds.py` | Seed resolution, folding, digit-string rule |
| `tests/unit/test_dice.py` | Notation grammar, faces, modifiers, `DiceError` |
| `tests/unit/test_d66.py` | `d66` specifically (SC-009) |
| `tests/unit/test_tasks.py` | Ladder, bands, skill states, `TaskError` |
| `tests/unit/test_rules.py` | Data loading and every `RulesDataError` path |
| `tests/unit/test_render.py` | Text and dict rendering |
| `tests/contract/test_json_contract.py` | Committed JSON shape, incl. `seed` is a string |
| `tests/integration/test_cli.py` | Both subcommands, streams, exit codes |
| `tests/integration/test_golden.py` | Rendered output vs `tests/golden/*.txt` |
| `tests/guards/test_seed_contract.py` | Module random state; `PYTHONHASHSEED` subprocesses |
| `tests/property/test_invariants.py` | Hypothesis invariants |

## A note on golden files

`tests/golden/*.txt` are reviewed as diffs. **No regeneration flag is provided**,
deliberately: updating one requires a human to write the new expected text, which
is what stops a rendering regression from being blessed by reflex.
