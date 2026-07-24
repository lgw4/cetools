# Phase 1 Data Model: Starship Generator

All types are frozen dataclasses / enums in `src/cetools/engine/ships/models.py`, following the
project's immutable-value-object convention (`__post_init__` calls a module-level `_validate_*` that
raises `ValueError` with a specific message). SRD numbers are the small integers / MCr floats
from [research.md](./research.md). Two record families exist: **`ShipDesign`** (declarative input,
mirrors the TOML schema) and **`Ship`** (computed output / sheet, carries its `ShipDesign`).

## Enums

### `Configuration`

| Member | Cost modifier | Rule |
|--------|---------------|------|
| `DISTRIBUTED` | ×0.9 | Cannot mount fuel scoops |
| `STANDARD` | ×1.0 | Default |
| `STREAMLINED` | ×1.1 | Includes fuel scoops |

Carries a `.cost_modifier` property.

### `ArmorType`

| Member | Protection / 5% | Cost (% base hull / 5%) | Min TL |
|--------|-----------------|-------------------------|--------|
| `TITANIUM_STEEL` | 2 | 5% | 7 |
| `CRYSTALIRON` | 4 | 20% | 10 |
| `BONDED_SUPERDENSE` | 6 | 50% | 14 |

### `HullClass`

`STARSHIP` (100–5,000 t, jump-capable) vs `SMALL_CRAFT` (10–95 t, no jump). Selects which rule set
(bridge vs cockpit, fuel minimum, armament caps) the builder applies.

## Input records (`ShipDesign` and parts)

### `ShipDesign`

The declarative build order, produced by `load_design` or the generator; consumed by `build_ship`.

| Field | Type | Range / Rule |
|-------|------|--------------|
| `hull_tons` | `int` | a tabulated hull size (100–5,000 standard, 10–95 small craft) |
| `configuration` | `Configuration` | default `STANDARD` |
| `hull_class` | `HullClass` | derived from `hull_tons` if unset |
| `jump_code` | `str \| None` | drive code letter; required for starship, forbidden for small craft |
| `maneuver_code` | `str \| None` | drive code letter; optional |
| `power_code` | `str \| None` | drive code letter; required for any powered craft |
| `jump_distance` | `int \| None` | intended jump range for fuel; `None` ⇒ assume full jump rating |
| `power_weeks` | `int` | ≥ 2 (starship) or ≥ 1 (small craft); defaults to the minimum |
| `armor` | `tuple[ArmorFit, ...]` | zero or more armor layers |
| `bridge` | `bool` | default `True` for starships; small craft use a cockpit instead |
| `cockpit` | `str \| None` | small-craft cockpit type; mutually exclusive with `bridge` |
| `computer` | `ComputerFit \| None` | model + options + software |
| `electronics` | `str \| None` | electronics package name |
| `staterooms` | `int` | ≥ 0 |
| `low_berths` | `int` | ≥ 0 |
| `emergency_low_berths` | `int` | ≥ 0 |
| `fittings` | `tuple[FittingFit, ...]` | armory, fuel scoops/processor, lab, library, luxuries, vault, hangar, detention |
| `turrets` | `tuple[TurretFit, ...]` | each: mount type + weapons + ammo |
| `bays` | `tuple[BayFit, ...]` | 50-ton bays (starship only) |
| `screens` | `tuple[ScreenFit, ...]` | meson screen, nuclear damper |
| `passengers_high` | `int` | ≥ 0 (drives steward/medic crew) |
| `passengers_middle` | `int` | ≥ 0 |
| `standard_design` | `bool` | default `False`; `True` applies the 10% discount |
| `name` | `str \| None` | optional ship name for the sheet |

**Validation (raises `ValueError`)—shape only.** `ShipDesign.__post_init__` checks that the record is
*well-formed*, never that it is *rules-legal*: field types and ranges (`staterooms ≥ 0`,
`computer.model` in 1–7), enum membership (`configuration`, `ArmorType`, mount/kind strings), drive
codes being letters in the SRD sequence, and `bridge` XOR `cockpit` (a structurally impossible record,
not an SRD rule).

**Every SRD rule check belongs to the builder** (FR-015), including the ones a reader might expect
here: `hull_tons` being a tabulated size, a starship having a `jump_code` and `power_code`, a small
craft carrying no jump drive and no bays, and armor arriving in 5% increments. This keeps a single
validation authority and is what makes FR-015's "first violation in SRD build order" observable—if
`__post_init__` rejected an armor increment, a design that *also* had an earlier hull error would
report the wrong rule. `load_design` is likewise shape-only (see contracts/design-schema.md).

Component-*interaction* checks (tonnage budget, power-plant rating, hardpoints, software rating) are
in the builder for the same reason, and additionally because they need derived totals.

### Component fits

All eight are part of the package's public surface (contracts/engine-api.md): building a `ShipDesign`
in code needs them.

- **`ArmorFit`**: `type: ArmorType`, `percent: int` (multiple of 5), `options: tuple[str, ...]`
  (`reflec`/`self_sealing`/`stealth`).
- **`ComputerFit`**: `model: int` (1–7), `jump_control: bool`, `hardened: bool`,
  `software: tuple[SoftwareFit, ...]` (name + rating level).
- **`FittingFit`**: `kind: str` (SRD fitting name), `quantity: int`, plus `vehicle_tons: int \| None`
  for a custom hangar.
- **`TurretFit`**: `mount: str` (single/double/triple/pop_up/fixed), `weapons: tuple[str, ...]`,
  `ammo: tuple[AmmoFit, ...]` (sand barrels, missiles by type).
- **`BayFit`**: `kind: str` (missile_bank/particle/meson/fusion).
- **`ScreenFit`**: `kind: str` (meson_screen/nuclear_damper).

## Output records (`Ship` and parts)

### `Ship`

The computed sheet, produced by `build_ship(design)` and `generate_ship(...)`.

| Field | Type | Meaning |
|-------|------|---------|
| `design` | `ShipDesign` | the originating design (enables lossless round-trip, SC-008) |
| `hull_tons` | `int` | echoed hull size |
| `configuration` | `Configuration` | echoed configuration |
| `jump_rating` | `int` | derived from `jump_code` + hull (0 if none) |
| `maneuver_rating` | `int` | derived from `maneuver_code` + hull (0 if none) |
| `power_rating` | `int` | derived from `power_code` + hull |
| `jump_fuel` | `float` | 0.1 × hull × jump distance |
| `assumed_jump_distance` | `int` | the jump range used for fuel; rendered on the sheet (FR-006, FR-022) |
| `power_fuel` | `float` | ⌊power tons ÷ 3⌋ × weeks (small craft: rounded to 0.1 t) |
| `tonnage_used` | `float` | sum of every component's tonnage |
| `cargo_tons` | `float` | `hull_tons − tonnage_used` (≥ 0; may be exactly 0) |
| `hull_points` | `int` | ⌊hull ÷ 50⌋ (+4 with a vault) |
| `structure_points` | `int` | ⌈hull ÷ 50⌉ (+4 with a vault) |
| `armor_protection` | `int` | Σ over armor layers of `protection_per_5_percent × increments` (0 if unarmored) |
| `hardpoints` | `int` | ⌊hull ÷ 100⌋ (1 for a small craft) |
| `hardpoints_used` | `int` | turrets + bays |
| `crew` | `Crew` | minimum crew breakdown (see below) |
| `total_cost` | `float` | MCr, discount applied iff `standard_design` |
| `build_weeks` | `int` | from the hull table |
| `line_items` | `tuple[LineItem, ...]` | per-component (name, tons, cost) for the sheet |

**Derived:**

- `is_valid` is implicit: a returned `Ship` is always valid; invalid designs never produce a `Ship`
  (the builder raises `ValueError` first).

`Ship` carries no rendering method: the sheet is produced by the free function `render_sheet(ship)` in
`ships/sheet.py`, so `models.py` never imports `sheet.py` and the dependency runs one way only.

### `Crew`

| Field | Type | Rule (SRD minimum, research Part I) |
|-------|------|-------------------------------------|
| `pilot` | `int` | 1 |
| `navigator` | `int` | 1, or 0 if Jump-Control software present |
| `engineers` | `int` | ⌈(drive+plant tons) ÷ 35⌉ (0 if no drives/plant) |
| `gunners` | `int` | turrets + bays |
| `screen_operators` | `int` | 1 per screen |
| `medic` | `int` | 0 when `passengers_high + passengers_middle == 0`; otherwise ⌈(crew + passengers) ÷ 120⌉ |
| `stewards` | `int` | per 4 high / 10 middle passengers (0 with no passengers) |

Only high and middle passengers count as "carries passengers" for the steward and medic triggers
(FR-012); occupied low berths trigger neither role and are excluded from the medic headcount.

**Derived:** `total` → sum of all roles.

### `LineItem`

`name: str`, `tons: float`, `cost: float` (MCr), `discountable: bool` (default `True`). The builder
appends one per component in build order; the sheet and the tonnage/cost totals both read from this
list, so "the numbers" and "the breakdown" can never disagree. `discountable=False` is set on jump
fuel, power-plant fuel, and ammunition—the SRD items the 10% standard-design discount never
applies to (FR-013)—as an explicit flag rather than a name-suffix check, so a future SRD entry whose
name happens to end in "fuel" or "ammo" is not silently exempted (SC-006).

## Builder-enforced constraints (rejections → `ValueError`, FR-015 / SC-005)

Each rejection message names the violated rule. The table is ordered by the SRD build order below, and
the builder evaluates the checks in exactly that order, so a design violating several constraints
reports the first one (FR-015):

| # | Constraint | Build step | Message shape |
|---|------------|------------|---------------|
| 1 | Unknown hull size | hull | `"N tons is not a tabulated hull size"` |
| 2 | Armor increment | armor | `"armor must be added in 5% increments (min 1 ton)"` |
| 3 | Drive not on this hull | drives | `"drive code X is not available on an N-ton hull"` |
| 4 | Missing required system | drives / power | `"starship requires a jump drive"` / `"powered craft requires a power plant"` |
| 5 | Small-craft jump drive | drives | `"small craft cannot mount a jump drive"` |
| 6 | Power-plant below drives | power | `"power plant rating N below required M (higher of jump/maneuver)"` |
| 7 | Small-craft hull built with a bridge | bridge/cockpit | `"small craft requires a cockpit, not a bridge"` |
| 8 | Starship hull built with a cockpit | bridge/cockpit | `"a starship requires a bridge, not a cockpit"` |
| 9 | Software over computer rating | computer | `"software rating N exceeds computer rating M"` |
| 10 | Fuel scoops on a distributed hull | fittings | `"a distributed hull cannot mount fuel scoops"` |
| 11 | Hardpoint limit | armaments | `"K weapon systems exceed J hardpoints (1 per 100 tons)"` |
| 12 | Small-craft bay weapon | armaments | `"small craft cannot mount a weapon bay"` |
| 13 | Small-craft energy-weapon cap | armaments | `"power plant code X allows at most K energy weapons"` |
| 14 | Tonnage over-allocation | cargo | `"components use N tons, hull holds M"` |

## Static tables (`ships/tables.py`)—data, not logic

| Name | Shape | Purpose |
|------|-------|---------|
| `HULLS` | `dict[int, HullRow]` | tons → (code, cost MCr, build weeks) for standard hulls |
| `SMALL_CRAFT_HULLS` | `dict[int, HullRow]` | tons → (code, cost, build weeks) for 10–95 t |
| `DRIVE_COSTS` | `dict[str, DriveRow]` | code → (jump t/cost, maneuver t/cost, power t/cost) |
| `DRIVE_PERFORMANCE` | `dict[str, dict[int, int]]` | code → {hull tons → rating}; missing = illegal |
| `CONFIG_MODIFIERS` | `dict[Configuration, float]` | ×0.9 / ×1.0 / ×1.1 |
| `ARMOR` | `dict[ArmorType, ArmorRow]` | protection per 5%, cost %, min TL |
| `BRIDGE_SIZES` | ordered `tuple[(max_tons, bridge_tons), ...]` | stepped bridge table |
| `COMPUTERS` | `dict[int, ComputerRow]` | model → (TL, rating, cost) |
| `SOFTWARE` | `dict[str, SoftwareRow]` | name → (rating cost, MCr cost rule) |
| `ELECTRONICS` | `dict[str, ElectronicsRow]` | package → (tons, cost) |
| `QUARTERS` | `dict[str, QuartersRow]` | stateroom / low / emergency-low → (tons, cost) |
| `FITTINGS` | `dict[str, FittingRow]` | fitting name → (tons, cost, extra rules) |
| `TURRET_MOUNTS` | `dict[str, MountRow]` | mount → (tons, cost, weapon slots) |
| `TURRET_WEAPONS` | `dict[str, WeaponRow]` | weapon → cost (+ ammo rules) |
| `AMMO` | `dict[str, AmmoRow]` | ammunition kind (sand barrels, missile by type) → (rounds/ton, cost/round) |
| `BAYS` | `dict[str, BayRow]` | bay → (50 t, cost, +1 t fire control) |
| `SCREENS` | `dict[str, ScreenRow]` | screen → (50 t, cost) |
| `COCKPITS` | `dict[str, CockpitRow]` | small-craft cockpit → (tons, crew, cost) |
| `SMALL_CRAFT_ENERGY_CAPS` | `dict[str, int]` | power-plant code band → max energy weapons |

Adding or adjusting any SRD entry (a new hull, weapon, or fitting) is a data edit to one of these
tables with no change to `builder.py`/`generator.py` (SC-006).

## Relationships

```text
ShipDesign ──build_ship──▶ Ship ──holds──▶ ShipDesign   (round-trip: emit design, rebuild, compare)
Ship ── line_items ─▶ tonnage_used, cargo_tons, total_cost   (single source for numbers + sheet)
Ship ── crew (derived from drives, weapons, passengers)
generate_ship(rolls) ─selects components→ ShipDesign ─build_ship→ Ship   (US2 layered on US1)
```

## Build order (dependencies)

`hull + configuration → armor → maneuver → jump → power (check ≥ drives) → fuel → bridge/cockpit →
computer + software (check ≤ rating) → electronics → quarters → fittings → turrets/bays/screens
(check ≤ hardpoints) → cargo = remainder (check ≥ 0) → crew → cost (discount iff standard) → build
time`. Matches the SRD checklist (research Part A).
