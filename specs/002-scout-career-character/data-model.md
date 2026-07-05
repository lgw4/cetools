# Data Model: Scout Career & Career Selection Flag

**Feature**: 002-scout-career-character | **Date**: 2026-06-18

---

## Existing Entities (unchanged)

### `Career` (frozen dataclass — `src/cetools/engine/careers/base.py`)

No new fields are added. All Scout-specific values fit the existing schema.

| Field | Type | Scout value |
|-------|------|-------------|
| `name` | `str` | `"Scout"` |
| `qualification_stat` | `str` | `"Intelligence"` |
| `qualification_target` | `int` | `6` |
| `survival_stat` | `str` | `"Endurance"` |
| `survival_target` | `int` | `7` |
| `commission_stat` | `str \| None` | `None` |
| `commission_target` | `int \| None` | `None` |
| `advancement_stat` | `str \| None` | `None` |
| `advancement_target` | `int \| None` | `None` |
| `reenlistment_target` | `int` | `6` |
| `service_skills` | `tuple[str, ...]` | `("Comms", "Electronics", "Gun Combat", "Gunnery", "Recon", "Piloting")` |
| `personal_development` | `tuple[str, ...]` | `("+1 Str", "+1 Dex", "+1 End", "Jack o' Trades", "+1 Edu", "Melee Combat")` |
| `specialist_skills` | `tuple[str, ...]` | `("Engineering", "Gunnery", "Demolitions", "Navigation", "Medicine", "Vehicle")` |
| `advanced_education` | `tuple[str, ...]` | `("Advocate", "Computer", "Linguistics", "Medicine", "Navigation", "Tactics")` |
| `ranks` | `tuple[RankEntry, ...]` | Single entry: `RankEntry(0, "Scout", ("Piloting",))` |
| `cash_benefits` | `tuple[int, ...]` | `(1000, 5000, 10000, 10000, 20000, 50000, 50000)` |
| `material_benefits` | `tuple[str, ...]` | `("Low Passage", "+1 Edu", "Weapon", "Mid Passage", "Explorers' Society", "Courier Vessel")` |

### `RankEntry` (frozen dataclass — `src/cetools/engine/careers/base.py`)

Unchanged. Scout uses a single entry: `RankEntry(rank=0, title="Scout", bonus_skills=("Piloting",))`.

The rank bonus is applied by the existing `_grant_rank_bonus` call in `generate_character` at rank 0 before term 1. Since basic training grants `Piloting` at level 0 (via `service_skills`), the rank-0 bonus raises it to level 1.

---

## Updated Entity

### `Character` (dataclass — `src/cetools/engine/models.py`)

One new field added:

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `drafted` | `bool` | `False` | True when career was assigned via the draft table (drives formatter output per FR-011) |

All other fields are unchanged.

---

## New Entities

### `SCOUT_CAREER` (module-level constant — `src/cetools/engine/careers/scout.py`)

A `Career` instance constructed with the values from the table above. Exported as the module's public symbol.

### `CAREER_REGISTRY` (module-level constant — `src/cetools/engine/careers/registry.py`)

```python
CAREER_REGISTRY: dict[str, Career] = {
    "navy": NAVY_CAREER,
    "scout": SCOUT_CAREER,
}
```

Keys are canonical lowercase career names. This is the single source of truth for:
- CLI validation of `--career` input (FR-007)
- Draft table career resolution (FR-010)
- The valid-careers list in error messages (FR-012)

### `DRAFT_TABLE` (module-level constant — `src/cetools/engine/careers/registry.py`)

```python
DRAFT_TABLE: tuple[str, ...] = ("navy", "navy", "navy", "navy", "scout", "navy")
```

Six-entry tuple indexed by `(1D6 roll - 1)`. Maps draft roll 5 to `"scout"`, all others to `"navy"`, per SRD.

---

## State Transitions

### Character Generation Flow

```text
CLI invocation
    │
    ├── --career <name>  →  normalize  →  validate vs CAREER_REGISTRY
    │                                         │
    │                                    generate_career_character(career)
    │                                         │
    │                                    roll_until_qualified(career, roller)
    │                                         │  loop until chars[qual_stat] >= qual_target
    │                                         ↓
    │                                    generate_character(career, roller,
    │                                        preset_characteristics=chars,
    │                                        bypass_qualification=True,
    │                                        hard_max_terms=True,
    │                                        drafted=False)
    │
    └── (no --career)    →  draft_character(roller)
                                  │
                             roll 1D6 → DRAFT_TABLE[roll-1] → career_name
                                  │
                             CAREER_REGISTRY[career_name] → career
                                  │  (if not found → GenerationFailure, exit 1)
                                  ↓
                             generate_career_character(career, roller,
                                 drafted=True)
                                  │  (calls roll_until_qualified, then generate_character
                                  │   with preset_characteristics, bypass_qualification=True,
                                  │   hard_max_terms=True, drafted=True — identical to
                                  │   the --career path above, just with drafted=True)
```

### Validation Rules

- `--career` input: strip whitespace → lowercase → must be a key in `CAREER_REGISTRY`; error on miss.
- Draft result: `DRAFT_TABLE[roll-1]` string must be a key in `CAREER_REGISTRY`; `GenerationFailure` on miss.
- `Character.drafted` is set once at construction and not mutated thereafter; formatter reads it once. (`Character` is a plain `@dataclass`, not frozen; this is a convention, not a language-enforced constraint.)

---

## Skill Interaction Notes

- Basic training (term 1): all `service_skills` granted at level 0 via existing engine code.
- Rank-0 bonus (`Piloting`): applied by `_grant_rank_bonus` before term 1. Since `Piloting` is in `service_skills`, basic training sets it to 0, then the rank bonus raises it to 1. Net result: `Piloting-1` after term 1 basic training, matching the SRD Pilot-1 outcome.
- Skill table selection: `_roll_skill` selects from up to 4 tables (advanced education excluded when `Education < 8`). Scout always has 3 available tables minimum.
- Material benefits: `Explorers' Society` and `Courier Vessel` are stored as `Benefit(kind="material", material_name=...)` with no mechanical effect applied (deferred per spec assumptions).
