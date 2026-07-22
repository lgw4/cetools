# Quickstart: World Generation

Runnable validation for the world-generation feature. Proves the three user stories end-to-end.
See [contracts/](./contracts/) for the full API/CLI and [data-model.md](./data-model.md) for types.

## Prerequisites

```bash
uv sync
```

## Library validation (Stories 1 & 2)

Generate a reproducible fully-described system from the engine directly:

```bash
uv run python -c "
import random
from cetools.engine.rolls import RandomRolls
from cetools.engine.worlds import generate_system

sys = generate_system(RandomRolls(random.Random(42)))
print(sys.world.profile)   # e.g. A867A9C-F
print(sys.data_line)       # full world-data line
assert sys == generate_system(RandomRolls(random.Random(42)))  # SC-005 reproducibility
"
```

**Expected**: a valid profile string and full line print, and the equality assertion passes
(same seed → identical system).

## CLI validation (Story 2)

```bash
uv run cetools world generate --seed 42
uv run cetools world generate --name Terra --seed 1
```

**Expected**: one world-data line each; the second is named `Terra`. Exit code 0.

## Subsector validation (Story 3)

```bash
uv run cetools world subsector --seed 7
uv run cetools world subsector --density dense --seed 7
```

**Expected**: a list of world-data lines keyed by `CCRR` hex. The `dense` run has more occupied
hexes than the default (SC-007). All world names in a run are unique (SC-008).

## SRD invariants (Story 1 correctness)

```bash
uv run python -c "
import random
from cetools.engine.rolls import RandomRolls
from cetools.engine.worlds import generate_world

r = RandomRolls(random.Random(0))
for _ in range(2000):
    w = generate_world(r)
    assert 0 <= w.size <= 10 and 0 <= w.atmosphere <= 15 and 0 <= w.hydrographics <= 10
    assert 0 <= w.population <= 10 and 0 <= w.government <= 15 and w.law_level >= 0
    assert w.tech_level >= 0 and w.starport in 'ABCDEX'
    if w.size == 0: assert w.atmosphere == 0 and w.hydrographics == 0
    if w.size <= 1: assert w.hydrographics == 0
    if w.population == 0: assert w.government == w.law_level == w.tech_level == 0
print('2000 worlds satisfy SRD ranges and dependencies')  # SC-001, SC-002
"
```

**Expected**: prints the success line with no `AssertionError`.

## Full quality gate

```bash
uv run black . && uv run flake8 src tests && uv run pytest && uv run python scripts/check_docs.py
```

**Expected**: Black clean, flake8 zero warnings, pytest green with `src/cetools` coverage ≥ 85%,
docs check passes (symbols resolve, module map complete including the `worlds/` package, dashes
tight).
