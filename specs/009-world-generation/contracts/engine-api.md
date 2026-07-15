# Contract: Engine Public API (`cetools.engine.worlds`)

The subpackage's `__init__.py` is the public surface. Callers import from `cetools.engine.worlds`,
never from submodules (mirrors `cetools.engine.careers`).

## Exported names

```text
generate_world      generate_system      generate_subsector
World   System   Subsector   TravelZone   Density
generate_world_name
```

## Functions

### `generate_world(rolls=None, *, name=None, travel_zone_red=False) -> World`

- `rolls: Rolls | None`—chance seam; defaults to `RandomRolls()`. Pass
  `RandomRolls(random.Random(seed))` for reproducibility.
- `name: str | None`—when `None`, a name is generated (hybrid stems); otherwise used verbatim.
- `travel_zone_red: bool`—caller override to mark the world `RED` (referee discretion). Amber is
  still assigned by rule when applicable and is superseded by an explicit `RED`.
- **Returns** a `World` obeying every invariant in data-model.md (SC-001, SC-002).
- **Determinism**: identical `rolls` state ⇒ identical `World` (FR-022, SC-005).

### `generate_system(rolls=None, *, name=None, hex=None, allegiance="Na", travel_zone_red=False) -> System`

- Generates a `World` then its stellar surroundings (belts, gas giants, bases) per SRD.
- `hex: str | None`—optional `"CCRR"` coordinate to stamp on the system.
- **Returns** a `System`; base-exclusion invariants always hold (SC-004); `size==0 ⇒ belts≥1`.

### `generate_subsector(rolls=None, *, density=Density.STANDARD) -> Subsector`

- Walks all 80 hexes (columns 01–08, rows 01–10). Per hex: present iff `1D6 + density.dm >= 4`.
- Each occupied hex → `generate_system(..., hex="CCRR")`.
- Auto-generated world names are unique within the subsector (regenerate on collision, bounded by a
  max-attempts guard) (FR-027, SC-008).
- **Returns** a `Subsector`.

### `generate_world_name(rolls=None) -> str`

- Assembles 2–3 curated stems into a title-cased, pronounceable invented name.
- Deterministic under a seeded `rolls`.

## Error behavior

- `generate_*` do not raise on any valid dice outcome—every roll resolves to a valid world (there
  is no "generation failure" analogue). A `Rolls` source that can never satisfy the name-uniqueness
  guard raises `ValueError` after the bounded attempts (defensive, not reachable with real dice).

## Rendering (via `System`/`World`)

- `World.profile` → `"A867A9C-F"` style string.
- `System.data_line` → `Name  CCRR  A867A9C-F  N  Ag Ni  A  234  Na`.
- Rendering is total (never raises) for any valid `World`/`System`.

## Backwards compatibility

- Purely additive: no existing engine module's public surface changes except `rolls.py` gaining new
  `RollName` members (additive; existing members untouched).
