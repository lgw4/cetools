# Data Model: Aerospace System Defense Career

The `Career` dataclass in `src/cetools/engine/careers/base.py` requires zero structural changes.
`AEROSPACE_CAREER` is a new frozen-dataclass instance with the following field values.

## AEROSPACE_CAREER

```python
# src/cetools/engine/careers/aerospace.py

AEROSPACE_CAREER = Career(
    name="Aerospace System Defense",
    qualification_stat="Endurance",
    qualification_target=5,
    survival_stat="Dexterity",
    survival_target=5,
    commission_stat="Education",
    commission_target=6,
    advancement_stat="Education",
    advancement_target=7,
    reenlistment_target=5,
    service_skills=(
        "Electronics",
        "Gun Combat",
        "Gunnery",
        "Melee Combat",
        "Survival",
        "Aircraft",
    ),
    personal_development=(
        "+1 Str",
        "+1 Dex",
        "+1 End",
        "Athletics",
        "Melee Combat",
        "Vehicle",
    ),
    specialist_skills=(
        "Comms",
        "Gravitics",
        "Gun Combat",
        "Gunnery",
        "Recon",
        "Piloting",
    ),
    advanced_education=(
        "Advocate",
        "Computer",
        "Jack o' Trades",
        "Medicine",
        "Leadership",
        "Tactics",
    ),
    ranks=(
        RankEntry(0, "Airman",          ("Aircraft",)),
        RankEntry(1, "Flight Officer",  ()),
        RankEntry(2, "Flight Lieutenant", ()),
        RankEntry(3, "Squadron Leader", ("Leadership",)),
        RankEntry(4, "Wing Commander",  ()),
        RankEntry(5, "Group Captain",   ()),
        RankEntry(6, "Air Commodore",   ()),
    ),
    cash_benefits=(1000, 5000, 10000, 10000, 20000, 50000, 50000),
    material_benefits=(
        "Low Passage",
        "+1 Edu",
        "Weapon",
        "Mid Passage",
        "Weapon",
        "High Passage",
        "+1 Soc",
    ),
)
```

## Field-Level Notes

| Field | Value | SRD Source |
|-------|-------|------------|
| `qualification_stat` | `"Endurance"` | FR-002 |
| `qualification_target` | `5` | FR-002 |
| `survival_stat` | `"Dexterity"` | FR-002 |
| `survival_target` | `5` | FR-002 |
| `commission_stat` | `"Education"` | FR-002 |
| `commission_target` | `6` | FR-002 |
| `advancement_stat` | `"Education"` | FR-002 |
| `advancement_target` | `7` | FR-002 |
| `reenlistment_target` | `5` | FR-002 |
| `ranks[0].bonus_skills` | `("Aircraft",)` | FR-003 — "Aircraft-1" at Airman |
| `ranks[3].bonus_skills` | `("Leadership",)` | FR-003 — "Leadership-1" at Squadron Leader |
| `material_benefits[4]` | `"Weapon"` | FR-005 — roll 5 = Weapon (not High Passage) |
| `material_benefits[5]` | `"High Passage"` | FR-005 — roll 6 = High Passage |
| `material_benefits[6]` | `"+1 Soc"` | FR-005 — roll 7 = +1 Soc |

## Registry Change

`registry.py` adds one key and corrects `DRAFT_TABLE`:

```python
from cetools.engine.careers.aerospace import AEROSPACE_CAREER

CAREER_REGISTRY: dict[str, Career] = {
    "aerospace system defense": AEROSPACE_CAREER,
    "navy": NAVY_CAREER,
    "scout": SCOUT_CAREER,
}

DRAFT_TABLE: tuple[str, ...] = (
    "aerospace system defense",  # roll 1 — was "navy", corrected per FR-008
    "navy",
    "navy",
    "navy",
    "scout",
    "navy",
)
```
