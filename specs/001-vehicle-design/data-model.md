# Phase 1 Data Model: Vehicle Design System

**Feature**: `001-vehicle-design` | **Date**: 2026-08-07 | **Plan**: [plan.md](./plan.md)

Every record here is a frozen dataclass validated from `__post_init__` by a module-level
`_validate_<name>` declared immediately above it, raising `ValueError` naming the offending value
and, for vocabulary errors, the legal set. Collections are tuples defaulting to `()`, never lists.
This is the ships house style throughout; where vehicles depart from it, the departure is called out.

## Layer 1: tables (`tables.py`)

Row types, one per table shape, each a frozen dataclass whose fields are the table's columns.
Values live in module-level annotated `SCREAMING_SNAKE` constants built with keyword arguments.
No functions, no in-package imports, one bare docstring under each constant naming its SRD table
and its key columns.

| Row type | Constant | Key | Notes |
|---|---|---|---|
| `ChassisRow` | `CHASSIS` | chassis code `"1"`–`"9"`, `"A"`–`"Q"` (no I, no O) | tons, spaces, price, build hours, size, example. Stops at 20 tons, which is what makes FR-013 a missing-row check rather than a special case. |
| `ConfigurationRow` | `CONFIGURATIONS` | `Configuration.value` | chassis price modifier only: closed ×1, open ×0.9. |
| `ArmorRow` | `ARMOR` | armor type name | `tl`, base, additional protection, price, max armor. |
| `HullStructureRow` | `HULL_STRUCTURE` | tons band | hull, structure at personal combat scale. |
| `PowerPlantRow` | `POWER_PLANTS` | power plant type | `tl`, space mod, price mod, fuel. Modifiers against the fusion baseline in `DRIVE_COSTS`. |
| `PropulsionRow` | `PROPULSION` | propulsion type | `tl`, contact or thrust, space mod, price mod, examples. |
| `DriveRow` | `DRIVE_COSTS` | drive code `"A"`–`"Z"` (no I, no O) | power plant spaces and price, contact spaces and price, thrust spaces and price. |
| n/a | `DRIVE_PERFORMANCE` | `dict[str, dict[str, int \| None]]`, drive code → chassis code | The book's two tables merged; their split is a page-width artifact. `None` is the printed em-dash. |
| `SpeedRow` | `BASE_SPEED` | propulsion type | `tl` plus speeds at performance 1–6, in kph. The Mole's values are meters per hour, flagged on the row. |
| `FuelRow` | `POWER_PLANT_FUEL` | drive code | spaces, then fuel per week, per day, per hour. Early-fusion baseline. |
| `FuelModRow` | `FUEL_CONSUMPTION` | power plant type | `tl`, fuel mod, price per space, notes. Antimatter is a special case, not a multiplier. |
| `AgilityRow` | `AGILITY_MODIFIERS` | agility factor name | additive modifier. Two rows are unreachable under the 20-ton cap and transcribe anyway. |
| `ControlRow` | `CONTROLS` | interface name | `tl`, spaces, price, agility, initiative, notes. Primitive's price is a chassis-price modifier, not a figure. |
| `DroneControllerRow` | `DRONE_CONTROLLERS` | interface name | `tl`, spaces, price, control DM, range. |
| `RobotBrainRow` | `ROBOT_BRAINS` | CPU type | spaces decrease as `tl` rises. |
| `CommunicationRow` | `COMMUNICATIONS` | class I–IV | `tl`, spaces, price, range. |
| `CommunicatorModRow` | `ALTERNATIVE_COMMUNICATORS` | laser, maser, meson | multipliers over `COMMUNICATIONS`. |
| `SensorRow` | `SENSORS` | package name | `tl`, spaces, price, comms DM, max range, includes. |
| `ComputerRow` | `COMPUTERS` | model 0–5 | `tl`, space, price. Models 2 and up take no space. |
| `AccommodationRow` | `ACCOMMODATIONS` | accommodation name | duration, spaces, price, occupancy notes. |
| `LifeSupportRow` | `LIFE_SUPPORT` | basic, extended | `tl`, spaces per head count, price per space. |
| `TrailerRow` | `CARGO_TRAILERS` | trailer size | price, capacity, description. |
| `ManipulatorRow` | `MANIPULATOR_MAXIMUMS` | tech level 5, 8, 11, 14 | max strength, max dexterity. One of only three transcribed tables whose values vary with TL. |
| `ComponentRow` | `ADDITIONAL_COMPONENTS` | component name | `tl`, spaces, price. Several rows defer to prose. |
| `GunPortWeaponRow` | `GUN_PORT_WEAPONS` | weapon name | `tl`, price, spaces, RoF, range, damage, recoil, LL. |
| `MountRow` | `WEAPON_MOUNTS` | mount type | `tl`, price, max spaces, stabilized. Gun Shield is priced per point of armor and has no `tl`. |
| `TurretRow` | `TURRETS` | turret type | spaces and price are formulas, so the row carries coefficients rather than figures. |
| `TurretWeaponRow` | `TURRET_WEAPONS` | weapon-at-TL name, e.g. `"howitzer-tl12"` | 76 rows; fourteen families recur at several TLs, so TL is part of the row identity. |
| `AmmunitionRow` | `WEAPON_AMMUNITION` | weapon family, TL-agnostic | price per space, rounds per space. Missile Rack defers to the missile table. |
| `OrdinanceRow` | `ORDINANCE_BAY_WEAPONS` | ordinance type | `tl`, spaces, price, range, damage, notes. Six torpedo rows are watercraft-only. |
| `MissileRow` | `MISSILES` | missile type | `tl`, spaces, price, range, damage. |
| `AntiMissileRow` | `ANTI_MISSILE_SYSTEMS` | system type | `tl`, effect, spaces, price, minimum range, uses, reload price. |
| `LiftEnvelopeRow` | `LIFT_ENVELOPES` | atmosphere density | envelope size formulas by lifting medium. |
| `GaitRow` | `ANIMAL_GAITS` | gait | speed modifier, range. |
| `AnimalRow` | `DRAFT_ANIMALS` | animal | strength, walk and run speed, endurance. Required by the Stagecoach. |
| `SailingRow` | `SAILING_SPEEDS` | vehicle medium | speed as a percentage of wind speed, by displacement band. |
| `DiveDepthRow` | `SUBMERSIBLE_DIVE_DEPTH` | tech level | safe dive depth, crush depth. Watercraft-only, transcribed under FR-003's completeness clause and read by nothing. |

Thirty-seven constants over thirty-eight SRD tables, the two Drive Performance tables having merged.
A test asserts both numbers (FR-003).

### Option families (`tables.py`)

The chapter prints six families of options as prose definition lists rather than as tables, and
FR-003a requires them as data all the same. One `OptionRow` type serves all six, because they share
a shape: a modifier rather than a figure.

`OptionRow`: `name: str`, `tl: int | None`, `spaces: float = 0.0`,
`spaces_pct_of_chassis: float = 0.0`, `price: float = 0.0`, `price_pct_of_chassis: float = 0.0`,
`price_per_ton: float = 0.0`, `price_per_space: float = 0.0`, `speed_mult: float = 1.0`,
`speed_pct: float = 0.0`, `agility_mod: int = 0`, `max_selections: int = 1`, `notes: str = ""`.

Every field defaults to the identity, so a row states only what the chapter states about it. The
zero-price, zero-space option is legal and common: several entries change only a derived figure.

| Constant | Entries | Shape it exercises |
|---|---|---|
| `CONFIGURATION_OPTIONS` | 11 | `price_pct_of_chassis` (Streamlined +300%, Open Frame −20%), `price_per_ton` (Self-Sealing), `price_per_space` (the four Environmental Protection Systems), `spaces_pct_of_chassis` (Wave-Piercing Hull, 5% rounded up), `speed_mult` (Streamlined ×5) |
| `ARMOR_OPTIONS` | 5 | `price` (Electrostatic Cr10,000, 1 space), `price_per_ton` (Reflec, Stealth), `price_pct_of_chassis` with `max_selections=2` (Reinforced Hull, Reinforced Structure) |
| `DRIVE_OPTIONS` | 11 | `price_pct_of_chassis` (Increased Agility +50%, Decreased Agility −25%), `agility_mod`, plus Extended Operational Environment Range, relocated here from Atmospheres and Aircraft per FR-003a and recorded at the site |
| `CONTROL_OPTIONS` | 1 | Autopilot: `price` plus a TL-derived skill level in `notes` |
| `COMPUTER_OPTIONS` | 1 | Hardened Systems: `price_pct` of the computer, expressed as `ComputerFit.hardened` |
| `ARMAMENT_OPTIONS` | 5 | multipliers on a weapon's price, RoF and damage rather than on the vehicle |

Thirty-four entries in six constants, and a test asserts that count as it does FR-003's.

Two derived constants, both data rather than logic, both asserted by tests:

- `LOCOMOTION_ALIASES: dict[str, tuple[str, ...]]`—the coarse aliases FR-026a requires (`grav`,
  `wheeled`, `tracked`, `rotor`, `jet`, `legged`, `rail`, `mole`, `non-powered`), each mapped to
  `PROPULSION` keys. SC-010 is a test that every alias resolves to at least one row.
- `WATERCRAFT_ONLY: frozenset[str]`—the configuration options, propulsion types, sensor package,
  ordinance rows and components that only make sense afloat. FR-013's message reads from it.

**Tech level is a gate, not a dimension.** `tl` is a scalar column on the rows that have one.
`getattr(row, "tl", None)` is how the builder derives a vehicle's TL, so adding a `tl` column to a
row type later widens the derivation with no code change. That is ships' idiom and it holds here.

## Layer 2: input records (`models.py`)

### Enums

Plain `Enum`, lowercase snake string values, as in `ships/models.py`.

- `Configuration`—`OPEN`, `CLOSED`.
- `PowerPlantType`, `PropulsionType`—mirror their table keys.
- `ControlInterface`—the five interface names shared by `CONTROLS` and `DRONE_CONTROLLERS`.
- `MountKind`—`TURRET`, `GUN_PORT`, `ORDINANCE_BAY`, `MISSILE_RACK`.

### Component fits

| Record | Fields | Validation |
|---|---|---|
| `ArmorFit` | `type: str`, `increments: int = 1` | type in `ARMOR`; increments at least 1 and within the row's max armor. Additional armor is bought in 5%-of-chassis increments, minimum one space. |
| `DriveFit` | `code: str`, `kind: PowerPlantType \| PropulsionType` | code in `DRIVE_COSTS`. |
| `ComputerFit` | `model: int`, `hardened: bool = False` | model in `COMPUTERS`. |
| `AccommodationFit` | `kind: str`, `count: int = 1` | kind in `ACCOMMODATIONS`; count at least 1. |
| `ComponentFit` | `kind: str`, `count: int = 1` | kind in `ADDITIONAL_COMPONENTS`. |
| `AmmunitionFit` | `spaces: float`, `kind: str \| None = None` | spaces above 0. Not expressible outside a `WeaponFit`. |
| `WeaponFit` | `name: str`, `ammunition: tuple[AmmunitionFit, ...] = ()`, `options: tuple[str, ...] = ()` | name in `TURRET_WEAPONS`, `GUN_PORT_WEAPONS`, `ORDINANCE_BAY_WEAPONS` or `MISSILES`; ammunition rejected outright for a weapon whose family has no `WEAPON_AMMUNITION` row (FR-016 and the edge case); each option in `ARMAMENT_OPTIONS`, because an armament option modifies the weapon rather than the vehicle, and Heavy and Light Turret Weapon are mutually exclusive by the chapter's own sentence. |
| `MountFit` | `kind: MountKind`, `mount: str`, `weapons: tuple[WeaponFit, ...] = ()` | mount in `WEAPON_MOUNTS` or `TURRETS`; a mount with no weapon is legal and costs what an empty mount costs; a weapon illegal in this mount is rejected. |

**The nesting is the constraint.** FR-015 is satisfied structurally rather than by validation:
a magazine is a field of a weapon and a weapon is a field of a mount, so a magazine without a
weapon and a weapon outside a mount are not expressible in the type, let alone in the file.

### `VehicleDesign`

The referee's authored input, mirroring the TOML one-to-one. Frozen; every field except
`tech_level` and `chassis` defaulted.

| Field | Type | Notes |
|---|---|---|
| `tech_level` | `int` | **Required.** FR-011: no default, and a design without one fails to build. |
| `chassis` | `str` | Required. A chassis code key into `CHASSIS`. |
| `configuration` | `Configuration` | Defaults to `CLOSED`. |
| `configuration_options` | `tuple[str, ...]` | Each must be a `CONFIGURATION_OPTIONS` key. Streamlined, Open Frame, Self-Sealing and the rest. Watercraft options load cleanly and are rejected at build (FR-013). |
| `armor` | `tuple[ArmorFit, ...]` | |
| `armor_options` | `tuple[str, ...]` | Each must be an `ARMOR_OPTIONS` key. |
| `power_plant` | `DriveFit \| None` | `None` is legal: the Stagecoach has none. |
| `propulsion` | `DriveFit \| None` | `None` for animal-drawn and sailed vehicles. |
| `drive_options` | `tuple[str, ...]` | Each must be a `DRIVE_OPTIONS` key. Renamed from `propulsion_options`: the chapter calls them Vehicle Drive Options and several apply to the power plant rather than to propulsion, so the old name was both off-SRD and wrong. |
| `control_options` | `tuple[str, ...]` | Each must be a `CONTROL_OPTIONS` key. Autopilot is the only entry, and it was previously unexpressible. |
| `fuel_weeks` | `float` | Endurance, from which fuel spaces are derived. |
| `controls` | `ControlInterface` | |
| `drone_controller` | `ControlInterface \| None` | |
| `robot_brain` | `str \| None` | |
| `communications` | `str \| None` | |
| `communicator_type` | `str \| None` | Laser, maser or meson modifier over the base class. |
| `sensors` | `str \| None` | |
| `computer` | `ComputerFit \| None` | |
| `crew` | `int` | |
| `accommodations` | `tuple[AccommodationFit, ...]` | |
| `life_support` | `str \| None` | |
| `components` | `tuple[ComponentFit, ...]` | |
| `mounts` | `tuple[MountFit, ...]` | |
| `trailer` | `str \| None` | |
| `standard_design` | `bool` | One flag, three effects (FR-007): the 10% discount, no design fee, and base build hours rather than ten times them. There is deliberately no second `mass_produced` field, because the chapter defines base construction time as being "for mass production of a standard design," so a design that could set them apart would be expressing a state the rules do not have. |

**Every option tuple validates against its family.** An unknown option raises `ValueError` naming the
option and the legal set, exactly as an unknown component does. That is what turns FR-013's refusal
of Submersible, Hydrofoils and Wave-Piercing Hull into a `WATERCRAFT_ONLY` membership test over a
vocabulary that exists, rather than a string comparison against a list that lives nowhere.

**No `cargo` field.** FR-006 makes cargo the unconsumed remainder, and a design file that could
declare it would let a referee state a figure the builder then contradicts.

## Layer 3: output records (`models.py`)

### `LineItem`

`name: str`, `spaces: float`, `price: float`, `discountable: bool = True`.

The `discountable` flag is where research correction C-002 lands: fuel and ammunition line items
are built with `discountable=False`, because the construction rules exempt them from the standard
design discount even though the published examples appear to discount the whole total. The
divergence that creates is recorded on `DIVERGENCES.md`.

### `Vehicle`

The built result, frozen, carrying `design` plus everything derived from it.

| Field | Type | Derivation |
|---|---|---|
| `design` | `VehicleDesign` | As given. |
| `tech_level` | `int` | The design's, used as stated and never clamped. |
| `spaces` | `float` | Chassis capacity, twelve to the displacement ton. |
| `spaces_used` | `float` | `sum(item.spaces for item in line_items)`, fractional throughout. |
| `cargo_spaces` | `float` | `spaces - spaces_used`. Negative is FR-014's rejection, not a value. |
| `armor_protection` | `int` | |
| `agility` | `int` | Sum over `AGILITY_MODIFIERS` rows the design earns. |
| `speed` | `float \| None` | From `BASE_SPEED` at the propulsion's drive performance. `None` when unpowered. |
| `cruise_speed` | `float \| None` | 75% of `speed`. |
| `range_km` | `float \| None` | From endurance and speed, +50% at cruise. |
| `power_performance` | `int \| None` | `DRIVE_PERFORMANCE[code][chassis]`. |
| `propulsion_performance` | `int \| None` | Same table, contact or thrust column. |
| `hull` | `int` | `HULL_STRUCTURE`. |
| `structure` | `int` | `HULL_STRUCTURE`. |
| `crew` | `int` | |
| `passengers` | `int` | From `ACCOMMODATIONS` occupancy less crew. |
| `fuel_spaces` | `float` | |
| `design_fee` | `float` | `0.0` for a standard design; otherwise 1% of the discounted total, floored at Cr100 (FR-007). Its own non-discountable `LineItem`. |
| `price` | `float` | Discountable lines ×0.9 when elected, plus exempt lines, plus `design_fee`. The description prints this figure, which is what the template's "(including discounts and fees)" asks for. |
| `build_hours` | `float` | Chassis base hours × total armor, floored at ×1; ×10 again when `design.standard_design` is false, which is the chapter's "custom-made". |
| `line_items` | `tuple[LineItem, ...]` | The component table FR-025a prints. |

## Layer 4: catalog and published figures

### `CatalogEntry` (`catalog.py`)

Not a stored record but the pairing the module exposes: a stable kebab-case `name`, the installed
`catalog/<name>.toml`, and the `PUBLISHED[name]` figures. Public surface is
`catalog_names() -> tuple[str, ...]` and `load_catalog(name) -> VehicleDesign`, the latter raising
`ValueError` naming the available names when the name is unknown (FR-024a).

The fifteen names, in the sorted order `catalog_names()` returns and the `catalog` command prints:
`afv-tracked`, `air-raft`, `atv-tracked`, `biplane`, `g-carrier`, `grav-bike`, `grav-floater`,
`grav-tank`, `ground-car`, `helicopter`, `speeder`, `stagecoach`, `tunnel-boring-machine`,
`twin-engine-jet`, `van`. This is the canonical list; `spec.md` FR-021 groups the same fifteen by
chapter for readability and `contracts/library.md` names none of them.

### `PUBLISHED` (`published.py`)

`dict[str, dict[str, object]]`, catalog name → figure name → the value the book prints. Transcribed
from the SRD text, verified against it rather than against the builder. Figure names are the stat
block's own labels: `spaces`, `cargo`, `price`, `discounted_price`, `prose_price`, `agility`,
`speed`, `armor`, `crew`, `build_time`.

This lives in the package, not in `tests/`, for two reasons: it is transcribed SRD data and
Principle I puts that in data separate from the code that consults it, and `scripts/check_docs.py`
has to read it without importing from the test tree.

### `Divergence`

A row of `DIVERGENCES.md`, parsed rather than stored: vehicle, figure, published value, cetools
value, reason. Both enforcement paths read the same markdown table, which is what keeps them from
disagreeing about what has been documented.

## Layer 5: generation (`generator.py`)

### `Role`

New machinery, and the one place vehicles departs from ships by design. A plain `Enum` naming what
a vehicle is for, each member paired with a `LoadoutProfile` deciding which categories are filled
and from what pool: which chassis sizes, which locomotion families, whether armaments are drawn at
all, which accommodations and which additional components suit it.

Roles live in `generator.py`, are never imported by `builder.py`, and are documented as cetools
generation policy rather than SRD rules (FR-026c). A generated vehicle is still built by the
ordinary builder, so a profile cannot produce something a referee could not have authored.

### `GenerationConstraints`

Frozen, every field defaulted, one value rather than a keyword per field, with `UNCONSTRAINED` as
the module-level default instance. Fields: `tech_level`, `chassis`, `locomotion`, `role`.

Optional components follow ships' three-state convention where they appear: unset means roll it, a
value means pin it, and the `ABSENT` sentinel means pin its absence.

### `UnmetConstraint`

`field: str`, `asked: str`, `got: str`, `reason: str`. `field` is spelled exactly as a
`GenerationConstraints` field name.

The split ships settled carries over unchanged, and it is the answer to the spec's edge case about
a locomotion no chassis supports:

- **Refused up front with `ValueError`**—anything decidable from the tables alone: an unknown
  chassis code, an alias matching no propulsion row, a tech level below a chassis minimum.
- **Degraded and recorded**—anything that depends on the running spaces budget. Generation still
  returns a vehicle.

The governing distinction, worth carrying into the code comments: **a pin is a promise, a roll is
only a preference.** A drawn value that will not fit is dropped in silence and produces no
`UnmetConstraint`.

### `GenerationResult`

`vehicle: Vehicle`, `unmet: tuple[UnmetConstraint, ...] = ()`. Generation never fails on spaces.

### `SpacesLedger`

The one deliberately mutable class in the domain, modeled on ships' `TonnageLedger`: a running
budget with `spend`, `affords`, `decline` and `declined`, owning both the arithmetic and the record
of what it could not honor.

## Entity relationships

```text
VehicleDesign ──1:1──> Vehicle           (build_vehicle)
VehicleDesign ──1:N──> MountFit ──1:N──> WeaponFit ──1:N──> AmmunitionFit
Vehicle       ──1:N──> LineItem          (the component table)
CatalogEntry  ──1:1──> VehicleDesign     (an installed catalog/<name>.toml)
CatalogEntry  ──1:1──> PUBLISHED[name]   (the transcribed stat block)
Divergence    ──N:1──> CatalogEntry      (a row of DIVERGENCES.md)
Role          ──1:1──> LoadoutProfile ──> GenerationConstraints ──> GenerationResult
```

## State transitions

None. Every record is frozen and every operation is a pure function from one to the next:
TOML → `VehicleDesign` → `Vehicle` → text. The one mutable object, `SpacesLedger`, lives inside a
single generation call and never escapes it.
