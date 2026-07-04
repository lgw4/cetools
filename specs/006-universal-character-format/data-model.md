# Data Model: Universal Character Format Output

## Character (modified)

`src/cetools/engine/models.py::Character` — existing dataclass, gains exactly one new field.

| Field | Type | Notes |
|---|---|---|
| `name` | `str` | **New.** Full name (`"<first> <last>"`), assigned once at generation time. Required (no default), consistent with every other identity field on `Character` (`upp`, `career`, `rank_title`). |
| *(all existing fields)* | — | Unchanged: `characteristics`, `upp`, `age`, `career`, `rank`, `rank_title`, `terms_served`, `skills`, `benefits`, `pension`, `terms`, `drafted`. |

No validation rules beyond "non-empty string" are needed — `generate_name` (below) always returns
a two-word string built from two non-empty data tables.

**Field position**: `drafted: bool = False` is the *only* field on `Character` with a default
value, and it is currently declared last. Python dataclasses require every field without a
default to precede every field with a default, so `name` (no default) MUST be declared somewhere
*before* `drafted` in the class body — e.g. grouped with the other identity fields, immediately
after `age` or `rank_title` — never appended after `drafted`. Appending it last would raise
`TypeError: non-default argument 'name' follows default argument` at import time.

`drafted` and `pension` remain on `Character` (FR-010: no existing mechanics change) even though
`format_character` no longer renders them (FR-009). They stay available to any future consumer
that needs them; only the default textual output drops them.

## Name Source (new)

`src/cetools/engine/names.py` — new module, two data tuples plus one generation function,
mirroring the existing `careers/*.py` data-table convention.

| Name | Type | Notes |
|---|---|---|
| `FIRST_NAMES` | `tuple[str, ...]` | Single unisex list — no gendered split. MUST have at least 10 entries (no upper bound); not constrained to a multiple of 6 (unlike career skill tables, which the `Career.__post_init__` invariant fixes at exactly 6). Proper-cased words; intra-list duplicate entries are permitted (affect draw probability only). |
| `LAST_NAMES` | `tuple[str, ...]` | Independent list, combined with a `FIRST_NAMES` draw to form a full name. Same size/content constraints as `FIRST_NAMES`. |
| `generate_name(roller: DiceRoller) -> str` | function | Makes exactly two independent calls, `roller.roll(len(FIRST_NAMES))` and `roller.roll(len(LAST_NAMES))` — never a single shared roll or index — and returns `f"{first} {last}"`. |

No relationships, no state transitions — this is a static data source read once per character,
exactly like `Career.service_skills` etc.

## Derived display values (formatter, not stored on Character)

These are computed in `format_character` at render time and are not new `Character` fields — they
are folded views over existing data, matching FR-005/FR-006/FR-007:

| Value | Derivation |
|---|---|
| Funds | `sum(b.cash_amount for b in character.benefits if b.kind == "cash")`, formatted `Cr{amount:,}` (→ `"Cr0"` when the sum is 0). |
| Skills line | `sorted(character.skills.items())` → `"<Name>-<Level>"` joined by `", "` (unchanged from current formatter). |
| Equipment line | `[b.material_name for b in character.benefits if b.kind == "material"]` joined by `", "`; the line is omitted entirely when this list is empty. |

## Removed from output (not removed from the model)

Per FR-009, these existing `Character` fields/derivations are no longer rendered by
`format_character`, but nothing is deleted from `models.py`/`generator.py`:

- Per-characteristic breakdown (`characteristics`, pseudohex-per-stat)
- Cash/material benefit type labels (folded into funds + equipment instead)
- `pension`
- `drafted` / "(Drafted)" annotation
