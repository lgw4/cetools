# Contract: Engine Public API (`cetools.engine.ships`)

The subpackage's `__init__.py` is the public surface. Callers import from `cetools.engine.ships`,
never from submodules (mirrors `cetools.engine.worlds` and `cetools.engine.careers`).

## Exported names

```text
build_ship        generate_ship
load_design       dump_design       render_sheet
Ship   ShipDesign   Crew   LineItem
Configuration   ArmorType   HullClass
```

## Functions

### `build_ship(design: ShipDesign) -> Ship`

- Pure, deterministic: the same `ShipDesign` always yields an equal `Ship` (no randomness).
- Allocates tonnage, costs every component, derives drive ratings, fuel, crew, hull/structure points,
  hardpoints, cargo, total cost, and build time per the SRD (research Parts B–J).
- **Raises `ValueError`** with a rule-specific message for any invalid design (data-model
  "Builder-enforced constraints"): over-allocation, power-plant below drives, hardpoint limit,
  missing required system, disallowed small-craft armament, illegal drive-on-hull, software over
  computer rating, bad armor increment (FR-015, SC-005).
- **Returns** a `Ship` obeying every invariant in data-model.md; `cargo_tons ≥ 0`.

### `generate_ship(rolls=None, *, hull_size=None, small_craft=False) -> Ship`

- `rolls: Rolls | None`—chance seam; defaults to `RandomRolls()`. Pass `RandomRolls.seeded(seed)` for
  reproducibility.
- `hull_size: int | None`—when given, constrains generation to that hull size while staying legal
  (FR-018); when `None`, a size is chosen.
- `small_craft: bool`—generate under the small-craft ruleset (10–95 t, no jump) (FR-019).
- Selects rules-legal components from the same tables `build_ship` validates against, assembles a
  `ShipDesign`, and returns `build_ship(design)`—so **every** generated ship passes the builder's own
  validation (FR-016, SC-003).
- **Determinism**: identical `rolls` state ⇒ identical `Ship` (FR-017, SC-004). The generated
  `Ship.design` round-trips through TOML (SC-008).

### `load_design(source: str | os.PathLike) -> ShipDesign`

- Parses a TOML design file (or TOML text) with stdlib `tomllib` into a validated `ShipDesign`
  (FR-021).
- **Raises `ValueError`** for malformed TOML, unknown keys, wrong types, or a schema-invalid design,
  with a clear message identifying the problem.

### `dump_design(design: ShipDesign) -> str`

- Serializes a `ShipDesign` to builder-compatible TOML text (FR-022, FR-023) via the in-repo writer.
- **Round-trip guarantee**: `load_design(dump_design(d))` equals `d`, and
  `build_ship(load_design(dump_design(ship.design)))` equals `ship` (SC-008).

### `render_sheet(ship: Ship) -> str`

- Produces the human-readable ship sheet (FR-022): hull + configuration, drives + performance, power
  plant, fuel, computer + software, electronics, crew, quarters, fittings, armaments, tonnage summary
  (used / cargo), hull/structure points, total cost, build time.
- Total (never raises) for any valid `Ship`; deterministic (byte-identical for equal ships, SC-004).

## Error behavior

- The builder is the single validation authority. `build_ship`, `load_design`, and (transitively)
  `generate_ship` raise `ValueError` on invalid input; the CLI catches these and exits 1 to stderr.
- `generate_ship` does not raise for any valid dice outcome—it selects only legal components, so its
  internal `build_ship` call always succeeds.

## Backwards compatibility

- Purely additive: no existing engine module's public surface changes except `rolls.py` gaining new
  `SHIP_*` `RollName` members (additive; existing members untouched).
