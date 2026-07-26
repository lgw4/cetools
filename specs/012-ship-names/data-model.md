# Phase 1 Data Model: Ship Names

**Feature**: `012-ship-names` | **Date**: 2026-07-25 | **Spec**: [spec.md](./spec.md)

Three new types, one new enum member, and one new field value on an existing record. Nothing
else in the ship domain changes shape.

## New: `Tradition` (StrEnum)

`src/cetools/engine/ships/names.py`

The provenance of a catalogue name (spec: *Source tradition*). Exactly three members, matching
FR-004, FR-005 and FR-006.

| Member | Value | Carries a basis? |
|--------|-------|------------------|
| `MYTHOLOGY_FOLKLORE` | `"mythology_folklore"` | No — the tradition is its own warrant (FR-016a) |
| `WRITTEN_SF` | `"written_sf"` | Yes (FR-016a) |
| `SCREEN_SF` | `"screen_sf"` | Yes (FR-016a) |

A `StrEnum`, following `Configuration` and `ArmorType` in `models.py`, so a tradition is
self-describing in a test failure message and stable as a dict key.

**Assignment rule (FR-007a; research.md C2)**: a name belongs to the *earliest* tradition it
belongs to, and is catalogued exactly once. Mythological names claimed by later fiction stay under
`MYTHOLOGY_FOLKLORE`.

## New: `BasisKind` (StrEnum)

`src/cetools/engine/ships/names.py`

The fixed set FR-016a requires. A closed enum rather than free text, so FR-016b's machine check
is a membership test. Exactly one kind is recorded per entry; where a name qualifies under more
than one, the most direct is chosen (FR-016a).

| Member | Value | What it asserts |
|--------|-------|-----------------|
| `ORDINARY_WORD` | `"ordinary_word"` | The name is a common English word with a meaning independent of any fiction |
| `REAL_VESSEL` | `"real_vessel"` | A real historical ship of that name existed |
| `PUBLIC_DOMAIN_WORK` | `"public_domain_work"` | The source work borrowed the name from public-domain literature |

## New: `ShipName` (frozen dataclass)

`src/cetools/engine/ships/names.py`

One catalogue entry (spec: *Ship name catalogue* entry + *Sourcing basis*).

| Field | Type | Default | Meaning |
|-------|------|---------|---------|
| `name` | `str` | — | The bare proper name as it renders: ASCII, no type designation (FR-017, FR-018) |
| `tradition` | `Tradition` | — | Where the name comes from (FR-007) |
| `basis_kind` | `BasisKind \| None` | `None` | Which FR-016 test the name passes; `None` only for `MYTHOLOGY_FOLKLORE` |
| `basis_reference` | `str` | `""` | Short free text naming the specific word, vessel or work; non-empty exactly when `basis_kind` is set |

Frozen, matching every row type in `tables.py`. The basis is two fields on the entry rather than
a nested record: it is always exactly one kind plus one reference, and a nested type would add a
layer with no second use.

### Validation rules

Enforced by tests (FR-016b, SC-007), not at import — the catalogue is a literal, and a test
failure names the offending entry more usefully than an import-time exception.

| Rule | Requirement | Source |
|------|-------------|--------|
| V1 | Every entry with `tradition` in `{WRITTEN_SF, SCREEN_SF}` has a `basis_kind` that is a `BasisKind` member | FR-016a, FR-016b, SC-007 |
| V2 | Every such entry has a `basis_reference` that is non-empty after stripping | FR-016a, FR-016b, SC-007 |
| V3 | Every `MYTHOLOGY_FOLKLORE` entry has `basis_kind is None` and `basis_reference == ""` | FR-016a |
| V4 | `name` is non-empty and ASCII (`str.isascii()`) | FR-018 |
| V4a | `name` has no leading, trailing, doubled or non-space whitespace; multi-word names use single spaces | FR-018a |
| V5 | `name` does not begin with a ship-type designation from the deny-list | FR-017 |
| V6 | `name` survives `ShipDesign(hull_tons=…, name=entry.name)` construction unchanged | existing `_validate_author_prose` |
| V7 | No two entries share a `name` after stripping and case-folding | FR-009 |

## New: `SHIP_NAMES` (module constant)

`src/cetools/engine/ships/names.py`

```
SHIP_NAMES: tuple[ShipName, ...]
```

An **ordered** tuple — `Rolls.choose` indexes into it, so order is part of what a seed resolves
against (research.md Part A). Grouped by tradition in source order for readability, but the
grouping carries no meaning.

### Composition rules

| Rule | Requirement | Source |
|------|-------------|--------|
| C1 | `len(SHIP_NAMES) >= 150` | FR-008 |
| C2 | Each of the three traditions contributes `>= 20` entries | FR-008, SC-005 |
| C3 | No tradition accounts for more than half the catalogue | SC-005 |

**Target composition** (research.md C3): 160 entries — 76 `MYTHOLOGY_FOLKLORE`, 42 `WRITTEN_SF`,
42 `SCREEN_SF`. Tests assert C1–C3, never these exact numbers, so adding a name is never a test
edit.

## New: `RollName.SHIP_NAME`

`src/cetools/engine/rolls.py`, in the "Uniform picks from a list" block alongside `FIRST_NAME`,
`LAST_NAME`, `WORLD_NAME_STEM` and the other `SHIP_*` members.

```
SHIP_NAME = "ship_name"
```

Adding a `StrEnum` member changes no behaviour and consumes no randomness; it names the one new
draw so a test can script it by intent (`choices={RollName.SHIP_NAME: 3}`).

## Changed: `ShipDesign.name`

`src/cetools/engine/ships/models.py` — **no shape change**. The field already exists as
`name: str | None = None` and is already validated, rendered and round-tripped (research.md
Part D). What changes is only that `generate_ship` now populates it.

| Path | Before | After |
|------|--------|-------|
| `generate_ship(...)` | `name` unset → renders `"Unnamed Ship"` | `name` set from the catalogue (FR-001, FR-002) |
| `build_ship(load_design(...))` | author's `name`, or `"Unnamed Ship"` | unchanged (FR-014, FR-015) |
| `dump_design` / `load_design` | emits and reads `name` when set | unchanged (FR-013) |

## Entity relationships

```text
generate_ship(rolls)                    generate_ship_name(rolls)
        │                                        │
        │ last draw in the path ─────────────────┤
        │                                        │
        │                                  rolls.choose(SHIP_NAMES, RollName.SHIP_NAME)
        │                                        │
        │                                        ▼
        │                                   ShipName ──── tradition ──▶ Tradition
        │                                        │
        │                                        └─ basis_kind ───────▶ BasisKind | None
        │                                           basis_reference
        ▼                                        │
   ShipDesign(name=◀─────────────────────────────┘ .name)
        │
        ▼
   build_ship ──▶ Ship ──▶ render_description  (heading + first sentence)
                       └─▶ dump_design         (name = "…")
```

## Out of the model

Deliberately absent, per the spec's Out of Scope and Assumptions:

- No per-tradition, per-hull or per-culture selection filter — one combined pool, drawn whole.
- No weighting field on an entry — every entry is equally likely.
- No used-name registry or cross-ship uniqueness state — each ship draws independently.
- No name option on `generate_ship` or on the CLI — a referee who wants a specific name exports
  the design and sets it there.
