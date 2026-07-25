# Contract: engine public surface (delta)

**Feature**: 011-universal-ship-format

Changes to `cetools.engine.ships`'s public surface, established by
[feature 010's engine-api.md](../../010-starship-generator/contracts/engine-api.md). Everything
not listed here is unchanged.

---

## Removed

```python
from cetools.engine.ships import render_sheet   # gone
```

`render_sheet(ship) -> str` and the module `cetools/engine/ships/sheet.py` are deleted. FR-002
makes USDF the output rather than one of two formats, following the feature 006 precedent
where the Universal Character Format replaced the per-characteristic output. Callers move to
`render_description`.

## Added

```python
from cetools.engine.ships import render_description

def render_description(ship: Ship) -> str: ...
```

`cetools/engine/ships/description.py`. Renders one built ship as a USDF heading line, a blank
line, and one paragraph. Pure, total and deterministic: a function of `ship` alone, raising for
no `Ship` that `build_ship` can return, and byte-identical for equal ships (FR-003, SC-001,
SC-003). Output is fully specified by
[description-format.md](./description-format.md).

```python
from cetools.engine.ships import prose   # module, not re-exported symbol-by-symbol
```

`cetools/engine/ships/prose.py`. Number, list and article primitives with no dependency on any
other ships module — the testable seam for FR-022 through FR-025. Signatures are in
[data-model.md §5](../data-model.md). It is engine-internal in practice but importable, like
every other module in the package.

## Changed

### `ShipDesign`

```python
@dataclass(frozen=True)
class ShipDesign:
    ...
    purpose: str | None = None       # NEW
    tech_level: int | None = None    # NEW
```

Both optional and defaulted, so every existing construction site and every existing design file
is unaffected. Shape validation only: a present `purpose` must be a non-empty `str`; a present
`tech_level` must be an `int >= 0`. Neither is checked against SRD rules anywhere — FR-028b
makes an explicit tech level a statement, not a constraint.

### `Ship`

```python
@dataclass(frozen=True)
class Ship:
    ...
    tech_level: int                  # NEW
```

Computed by `build_ship`: `design.tech_level` when supplied, else the highest tech level among
the fitted components (FR-028, FR-028a). Always an `int` — the Standard electronics package
every ship carries sets a floor of 8. Derivation table:
[data-model.md §3](../data-model.md).

`build_ship` passes keywords, so field order is not a concern. But `tech_level` is **required
and carries no default**, so every direct `Ship(...)` construction must supply it or fail with
a missing-argument `TypeError`. Two such sites exist outside `build_ship` —
`tests/test_ship_models.py:368` and `:401` — and are updated alongside the rest of this
feature's test edits (spec SC-005).

### `build_ship`

Unchanged signature and unchanged arithmetic. It gains one derivation step, after costing, that
populates `Ship.tech_level`. No tonnage, cost, crew, hull/structure, hardpoint or build-time
value changes (FR-032, SC-005).

### Tables

`cetools.engine.ships.tables` gains display-name, plural and tech-level columns on the rows the
paragraph can name, plus two new tables and two removals. Full column list:
[data-model.md §4](../data-model.md).

```python
CONFIGURATIONS: dict[str, ConfigurationRow]   # NEW — replaces CONFIG_MODIFIERS
CREW_POSITIONS: tuple[CrewPositionRow, ...]   # NEW
CONFIG_MODIFIERS                              # REMOVED (superseded)
ArmorRow.min_tl                               # RENAMED to ArmorRow.tl
```

`Configuration.cost_modifier` now reads `CONFIGURATIONS[self.value].cost_modifier` and returns
the same three values as before.

---

## Import-direction invariants (unchanged, and extended)

```text
prose.py    →  (nothing in the package)
tables.py   →  (nothing in the package)
models.py   →  tables.py
builder.py  →  models.py, tables.py
description.py → models.py, tables.py, prose.py
```

`models.py` must not import `description.py`; the ship carries no rendering method. `prose.py`
must not import `tables.py` or `models.py` — it knows about numbers and strings, not ships.
`description.py` is the sole reader of the display-name and plural columns.

## Determinism and purity

Unchanged from feature 010, and extended to the new function: no engine module imports
`random` except through the `Rolls` seam, and `render_description` touches neither.
