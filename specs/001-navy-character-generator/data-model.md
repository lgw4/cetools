# Data Model: Navy Character Generator

All entities live under `src/cetools/navy/`. SRD source: https://cepheus-srd.opengamingnetwork.com/cepheus-engine-srd/cepheus-engine-character-creation/

---

## Entities

### Character

The generated person. The top-level output of the generator.

| Field | Type | Description |
|---|---|---|
| `characteristics` | `dict[str, int]` | Six-entry dict keyed `STR`, `DEX`, `END`, `INT`, `EDU`, `SOC`; each value is 2–15 |
| `terms` | `int` | Terms of Navy service completed (1–7) |
| `age` | `int` | 18 + (4 × terms); purely derived, no aging effects applied |
| `rank` | `int` | Final Navy rank (0–6) |
| `skills` | `dict[str, int]` | Skill name → level; duplicates combined into higher level |
| `benefits` | `list[Benefit]` | Mustering-out benefits in acquisition order |
| `career_history` | `list[CareerTerm]` | Per-term record; excluded from JSON output |

**Derived properties**:
- `upp: str` — six-character pseudo-hexadecimal UPP string (e.g. `"777777"`). Each characteristic value maps to a pseudo-hex character per the CE SRD table (see research.md §2). The sequence is `0–9 A B C D E F G H J K L M N P Q R S T U V W X Y Z`; letters `I` and `O` are skipped to avoid confusion with `1` and `0`. In practice, initial 2d6 rolls produce values 2–12 (`2`–`C`); Personal Development can push values higher.
- `rank_title: str` — Navy rank title from the SRD rank table (e.g. `"Starman"`, `"Lieutenant"`).

**JSON output schema** (per FR-010):

```json
{
  "upp": "787977",
  "age": 26,
  "rank": "Lieutenant",
  "terms": 2,
  "skills": {"Pilot": 1, "Gun Combat": 1},
  "benefits": [
    {"type": "cash", "value": 5000},
    {"type": "material", "value": "Weapon"}
  ]
}
```

`rank` is the rank title string. For rank 0 (Starman), the value is `"Starman"` (not empty string; see research.md §11-C). `career_history` is intentionally excluded.

---

### CareerTerm

A four-year period of Navy service. Records outcomes for one term only; does not hold character state.

| Field | Type | Description |
|---|---|---|
| `term_number` | `int` | 1-based index of this term (1–7) |
| `survived` | `bool` | True if survival roll passed |
| `commissioned` | `bool` | True if a commission roll was made and succeeded this term |
| `promoted` | `bool` | True if an advancement roll was made and succeeded this term |
| `skills_gained` | `list[str]` | Skill names (or characteristic labels like `"+1 STR"`) gained this term |

A term where `survived = False` is the last term in the career.

---

### Benefit

A single mustering-out reward.

| Field | Type | Constraint |
|---|---|---|
| `type` | `str` | `"cash"` or `"material"` |
| `value` | `int \| str` | Credits (int) for cash; SRD benefit name (str) for material |

Valid material `value` strings (from SRD Material Benefits table):
`"Low Passage"`, `"+1 Edu"`, `"Weapon"`, `"Mid Passage"`, `"+1 Soc"`, `"High Passage"`, `"Explorers' Society"`

---

## SRD Constants (`tables.py`)

The following constants are derived entirely from the CE SRD. All must be importable and testable without invoking the CLI (FR-011, FR-012).

### Pseudo-Hex Encoding

```python
PSEUDO_HEX = "0123456789ABCDEFGHJKLMNPQRSTUVWXYZ"

def to_pseudo_hex(value: int) -> str:
    idx = min(value, len(PSEUDO_HEX) - 1)
    return PSEUDO_HEX[idx]
```

Letters `I` and `O` are omitted from `PSEUDO_HEX` (see research.md §2). This string is the canonical implementation source; all UPP encoding must use it.

### Characteristic Modifier Function

```python
def characteristic_modifier(value: int) -> int:
    # Returns DM for the given raw characteristic score.
    # Thresholds: ≤2→-2, ≤5→-1, ≤8→0, ≤11→+1, ≤14→+2, ≤17→+3, ≤20→+4, ...
```

### Navy Career Checks

```python
NAVY_QUALIFICATION = ("INT", 6)   # (characteristic_key, target)
NAVY_SURVIVAL     = ("INT", 5)
NAVY_COMMISSION   = ("SOC", 7)
NAVY_ADVANCEMENT  = ("EDU", 6)
NAVY_REENLISTMENT = 5             # flat 2d6 target, no characteristic
```

### Draft Table

```python
DRAFT_TABLE = {
    1: "Aerospace System Defense",
    2: "Marine",
    3: "Maritime System Defense",
    4: "Navy",
    5: "Scout",
    6: "Surface System Defense",
}
NAVY_DRAFT_RESULT = 4  # the only draft result that produces a Navy character
```

### Rank Table

```python
NAVY_RANKS = {
    0: "Starman",
    1: "Midshipman",
    2: "Lieutenant",
    3: "Lt Commander",
    4: "Commander",
    5: "Captain",
    6: "Commodore",
}

NAVY_RANK_BONUS_SKILLS = {
    0: ("Zero-G", 1),      # granted on career entry
    3: ("Tactics", 1),     # granted when promoted to Lt Commander
}
```

### Skill Tables

```python
NAVY_PERSONAL_DEVELOPMENT = {
    1: ("+1", "STR"),  # characteristic increase
    2: ("+1", "DEX"),
    3: ("+1", "END"),
    4: ("+1", "INT"),
    5: ("+1", "EDU"),
    6: ("skill", "Melee Combat"),
}

NAVY_SERVICE_SKILLS = {
    1: "Comms",
    2: "Engineering",
    3: "Gun Combat",
    4: "Gunnery",
    5: "Melee Combat",
    6: "Vehicle",
}

NAVY_SPECIALIST_SKILLS = {
    1: "Gravitics",
    2: "Jack o' Trades",
    3: "Melee Combat",
    4: "Navigation",
    5: "Leadership",
    6: "Piloting",
}

NAVY_ADVANCED_EDUCATION = {
    1: "Advocate",
    2: "Computer",
    3: "Engineering",
    4: "Medicine",
    5: "Navigation",
    6: "Tactics",
}
NAVY_ADVANCED_EDUCATION_MIN_EDU = 8
```

### Mustering-Out Tables

```python
NAVY_CASH_BENEFITS = {
    1: 1_000,
    2: 5_000,
    3: 10_000,
    4: 10_000,
    5: 20_000,
    6: 50_000,
    7: 50_000,
}

NAVY_MATERIAL_BENEFITS = {
    1: "Low Passage",
    2: "+1 Edu",
    3: "Weapon",
    4: "Mid Passage",
    5: "+1 Soc",
    6: "High Passage",
    7: "Explorers' Society",
}

NAVY_MUSTEROUT_RANK_BONUS = {
    4: 1,   # Commander: +1 roll
    5: 2,   # Captain:   +2 rolls
    6: 3,   # Commodore: +3 rolls
}
NAVY_MAX_CASH_ROLLS = 3
NAVY_MATERIAL_DM_MIN_RANK = 5   # rank 5+ gets +1 on material rolls
```

---

## State Transitions

### Career Flow

```
START
  └─ Roll 6 characteristics (2d6 each)
  └─ Roll qualification (INT 6+)
       ├─ Pass → enter Navy at Rank 0, gain Zero-G 1
       └─ Fail → roll draft (1d6)
                  ├─ Result = 4 → enter Navy at Rank 0, gain Zero-G 1
                  └─ Result ≠ 4 → restart (re-roll characteristics)
                                  [terminate after 1,000 restarts with error]

TERM LOOP (term 1..7):
  └─ Roll 1d6 on chosen skill table → apply result
  └─ Roll survival (INT 5+)
       └─ Fail → career ends; muster out
  └─ If rank = 0: roll commission (SOC 7+)
       └─ Pass → rank = 1; gain 1 extra skill roll; apply rank bonus if any
  └─ If 1 ≤ rank ≤ 5: roll advancement (EDU 6+)
       └─ Pass → rank += 1; gain 1 extra skill roll; apply rank bonus if any
  └─ If term ≥ 5 (i.e., after 4th term complete): roll re-enlistment (2d6 ≥ 5)
       └─ Fail → career ends; muster out
  └─ If term = 7: career ends (cap); muster out

MUSTER OUT:
  └─ Compute total benefit rolls = terms + rank_bonus[rank]
  └─ Cap cash rolls at 3
  └─ Apply material DM (+1) if rank ≥ 5
  └─ Apply gambling DM (+1 cash rolls) if "Gambling" in skills
  └─ Roll and record each benefit
```

### Skill Merge Rule

When a skill name is gained and already present in the character's skill dict, increment the existing level by 1. When a skill name is gained and not present, add it at level 1. Rank bonus skills at level 1 follow the same merge rule (e.g., gaining Zero-G when Zero-G 1 already exists produces Zero-G 2).

Characteristic increases from Personal Development increment the corresponding value in `characteristics`. There is no cap beyond 15 (the highest value the modifier table addresses before repeating), but in practice rolls rarely exceed 12–13.
