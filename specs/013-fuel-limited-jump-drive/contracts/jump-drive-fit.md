# Contract: Jump-Drive Fit

**Feature**: `013-fuel-limited-jump-drive`

cetools exposes two external interfaces: the `cetools.engine` library API and the `cetools` CLI.
This feature changes **no signature in either**. What it changes is a behavioural guarantee. This
document states the guarantee that callers may now rely on, and the internal helper contract that
delivers it.

---

## 1. Public: `generate_ship` — behavioural contract

```python
from cetools.engine.ships import generate_ship

generate_ship(rolls=None, *, hull_size=None, small_craft=False) -> Ship
```

Signature, parameters, return type and exceptions: **unchanged**.

### New guarantees (standard-hull path only)

Given `ship = generate_ship(...)` with `small_craft=False`:

| ID | Guarantee |
| --- | --- |
| G1 | `ship.jump_fuel >= 0.1 * ship.hull_tons * ship.jump_rating` (FR-001) |
| G2 | `ship.assumed_jump_distance == ship.jump_rating` (FR-001) |
| G3 | `render_description(ship)` reports one or more jumps (FR-007) |
| G4 | `ship.design.jump_code` is the lightest drive legal for `ship.hull_tons` at `ship.jump_rating` (FR-004) |
| G5 | `ship.cargo_tons >= 0` (FR-013, unchanged but now measured against a smaller drive) |

**Exception — the FR-014 starved hull.** G1–G4 hold unless no drive legal for the hull can be
fuelled for one complete jump within the tonnage left after the bridge, maneuver drive, power plant
and power-plant fuel. In that case the lowest-rated legal drive is installed, whatever fuel fits is
bought, and only G4 and G5 hold. This case is **unreachable with the current SRD tables** — verified
over the full cross product of hull, maneuver code and power code, not merely sampled (research.md
Part E) — and is specified so the boundary is defined rather than undefined.

### Preserved guarantees

| ID | Guarantee |
| --- | --- |
| P1 | Equal seeds yield equal ships: `generate_ship(RandomRolls.seeded(n)) == generate_ship(RandomRolls.seeded(n))` (FR-009) |
| P2 | `hull_size=n` yields `ship.hull_tons == n` (FR-011) |
| P3 | `build_ship(loads_design(dump_design(ship.design))) == ship` |
| P4 | The `RollName.SHIP_NAME` draw is the last draw of every path (FR-008) |
| P5 | `small_craft=True` output is equal to pre-feature output for every seed (FR-010, SC-005) |

### Explicitly **not** guaranteed

**Seed-to-ship stability across this feature.** A given seed may now yield a different standard-hull
ship than it did before. Approximately 54% of seeds move: 5.5% because their drive is downgraded,
the rest because their drive letter is replaced by a lighter one of the same rating (research.md
Part D). This is intended, is stated in the spec's Assumptions, and is why the feature-012 pinned
baseline is replaced rather than satisfied.

The seed-to-ship mapping *within* a release remains stable (P1); it is the cross-version mapping
that moves, exactly as it did when features 010 and 012 landed.

---

## 2. Public: `build_ship` — explicitly unchanged

```python
build_ship(design: ShipDesign) -> Ship
```

`build_ship` is the sole validation authority and this feature does not touch it. A design that
specifies `jump_distance` below one full jump at its drive's rating **builds as written** and is
never silently adjusted (FR-012).

This is the boundary the feature respects: the correction is *generation policy*, applied only when
cetools is choosing components on the caller's behalf. An author who deliberately designs a
short-legged ship is making a decision, not a mistake.

Verified by: all six of the repository's authored example designs — the five under
`specs/010-starship-generator/examples/` and
`specs/011-universal-ship-format/examples/subsidized-merchant.toml` — plus a design with an
explicit short `jump_distance`, built before and after, producing identical `Ship` values.

---

## 3. Public: `cetools ship generate` — behavioural contract

Command syntax, flags, exit codes and output format: **unchanged**. The rendered description now
reports a non-zero jump count for every generated starship (G3). Exit codes remain 0 for success and
1 for user-facing failure, per Constitution III.

`cetools ship build <file>` is unaffected, per section 2.

---

## 4. Internal: the fit helper

Module-private to `engine/ships/generator.py`. Not exported from `cetools.engine.ships`, not part of
the public surface, and free to change shape — stated here because it is where every guarantee above
is actually enforced, and because it is the unit under test for FR-014.

```python
def _fit_jump_drive(hull_tons: int, drawn_code: str, budget: float) -> str
```

### Preconditions

- `hull_tons in HULLS`
- `hull_tons in DRIVE_PERFORMANCE[drawn_code]` — the drawn code is legal for the hull
- `budget` is the hull tonnage less the bridge, maneuver drive, power plant and power-plant fuel;
  the jump drive is **not** deducted

### Postconditions

Let `r(c) = DRIVE_PERFORMANCE[c][hull_tons]`, `t(c) = DRIVE_COSTS[c].jump_tons`, and
`result = _fit_jump_drive(hull_tons, drawn_code, budget)`.

| ID | Postcondition | Requirement |
| --- | --- | --- |
| C1 | `hull_tons in DRIVE_PERFORMANCE[result]` — the result is legal for the hull | FR-013 |
| C2 | `r(result) <= r(drawn_code)` — the rating is never raised | FR-003, FR-006, SC-007 |
| C3 | `result` is the unique lightest legal code at `r(result)`: no legal `c` has `r(c) == r(result)` and `t(c) < t(result)` | FR-004 |
| C4 | If any legal `c` with `r(c) <= r(drawn_code)` satisfies `t(c) + 0.1 * hull_tons * r(c) <= budget`, then `result` satisfies it too, and no such `c` has `r(c) > r(result)` — the highest affordable rating wins | FR-003 |
| C5 | If no such `c` exists, `r(result) == min(r(c))` over all legal `c` — the starved-hull fallback | FR-014 |
| C6 | Total: never raises for any input satisfying the preconditions | FR-014 |
| C7 | Pure: reads only `hull_tons`, `drawn_code`, `budget` and the static tables; consumes no `Rolls` draw | FR-008 |
| C8 | Idempotent: `_fit_jump_drive(hull_tons, result, budget) == result` | — |

### Worked examples

| Hull | Drawn | Budget | Result | Why |
| --- | --- | --- | --- | --- |
| 400 | `C` (J-1, 20 t) | 200 | `B` | B is J-1 at 15 t; same rating, 5 t lighter (C3/FR-004) |
| 700 | `Z` (J-6, 125 t) | 600 | `U` | U is J-6 at 100 t, needing 520 t; rating kept, 25 t saved (C3) |
| 700 | `Z` (J-6, 125 t) | 400 | `N` | J-6 needs 520 t; J-4 via N needs 70 + 280 = 350 ≤ 400 (C4) |
| 100 | `C` (J-6, 20 t) | 72 | `B` | J-6 needs 20 + 60 = 80 > 72; J-4 via B needs 15 + 40 = 55 ≤ 72 (C4) |
| 100 | `A` (J-2, 10 t) | 5 | `A` | Nothing fits; A is the lowest-rated legal drive (C5/FR-014) |

The fourth row is the spec's Overview scenario: a 100-ton hull carrying maneuver drive A and power
plant C, which leaves 72 tons for the jump drive and its fuel once the 10-ton bridge, the 2-ton
maneuver drive, the 10-ton power plant and its 6 tons of fuel are paid for. Today it mounts a Jump-6
drive and buys 5 jump-numbers of fuel for a reported range of zero. It now mounts a Jump-4 drive and
flies.

The budget here is 72, not the 56 tons of *fuel tankage* the ship's description reports. That 56 is
50 tons of jump fuel plus 6 of power-plant fuel, an output of the allocation rather than an input to
it. The two were conflated in an earlier draft; the resulting drive is `B` either way, so the error
was invisible in the outcome.
