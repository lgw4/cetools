# Contract: New public surface on `cetools.engine.ships`

**Branch**: `001-prompt-acceptable-values` | **Date**: 2026-07-29

Eleven accessors are added to `src/cetools/engine/ships/generator.py` and exported from
`src/cetools/engine/ships/__init__.py`. Rationale and the alternatives rejected are in
[research.md Decision 1](../research.md).

Each exists because the prompt must read the same table the acceptance check reads (FR-003,
SC-006), and because `tables.py` is not on the package's public surface, so `cli/` cannot read it
without breaching Constitution II.

---

## Signatures

```python
def hull_tonnages(hull_class: HullClass) -> tuple[int, ...]: ...
def armor_options() -> tuple[str, ...]: ...
def computer_models() -> tuple[int, ...]: ...
def electronics_packages() -> tuple[str, ...]: ...
def fitting_kinds() -> tuple[str, ...]: ...
def bay_kinds() -> tuple[str, ...]: ...
def screen_kinds() -> tuple[str, ...]: ...
def turret_mounts() -> tuple[str, ...]: ...
def turret_weapons() -> tuple[str, ...]: ...
def small_craft_weapons(
    hull_tons: int, power_rating: int, mount: str | None = None
) -> tuple[str, ...]: ...
def hardpoints(hull_class: HullClass, hull_tons: int) -> int: ...
```

## Behaviour

| Accessor | Returns | Ordering | Paired validator it must agree with |
|---|---|---|---|
| `hull_tonnages(hull_class)` | every tabulated tonnage for that ruleset | ascending | `validate_hull_tons` |
| `armor_options()` | every key of `ARMOR_OPTIONS` | table order | `ArmorFit.__post_init__` |
| `computer_models()` | every tabulated model number | ascending | `ComputerFit.__post_init__` |
| `electronics_packages()` | every key of `ELECTRONICS` | table order (`standard` first) | `validate_electronics` |
| `fitting_kinds()` | every fitting installable from a bare kind—`FITTINGS` less the vehicle-sized ones | table order | `FittingFit.__post_init__` |
| `bay_kinds()` | every key of `BAYS` | table order | `BayFit.__post_init__` |
| `screen_kinds()` | every key of `SCREENS` | table order | `ScreenFit.__post_init__` |
| `turret_mounts()` | every key of `TURRET_MOUNTS` | table order | `validate_turret_mount` |
| `turret_weapons()` | every key of `TURRET_WEAPONS` | table order | `validate_turret_weapon` |
| `small_craft_weapons(tons, rating, mount)` | every turret weapon this plant can run in this mount | as `turret_weapons()` | `validate_small_craft_weapon` |
| `hardpoints(hull_class, tons)` | how many turrets this hull can mount | n/a | `validate_turret_count` |

**Ordering**: table order is preserved rather than sorted, because the SRD tables are already in a
meaningful order (`ELECTRONICS` runs `standard` → `very advanced`; `TURRET_MOUNTS` runs
`single` → `fixed`) and a referee reads a progression more easily than an alphabetisation. The
numeric sets sort ascending so run collapsing (FR-005) can apply. This is a change of habit from the
existing `_TURRET_MOUNTS`/`_TURRET_WEAPONS` module constants, which sort; those are roll tables and
are left alone.

**Empty results**: `small_craft_weapons` is never empty—a sandcaster and a missile rack cost no
energy allowance. `hardpoints` returns at least 1 for every tabulated hull. Only
`small_craft_power_ratings` (pre-existing) can come back empty; see
[research.md Decision 9](../research.md).

**`fitting_kinds()` and the vehicle-sized exclusion**: the exclusion is derived from the table, not
listed—a row whose `tons` is `None` is vehicle-sized, which is what `models._vehicle_sized_fittings`
already asks. Adding another vehicle-sized fitting therefore drops out of the prompt with no edit
(SC-006). Today this excludes `vehicle_hangar` only.

**`hardpoints` is a rename, not new logic**: it exposes the existing `_hardpoints_for`, which
`validate_turret_count` already calls. The private name becomes an alias or is replaced outright.

## Invariants under test

For each row of the table above, a test in `tests/test_ship_generator.py` asserts:

1. **Accessor accepts**: every value the accessor returns passes its paired validator (or
   constructs its paired record) without raising.
2. **Accessor is complete**: every value the paired validator accepts is returned by the
   accessor, asserted by walking the underlying table and checking that each key the validator
   accepts is in the accessor's result.

Together these two make `set(accessor()) == {values the validator accepts}`, which is the fact
`contracts/prompt-contract.md` §7 builds the CLI's `displayed == accepted` invariant on.

## What is not added

- **No accessor for armour type, configuration or hull class.** `ArmorType`, `Configuration` and
  `HullClass` are already exported, and `tuple(member.value for member in Enum)` is the set.
- **No accessor for the ratings.** `available_ratings`, `small_craft_maneuver_ratings`,
  `small_craft_power_ratings` and `power_floor` already exist and are reused unchanged.
- **No accessor for software, ammo, quarters, cockpits or bridge sizes.** No prompt asks for them;
  they stay reachable through hand-authored TOML (spec Assumptions).
- **No change to any table, any validator's logic, or any roll.** `RollName` is untouched, so
  Constitution IV's seam and SC-007's seed parity are unaffected.

## Documentation obligation

`scripts/check_docs.py` fails if a backticked symbol in `README.md`, `CONTRIBUTING.md` or
`AGENTS.md` no longer resolves in the package. Any of these names written into the README's
library-caller section must therefore exist and be exported. The module map in `CONTRIBUTING.md`
covers `engine/` only (verified: `check_docs.py:38`), so a new `cli/prompts.py` needs no map entry.
