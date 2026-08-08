# Contract: the `cetools.engine.vehicles` public surface

**Feature**: `001-vehicle-design` | **Date**: 2026-08-07

Principle II makes a subpackage's `__init__.py` its public surface, and callers import from the
package rather than reaching into its modules. `vehicles/__init__.py` contains imports and an
explicit sorted `__all__`, no logic, as `ships/__init__.py` does. FR-002 requires every capability
be reachable here without a process boundary.

## Exported

### Building

- `build_vehicle(design: VehicleDesign) -> Vehicle`—the single authority on the construction
  rules. One positional argument, no `rolls`, pure and deterministic. Raises `ValueError` naming the
  rule and the offending numbers.

### Design file I/O

- `loads_design(text: str) -> VehicleDesign`
- `load_design(path: str | os.PathLike) -> VehicleDesign`
- `dump_design(design: VehicleDesign) -> str`

### Description

- `render_description(vehicle: Vehicle) -> str`—the Universal Vehicle Description Format
  paragraph.
- `render_component_table(vehicle: Vehicle) -> str`—every line item with its spaces and price,
  then the summed price, the discount if elected, the final price and the build time (FR-025a).

### Catalog

- `catalog_names() -> tuple[str, ...]`—the fifteen stable names, sorted.
- `load_catalog(name: str) -> VehicleDesign`—raises `ValueError` naming the available names when
  the name is unknown.
- `PUBLISHED: dict[str, dict[str, object]]`—the transcribed published stat blocks, catalog name to
  figure name to printed value.

### Generation

- `generate_vehicle(rolls: Rolls | None = None, *, constraints: GenerationConstraints = UNCONSTRAINED) -> GenerationResult`
- `GenerationConstraints`, `UNCONSTRAINED`, `GenerationResult`, `UnmetConstraint`, `Role`
- `locomotion_names() -> tuple[str, ...]` and `locomotion_aliases() -> tuple[str, ...]`—the two
  vocabularies FR-026a requires be documented, exposed so the CLI's help and the docs can name them
  without duplicating the table.

### Records and enums

`VehicleDesign`, `Vehicle`, `LineItem`, `Configuration`, `ControlInterface`, `MountKind`,
`PowerPlantType`, `PropulsionType`, and the component fits: `ArmorFit`, `DriveFit`, `ComputerFit`,
`AccommodationFit`, `ComponentFit`, `MountFit`, `WeaponFit`, `AmmunitionFit`.

## Not exported

`tables.py` and `prose.py` are internal to the domain, matching ships, where neither `HULLS` nor the
prose primitives are re-exported. A caller who needs a table row gets it off a built `Vehicle` or a
validated fit, not by reaching into the data.

## Import discipline

`vehicles` imports from `cetools.engine.rolls` and from nothing else outside itself. **It does not
import from `cetools.engine.ships`** (FR-001), including `ships/prose.py`, whose overlap with
`vehicles/prose.py` is real and deliberate: see research decision R-005 for why promoting it to a
shared module was rejected.

Within the domain the direction is one-way: `tables` and `prose` import nothing in-package;
`models` imports `tables`; `design`, `builder` and `description` import `models`; `generator`
imports `builder`; `catalog` imports `design`; `published` imports nothing; `__init__` imports
everything.

## Errors

`ValueError` everywhere, with no custom exception class anywhere in the domain, matching ships.
Messages name the offending value with `!r` and, for a vocabulary error, the legal set. Because the
builder runs the SRD's own build order, a design breaking several rules reports the first in build
order, and that ordering is part of the contract.
