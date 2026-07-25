# Contract: TOML design schema (delta)

**Feature**: 011-universal-ship-format

Changes to the design-file schema established by
[feature 010's design-schema.md](../../010-starship-generator/contracts/design-schema.md).
Everything not listed here is unchanged, and **every existing design file remains valid**
(spec Assumptions, FR-033).

---

## Two new top-level keys, both optional

| Key | Type | Default | Meaning |
|---|---|---|---|
| `purpose` | string | absent | Completes "the \<name\> is …" in the description's first sentence (FR-029). |
| `tech_level` | integer | absent | Overrides the derived tech level shown in the heading (FR-028, FR-028b). |

```toml
name = "Beowulf"
purpose = "a subsidized merchant plying the routes an interstellar polity's mail contracts do not reach"
tech_level = 11
hull_tons = 200
standard_design = true

[drives]
jump = "A"
maneuver = "A"
power = "A"
```

Renders as:

```text
TL11 Beowulf

Using a 200-ton hull (4 Hull, 4 Structure), the Beowulf is a subsidized merchant plying the
routes an interstellar polity's mail contracts do not reach. …
```

### Validation (shape only, as everywhere in `design.py`)

- `purpose` must be a string; `loads_design` raises `ValueError` otherwise. `models.py` then
  rejects an empty or whitespace-only string.
- `tech_level` must be an integer (not a bool, per the existing `_require_int`); `models.py`
  rejects a negative value.
- Neither key is checked against SRD rules. An explicit `tech_level` above the derived value is
  used as given (FR-028b) — it describes the yard that built the ship, not a constraint to
  re-check.
- `purpose` carries no trailing period. The renderer supplies the sentence's own; an authored
  period would produce "… is a fast courier..".

Both keys join `_TOP_LEVEL_KEYS`, so a misspelling (`purspose`) still fails with the existing
"unknown key(s) in design" message rather than being silently ignored.

## Round trip (FR-033)

`dump_design` emits each key only when the field is set, in the existing canonical order —
after `name`, before `hull_tons` for `purpose`; alongside the other scalar top-level keys for
`tech_level`:

```toml
name = "Beowulf"
purpose = "a subsidized merchant"
hull_tons = 200
tech_level = 11
standard_design = true
```

`loads_design(dump_design(d)) == d` continues to hold for every well-formed `d`, including
designs that set neither key, exactly one, or both. `purpose` is escaped by the existing
`_toml_str`, so a purpose containing a quote or a backslash round-trips.

## What does not change

- Every existing key, table and array-of-tables: `hull_tons`, `configuration`,
  `standard_design`, `electronics`, `[drives]`, `[bridge]`, `[computer]`, `[quarters]`,
  `[[armor]]`, `[[fittings]]`, `[[turrets]]`, `[[bays]]`, `[[screens]]`, `[passengers]`.
- Component keys stay identifiers, not prose. The new `name` columns in `tables.py` are display
  spellings only: `sand_barrels` remains the ammunition kind a design writes, even though the
  paragraph calls them canisters; `vehicle_hangar` remains the fitting kind, even though the
  paragraph calls it a small craft hangar.
- The checked-in example designs under `specs/010-starship-generator/examples/`, which are
  test fixtures for hand-worked SRD figures. This feature adds one new example carrying
  `purpose` and `tech_level` rather than editing them.
