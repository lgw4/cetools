# Quickstart: Validating Ship Names

**Feature**: `012-ship-names` | **Date**: 2026-07-25

How to prove the feature works end to end, once implemented. Every command below is runnable
from the repository root. Types, invariants and guarantees referenced here are defined in
[data-model.md](./data-model.md) and [contracts/name-catalogue.md](./contracts/name-catalogue.md);
they are not repeated.

## Prerequisites

```bash
uv sync
```

## Scenario 1 — A generated ship arrives already named (User Story 1, SC-001)

```bash
uv run cetools ship generate --seed 42
uv run cetools ship generate --seed 7 --small-craft
```

**Expected**: each prints a `TL<n> <name>` heading and a paragraph whose first sentence reads
`… the <name> is a starship.` (or `… a small craft.`). `Unnamed Ship` appears in neither.

Sweep for the absence of the placeholder across many seeds:

```bash
uv run python -c "
from cetools.engine.rolls import RandomRolls
from cetools.engine.ships import generate_ship, render_description
for small in (False, True):
    for seed in range(100):
        ship = generate_ship(RandomRolls.seeded(seed), small_craft=small)
        assert ship.design.name, (small, seed)
        assert 'Unnamed Ship' not in render_description(ship), (small, seed)
print('SC-001 OK: 200 ships, all named')
"
```

## Scenario 2 — The name survives export and rebuild (User Story 1, SC-002)

```bash
uv run cetools ship generate --seed 42 --toml --out /tmp/ship.toml
grep '^name = ' /tmp/ship.toml
uv run cetools ship build /tmp/ship.toml | head -1
```

**Expected**: the TOML carries a `name = "…"` line, and the rebuilt description's heading names
the same ship. The generated description and the rebuilt description are byte-identical.

## Scenario 3 — Same seed, same name (User Story 2, SC-002)

```bash
uv run python -c "
from cetools.engine.rolls import RandomRolls
from cetools.engine.ships import generate_ship
a = generate_ship(RandomRolls.seeded(42))
b = generate_ship(RandomRolls.seeded(42))
assert a == b and a.design.name == b.design.name, 'seed 42 not reproducible'
names = {generate_ship(RandomRolls.seeded(s)).design.name for s in range(20)}
assert len(names) >= 17, f'only {len(names)} distinct names in 20 seeds'
print(f'SC-002/SC-003 OK: reproducible; {len(names)}/20 distinct')
"
```

**Expected**: reproducible, and at least 17 of 20 seeds yield distinct names (SC-003).

## Scenario 4 — Naming is purely additive to every pre-existing seed (SC-008)

This is the scenario the feature most needs to prove, and the only one that depends on an
artifact captured before implementation: `baseline/designs.json` holds `dump_design` output for
seeds 0–49 on both paths, recorded at commit `d387b70`.

```bash
uv run python -c "
import json, dataclasses
from cetools.engine.rolls import RandomRolls
from cetools.engine.ships import dump_design, generate_ship
baseline = json.load(open('specs/012-ship-names/baseline/designs.json'))
for key, expected in baseline.items():
    path, seed = key.split(':')
    ship = generate_ship(RandomRolls.seeded(int(seed)), small_craft=(path == 'small_craft'))
    assert ship.design.name, key
    stripped = dataclasses.replace(ship.design, name=None)
    assert dump_design(stripped) == expected, f'{key} changed beyond its name'
print(f'SC-008 OK: {len(baseline)} pinned seeds unchanged except for the name')
"
```

**Expected**: every pinned seed still produces the identical design once the name is cleared. A
failure here means a draw was inserted somewhere other than the end of a generation path
(research.md Part A).

## Scenario 5 — An author's own name is never overwritten (SC-006)

```bash
uv run cetools ship build specs/010-starship-generator/examples/free-trader.toml | head -1
```

**Expected**: `TL8 Beowulf` — unchanged from today. Building never assigns a name (FR-015), and a
supplied name always wins (FR-014).

Blank and absent names still fall back:

```bash
uv run python -c "
import dataclasses
from cetools.engine.ships import build_ship, load_design, render_description
base = load_design('specs/010-starship-generator/examples/free-trader.toml')
for value in (None, ''):
    ship = build_ship(dataclasses.replace(base, name=value))
    assert 'Unnamed Ship' in render_description(ship), repr(value)
print('FR-015 OK: hand-authored designs are untouched by naming')
"
```

## Scenario 6 — The catalogue is balanced, sourced and auditable (User Story 3, SC-005, SC-007)

```bash
uv run python -c "
from collections import Counter
from cetools.engine.ships import SHIP_NAMES, BasisKind, Tradition
counts = Counter(e.tradition for e in SHIP_NAMES)
total = len(SHIP_NAMES)
assert total >= 150, total
assert len({e.name for e in SHIP_NAMES}) == total, 'duplicate names'
assert all(counts[t] >= 20 for t in Tradition), counts
assert max(counts.values()) <= total // 2, counts
fiction = [e for e in SHIP_NAMES if e.tradition is not Tradition.MYTHOLOGY_FOLKLORE]
assert all(isinstance(e.basis_kind, BasisKind) and e.basis_reference.strip() for e in fiction)
myth = [e for e in SHIP_NAMES if e.tradition is Tradition.MYTHOLOGY_FOLKLORE]
assert all(e.basis_kind is None and e.basis_reference == '' for e in myth)
assert all(e.name.isascii() for e in SHIP_NAMES), 'non-ASCII entry'
print(f'SC-005/SC-007 OK: {total} names, {dict(counts)}, {len(fiction)} bases verified')
"
```

**Expected**: prints the catalogue size and per-tradition counts, having verified the size floor,
the per-tradition floor, the 50% cap, uniqueness, every fiction entry's basis, and ASCII-only
spellings.

## Full quality gate

The four commands the constitution requires before any commit:

```bash
uv run black . && uv run flake8 src tests && uv run pytest && uv run python scripts/check_docs.py
```

**Expected**: formatted, no lint findings, all tests green with coverage above the 85% floor, and
`check_docs.py` clean — which requires that `CONTRIBUTING.md`'s module map gains
`ships/names.py`, and that any new backticked symbol named in `README.md` or `CONTRIBUTING.md`
resolves.
