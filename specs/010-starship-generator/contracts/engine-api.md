# Contract: Engine Public API (`cetools.engine.ships`)

The subpackage's `__init__.py` is the public surface. Callers import from `cetools.engine.ships`,
never from submodules (mirrors `cetools.engine.worlds` and `cetools.engine.careers`).

## Exported names

```text
build_ship        generate_ship
load_design       loads_design      dump_design       render_sheet
Ship   ShipDesign   Crew   LineItem
Configuration   ArmorType   HullClass
ArmorFit   ComputerFit   SoftwareFit   FittingFit   TurretFit   AmmoFit   BayFit   ScreenFit
```

The component fits are public because constructing a `ShipDesign` in code (rather than from TOML)
requires them—see the library examples in [quickstart.md](../quickstart.md).

## Functions

### `build_ship(design: ShipDesign) -> Ship`

- Pure, deterministic: the same `ShipDesign` always yields an equal `Ship` (no randomness).
- Allocates tonnage, costs every component, derives drive ratings, fuel, crew, hull/structure points,
  hardpoints, cargo, total cost, and build time per the SRD (research Parts B–J).
- **Raises `ValueError`** with a rule-specific message for any invalid design (data-model
  "Builder-enforced constraints"): unknown hull size, bad armor increment, illegal drive-on-hull,
  missing required system, power-plant below drives, software over computer rating, fuel scoops on a
  distributed hull, hardpoint limit, disallowed small-craft armament, over-allocation. Checks run in
  SRD build order, so a design violating several reports the first (FR-015, SC-005).
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

### `load_design(path: str | os.PathLike) -> ShipDesign`

- Reads the file at `path` and parses it with `loads_design` (FR-021). A `str` is always a path here,
  never TOML text—mirroring `json.load` / `json.loads`, so there is no path-vs-content guessing.
- **Raises `ValueError`** for anything `loads_design` rejects; propagates `OSError` if the file cannot
  be read (the CLI turns that into `"cannot read design file: <path>"`).

### `loads_design(text: str) -> ShipDesign`

- Parses TOML *text* with stdlib `tomllib` into a well-formed `ShipDesign`.
- **Raises `ValueError`** for malformed TOML, unknown keys, wrong value types, or an unknown enum
  string, with a clear message identifying the problem. It does **not** check SRD rules—that is
  `build_ship`'s job (FR-015); see contracts/design-schema.md.

### `dump_design(design: ShipDesign) -> str`

- Serializes a `ShipDesign` to builder-compatible TOML text (FR-022, FR-023) via the in-repo writer.
- **Round-trip guarantee**: `loads_design(dump_design(d))` equals `d`, and
  `build_ship(loads_design(dump_design(ship.design)))` equals `ship` (SC-008).

### `render_sheet(ship: Ship) -> str`

- Produces the human-readable ship sheet (FR-022): hull + configuration, drives + performance, power
  plant, fuel (including `assumed_jump_distance`, the jump range the fuel figure assumes, FR-006),
  computer + software, electronics, crew, quarters, fittings, armaments, tonnage summary
  (used / cargo), hull/structure points, total cost, build time.
- A function of the `Ship` alone: it renders nothing the `Ship` does not carry (notably not the
  generator seed, which the CLI reports separately on stderr).
- Total (never raises) for any valid `Ship`; deterministic (byte-identical for equal ships, SC-004).

## Error behavior

- The builder is the single validation authority for SRD *rules*; `load_design` / `loads_design` and
  `ShipDesign.__post_init__` reject only malformed *shape* (bad TOML, unknown key, wrong type, unknown
  enum value). Both kinds raise `ValueError`; the CLI catches them and exits 1 to stderr.
- `generate_ship` does not raise for any valid dice outcome—it selects only legal components, so its
  internal `build_ship` call always succeeds.

## Backwards compatibility

- Purely additive: no existing engine module's public surface changes except `rolls.py` gaining new
  `SHIP_*` `RollName` members (additive; existing members untouched).
