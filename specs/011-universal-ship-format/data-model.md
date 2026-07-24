# Phase 1 Data Model: Universal Ship Description Format

**Feature**: 011-universal-ship-format | **Date**: 2026-07-24

This feature adds no new domain records. It adds **two optional input fields**, **one derived
output field**, and **display-name / tech-level columns** to the existing SRD tables. Every
number the paragraph states is already computed by `build_ship` (FR-032).

Entity vocabulary follows the spec's Key Entities; module layout follows
[research.md Part G](./research.md#part-g--where-the-description-lives).

---

## 1. Ship description

The rendered USDF text for one built ship: a heading line, a blank line, and one paragraph.

**Not a record.** It is the return value of `render_description(ship) -> str`. It holds no
state, has no identity, and is derived entirely from the `Ship` passed in (FR-003). Two equal
`Ship` values render byte-identically (SC-003); nothing ambient — seed, clock, locale, dict
iteration order over unordered input — reaches the output.

Full per-sentence contract: [contracts/description-format.md](./contracts/description-format.md).

---

## 2. `ShipDesign` — two new optional fields

`src/cetools/engine/ships/models.py`. Both default to `None`, so every existing design file
stays valid and every existing design stays buildable (spec Assumptions).

| Field | Type | Default | Meaning | Shape validation |
|---|---|---|---|---|
| `purpose` | `str \| None` | `None` | The clause completing "the \<name\> is …" (FR-029). Author-supplied prose; cetools never generates one. | Must be a non-empty string when present. |
| `tech_level` | `int \| None` | `None` | Designer's override for the heading's tech level (FR-028, FR-028b). | Must be `>= 0` when present. |

**Validation is shape only**, as everywhere in `models.py`: `_validate_ship_design` rejects a
negative `tech_level` and an empty `purpose`. It does **not** compare `tech_level` against the
derived value — FR-028b makes an explicit tech level a statement about the yard that built the
ship, not a constraint. `build_ship` adds no check either.

`purpose` is free prose and is rendered verbatim into sentence 1. It carries no trailing
period; the renderer supplies the sentence's own.

**Round trip (FR-033).** Both fields are top-level TOML keys, emitted by `dump_design` only
when set, so `loads_design(dump_design(d)) == d` continues to hold for every well-formed `d`,
including designs that set neither. See
[contracts/design-schema.md](./contracts/design-schema.md).

---

## 3. `Ship` — one new derived field

| Field | Type | Meaning |
|---|---|---|
| `tech_level` | `int` | The ship's tech level: `design.tech_level` when the designer supplied one, otherwise the highest tech level among the components fitted (FR-028). |

Computed by `build_ship`, never authored. Always an `int`, never `None`: every ship carries the
Standard electronics package included in its bridge or cockpit, so the derived value has a
floor of `ELECTRONICS["standard"].tl` (= 8). See
[research.md Part D](./research.md#part-d--tech-level-which-categories-the-srd-tabulates).

`_validate_ship` gains `tech_level` to its `>= 0` sweep.

### Derivation

```text
derived = max(tl for every fitted component whose table row carries a tl)
```

Contributing rows, each via its own `tl` column, and each contributing only when actually
fitted:

| Fitted component | Row read |
|---|---|
| each armour layer | `ARMOR[fit.type.value].tl` |
| each armour option, on any layer | `ARMOR_OPTIONS[option].tl` |
| the computer | `COMPUTERS[fit.model].tl` |
| the electronics package (`"standard"` when the design names none) | `ELECTRONICS[name].tl` |
| each turret's mount | `TURRET_MOUNTS[mount].tl` (`None` for `fixed` — contributes nothing) |
| each turret weapon | `TURRET_WEAPONS[weapon].tl` |
| each ammunition load | the matching `AMMO` row's `tl` |
| each weapon bay | `BAYS[kind].tl` |
| each screen | `SCREENS[kind].tl` |

Categories with **no** `tl` column, contributing nothing because the SRD tabulates none:
hulls (standard and small-craft), configurations, drives, cockpits, quarters, fittings, and
software. This is a finding, not an omission — see research.md Part D. A `tl` of `None` on an
individual row (the fixed mounting) is skipped the same way.

**Adding a component row with a `tl` automatically widens the derivation** — the walk is over
the fitted components' rows, with no per-category list of "things that have a TL" (SC-007).

---

## 4. Table columns added

`src/cetools/engine/ships/tables.py`. Every column below is transcribed from the SRD; none is
invented. `name` is the SRD's prose spelling (FR-030); `plural` is its explicit plural, not
derived (research.md Part E); `tl` is the SRD's tech level (FR-028a).

| Row type | New columns | Notes |
|---|---|---|
| `ArmorRow` | `name` | `min_tl` is **renamed** `tl` — it is the SRD's TL column and is now read. Its "deliberately unenforced" docstring is retired. |
| `ArmorOptionRow` | `name`, `tl` | `name` is the SRD's noun phrase: "a reflec coating", "a self-sealing hull", "a stealth coating". TLs 10 / 9 / 11 from the Ship Armor Options prose. |
| `ComputerRow` | — | already carries `tl`; its "deliberately unenforced" docstring is retired. |
| `ElectronicsRow` | `name`, `tl`, `dm` | "Standard"/"Basic Civilian"/…; TL 8–12; DM −4, −2, +0, +1, +2 (FR-030a). |
| `MountRow` | `name`, `plural`, `tl` | "single turret"/"single turrets" … "fixed mounting"/"fixed mountings"; TL 7/8/9/10 and `None` for fixed. |
| `WeaponRow` | `name`, `plural`, `tl` | Armament-clause spelling: "missile"/"missiles", "pulse laser"/"pulse lasers", "sandcaster"/"sandcasters", "particle beam"/"particle beams". TL 6/7/7/8. |
| `AmmoRow` | `name`, `plural`, `tl`, `weapon` | "smart missile"/"smart missiles", "canister"/"canisters". TL 6/6/8 and 5 for canisters. `weapon` is the `TURRET_WEAPONS` key this ammunition feeds. |
| `BayRow` | `name`, `plural`, `tl` | "missile bay"/"missile bays", "particle beam bay", "meson gun bay", "fusion gun bay". TL 6/8/11/12. |
| `ScreenRow` | `name`, `plural`, `tl` | "meson screen"/"meson screens", "nuclear damper"/"nuclear dampers". TL 12/12. |
| `FittingRow` | `name`, `plural`, `counted_in_tons`, `unrefined_fuel_per_ton` | `name` carries its indefinite article ("an armory", "a vault", "fuel scoops"); `plural` does not. `counted_in_tons` is `True` for `fuel_processor` and `luxuries`. `unrefined_fuel_per_ton` is `20.0` on `fuel_processor`, `None` elsewhere (FR-017). No `tl`: the SRD tabulates none. |
| `HullRow`, `DriveRow`, `QuartersRow`, `CockpitRow` | — | No display name is needed and the SRD tabulates no TL. A cockpit is never named as a catalog item: FR-027 requires only the word "cockpit" in the computer sentence, which is a hull-class distinction, not a component spelling. (FR-030's original list named cockpits; the spec was corrected during checklist review.) |

### Two new tables

**`CONFIGURATIONS: dict[str, ConfigurationRow]`** replaces `CONFIG_MODIFIERS: dict[str,
float]`, keyed identically by `Configuration.value`. `ConfigurationRow(name: str,
cost_modifier: float)` — "distributed"/"standard"/"streamlined", lower case, ×0.9/×1.0/×1.1.
`Configuration.cost_modifier` reads `CONFIGURATIONS[self.value].cost_modifier`, so no builder
arithmetic changes (FR-032).

**`CREW_POSITIONS: tuple[CrewPositionRow, ...]`** — `CrewPositionRow(field: str, name: str,
plural: str)`, in the order FR-018's breakdown prints:

| `field` | `name` | `plural` |
|---|---|---|
| `pilot` | pilot | pilots |
| `navigator` | navigator | navigators |
| `engineers` | engineer | engineers |
| `gunners` | gunner | gunners |
| `screen_operators` | screen operator | screen operators |
| `medic` | medic | medics |
| `stewards` | steward | stewards |

`field` names a `Crew` attribute. The tuple is the single source of both the spelling and the
order, and a position whose count is zero is omitted (FR-018).

**Invariant tests** (`tests/test_ship_tables.py`): every `CREW_POSITIONS.field` is a `Crew`
field and every `Crew` field appears exactly once; every `AmmoRow.weapon` is a `TURRET_WEAPONS`
key; every nameable row has a non-empty `name`, and every counted row a non-empty `plural`.

---

## 5. `prose.py` — text primitives

`src/cetools/engine/ships/prose.py`. Pure functions over numbers and strings, with **no
import from `models.py`, `tables.py` or any other ships module**. This is the seam that makes
FR-022 through FR-025 testable without building a ship.

| Function | Rule | Requirement |
|---|---|---|
| `count(n: int) -> str` | Word for 0–10 ("zero" … "ten"), digits above ten. | FR-022 |
| `tons(value: float) -> str` | `count()` when `value` is a whole number, else the stripped decimal. | FR-022 rule 2, research.md Part C |
| `number(value: float) -> str` | Digits always; trailing zeros stripped; no scientific notation; no thousands separator. | FR-022a, FR-025 |
| `money(value: float) -> str` | As `number()`, plus thousands separators on the integer part. | FR-020, FR-025 |
| `signed(n: int) -> str` | `"+1"` / `"-2"` / `"+0"` — always an explicit sign. | FR-009 |
| `plural(n, singular, plural) -> str` | `singular` when `n == 1`, else `plural`. Spellings come from the caller (a data row), never from a suffix rule. | FR-023 |
| `join(items: Sequence[str]) -> str` | `"a"` / `"a and b"` / `"a, b and c"` — no serial comma. | FR-024 |
| `article(word: str) -> str` | `"an"` before a leading vowel letter, else `"a"`. | Sentences 9, 13 |
| `tonnage_article(tons: int) -> str` | `"an"` when the leading digit is 8, else `"a"`. | Sentence 1, research.md Part C |

`number()` and `money()` share one implementation detail worth pinning: format at a fixed six
decimal places, *then* strip trailing zeros — never `:g`, which caps at six **significant**
figures and switches to scientific notation, rendering `2768.145` as `2768.14` and failing both
FR-025 and the fractional-cost edge case. Fixed-then-strip also satisfies FR-025a: a total cost
accumulated from dozens of floats prints `29.772`, not `29.771999999999998`. Six places sits
below the smallest figure the rules price (a standard missile, MCr0.00125) and above any
artefact.

---

## 6. Rendering pipeline

`src/cetools/engine/ships/description.py`.

```text
render_description(ship) -> str
    heading  = f"TL{ship.tech_level} {name}"
    sentences = [s for s in (_hull(ship), _drives(ship), … , _cost(ship)) if s is not None]
    return heading + "\n\n" + " ".join(sentences)
```

Sixteen private sentence builders, one per FR-004 sentence, called in that fixed order. Each
returns `str | None`; `None` means the ship carries nothing for that sentence and it is
omitted entirely (FR-021). Omission is the *only* control flow between sentences — no builder
reads another's output — so the paragraph stays grammatical however many drop out, and
sentence order is a single literal tuple.

| # | Builder | Omitted when |
|---|---|---|
| 1 | `_hull` | never |
| 2 | `_drives` | never |
| 3 | `_fuel` | never |
| 4 | `_computer` | no computer fitted |
| 5 | `_sensors` | never (Standard when none purchased) |
| 6 | `_quarters` | no staterooms, low berths or emergency low berths |
| 7 | `_hardpoints` | never |
| 8 | `_weapons` | no turrets and no bays |
| 9 | `_screens` | no screens |
| 10 | `_hangars` | no vehicle-sized fitting |
| 11 | `_cargo` | never |
| 12 | `_configuration` | never (armour clause drops when no armour) |
| 13 | `_special_features` | no non-hangar fittings |
| 14 | `_crew` | never |
| 15 | `_passengers` | never (states "cannot carry any" when zero) |
| 16 | `_cost` | never |

`render_description` is **total**: it raises for no valid `Ship`.

### Grouping

Three sentences collapse repeats (FR-012, FR-013, edge case "repeated identical turrets"):

- **Turrets** group by `(mount, weapons)`, in first-appearance order over `design.turrets`.
- **Bays** and **screens** group by `kind`, in first-appearance order.
- **Ammunition** aggregates counts by `(kind, type)` across every turret, in first-appearance
  order, then names its weapon through `AmmoRow.weapon`.

First-appearance order over an ordered tuple, not set or dict-hash order, is what makes SC-003
byte-identical.

---

## 7. What does not change

- Every `build_ship` computation: tonnage, cost, crew, hull and structure points, hardpoints,
  fuel, build time (FR-032). `Configuration.cost_modifier` is re-routed through
  `CONFIGURATIONS` but returns the same three values.
- Every `ShipDesign` field that exists today, and the meaning of every TOML key.
- `generate_ship`, which sets neither new field, so generated ships take the derived tech
  level and the hull-class purpose fallback.
- The `--toml` output of `cetools ship build` and `cetools ship generate`, except that a
  design carrying `purpose` or `tech_level` now round-trips them.

## 8. What is removed

- `src/cetools/engine/ships/sheet.py` and `render_sheet` — replaced, per FR-002 and the
  feature 006 precedent. The name is retired rather than kept, and the docs that name it move
  with it (README's worked example, CONTRIBUTING's module map, CONTEXT.md's vocabulary), which
  the repo's `scripts/check_docs.py` gate enforces.
- `CONFIG_MODIFIERS`, superseded by `CONFIGURATIONS`.
- `ArmorRow.min_tl`, renamed `tl`.
