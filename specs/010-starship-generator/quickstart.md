# Quickstart: Starship Generator

Runnable validation for the starship-generator feature. Proves the user stories end-to-end. See
[contracts/](./contracts/) for the API/CLI/schema and [data-model.md](./data-model.md) for types.

## Prerequisites

```bash
uv sync
```

## Builder validation (Story 1)

Build a known design from the engine directly and confirm the computed sheet:

```bash
uv run python -c "
from cetools.engine.ships import build_ship, load_design

ship = build_ship(load_design('specs/010-starship-generator/examples/free-trader.toml'))
print(ship.tonnage_used, ship.cargo_tons, ship.total_cost)
print(ship.hull_points, ship.structure_points, ship.crew.total)
print(ship.jump_fuel, ship.power_fuel, ship.build_weeks)
"
```

**Expected**: tonnage, cargo, cost, hull/structure points, crew, fuel, and build time match a
hand-worked SRD reference design (SC-002).

Confirm an invalid design is rejected with a specific message:

```bash
uv run python -c "
from cetools.engine.ships import build_ship, ShipDesign, Configuration
try:
    build_ship(ShipDesign(hull_tons=200, jump_code='C', power_code='A'))  # power plant below jump
except ValueError as e:
    print('rejected:', e)
"
```

**Expected**: prints `rejected: power plant rating ... below required ...` (SC-005).

## Random generator validation (Story 2)

```bash
uv run python -c "
from cetools.engine.rolls import RandomRolls
from cetools.engine.ships import generate_ship, build_ship, loads_design, dump_design

a = generate_ship(RandomRolls.seeded(42))
b = generate_ship(RandomRolls.seeded(42))
assert a == b                                              # SC-004 reproducibility
assert build_ship(loads_design(dump_design(a.design))) == a  # SC-008 round-trip
print('seed 42 reproducible; round-trip lossless; cargo', a.cargo_tons)
"
```

**Expected**: prints the success line with no `AssertionError`; every generated ship is valid
(SC-003, guaranteed because generation ends in `build_ship`).

## CLI validation (Stories 1 & 2)

```bash
uv run cetools ship build specs/010-starship-generator/examples/free-trader.toml
uv run cetools ship generate --seed 42
uv run cetools ship generate --seed 42 --toml        # round-trippable design file
uv run cetools ship generate --hull 10 --small-craft --seed 7   # 10–95 t with --small-craft
```

**Expected**: a human-readable ship sheet (or TOML with `--toml`); the two `--seed 42` runs are
byte-identical; the small-craft run has no jump drive and a cockpit. Exit code 0. Invalid input or a
rules-illegal design exits 1 with the violated rule on stderr. `--hull 100 --small-craft` is out of
range for a small craft and exits 1.

## Small craft and bays (Stories 3 & 4)

```bash
uv run python -c "
from dataclasses import replace
from cetools.engine.ships import build_ship, load_design, BayFit

sc = build_ship(load_design('specs/010-starship-generator/examples/fighter.toml'))
assert sc.jump_rating == 0                     # no jump drive on small craft
print('fighter cargo', sc.cargo_tons, 'crew', sc.crew.total)

try:                                           # FR-020: bays are starship-only
    build_ship(replace(sc.design, turrets=(), bays=(BayFit(kind='particle'),)))
except ValueError as e:
    print('rejected:', e)
"
```

**Expected**: the small craft builds with a cockpit, one-week fuel minimum, and no jump drive
(FR-019); the bay attempt prints `rejected: small craft cannot mount a weapon bay` (FR-020).

Bays and screens on a large hull (Story 4):

```bash
uv run python -c "
from cetools.engine.ships import build_ship, load_design

cruiser = build_ship(load_design('specs/010-starship-generator/examples/heavy-cruiser.toml'))
print('hardpoints', cruiser.hardpoints_used, '/', cruiser.hardpoints)
print('gunners', cruiser.crew.gunners, 'screen operators', cruiser.crew.screen_operators)
print('tonnage', cruiser.tonnage_used, 'cost MCr', cruiser.total_cost)
"
```

**Expected**: each bay consumes 50 t plus 1 t of fire control and one hardpoint, each screen 50 t;
gunners cover turrets and bays, screen operators are counted separately, and the figures match the
hand-worked header in `heavy-cruiser.toml` (FR-020).

## Full quality gate

```bash
uv run black . && uv run flake8 src tests && uv run pytest && uv run python scripts/check_docs.py
```

**Expected**: Black clean, flake8 zero warnings, pytest green with `src/cetools` coverage ≥ 85%,
docs check passes (symbols resolve, module map complete including the `ships/` package, dashes tight).
