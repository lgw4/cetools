# Contract: Ship Name Catalogue and Selection

**Feature**: `012-ship-names` | **Date**: 2026-07-25

cetools exposes two external interfaces: the engine library and the `cetools` CLI. This feature
adds to the first and changes the observable output of the second without changing its surface.

## 1. Library contract

### New public symbols

Exported from `cetools.engine.ships` (added to `__init__.py`'s imports and `__all__`), defined in
`cetools.engine.ships.names`.

```python
class Tradition(StrEnum):
    MYTHOLOGY_FOLKLORE = "mythology_folklore"
    WRITTEN_SF = "written_sf"
    SCREEN_SF = "screen_sf"

class BasisKind(StrEnum):
    ORDINARY_WORD = "ordinary_word"
    REAL_VESSEL = "real_vessel"
    PUBLIC_DOMAIN_WORK = "public_domain_work"

@dataclass(frozen=True)
class ShipName:
    name: str
    tradition: Tradition
    basis_kind: BasisKind | None = None
    basis_reference: str = ""

SHIP_NAMES: tuple[ShipName, ...]

def generate_ship_name(rolls: Rolls | None = None) -> str: ...
```

### `generate_ship_name`

| Guarantee | Statement |
|-----------|-----------|
| Return value | The `name` of one `SHIP_NAMES` entry — never a constructed or concatenated string (FR-003) |
| Randomness | Exactly one `rolls.choose(SHIP_NAMES, RollName.SHIP_NAME)` call; no other entropy (FR-011) |
| Determinism | Equal `rolls` state ⇒ equal result (FR-010) |
| Default | `rolls=None` means `RandomRolls()`, matching `generate_ship` and `generate_world_name` |
| Purity | No I/O, no clock, no ambient state |
| Total | Never raises for a non-empty catalogue; the catalogue is non-empty by C1 |

### `generate_ship` — behaviour change

| Guarantee | Statement |
|-----------|-----------|
| Naming | The returned `Ship.design.name` is a catalogue name, on both the starship and small-craft paths (FR-001, FR-002) |
| Draw position | The name is the **last** `Rolls` draw of the call, on every path (FR-010a) |
| Additivity | For any seed, every other field of the returned `ShipDesign` equals what the same seed produced before this feature (FR-010a, SC-008) |
| Signature | Unchanged — no `name` parameter is added (spec Assumptions, Out of Scope) |

### `build_ship`, `load_design`, `dump_design` — unchanged

| Guarantee | Statement |
|-----------|-----------|
| `build_ship` | Never assigns a name. A nameless design still renders `"Unnamed Ship"` (FR-015) |
| Author's name wins | A design that carries a name is built and rendered under it (FR-014, SC-006) |
| Blank name | `name = ""` or whitespace remains *no* name: `"Unnamed Ship"` (spec Edge Cases) |
| Round trip | `build_ship(loads_design(dump_design(design))) == build_ship(design)`, name included (FR-013) |

### Catalogue invariants (the machine-checkable part of FR-016b)

Any consumer — including the test suite — may rely on all of these:

```
C1  len(SHIP_NAMES) >= 150
C2  every Tradition member has >= 20 entries
C3  no Tradition member has > len(SHIP_NAMES) // 2 entries
V1  tradition in {WRITTEN_SF, SCREEN_SF}  =>  isinstance(basis_kind, BasisKind)
V2  tradition in {WRITTEN_SF, SCREEN_SF}  =>  basis_reference.strip() != ""
V3  tradition is MYTHOLOGY_FOLKLORE       =>  basis_kind is None and basis_reference == ""
V4  name.isascii() and name.strip() == name != ""
V5  name does not begin with a ship-type designation
V6  ShipDesign(hull_tons=100, name=name) constructs without raising
V7  names are unique, exact and case-sensitive
```

### Stability

`SHIP_NAMES` is an **ordered** tuple and selection is an index into it. Adding, removing or
reordering entries changes which name a given seed yields. **The seed-to-name mapping is not a
compatibility surface**; the seed-to-*ship* mapping is (FR-010a), and it is protected by the
`specs/012-ship-names/baseline/designs.json` regression test. Catalogue growth is a data-only
edit that requires no test edit, because the tests assert the floors in C1–C3, not exact counts.

## 2. CLI contract

**No change to any command, option, argument, exit code or stream.** `cetools ship generate` and
`cetools ship build` keep their existing surface exactly as documented in
[`specs/010-starship-generator/contracts/cli.md`](../../010-starship-generator/contracts/cli.md).

The observable difference is in `generate`'s output content:

| Command | Before | After |
|---------|--------|-------|
| `cetools ship generate` | Heading `TL9 Unnamed Ship`; first sentence `…the Unnamed Ship is a starship.` | Heading `TL9 <name>`; first sentence `…the <name> is a starship.` |
| `cetools ship generate --small-craft` | as above, `…a small craft.` | named on the same terms (FR-002) |
| `cetools ship generate --toml` | design has no `name` key | design carries `name = "<name>"` (FR-013) |
| `cetools ship generate --seed N` | reproducible ship | same ship, same name, every run (FR-010, SC-002) |
| `cetools ship build FILE` | author's name, or `Unnamed Ship` | **unchanged** (FR-014, FR-015) |
| Exit codes | 0 success, 1 user-facing failure on stderr | unchanged |
| `seed: N` on stderr when `--seed` is omitted | present | unchanged |

Round trip across the two commands:

```
cetools ship generate --seed 42 --toml --out ship.toml
cetools ship build ship.toml            # renders under the generated name
```
