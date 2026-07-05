# Data Model: Marine Career

The `Career` dataclass in `src/cetools/engine/careers/base.py` requires zero structural changes.
`MARINE_CAREER` is a new frozen-dataclass instance with the following field values.

## MARINE_CAREER

```python
# src/cetools/engine/careers/marine.py

from cetools.engine.careers.base import Career, RankEntry

MARINE_CAREER = Career(
    name="Marine",
    qualification_stat="Intelligence",
    qualification_target=6,
    survival_stat="Endurance",
    survival_target=6,
    commission_stat="Education",
    commission_target=6,
    advancement_stat="Social Standing",
    advancement_target=7,
    reenlistment_target=6,
    service_skills=(
        "Comms",
        "Demolitions",
        "Gun Combat",
        "Gunnery",
        "Melee Combat",
        "Battle Dress",
    ),
    personal_development=(
        "+1 Str",
        "+1 Dex",
        "+1 End",
        "+1 Int",
        "+1 Edu",
        "Melee Combat",
    ),
    specialist_skills=(
        "Electronics",
        "Gun Combat",
        "Melee Combat",
        "Survival",
        "Recon",
        "Vehicle",
    ),
    advanced_education=(
        "Advocate",
        "Computer",
        "Gravitics",
        "Medicine",
        "Navigation",
        "Tactics",
    ),
    ranks=(
        RankEntry(0, "Trooper",    ("Zero-G",)),
        RankEntry(1, "Lieutenant", ()),
        RankEntry(2, "Captain",    ()),
        RankEntry(3, "Major",      ("Tactics",)),
        RankEntry(4, "Lt Colonel", ()),
        RankEntry(5, "Colonel",    ()),
        RankEntry(6, "Brigadier",  ()),
    ),
    cash_benefits=(1000, 5000, 10000, 10000, 20000, 50000, 50000),
    material_benefits=(
        "Low Passage",
        "+1 Edu",
        "Weapon",
        "Mid Passage",
        "+1 Soc",
        "High Passage",
        "Explorers' Society",
    ),
)
```

## Field-Level Notes

| Field | Value | SRD Source |
|-------|-------|------------|
| `qualification_stat` | `"Intelligence"` | FR-002 |
| `qualification_target` | `6` | FR-002 |
| `survival_stat` | `"Endurance"` | FR-002 |
| `survival_target` | `6` | FR-002 |
| `commission_stat` | `"Education"` | FR-002 |
| `commission_target` | `6` | FR-002 |
| `advancement_stat` | `"Social Standing"` | FR-002 — first career using this advancement stat (validates engine's stat-agnostic advancement logic per User Story 2) |
| `advancement_target` | `7` | FR-002 |
| `reenlistment_target` | `6` | FR-002 |
| `ranks[0].bonus_skills` | `("Zero-G",)` | FR-003 — SRD "Zero-G-1" at Trooper; bare name + engine-applied level 1, matching `NAVY_CAREER.ranks[0]` convention |
| `ranks[3].bonus_skills` | `("Tactics",)` | FR-003 — SRD "Tactics-1" at Major |
| `material_benefits[4]` | `"+1 Soc"` | FR-005 — roll 5 = +1 Soc (matches Navy's roll-5 "+1 Soc"; differs from Aerospace's roll-5 "Weapon") |
| `material_benefits[6]` | `"Explorers' Society"` | FR-005 — exact spelling (plural possessive) matches `SCOUT_CAREER.material_benefits[4]`; supersedes the singular "Explorer's Society" spelling used in earlier drafts |

## Registry Change

`registry.py` adds one key and corrects `DRAFT_TABLE` index 1:

```python
from cetools.engine.careers.aerospace import AEROSPACE_CAREER
from cetools.engine.careers.marine import MARINE_CAREER
from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.careers.scout import SCOUT_CAREER

CAREER_REGISTRY: dict[str, Career] = {
    "aerospace system defense": AEROSPACE_CAREER,
    "marine": MARINE_CAREER,
    "navy": NAVY_CAREER,
    "scout": SCOUT_CAREER,
}

DRAFT_TABLE: tuple[str, ...] = (
    "aerospace system defense",
    "marine",  # roll 2 — was "navy", corrected per FR-008
    "navy",
    "navy",
    "scout",
    "navy",
)
```

## Validation

`Career.__post_init__` (unchanged, `base.py`) validates `MARINE_CAREER` at import time:

- `qualification_stat="Intelligence"` and `survival_stat="Endurance"` are members of
  `STAT_NAMES` — pass.
- `commission_stat="Education"` and `advancement_stat="Social Standing"` are members of
  `STAT_NAMES` — pass.
- All four skill tables (`service_skills`, `personal_development`, `specialist_skills`,
  `advanced_education`) have exactly 6 entries — pass.
- `ranks` has 7 entries (within the 1–7 bound) with consecutive indices 0–6 — pass.

No new validation logic is needed; `MARINE_CAREER` satisfies every existing invariant the same
way `NAVY_CAREER`, `SCOUT_CAREER`, and `AEROSPACE_CAREER` do.
