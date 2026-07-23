# Phase 1 Data Model: Starship Generator

All types are frozen dataclasses / enums in `src/cetools/engine/ships/models.py`, following the
project's immutable-value-object convention (`__post_init__` calls a module-level `_validate_*` that
raises `ValueError` with a rule-specific message). SRD numbers are the small integers / MCr floats
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

**Validation (raises `ValueError`):** `hull_tons` is a known size; `jump_code`/`maneuver_code`/
`power_code` are legal letters; small craft has no `jump_code`, no bays, no bridge; a starship has a
`jump_code` and `power_code`; armor increments are multiples of 5% (min 1 t); cockpit XOR bridge.
Component-*interaction* checks (tonnage budget, power-plant rating, hardpoints, software rating) live
in the builder, not here, because they need derived totals.

### Component fits

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
| `assumed_jump_distance` | `int` | the jump range used for fuel (reported per FR-006) |
| `power_fuel` | `float` | ⌊power tons ÷ 3⌋ × weeks (small craft: rounded to 0.1 t) |
| `tonnage_used` | `float` | sum of every component's tonnage |
| `cargo_tons` | `float` | `hull_tons − tonnage_used` (≥ 0; may be exactly 0) |
| `hull_points` | `int` | ⌊hull ÷ 50⌋ (+4 with a vault) |
| `structure_points` | `int` | ⌈hull ÷ 50⌉ (+4 with a vault) |
| `hardpoints` | `int` | ⌊hull ÷ 100⌋ (1 for a small craft) |
| `hardpoints_used` | `int` | turrets + bays |
| `crew` | `Crew` | minimum crew breakdown (see below) |
| `total_cost` | `float` | MCr, discount applied iff `standard_design` |
| `build_weeks` | `int` | from the hull table |
| `line_items` | `tuple[LineItem, ...]` | per-component (name, tons, cost) for the sheet |

**Derived (methods/properties):**

- `sheet` → the human-readable ship sheet (delegates to `ships/sheet.py`).
- `is_valid` is implicit: a returned `Ship` is always valid; invalid designs never produce a `Ship`
  (the builder raises `ValueError` first).

### `Crew`

| Field | Type | Rule (SRD minimum, research Part I) |
|-------|------|-------------------------------------|
| `pilot` | `int` | 1 |
| `navigator` | `int` | 1, or 0 if Jump-Control software present |
| `engineers` | `int` | ⌈(drive+plant tons) ÷ 35⌉ (0 if no drives/plant) |
| `gunners` | `int` | turrets + bays + screens |
| `medic` | `int` | ⌈(crew+passengers) ÷ 120⌉ |
| `stewards` | `int` | per 4 high / 10 middle passengers (0 with no passengers) |

**Derived:** `total` → sum of all roles.

### `LineItem`

`name: str`, `tons: float`, `cost: float` (MCr). The builder appends one per component in build
order; the sheet and the tonnage/cost totals both read from this list, so "the numbers" and "the
breakdown" can never disagree.

## Builder-enforced constraints (rejections → `ValueError`, FR-015 / SC-005)

Each rejection message names the violated rule:

| Constraint | Message shape |
|------------|---------------|
| Tonnage over-allocation | `"components use N tons, hull holds M"` |
| Power-plant below drives | `"power plant rating N below required M (higher of jump/maneuver)"` |
| Hardpoint limit | `"K weapon systems exceed J hardpoints (1 per 100 tons)"` |
| Missing required system | `"starship requires a jump drive"` / `"powered craft requires a power plant"` |
| Small-craft violation | `"small craft cannot mount a jump drive"` / `"…a weapon bay"` |
| Drive not on this hull | `"drive code X is not available on an N-ton hull"` |
| Software over computer rating | `"software rating N exceeds computer rating M"` |
| Armor increment | `"armor must be added in 5% increments (min 1 ton)"` |
| Small-craft energy-weapon cap | `"power plant code X allows at most K energy weapons"` |

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
