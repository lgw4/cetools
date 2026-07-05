# Data Model: Navy Character Generator

**Phase**: 1 | **Date**: 2026-06-17 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)
**Rules Sources**:
- https://evolvedexperiment.github.io/cepheus-srd/character-creation.html#career-tables
- https://evolvedexperiment.github.io/cepheus-srd/introduction.html#pseudo-hexadecimal-notation
- https://evolvedexperiment.github.io/cepheus-srd/introduction.html#important-terms

> **Terminology note**: All terms follow the Cepheus Engine SRD canonical definitions. See [research.md — Canonical Terminology](research.md#canonical-cepheus-engine-terminology). Key rules: use "characteristic score" (not "stat"), "characteristic modifier" (not "modifier"), "DM" for dice modifier, "2D6"/"1D6" in documentation, "Referee" (not "GM"), "Check" (not "roll" as a noun).

---

## Entities

### `Characteristic`

One of the six basic character traits (Strength, Dexterity, Endurance, Intelligence, Education, Social Standing). The characteristic score is an integer (minimum 0, typical range 2–12 at creation from 2D6, may increase or decrease through career events and aging).

| Field | Type | Notes |
|-------|------|-------|
| `name` | `str` | Full name: "Strength", "Dexterity", "Endurance", "Intelligence", "Education", "Social Standing" |
| `value` | `int` | The characteristic score; non-negative; no hard cap but pseudo-hex displays max Z (33) |
| `modifier` | `int` | The characteristic modifier; derived from score per SRD table below |

Characteristic modifier table (from SRD https://evolvedexperiment.github.io/cepheus-srd/):

| Score | Modifier |
|-------|---------|
| 0–2 | -2 |
| 3–5 | -1 |
| 6–8 | +0 |
| 9–11 | +1 |
| 12–14 | +2 |
| 15–17 | +3 |
| 18–20 | +4 |
| 21–23 | +5 |
| 24–26 | +6 |
| 27–29 | +7 |
| 30–32 | +8 |
| 33+ | +9 |

Floor is -2 (not -3). Table extends to +9 to cover pseudo-hex values up to 33.

---

### `Skill`

A named capability at a numeric level. Multiple rolls in the same skill stack: each additional roll adds 1 to the level (Level 0 → Level 1 → Level 2, etc.).

| Field | Type | Notes |
|-------|------|-------|
| `name` | `str` | e.g., "Gunnery", "Navigation", "Zero-G" |
| `level` | `int` | Minimum 0; starts at 0 on first acquisition |

Characteristic boost results (e.g., "+1 Str" from Personal Development table) are applied directly to the character's characteristic value, not stored as a skill.

---

### `Benefit`

A mustering-out reward received at career end.

| Field | Type | Notes |
|-------|------|-------|
| `kind` | `Literal["cash", "material"]` | Determines which table was rolled |
| `cash_amount` | `int \| None` | Credits; set if `kind == "cash"` |
| `material_name` | `str \| None` | e.g., "Low Passage", "Weapon", "+1 Edu"; set if `kind == "material"` |

---

### `Term`

A 4-year period of career service.

| Field | Type | Notes |
|-------|------|-------|
| `number` | `int` | 1-indexed |
| `survived` | `bool` | False if survival roll failed (character died) |
| `commissioned` | `bool` | True if commission roll succeeded during this term |
| `promoted` | `bool` | True if advancement roll succeeded during this term |
| `rank_at_end` | `int` | Character's rank after this term (0–6) |
| `skills_gained` | `list[str]` | Skill names gained this term (before stacking resolution) |

---

### `Character`

The generated persona. Represents the complete output of a successful generation run.

| Field | Type | Notes |
|-------|------|-------|
| `characteristics` | `dict[str, int]` | Keys: stat names; values: current values after career events and aging |
| `upp` | `str` | 6-character pseudo-hex string, derived on output |
| `age` | `int` | 18 + (4 × terms_served) |
| `career` | `str` | Career name (always "Navy" in MVP) |
| `rank` | `int` | Final rank (0–6) |
| `rank_title` | `str` | Human-readable rank title |
| `terms_served` | `int` | Number of completed terms |
| `skills` | `dict[str, int]` | Fully stacked skill name → level mapping |
| `benefits` | `list[Benefit]` | Ordered list of mustering-out benefits received |
| `pension` | `int \| None` | Annual pension in Credits (None if fewer than 5 terms) |
| `terms` | `list[Term]` | Full term-by-term history (for formatted output) |

---

### `GenerationFailure`

Represents a failed generation (enlistment rejected or character died during career).

| Field | Type | Notes |
|-------|------|-------|
| `reason` | `str` | Human-readable cause (e.g., "Navy enlistment failed", "Killed in action during term 2 survival check") |
| `exit_code` | `int` | Always 1 for MVP |

---

## Career Data Interface

### `RankEntry` (frozen dataclass)

| Field | Type | Notes |
|-------|------|-------|
| `rank` | `int` | Rank number (0–6) |
| `title` | `str` | Human-readable title |
| `bonus_skills` | `tuple[str, ...]` | Skills granted automatically on promotion to this rank (may be empty) |

### `Career` (frozen dataclass — extensibility interface)

All career variation lives in this struct. The generation engine uses only these fields; no career-specific logic is hardcoded in the engine.

| Field | Type | Notes |
|-------|------|-------|
| `name` | `str` | Career identifier |
| `qualification_stat` | `str` | Stat name used for enlistment |
| `qualification_target` | `int` | Minimum 2D6 roll (after modifier) to qualify |
| `survival_stat` | `str` | Stat name used for survival check |
| `survival_target` | `int` | Minimum 2D6 roll to survive |
| `commission_stat` | `str \| None` | Stat for commission; None if career has no commission track |
| `commission_target` | `int \| None` | Minimum roll for commission |
| `advancement_stat` | `str \| None` | Stat for advancement; None if no advancement track |
| `advancement_target` | `int \| None` | Minimum roll for advancement |
| `reenlistment_target` | `int` | Minimum roll to re-enlist |
| `service_skills` | `tuple[str, ...]` | 6-entry table (index 0–5, roll 1D6-1) |
| `personal_development` | `tuple[str, ...]` | 6-entry table; entries prefixed "+1 " are stat boosts |
| `specialist_skills` | `tuple[str, ...]` | 6-entry table |
| `advanced_education` | `tuple[str, ...]` | 6-entry table (accessible only with Edu 8+) |
| `ranks` | `tuple[RankEntry, ...]` | One entry per rank level (0-indexed) |
| `cash_benefits` | `tuple[int, ...]` | 7-entry cash table (index 0–6, roll 1D6-1) |
| `material_benefits` | `tuple[str, ...]` | 7-entry material table (index 0–6, roll 1D6-1) |

### Navy Career Data (concrete instance)

```
Career(
    name="Navy",
    qualification_stat="Intelligence",
    qualification_target=6,
    survival_stat="Intelligence",
    survival_target=5,
    commission_stat="Social Standing",
    commission_target=7,
    advancement_stat="Education",
    advancement_target=6,
    reenlistment_target=5,
    service_skills=("Comms", "Engineering", "Gun Combat", "Gunnery", "Melee Combat", "Vehicle"),
    personal_development=("+1 Str", "+1 Dex", "+1 End", "+1 Int", "+1 Edu", "Melee Combat"),
    specialist_skills=("Gravitics", "Jack o' Trades", "Melee Combat", "Navigation", "Leadership", "Piloting"),
    advanced_education=("Advocate", "Computer", "Engineering", "Medicine", "Navigation", "Tactics"),
    ranks=(
        RankEntry(0, "Starman", ("Zero-G",)),      # Zero-G-1 granted at enlistment
        RankEntry(1, "Midshipman", ()),
        RankEntry(2, "Lieutenant", ()),
        RankEntry(3, "Lt Commander", ("Tactics",)), # Tactics-1 on promotion to Rank 3
        RankEntry(4, "Commander", ()),
        RankEntry(5, "Captain", ()),
        RankEntry(6, "Commodore", ()),
    ),
    cash_benefits=(1000, 5000, 10000, 10000, 20000, 50000, 50000),
    material_benefits=("Low Passage", "+1 Edu", "Weapon", "Mid Passage", "+1 Soc", "High Passage", "Explorers' Society"),
)
```

---

## Generation State Machine

```
START
  → Roll 6 characteristics (2D6 each)
  → Assign 3 background skills at Level 0
  → Attempt Navy qualification (2D6 + Int modifier ≥ 6)
      FAIL → GenerationFailure("Navy enlistment failed")
      PASS → Grant Rank 0 (Starman), grant Zero-G-1, set age=18
  → LOOP (each term, max 7; mandatory 8th if natural 12 on re-enlistment):
      → First term: grant all 6 Service Skills at Level 0 (basic training)
      → Roll survival (2D6 + Int modifier ≥ 5)
          FAIL → GenerationFailure("Killed in action during term N")
      → If Rank == 0: roll commission (2D6 + Soc modifier ≥ 7)
          PASS → Rank = 1 (Midshipman); roll advancement next
      → If Rank ≥ 1: roll advancement (2D6 + Edu modifier ≥ 6)
          PASS → Rank += 1 (cap 6); grant rank bonus skills if any
      → Roll 1 skill (2 if neither commission nor advancement roll was attempted)
          (choose Personal Development, Service Skills, Specialist Skills, or
           Advanced Education if Edu ≥ 8)
      → Aging check if age ≥ 34 (i.e., term ≥ 4):
          roll 2D6 - terms_served → apply aging table to physical characteristic scores
      → Roll re-enlistment (2D6 ≥ 5)
          FAIL → exit loop (muster out)
          PASS on natural 12 at term 7 → mandatory term 8
          PASS otherwise → continue (or muster out voluntarily at 7 terms)
      → age += 4; terms_served += 1
  → Mustering-out phase:
      → total_rolls = terms_served + rank_bonus (O4=+1, O5=+2, O6=+3)
      → max 3 cash rolls; remainder must be material
      → Apply material benefit stat boosts to characteristics
  → Calculate pension (terms_served ≥ 5)
  → Encode UPP
  → Return Character
```

---

## Pseudo-Hexadecimal Encoding

The `pseudohex` module (name matches SRD's "pseudohexadecimal") exposes:

- `to_pseudohex(value: int) -> str` — maps characteristic score 0–33 to its pseudo-hexadecimal character; raises `ValueError` for out-of-range values
- `from_pseudohex(char: str) -> int` — inverse; raises `ValueError` for invalid characters
- `encode_upp(scores: dict[str, int]) -> str` — encodes all six characteristic scores in order into a 6-character UPP string

UPP order (SRD canonical): Strength, Dexterity, Endurance, Intelligence, Education, Social Standing.
